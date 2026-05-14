from pathlib import Path
import os
import re
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
QUERY_PLANNER_VERSION = "rule_based_v1"
QUERY_PLAN_MAX_RESULTS = 20
QUERY_PLAN_REPORTING_FIELDS = [
    "queries_total",
    "queries_succeeded",
    "queries_failed",
    "raw_total",
    "normalized_total",
    "unique_profiles",
    "duplicates_removed",
    "displayed",
    "hidden_by_profile_filter",
    "hidden_by_location_filter",
    "rescued_by_header_location",
    "hidden_by_negative_header_location",
    "weak_location_history_only",
    "unknown_non_country_domain_location",
    "location_filter_report",
    "query_contribution",
]

load_dotenv()

app = FastAPI(title="Engineers Search POC")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


CANONICAL_ROLE_FAMILIES = {
    "backend developer": "Backend Developer",
}
KNOWN_BACKEND_TECHNOLOGIES = {
    "java": "Java",
    "python": "Python",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "c#": "C#",
    "csharp": "C#",
    "go": "Go",
    "golang": "Go",
    "php": "PHP",
}
IMPLEMENTED_BACKEND_TECHNOLOGIES = {"Java"}
JAVA_STACK_VALUES = {
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "hibernate": "Hibernate",
    "kafka": "Kafka",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "aws": "AWS",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "microservices": "Microservices",
    "rest": "REST",
}
LOCATION_FILTER_CONFIG = {
    "ukraine": {
        "label": "Ukraine",
        "linkedin_domains": ["ua.linkedin.com"],
        "include_terms": [
            "Ukraine",
            "Kyiv",
            "Kiev",
            "Lviv",
            "Kharkiv",
            "Odesa",
            "Odessa",
            "Dnipro",
            "Vinnytsia",
            "Zaporizhzhia",
            "Chernivtsi",
            "Ternopil",
            "Ivano-Frankivsk",
        ],
        "negative_terms": [
            "Prague",
            "Praha",
            "Czechia",
            "Czech Republic",
        ],
    }
}
HEADER_LOCATION_SECTION_MARKERS = [
    "About",
    "Experience",
    "Education",
    "Licenses",
    "Certifications",
    "Skills",
    "Projects",
]
LOCATION_SIGNAL_STATUSES = [
    "country_domain",
    "rescued_header_location",
    "excluded_negative_header_location",
    "weak_history_only",
    "unknown_non_country_domain",
]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    max_results: int = Field(default=20, ge=1, le=20)
    linkedin_profiles_only: bool = False
    ukraine_linkedin_domain_only: bool = False


class StructuredSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_family: str | None = None
    technology: str | None = None
    stack: list[str] | None = None
    location: str | None = None
    linkedin_profiles_only: bool | None = None
    location_filter_enabled: bool | None = None


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


