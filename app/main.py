from pathlib import Path
import os
import re
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
    main_anchor: str = ""
    additional_anchors: list[str] = Field(default_factory=list)
    stack: list[str] = Field(default_factory=list)
    location: str = ""


def detect_source(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "linkedin.com" in domain:
        return "linkedin"
    return domain or "unknown"


def normalize_tavily_result(result: dict) -> dict:
    raw_title = result.get("title") or ""
    raw_content = result.get("content") or ""
    url = result.get("url") or ""

    return {
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
        "is_relevant": False,
        "relevance_reason": "",
    }


def contains_term(text: str, term: str) -> bool:
    normalized_term = term.strip().lower()
    if not normalized_term:
        return False

    normalized_text = text.lower()
    if re.fullmatch(r"[a-z0-9 ]+", normalized_term):
        pattern = r"\b" + re.escape(normalized_term) + r"\b"
        return re.search(pattern, normalized_text) is not None

    return normalized_term in normalized_text


def score_normalized_result(result: dict, request: SearchRequest) -> dict:
    search_text = " ".join(
        [
            result.get("title") or "",
            result.get("snippet") or "",
            result.get("url") or "",
            result.get("raw_title") or "",
            result.get("raw_content") or "",
        ]
    )
    matched_fields: list[str] = []
    missing_required_fields: list[str] = []
    score = 0.0

    if request.main_anchor.strip():
        if contains_term(search_text, request.main_anchor):
            score += 35
            matched_fields.append("position")
        else:
            missing_required_fields.append("position")

    additional_anchors = [item for item in request.additional_anchors if item.strip()]
    if additional_anchors:
        matched_additional = [
            item for item in additional_anchors if contains_term(search_text, item)
        ]
        if matched_additional:
            score += 20 * (len(matched_additional) / len(additional_anchors))
            matched_fields.append("additional_anchors")
        else:
            missing_required_fields.append("additional_anchors")

    stack_terms = [item for item in request.stack if item.strip()]
    if stack_terms:
        matched_stack = [item for item in stack_terms if contains_term(search_text, item)]
        if matched_stack:
            score += 25 * (len(matched_stack) / len(stack_terms))
            matched_fields.append("stack")
        else:
            missing_required_fields.append("stack")

    if request.location.strip():
        if contains_term(search_text, request.location):
            score += 10
            matched_fields.append("location")
        else:
            missing_required_fields.append("location")

    if result.get("source") == "linkedin":
        score += 5
        matched_fields.append("linkedin_source")

    completeness_checks = [
        result.get("name") and result.get("name") != "unknown",
        result.get("title") and result.get("title") != "unknown",
        result.get("url"),
        result.get("snippet"),
        result.get("source") and result.get("source") != "unknown",
    ]
    completeness = sum(1 for item in completeness_checks if item) / len(completeness_checks)
    if completeness:
        score += 5 * completeness
        matched_fields.append("data_completeness")

    is_relevant = not missing_required_fields
    result["score"] = min(100, round(score))
    result["is_relevant"] = is_relevant
    result["matched_fields"] = matched_fields
    result["missing_required_fields"] = missing_required_fields
    result["relevance_reason"] = (
        "Matched " + ", ".join(matched_fields) + "."
        if is_relevant
        else "Missing required fields: " + ", ".join(missing_required_fields) + "."
    )

    return result


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
    normalized_results = [
        score_normalized_result(normalize_tavily_result(result), request)
        for result in raw_results
    ]
    relevant_results = [
        result for result in normalized_results if result.get("is_relevant")
    ]

    return {
        "query": tavily_data.get("query", query),
        "results": raw_results,
        "normalized_results": normalized_results,
        "relevant_results": sorted(
            relevant_results,
            key=lambda result: result.get("score", 0),
            reverse=True,
        ),
        "counts": {
            "raw": len(raw_results),
            "normalized": len(normalized_results),
            "relevant": len(relevant_results),
        },
        "response_time": tavily_data.get("response_time"),
        "usage": tavily_data.get("usage"),
        "request_id": tavily_data.get("request_id"),
        "raw": tavily_data,
    }
