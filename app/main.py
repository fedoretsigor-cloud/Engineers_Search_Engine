from pathlib import Path
import os
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"

load_dotenv()

app = FastAPI(title="Engineers Search POC")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    max_results: int = Field(default=20, ge=1, le=20)
    linkedin_profiles_only: bool = False
    ukraine_linkedin_domain_only: bool = False


def detect_source(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "linkedin.com" in domain:
        return "linkedin"
    return domain or "unknown"


def is_linkedin_profile_url(url: str) -> bool:
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path_parts = [part for part in parsed_url.path.split("/") if part]

    is_linkedin_domain = domain == "linkedin.com" or domain.endswith(".linkedin.com")

    return is_linkedin_domain and len(path_parts) >= 2 and path_parts[0] == "in"


def is_ukraine_linkedin_profile_url(url: str) -> bool:
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path_parts = [part for part in parsed_url.path.split("/") if part]

    return domain == "ua.linkedin.com" and len(path_parts) >= 2 and path_parts[0] == "in"


def normalized_tavily_score(value: object) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0

    if score > 1:
        score = score / 100

    return min(1.0, max(0.0, score))


def apply_neutral_score(result: dict) -> dict:
    matched_fields: list[str] = []
    score = 0.0

    tavily_score = normalized_tavily_score(result.get("tavily_score"))
    if tavily_score:
        score += tavily_score * 80
        matched_fields.append("tavily_score")

    if is_linkedin_profile_url(result.get("url") or ""):
        score += 10
        matched_fields.append("linkedin_profile_url")

    completeness_checks = [
        result.get("title") and result.get("title") != "unknown",
        result.get("url"),
        result.get("snippet"),
        result.get("source") and result.get("source") != "unknown",
    ]
    completeness = sum(1 for item in completeness_checks if item) / len(completeness_checks)
    if completeness:
        score += completeness * 10
        matched_fields.append("data_completeness")

    result["score"] = min(100, round(score))
    result["is_relevant"] = True
    result["matched_fields"] = matched_fields
    result["missing_required_fields"] = []
    result["relevance_reason"] = (
        "Score signals: " + ", ".join(matched_fields) + "."
        if matched_fields
        else "Returned by Tavily for the submitted query."
    )

    return result


def normalize_tavily_result(result: dict) -> dict:
    raw_title = result.get("title") or ""
    raw_content = result.get("content") or ""
    url = result.get("url") or ""

    normalized_result = {
        "name": "unknown",
        "title": raw_title or "unknown",
        "url": url,
        "source": detect_source(url),
        "location": "unknown",
        "stack": [],
        "snippet": raw_content,
        "raw_title": raw_title,
        "raw_content": raw_content,
        "tavily_score": result.get("score"),
        "matched_fields": [],
        "missing_required_fields": [],
        "score": 0,
        "is_relevant": True,
        "relevance_reason": "Returned by Tavily for the submitted query.",
    }

    return apply_neutral_score(normalized_result)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "engineers-search-engine",
        "phase": "phase-1-poc",
    }


@app.post("/api/search")
async def search(request: SearchRequest) -> dict:
    api_key = os.getenv("TAVILY_API_KEY")
    query = request.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Search query is required.")

    if not api_key:
        raise HTTPException(status_code=503, detail="TAVILY_API_KEY is not configured.")

    payload = {
        "query": query,
        "search_depth": "basic",
        "topic": "general",
        "max_results": request.max_results,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
        "include_favicon": False,
        "include_domains": ["linkedin.com"],
        "include_usage": True,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                TAVILY_SEARCH_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Tavily search request failed.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Tavily search is unavailable.") from exc

    tavily_data = response.json()
    raw_results = tavily_data.get("results", [])
    normalized_results = [normalize_tavily_result(result) for result in raw_results]
    sorted_results = sorted(
        normalized_results,
        key=lambda result: result.get("score", 0),
        reverse=True,
    )
    displayed_results = sorted_results
    if request.linkedin_profiles_only:
        displayed_results = [
            result
            for result in displayed_results
            if is_linkedin_profile_url(result.get("url") or "")
        ]
    hidden_by_profile_filter = len(sorted_results) - len(displayed_results)

    before_ukraine_domain_filter = len(displayed_results)
    if request.ukraine_linkedin_domain_only:
        displayed_results = [
            result
            for result in displayed_results
            if is_ukraine_linkedin_profile_url(result.get("url") or "")
        ]
    hidden_by_ukraine_domain_filter = before_ukraine_domain_filter - len(displayed_results)

    return {
        "query": tavily_data.get("query", query),
        "results": raw_results,
        "normalized_results": sorted_results,
        "displayed_results": displayed_results,
        "relevant_results": displayed_results,
        "counts": {
            "raw": len(raw_results),
            "normalized": len(normalized_results),
            "displayed": len(displayed_results),
            "hidden_by_profile_filter": hidden_by_profile_filter,
            "hidden_by_ukraine_domain_filter": hidden_by_ukraine_domain_filter,
            "relevant": len(displayed_results),
        },
        "response_time": tavily_data.get("response_time"),
        "usage": tavily_data.get("usage"),
        "request_id": tavily_data.get("request_id"),
        "raw": tavily_data,
    }