def linkedin_domain(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if domain.startswith("www."):
        return domain[4:]

    return domain


def location_filter_config_for(location: str) -> dict | None:
    return LOCATION_FILTER_CONFIG.get(location.strip().lower())


def is_country_linkedin_profile_url(url: str, location_config: dict) -> bool:
    return (
        is_linkedin_profile_url(url)
        and linkedin_domain(url) in location_config["linkedin_domains"]
    )


def compact_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def first_public_profile_text(raw_result: dict, normalized_result: dict) -> str:
    for source in (raw_result, normalized_result):
        for field in ("content", "snippet", "raw_content"):
            value = source.get(field)
            if value:
                return str(value)

    return str(normalized_result.get("title") or raw_result.get("title") or "")


def combined_public_profile_text(raw_result: dict, normalized_result: dict) -> str:
    return "\n".join(
        str(value or "")
        for value in [
            raw_result.get("content"),
            raw_result.get("snippet"),
            raw_result.get("raw_content"),
            normalized_result.get("snippet"),
            normalized_result.get("raw_content"),
            normalized_result.get("title"),
            raw_result.get("title"),
        ]
    )


def extract_header_location_text(raw_result: dict, normalized_result: dict) -> str:
    text = first_public_profile_text(raw_result, normalized_result).replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    if len(lines) > 1:
        header_lines: list[str] = []
        for line in lines:
            if any(
                line.lower() == marker.lower()
                for marker in HEADER_LOCATION_SECTION_MARKERS
            ):
                break

            header_lines.append(line)
            lowered_line = line.lower()
            if "connections" in lowered_line or "followers" in lowered_line:
                break

        return "\n".join(header_lines).strip()

    one_line = compact_spaces(text)
    if not one_line:
        return ""

    marker_pattern = (
        r"\b("
        + "|".join(re.escape(marker) for marker in HEADER_LOCATION_SECTION_MARKERS)
        + r")\b"
    )
    marker_match = re.search(marker_pattern, one_line, flags=re.IGNORECASE)
    if marker_match:
        return one_line[: marker_match.start()].strip()

    return one_line


def match_location_terms(text: str, terms: list[str]) -> list[str]:
    lowered_text = text.lower()
    matched_terms: list[str] = []

    for term in terms:
        lowered_term = term.lower()
        pattern = r"(?<![a-z])" + re.escape(lowered_term) + r"(?![a-z])"
        if re.search(pattern, lowered_text):
            matched_terms.append(term)

    return matched_terms


def normalize_linkedin_profile_url(url: str) -> str | None:
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]

    path = parsed_url.path.rstrip("/")
    path_parts = [part for part in path.split("/") if part]
    is_linkedin_domain = domain == "linkedin.com" or domain.endswith(".linkedin.com")
    if not is_linkedin_domain or len(path_parts) < 2 or path_parts[0] != "in":
        return None

    return f"{domain}/{'/'.join(path_parts)}"


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


def result_completeness_key(result: dict) -> tuple[int, int]:
    title = result.get("title") or ""
    snippet = result.get("snippet") or ""
    return (len(title.strip()), len(snippet.strip()))


def choose_more_complete_result(current_result: dict, candidate_result: dict) -> dict:
    if result_completeness_key(candidate_result) > result_completeness_key(current_result):
        return candidate_result

    return current_result


def query_source_from_result(query_result: dict) -> dict:
    return {
        "id": query_result["query_id"],
        "category": query_result["category"],
        "query": query_result["query"],
    }


def append_unique_query_source(query_sources: list[dict], query_source: dict) -> None:
    if any(source["id"] == query_source["id"] for source in query_sources):
        return

    query_sources.append(query_source)


def empty_location_status_counts() -> dict[str, int]:
    return {status: 0 for status in LOCATION_SIGNAL_STATUSES}


def location_signal_for_result(
    raw_result: dict,
    normalized_result: dict,
    location_config: dict,
) -> dict:
    header_location_text = extract_header_location_text(raw_result, normalized_result)
    combined_text = combined_public_profile_text(raw_result, normalized_result)
    header_include_terms = match_location_terms(
        header_location_text,
        location_config["include_terms"],
    )
    header_negative_terms = match_location_terms(
        header_location_text,
        location_config["negative_terms"],
    )
    full_include_terms = match_location_terms(
        combined_text,
        location_config["include_terms"],
    )
    is_country_domain = is_country_linkedin_profile_url(
        normalized_result.get("url") or "",
        location_config,
    )

    if header_negative_terms:
        status = "excluded_negative_header_location"
    elif is_country_domain:
        status = "country_domain"
    elif header_include_terms:
        status = "rescued_header_location"
    elif full_include_terms:
        status = "weak_history_only"
    else:
        status = "unknown_non_country_domain"

    return {
        "status": status,
        "header_location_text": header_location_text,
        "location_signal_terms": sorted(
            set(header_include_terms + header_negative_terms + full_include_terms)
        ),
    }


def final_location_decision(location_signals: list[dict]) -> tuple[str, bool]:
    statuses = {signal["status"] for signal in location_signals}

    if "excluded_negative_header_location" in statuses:
        return "excluded_negative_header_location", False
    if "country_domain" in statuses:
        return "country_domain", True
    if "rescued_header_location" in statuses:
        return "rescued_header_location", True
    if "weak_history_only" in statuses:
        return "weak_history_only", False

    return "unknown_non_country_domain", False


def merge_location_signal_metadata(location_signals: list[dict]) -> dict:
    signal_terms: set[str] = set()
    header_texts: list[str] = []

    for signal in location_signals:
        signal_terms.update(signal.get("location_signal_terms", []))
        header_text = signal.get("header_location_text")
        if header_text and header_text not in header_texts:
            header_texts.append(header_text)

    return {
        "location_signal_terms": sorted(signal_terms),
        "header_location_text": header_texts[0] if header_texts else "",
    }


def build_deduped_results_and_report(
    query_plan: dict,
    query_results: list[dict],
) -> tuple[list[dict], dict]:
    filters = query_plan["filters"]
    candidates_by_url: dict[str, dict] = {}
    occurrence_records: list[dict] = []
    seen_urls: set[str] = set()
    query_contribution: list[dict] = []
    raw_total = 0
    normalized_total = 0
    hidden_by_profile_filter = 0
    hidden_by_location_filter = 0
    location_occurrence_counts = empty_location_status_counts()
    location_unique_counts = empty_location_status_counts()
    displayed = 0
    location_filter_enabled = filters.get("location_filter_enabled", False)
    location_config = (
        location_filter_config_for(query_plan["input_snapshot"]["location"])
        if location_filter_enabled
        else None
    )

    for query_result in query_results:
        contribution = {
            "id": query_result["query_id"],
            "category": query_result["category"],
            "raw": 0,
            "filtered": 0,
            "new_unique_profiles": 0,
            "duplicates": 0,
            "ok": query_result.get("ok", False),
            "error": query_result.get("error"),
        }

        if not query_result.get("ok"):
            query_contribution.append(contribution)
            continue

        for raw_result in query_result.get("raw_results", []):
            contribution["raw"] += 1
            raw_total += 1
            normalized_result = normalize_tavily_result(raw_result)
            normalized_total += 1
            url = normalized_result.get("url") or ""

            if filters.get("linkedin_profiles_only") and not is_linkedin_profile_url(url):
                hidden_by_profile_filter += 1
                continue

            normalized_url = normalize_linkedin_profile_url(url)
            if not normalized_url:
                continue

            location_signal = None
            if location_filter_enabled and location_config:
                location_signal = location_signal_for_result(
                    raw_result,
                    normalized_result,
                    location_config,
                )
                location_occurrence_counts[location_signal["status"]] += 1

            query_source = query_source_from_result(query_result)
            current_item = candidates_by_url.get(normalized_url)
            if current_item is None:
                candidates_by_url[normalized_url] = {
                    "normalized_url": normalized_url,
                    "result": normalized_result,
                    "query_sources": [query_source],
                    "location_signals": [location_signal] if location_signal else [],
                }
            else:
                current_item["result"] = choose_more_complete_result(
                    current_item["result"],
                    normalized_result,
                )
                append_unique_query_source(current_item["query_sources"], query_source)
                if location_signal:
                    current_item["location_signals"].append(location_signal)

            occurrence_records.append(
                {
                    "normalized_url": normalized_url,
                    "contribution": contribution,
                }
            )

        query_contribution.append(contribution)

    for candidate in candidates_by_url.values():
        if location_filter_enabled:
            final_status, is_displayed = final_location_decision(
                candidate["location_signals"]
            )
            location_unique_counts[final_status] += 1
            location_metadata = merge_location_signal_metadata(
                candidate["location_signals"]
            )
            candidate["location_signal_status"] = final_status
            candidate["location_signal_terms"] = location_metadata[
                "location_signal_terms"
            ]
            candidate["header_location_text"] = location_metadata[
                "header_location_text"
            ]
            candidate["location_filter_displayed"] = is_displayed
            candidate["result"]["location_signal_status"] = final_status
            candidate["result"]["location_signal_terms"] = location_metadata[
                "location_signal_terms"
            ]
            candidate["result"]["header_location_text"] = location_metadata[
                "header_location_text"
            ]
        else:
            candidate["location_signal_status"] = "not_applied"
            candidate["location_signal_terms"] = []
            candidate["header_location_text"] = ""
            candidate["location_filter_displayed"] = True

    deduped_results: list[dict] = []
    for occurrence in occurrence_records:
        normalized_url = occurrence["normalized_url"]
        contribution = occurrence["contribution"]
        candidate = candidates_by_url[normalized_url]

        if not candidate["location_filter_displayed"]:
            hidden_by_location_filter += 1
            continue

        contribution["filtered"] += 1
        displayed += 1

        if normalized_url in seen_urls:
            contribution["duplicates"] += 1
        else:
            contribution["new_unique_profiles"] += 1
            seen_urls.add(normalized_url)
            deduped_results.append(
                {
                    "normalized_url": normalized_url,
                    "result": candidate["result"],
                    "query_sources": candidate["query_sources"],
                    "location_signal_status": candidate["location_signal_status"],
                    "location_signal_terms": candidate["location_signal_terms"],
                    "header_location_text": candidate["header_location_text"],
                }
            )

    unique_profiles = len(deduped_results)
    location_filter_report = {
        "enabled": location_filter_enabled,
        "config_location": (
            location_config["label"]
            if location_filter_enabled and location_config
            else None
        ),
        "occurrence_breakdown": location_occurrence_counts,
        "unique_breakdown": location_unique_counts,
    }

    return (
        deduped_results,
        {
            "queries_total": len(query_plan["queries"]),
            "queries_succeeded": sum(1 for result in query_results if result.get("ok")),
            "queries_failed": sum(1 for result in query_results if not result.get("ok")),
            "raw_total": raw_total,
            "normalized_total": normalized_total,
            "displayed": displayed,
            "unique_profiles": unique_profiles,
            "duplicates_removed": displayed - unique_profiles,
            "hidden_by_profile_filter": hidden_by_profile_filter,
            "hidden_by_location_filter": hidden_by_location_filter,
            "rescued_by_header_location": location_occurrence_counts[
                "rescued_header_location"
            ],
            "hidden_by_negative_header_location": location_occurrence_counts[
                "excluded_negative_header_location"
            ],
            "weak_location_history_only": location_occurrence_counts[
                "weak_history_only"
            ],
            "unknown_non_country_domain_location": location_occurrence_counts[
                "unknown_non_country_domain"
            ],
            "location_filter_report": location_filter_report,
            "query_contribution": query_contribution,
        },
    )


def canonical_value(value: str | None, allowed_values: dict[str, str]) -> str | None:
    if value is None:
        return None

    normalized_key = value.strip().lower()
    if not normalized_key:
        return None

    return allowed_values.get(normalized_key)


def add_validation_error(errors: list[dict[str, str]], field: str, message: str) -> None:
    errors.append({"field": field, "message": message})


def normalize_stack_items(stack: list[str] | None) -> tuple[list[str], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    normalized_stack: list[str] = []
    seen_stack_values: set[str] = set()

    if not stack:
        add_validation_error(errors, "stack", "At least one Java stack item is required.")
        return normalized_stack, errors

    for item in stack:
        canonical_stack_item = canonical_value(item, JAVA_STACK_VALUES)
        if not canonical_stack_item:
            add_validation_error(errors, "stack", "Unsupported Java stack item.")
            continue

        if canonical_stack_item not in seen_stack_values:
            seen_stack_values.add(canonical_stack_item)
            normalized_stack.append(canonical_stack_item)

    if len(normalized_stack) > 3:
        add_validation_error(errors, "stack", "Java stack supports up to 3 selected items.")

    return normalized_stack, errors


def normalize_structured_search_request(
    request: StructuredSearchRequest,
) -> tuple[dict | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []

    role_family = canonical_value(request.role_family, CANONICAL_ROLE_FAMILIES)
    if request.role_family is None or not request.role_family.strip():
        add_validation_error(errors, "role_family", "Role family is required.")
    elif not role_family:
        add_validation_error(errors, "role_family", "Unsupported role family.")

    technology = canonical_value(request.technology, KNOWN_BACKEND_TECHNOLOGIES)
    if request.technology is None or not request.technology.strip():
        add_validation_error(errors, "technology", "Technology is required.")
    elif not technology:
        add_validation_error(errors, "technology", "Unsupported technology.")
    elif technology not in IMPLEMENTED_BACKEND_TECHNOLOGIES:
        add_validation_error(
            errors,
            "technology",
            "Technology is known but planner is not implemented yet.",
        )

    location = (request.location or "").strip()
    if not location:
        add_validation_error(errors, "location", "Location is required.")

    normalized_stack: list[str] = []
    if technology == "Java":
        normalized_stack, stack_errors = normalize_stack_items(request.stack)
        errors.extend(stack_errors)

    linkedin_profiles_only = (
        True
        if request.linkedin_profiles_only is None
        else request.linkedin_profiles_only
    )
    location_filter_config = location_filter_config_for(location)
    location_filter_enabled = (
        location_filter_config is not None
        if request.location_filter_enabled is None
        else request.location_filter_enabled
    )
    if location and location_filter_enabled and not location_filter_config:
        add_validation_error(
            errors,
            "location_filter_enabled",
            "Location filter config is not implemented for this location yet.",
        )

    if errors:
        return None, errors

    return (
        {
            "role_family": role_family,
            "technology": technology,
            "stack": normalized_stack,
            "location": location,
            "linkedin_profiles_only": linkedin_profiles_only,
            "location_filter_enabled": location_filter_enabled,
        },
        errors,
    )


def quote_query_value(value: str) -> str:
    escaped_value = value.replace('"', '\\"')
    return f'"{escaped_value}"'


def build_stack_or(stack: list[str]) -> str:
    quoted_stack_values = [quote_query_value(item) for item in stack]
    if len(quoted_stack_values) == 1:
        return quoted_stack_values[0]

    return "(" + " OR ".join(quoted_stack_values) + ")"


def build_query_slot(
    query_id: str,
    category: str,
    purpose: str,
    role_phrase: str,
    location: str,
    stack: list[str] | None = None,
) -> dict:
    quoted_location = quote_query_value(location)
    quoted_role_phrase = quote_query_value(role_phrase)
    query_parts = ["site:linkedin.com/in", "AND", quoted_role_phrase]
    uses_stack = stack or []

    if uses_stack:
        query_parts.extend(["AND", build_stack_or(uses_stack)])

    query_parts.extend(["AND", quoted_location])

    return {
        "id": query_id,
        "category": category,
        "purpose": purpose,
        "query": " ".join(query_parts),
        "uses_stack": uses_stack,
        "max_results": QUERY_PLAN_MAX_RESULTS,
    }


async def run_tavily_query(query: str, max_results: int) -> dict:
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise HTTPException(status_code=503, detail="TAVILY_API_KEY is not configured.")

    payload = {
        "query": query,
        "search_depth": "basic",
        "topic": "general",
        "max_results": max_results,
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

    return response.json()


async def run_query_slot(query_slot: dict) -> dict:
    try:
        tavily_data = await run_tavily_query(
            query_slot["query"],
            query_slot["max_results"],
        )
    except HTTPException as exc:
        return {
            "query_id": query_slot["id"],
            "category": query_slot["category"],
            "query": query_slot["query"],
            "ok": False,
            "raw_results": [],
            "raw_count": 0,
            "response_time": None,
            "usage": None,
            "request_id": None,
            "error": exc.detail,
        }

    raw_results = tavily_data.get("results", [])
    return {
        "query_id": query_slot["id"],
        "category": query_slot["category"],
        "query": query_slot["query"],
        "ok": True,
        "raw_results": raw_results,
        "raw_count": len(raw_results),
        "response_time": tavily_data.get("response_time"),
        "usage": tavily_data.get("usage"),
        "request_id": tavily_data.get("request_id"),
        "error": None,
    }


class RuleBasedQueryPlannerV1:
    version = QUERY_PLANNER_VERSION

    def build(self, normalized_request: dict) -> dict:
        location = normalized_request["location"]
        stack = normalized_request["stack"]

        queries = [
            build_query_slot(
                "Q01",
                "role_based",
                "Find broad Java Developer profiles for the selected location.",
                "Java Developer",
                location,
            ),
            build_query_slot(
                "Q02",
                "role_based",
                "Find Java Software Engineer profiles for the selected location.",
                "Java Software Engineer",
                location,
            ),
            build_query_slot(
                "Q03",
                "backend_role",
                "Find Java Backend Engineer profiles for the selected location.",
                "Java Backend Engineer",
                location,
            ),
            build_query_slot(
                "Q04",
                "role_based",
                "Find Java Engineer profiles for the selected location.",
                "Java Engineer",
                location,
            ),
            build_query_slot(
                "Q05",
                "role_based",
                "Find Java Programmer profiles for the selected location.",
                "Java Programmer",
                location,
            ),
            build_query_slot(
                "Q06",
                "role_based",
                "Find Java Application Developer profiles for the selected location.",
                "Java Application Developer",
                location,
            ),
            build_query_slot(
                "Q07",
                "stack_focused",
                "Find Java Developer profiles that mention selected stack signals.",
                "Java Developer",
                location,
                stack,
            ),
            build_query_slot(
                "Q08",
                "stack_focused",
                "Find Java Engineer profiles that mention selected stack signals.",
                "Java Engineer",
                location,
                stack,
            ),
            build_query_slot(
                "Q09",
                "stack_focused",
                "Find Java Backend Engineer profiles that mention selected stack signals.",
                "Java Backend Engineer",
                location,
                stack,
            ),
            build_query_slot(
                "Q10",
                "stack_focused",
                "Find Java Application Developer profiles that mention selected stack signals.",
                "Java Application Developer",
                location,
                stack,
            ),
        ]

        return {
            "planner_version": self.version,
            "input_snapshot": normalized_request,
            "queries": queries,
            "filters": {
                "linkedin_profiles_only": normalized_request["linkedin_profiles_only"],
                "location_filter_enabled": normalized_request["location_filter_enabled"],
            },
            "execution": {
                "mode": "sequential",
                "max_results_per_query": QUERY_PLAN_MAX_RESULTS,
            },
            "reporting": QUERY_PLAN_REPORTING_FIELDS,
        }


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


@app.post("/api/structured-search/validate")
def validate_structured_search(request: StructuredSearchRequest) -> dict:
    normalized_request, errors = normalize_structured_search_request(request)

    if errors:
        return {"ok": False, "errors": errors}

    return {"ok": True, "normalized_request": normalized_request}


@app.post("/api/query-plan")
def create_query_plan(request: StructuredSearchRequest) -> dict:
    normalized_request, errors = normalize_structured_search_request(request)

    if errors:
        return {"ok": False, "errors": errors}

    query_plan = RuleBasedQueryPlannerV1().build(normalized_request)

    return {"ok": True, "query_plan": query_plan}


@app.post("/api/structured-search")
async def structured_search(request: StructuredSearchRequest) -> dict:
    normalized_request, errors = normalize_structured_search_request(request)

    if errors:
        return {"ok": False, "errors": errors}

    if not os.getenv("TAVILY_API_KEY"):
        return {
            "ok": False,
            "errors": [
                {
                    "field": "tavily_api_key",
                    "message": "TAVILY_API_KEY is not configured.",
                }
            ],
        }

    query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
    query_results = []

    for query_slot in query_plan["queries"]:
        query_results.append(await run_query_slot(query_slot))

    successful_queries = sum(1 for result in query_results if result["ok"])
    deduped_results, report = build_deduped_results_and_report(
        query_plan,
        query_results,
    )

    return {
        "ok": successful_queries > 0,
        "query_plan": query_plan,
        "query_results": query_results,
        "deduped_results": deduped_results,
        "report": report,
    }


@app.post("/api/search")
async def search(request: SearchRequest) -> dict:
    query = request.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Search query is required.")

    tavily_data = await run_tavily_query(query, request.max_results)
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
