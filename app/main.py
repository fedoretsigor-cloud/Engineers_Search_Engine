from pathlib import Path
from datetime import datetime, timezone
import html
import json
import logging
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
PROJECT_DIR = BASE_DIR.parent
STATIC_DIR = BASE_DIR / "static"
SEARCH_RUN_LOG_DIR = PROJECT_DIR / "logs" / "search-runs"
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
    "hidden_by_foreign_current_location",
    "weak_location_history_only",
    "unknown_non_country_domain_location",
    "location_filter_report",
    "query_contribution",
]

load_dotenv()

logger = logging.getLogger("engineers_search_engine")
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
JAVA_STACK_TERMS = [
    "Spring",
    "Spring Boot",
    "Hibernate",
    "Kafka",
    "PostgreSQL",
    "AWS",
    "Docker",
    "Kubernetes",
    "Microservices",
    "REST",
]
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
SEARCH_DOMAIN_CONFIG = {
    "Backend Developer": {
        "Java": {
            "planner": {
                "queries": [
                    {
                        "id": "Q01",
                        "category": "role_based",
                        "purpose": "Find broad Java Developer profiles for the selected location.",
                        "role_phrase": "Java Developer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q02",
                        "category": "role_based",
                        "purpose": "Find Java Software Engineer profiles for the selected location.",
                        "role_phrase": "Java Software Engineer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q03",
                        "category": "backend_role",
                        "purpose": "Find Java Backend Engineer profiles for the selected location.",
                        "role_phrase": "Java Backend Engineer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q04",
                        "category": "role_based",
                        "purpose": "Find Java Engineer profiles for the selected location.",
                        "role_phrase": "Java Engineer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q05",
                        "category": "role_based",
                        "purpose": "Find Java Programmer profiles for the selected location.",
                        "role_phrase": "Java Programmer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q06",
                        "category": "role_based",
                        "purpose": "Find Java Application Developer profiles for the selected location.",
                        "role_phrase": "Java Application Developer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q07",
                        "category": "stack_focused",
                        "purpose": "Find Java Developer profiles that mention selected stack signals.",
                        "role_phrase": "Java Developer",
                        "uses_selected_stack": True,
                    },
                    {
                        "id": "Q08",
                        "category": "stack_focused",
                        "purpose": "Find Java Engineer profiles that mention selected stack signals.",
                        "role_phrase": "Java Engineer",
                        "uses_selected_stack": True,
                    },
                    {
                        "id": "Q09",
                        "category": "stack_focused",
                        "purpose": "Find Java Backend Engineer profiles that mention selected stack signals.",
                        "role_phrase": "Java Backend Engineer",
                        "uses_selected_stack": True,
                    },
                    {
                        "id": "Q10",
                        "category": "stack_focused",
                        "purpose": "Find Java Application Developer profiles that mention selected stack signals.",
                        "role_phrase": "Java Application Developer",
                        "uses_selected_stack": True,
                    },
                ]
            },
            "quality": {
                "technology": {
                    "exact_terms": ["Java"],
                    "exclude_terms": ["JavaScript"],
                    "related_terms": ["Kotlin", "Scala"],
                },
                "stack": {
                    "allowed_terms": JAVA_STACK_TERMS,
                    "related_terms": [],
                },
            },
        },
    },
}
LOCATION_FILTER_CONFIG = {
    "ukraine": {
        "label": "Ukraine",
        "linkedin_domains": ["ua.linkedin.com"],
        "target_location_terms": [
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
CURRENT_LOCATION_SOCIAL_MARKER_PATTERN = re.compile(
    r"\b(?:\d+(?:[.,]\d+)?\s*[km]?\+?\s+)?(?:followers|connections)\b",
    flags=re.IGNORECASE,
)
LOCATION_QUALIFIER_PATTERN = re.compile(
    r"\b(area|city|county|district|province|region|state|voivodeship)\b",
    flags=re.IGNORECASE,
)
NON_LOCATION_FRAGMENT_PATTERN = re.compile(
    r"\b("
    r"academy|architect|backend|college|company|consultant|developer|education|"
    r"engineer|frontend|full[- ]?stack|hibernate|inc|institute|java|kafka|lead|"
    r"llc|ltd|manager|middle|polytechnic|programmer|python|school|senior|"
    r"software|solutions|spring|systems|technologies|technology|university"
    r")\b",
    flags=re.IGNORECASE,
)
LOCATION_SIGNAL_STATUSES = [
    "target_location",
    "country_domain",
    "rescued_header_location",
    "excluded_foreign_current_location",
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


PROFILE_NAME_REJECT_TERMS = {
    "architect",
    "backend",
    "consultant",
    "developer",
    "engineer",
    "frontend",
    "fullstack",
    "java",
    "javascript",
    "kafka",
    "kotlin",
    "lead",
    "linkedin",
    "manager",
    "middle",
    "programmer",
    "python",
    "recruiter",
    "scala",
    "senior",
    "software",
    "spring",
    "technologies",
    "technology",
}


def clean_profile_text(value: object) -> str:
    if value is None:
        return ""

    text = html.unescape(str(value))
    text = text.replace("\xa0", " ")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_linkedin_suffix(value: str) -> str:
    text = clean_profile_text(value)
    text = re.sub(r"(?i)(?:\s*[-|]\s*)?linkedin\s*$", "", text)
    text = re.sub(r"(?i)\s*\|\s*linkedin\b.*$", "", text)
    text = re.sub(r"(?i)\s*-\s*linkedin\b.*$", "", text)
    return text.strip(" -|.")


def looks_like_person_name(value: str) -> bool:
    name = strip_linkedin_suffix(value)
    if not name or len(name) > 80:
        return False
    if any(marker in name for marker in ("@", "/", "\\", "|", ":")):
        return False
    if re.search(r"\d", name):
        return False

    lowered_name = name.lower()
    if any(term in lowered_name.split() for term in PROFILE_NAME_REJECT_TERMS):
        return False

    tokens = [token.strip(".,") for token in name.split() if token.strip(".,")]
    if not 2 <= len(tokens) <= 6:
        return False

    return all(any(char.isalpha() for char in token) for token in tokens)


def clean_headline_value(value: str) -> str:
    headline = strip_linkedin_suffix(value)
    headline = re.sub(r"(?i)\b(?:\d+(?:[.,]\d+)?\s*)?(?:followers|connections)\b.*$", "", headline)
    return headline.strip(" -|.")


def identity_from_parts(name_candidate: str, headline_candidate: str) -> dict | None:
    name = strip_linkedin_suffix(name_candidate)
    headline = clean_headline_value(headline_candidate)

    if not looks_like_person_name(name):
        return None
    if not headline or "linkedin" in headline.lower():
        return None

    return {"name": name, "headline": headline}


def extract_identity_from_profile_text(value: object) -> dict | None:
    text = strip_linkedin_suffix(clean_profile_text(value))
    if not text:
        return None

    dash_parts = [
        part.strip()
        for part in re.split(r"\s+-\s+", text, maxsplit=1)
        if part.strip()
    ]
    if len(dash_parts) == 2:
        identity = identity_from_parts(dash_parts[0], dash_parts[1])
        if identity:
            return identity

    pipe_parts = [part.strip() for part in text.split("|") if part.strip()]
    if len(pipe_parts) >= 2:
        identity = identity_from_parts(pipe_parts[0], pipe_parts[1])
        if identity:
            return identity

    sentence_parts = [
        part.strip()
        for part in re.split(r"\.\s+", text, maxsplit=2)
        if part.strip()
    ]
    if len(sentence_parts) >= 2:
        identity = identity_from_parts(sentence_parts[0], sentence_parts[1])
        if identity:
            return identity

    return None


def extract_profile_identity(raw_result: dict) -> dict:
    for field in ("title", "content", "snippet", "raw_content"):
        identity = extract_identity_from_profile_text(raw_result.get(field))
        if identity:
            return identity

    return {"name": "unknown", "headline": "n/a"}


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


def header_lines(header_location_text: str) -> list[str]:
    return [
        line.strip()
        for line in header_location_text.replace("\r", "\n").split("\n")
        if line.strip()
    ]


def contains_social_marker(text: str) -> bool:
    return bool(CURRENT_LOCATION_SOCIAL_MARKER_PATTERN.search(text))


def clean_current_location_fragment(fragment: str) -> str:
    compact_fragment = compact_spaces(fragment)
    if not compact_fragment or compact_fragment.endswith(","):
        return ""

    return compact_fragment.strip(" .;:")


def is_plausible_current_location_fragment(
    fragment: str,
    target_location_terms: list[str],
    require_location_shape: bool,
) -> bool:
    if not fragment or len(fragment) > 120:
        return False
    if fragment.endswith(","):
        return False
    if NON_LOCATION_FRAGMENT_PATTERN.search(fragment):
        return False

    matched_target_terms = match_location_terms(fragment, target_location_terms)
    if not require_location_shape:
        return True

    return bool(
        matched_target_terms
        or "," in fragment
        or LOCATION_QUALIFIER_PATTERN.search(fragment)
    )


def extract_one_line_current_location_line(
    header_location_text: str,
    target_location_terms: list[str],
) -> str:
    one_line = compact_spaces(header_location_text)
    marker_match = CURRENT_LOCATION_SOCIAL_MARKER_PATTERN.search(one_line)
    if not marker_match:
        return ""

    before_marker = one_line[: marker_match.start()].strip()
    fragments = [
        fragment.strip()
        for fragment in re.split(r"\.\s+", before_marker)
        if fragment.strip()
    ]

    for fragment in reversed(fragments):
        current_location_line = clean_current_location_fragment(fragment)
        if is_plausible_current_location_fragment(
            current_location_line,
            target_location_terms,
            require_location_shape=True,
        ):
            return current_location_line

    return ""


def extract_current_location_line(
    header_location_text: str,
    target_location_terms: list[str],
) -> str:
    lines = header_lines(header_location_text)
    if len(lines) > 1:
        for index, line in enumerate(lines):
            if contains_social_marker(line):
                if index < 2:
                    return ""

                current_location_line = clean_current_location_fragment(
                    lines[index - 1]
                )
                if is_plausible_current_location_fragment(
                    current_location_line,
                    target_location_terms,
                    require_location_shape=False,
                ):
                    return current_location_line
                return ""

        if len(lines) >= 3:
            current_location_line = clean_current_location_fragment(lines[2])
            if is_plausible_current_location_fragment(
                current_location_line,
                target_location_terms,
                require_location_shape=False,
            ):
                return current_location_line

        return ""

    return extract_one_line_current_location_line(
        header_location_text,
        target_location_terms,
    )


def header_target_terms_can_rescue(
    header_location_text: str,
    target_location_terms: list[str],
) -> bool:
    if not match_location_terms(header_location_text, target_location_terms):
        return False
    if len(header_lines(header_location_text)) > 1:
        return True
    if NON_LOCATION_FRAGMENT_PATTERN.search(header_location_text):
        return False

    return bool(
        contains_social_marker(header_location_text)
        or "," in header_location_text
        or LOCATION_QUALIFIER_PATTERN.search(header_location_text)
    )


def classify_current_location(
    header_location_text: str,
    location_config: dict,
) -> dict:
    target_location_terms = location_config["target_location_terms"]
    current_location_line = extract_current_location_line(
        header_location_text,
        target_location_terms,
    )
    target_terms = match_location_terms(current_location_line, target_location_terms)

    if not current_location_line:
        classification = "unknown_current_location"
    elif target_terms:
        classification = "target_location"
    else:
        classification = "foreign_current_location"

    return {
        "classification": classification,
        "current_location_line": current_location_line,
        "target_location_terms": target_terms,
    }


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
    profile_identity = extract_profile_identity(result)

    normalized_result = {
        "name": profile_identity["name"],
        "headline": profile_identity["headline"],
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
        "role_phrase": query_result.get("role_phrase"),
        "uses_stack": query_result.get("uses_stack", []),
        "query": query_result["query"],
    }


def append_unique_query_source(query_sources: list[dict], query_source: dict) -> None:
    if any(source["id"] == query_source["id"] for source in query_sources):
        return

    query_sources.append(query_source)


def search_domain_config_for(role_family: str, technology: str) -> dict:
    return SEARCH_DOMAIN_CONFIG.get(role_family, {}).get(technology, {})


def ordered_unique(values: list[str]) -> list[str]:
    seen_values: set[str] = set()
    unique_values: list[str] = []

    for value in values:
        if value and value not in seen_values:
            seen_values.add(value)
            unique_values.append(value)

    return unique_values


def term_match_pattern(term: str) -> str:
    escaped_term = re.escape(term.strip()).replace(r"\ ", r"\s+")
    return r"(?<![a-z0-9])" + escaped_term + r"(?![a-z0-9])"


def find_term_match(text: str, term: str) -> re.Match | None:
    if not text or not term:
        return None

    return re.search(term_match_pattern(term), text, flags=re.IGNORECASE)


def match_config_terms(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if find_term_match(text, term)]


def candidate_text_sources(result: dict) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    seen_values: set[str] = set()
    source_fields = [
        ("headline", result.get("headline")),
        ("title", result.get("title")),
        ("snippet", result.get("snippet")),
        ("raw_content", result.get("raw_content")),
    ]

    for source, raw_value in source_fields:
        value = clean_profile_text(raw_value)
        if not value or value.lower() in {"unknown", "n/a"}:
            continue

        value_key = value.lower()
        if value_key in seen_values:
            continue

        seen_values.add(value_key)
        sources.append({"source": source, "value": value})

    return sources


def collect_term_evidence(
    sources: list[dict[str, str]],
    terms: list[str],
) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    seen_terms: set[str] = set()

    for source in sources:
        value = source["value"]
        for term in terms:
            if term in seen_terms:
                continue
            if find_term_match(value, term):
                seen_terms.add(term)
                evidence.append(
                    {
                        "term": term,
                        "source": source["source"],
                        "value": value,
                    }
                )

    return evidence


def terms_from_evidence(
    evidence: list[dict],
    term_order: list[str],
) -> list[str]:
    found_terms = {item.get("term") for item in evidence if item.get("term")}
    return [term for term in term_order if term in found_terms]


def query_plan_by_id(query_plan: dict) -> dict[str, dict]:
    return {query["id"]: query for query in query_plan.get("queries", [])}


def role_context_phrases(query_sources: list[dict], query_plan: dict) -> list[str]:
    queries_by_id = query_plan_by_id(query_plan)
    role_phrases: list[str] = []

    for source in query_sources:
        role_phrase = source.get("role_phrase")
        if not role_phrase:
            query = queries_by_id.get(source.get("id"))
            role_phrase = query.get("role_phrase") if query else None
        if role_phrase:
            role_phrases.append(role_phrase)

    input_snapshot = query_plan.get("input_snapshot") or {}
    if input_snapshot.get("role_family"):
        role_phrases.append(input_snapshot["role_family"])

    for query in query_plan.get("queries", []):
        if query.get("role_phrase"):
            role_phrases.append(query["role_phrase"])

    return ordered_unique(role_phrases)


def derived_role_phrases(
    role_phrases: list[str],
    technology_terms: list[str],
) -> list[dict[str, str]]:
    derived_phrases: list[dict[str, str]] = []
    seen_phrases: set[str] = set()

    for role_phrase in role_phrases:
        derived_phrase = role_phrase
        for technology_term in technology_terms:
            derived_phrase = re.sub(
                term_match_pattern(technology_term),
                " ",
                derived_phrase,
                flags=re.IGNORECASE,
            )

        derived_phrase = compact_spaces(derived_phrase)
        if (
            derived_phrase
            and derived_phrase.lower() != role_phrase.lower()
            and derived_phrase.lower() not in seen_phrases
        ):
            seen_phrases.add(derived_phrase.lower())
            derived_phrases.append(
                {
                    "phrase": derived_phrase,
                    "source_role_phrase": role_phrase,
                }
            )

    return derived_phrases


def role_prefix_terms(
    role_phrases: list[str],
    technology_terms: list[str],
) -> list[str]:
    terms = ["Junior", "Middle", "Mid", "Senior", "Lead", "Principal", "Staff"]
    for phrase in role_phrases + technology_terms:
        terms.extend(re.findall(r"[A-Za-z][A-Za-z+#.]*", phrase))

    return sorted(ordered_unique(terms), key=len, reverse=True)


def role_display_from_match(
    value: str,
    match: re.Match,
    technology_terms: list[str],
    role_phrases: list[str],
) -> str:
    start = match.start()
    end = match.end()
    prefix_terms = role_prefix_terms(role_phrases, technology_terms)
    prefix_options = "|".join(re.escape(term) for term in prefix_terms) or r"$^"
    prefix_pattern = r"(?:(?:" + prefix_options + r")\s+){0,5}$"
    prefix_match = re.search(prefix_pattern, value[:start], flags=re.IGNORECASE)
    if prefix_match and prefix_match.group(0).strip():
        start = prefix_match.start()

    return clean_headline_value(value[start:end])


def find_role_match(
    sources: list[dict[str, str]],
    role_phrases: list[str],
    technology_terms: list[str],
) -> dict | None:
    ordered_role_phrases = sorted(role_phrases, key=len, reverse=True)
    derived_phrases = sorted(
        derived_role_phrases(role_phrases, technology_terms),
        key=lambda item: len(item["phrase"]),
        reverse=True,
    )

    for source in sources:
        value = source["value"]
        for role_phrase in ordered_role_phrases:
            match = find_term_match(value, role_phrase)
            if match:
                return {
                    "role_display": role_display_from_match(
                        value,
                        match,
                        technology_terms,
                        role_phrases,
                    ),
                    "role_fit": "target_or_close_role",
                    "evidence": {
                        "source": source["source"],
                        "value": value,
                        "matched_phrase": role_phrase,
                        "match_type": "role_phrase",
                    },
                }

    for source in sources:
        value = source["value"]
        for derived_phrase in derived_phrases:
            match = find_term_match(value, derived_phrase["phrase"])
            if match:
                return {
                    "role_display": role_display_from_match(
                        value,
                        match,
                        technology_terms,
                        role_phrases,
                    ),
                    "role_fit": "similar_role",
                    "evidence": {
                        "source": source["source"],
                        "value": value,
                        "matched_phrase": derived_phrase["phrase"],
                        "source_role_phrase": derived_phrase["source_role_phrase"],
                        "match_type": "derived_role_phrase",
                    },
                }

    return None


def build_role_quality(
    result: dict,
    query_sources: list[dict],
    query_plan: dict,
    domain_config: dict,
) -> dict:
    quality_config = domain_config.get("quality", {})
    technology_terms = quality_config.get("technology", {}).get("exact_terms", [])
    role_phrases = role_context_phrases(query_sources, query_plan)
    sources = candidate_text_sources(result)
    role_match = find_role_match(sources, role_phrases, technology_terms)

    if not role_match:
        return {
            "role_display": "n/a",
            "role_fit": "missing_role",
            "role_evidence": [],
            "review_flags": ["role_missing"],
        }

    review_flags: list[str] = []
    evidence_source = role_match["evidence"]["source"]
    if evidence_source not in {"headline", "title"}:
        review_flags.append("role_from_snippet_only")
    if role_match["role_fit"] == "similar_role":
        review_flags.append("role_similar_only")

    return {
        "role_display": role_match["role_display"] or "n/a",
        "role_fit": role_match["role_fit"],
        "role_evidence": [role_match["evidence"]],
        "review_flags": review_flags,
    }


def build_technology_quality(
    result: dict,
    domain_config: dict,
) -> dict:
    quality_config = domain_config.get("quality", {})
    technology_config = quality_config.get("technology", {})
    exact_terms = technology_config.get("exact_terms", [])
    exclude_terms = technology_config.get("exclude_terms", [])
    related_terms = technology_config.get("related_terms", [])
    sources = candidate_text_sources(result)
    exact_evidence = collect_term_evidence(sources, exact_terms)
    exclude_evidence = collect_term_evidence(sources, exclude_terms)
    related_evidence = collect_term_evidence(sources, related_terms)
    exact_matches = terms_from_evidence(exact_evidence, exact_terms)
    related_matches = terms_from_evidence(related_evidence, related_terms)
    review_flags: list[str] = []

    if exact_matches:
        return {
            "technology_display": ", ".join(exact_matches),
            "technology_fit": "exact",
            "technology_evidence": exact_evidence + exclude_evidence,
            "review_flags": review_flags,
        }

    if related_matches:
        review_flags.append("technology_related_only")
        if exclude_evidence:
            review_flags.append("possible_technology_false_positive")
        return {
            "technology_display": ", ".join(related_matches),
            "technology_fit": "related_only",
            "technology_evidence": related_evidence + exclude_evidence,
            "review_flags": review_flags,
        }

    if exclude_evidence:
        return {
            "technology_display": "n/a",
            "technology_fit": "ambiguous",
            "technology_evidence": exclude_evidence,
            "review_flags": [
                "technology_ambiguous",
                "possible_technology_false_positive",
            ],
        }

    return {
        "technology_display": "n/a",
        "technology_fit": "missing",
        "technology_evidence": [],
        "review_flags": ["technology_missing"],
    }


def query_source_stack_evidence(
    query_sources: list[dict],
    query_plan: dict,
) -> list[dict]:
    queries_by_id = query_plan_by_id(query_plan)
    evidence: list[dict] = []
    seen_query_ids: set[str] = set()

    for source in query_sources:
        query_id = source.get("id")
        if not query_id or query_id in seen_query_ids:
            continue

        uses_stack = source.get("uses_stack")
        if uses_stack is None:
            query = queries_by_id.get(query_id)
            uses_stack = query.get("uses_stack") if query else []

        if not uses_stack:
            continue

        seen_query_ids.add(query_id)
        evidence.append(
            {
                "terms": uses_stack,
                "source": "query_source",
                "query_id": query_id,
                "category": source.get("category"),
                "evidence_type": "stack_query_group",
            }
        )

    return evidence


def build_stack_quality(
    result: dict,
    query_sources: list[dict],
    query_plan: dict,
    domain_config: dict,
) -> dict:
    input_snapshot = query_plan.get("input_snapshot") or {}
    selected_stack = input_snapshot.get("stack") or []
    quality_config = domain_config.get("quality", {})
    stack_config = quality_config.get("stack", {})
    allowed_terms = stack_config.get("allowed_terms", [])
    related_terms = stack_config.get("related_terms", [])
    selected_terms = [term for term in selected_stack if term in allowed_terms]
    sources = candidate_text_sources(result)
    selected_evidence = collect_term_evidence(sources, selected_terms)
    related_evidence = collect_term_evidence(sources, related_terms)
    query_group_evidence = query_source_stack_evidence(query_sources, query_plan)
    selected_matches = terms_from_evidence(selected_evidence, selected_terms)
    related_matches = terms_from_evidence(related_evidence, related_terms)

    if selected_matches:
        return {
            "stack_display": ", ".join(selected_matches),
            "stack_fit": "selected_stack_found",
            "stack_evidence": selected_evidence + query_group_evidence,
            "review_flags": [],
        }

    if query_group_evidence:
        return {
            "stack_display": "n/a",
            "stack_fit": "stack_query_source_only",
            "stack_evidence": query_group_evidence,
            "review_flags": [
                "selected_stack_missing",
                "stack_from_query_source_only",
            ],
        }

    if related_matches:
        return {
            "stack_display": ", ".join(related_matches),
            "stack_fit": "related_stack_only",
            "stack_evidence": related_evidence,
            "review_flags": ["stack_related_only"],
        }

    return {
        "stack_display": "n/a",
        "stack_fit": "missing_selected_stack" if selected_stack else "missing",
        "stack_evidence": [],
        "review_flags": ["selected_stack_missing"] if selected_stack else [],
    }


def merge_review_flags(existing_flags: list[str], new_flags: list[str]) -> list[str]:
    return ordered_unique(existing_flags + new_flags)


def build_candidate_quality(
    result: dict,
    query_sources: list[dict],
    query_plan: dict,
) -> dict:
    input_snapshot = query_plan.get("input_snapshot") or {}
    domain_config = search_domain_config_for(
        input_snapshot.get("role_family") or "",
        input_snapshot.get("technology") or "",
    )
    quality: dict = {}
    review_flags = list(result.get("review_flags", []))

    for quality_part in (
        build_role_quality(result, query_sources, query_plan, domain_config),
        build_technology_quality(result, domain_config),
        build_stack_quality(result, query_sources, query_plan, domain_config),
    ):
        review_flags = merge_review_flags(
            review_flags,
            quality_part.pop("review_flags", []),
        )
        quality.update(quality_part)

    quality["review_flags"] = review_flags
    return quality


def empty_location_status_counts() -> dict[str, int]:
    return {status: 0 for status in LOCATION_SIGNAL_STATUSES}


def location_signal_for_result(
    raw_result: dict,
    normalized_result: dict,
    location_config: dict,
) -> dict:
    header_location_text = extract_header_location_text(raw_result, normalized_result)
    combined_text = combined_public_profile_text(raw_result, normalized_result)
    target_location_terms = location_config["target_location_terms"]
    current_location_signal = classify_current_location(
        header_location_text,
        location_config,
    )
    header_target_terms = match_location_terms(
        header_location_text,
        target_location_terms,
    )
    full_target_terms = match_location_terms(
        combined_text,
        target_location_terms,
    )
    is_country_domain = is_country_linkedin_profile_url(
        normalized_result.get("url") or "",
        location_config,
    )
    current_location_classification = current_location_signal["classification"]

    if current_location_classification == "foreign_current_location":
        status = "excluded_foreign_current_location"
    elif current_location_classification == "target_location":
        status = "target_location"
    elif is_country_domain:
        status = "country_domain"
    elif header_target_terms_can_rescue(header_location_text, target_location_terms):
        status = "rescued_header_location"
    elif full_target_terms:
        status = "weak_history_only"
    else:
        status = "unknown_non_country_domain"

    return {
        "status": status,
        "header_location_text": header_location_text,
        "current_location_line": current_location_signal["current_location_line"],
        "current_location_classification": current_location_classification,
        "location_signal_terms": sorted(
            set(
                current_location_signal["target_location_terms"]
                + header_target_terms
                + full_target_terms
            )
        ),
    }


def final_location_decision(location_signals: list[dict]) -> tuple[str, bool]:
    statuses = {signal["status"] for signal in location_signals}

    if "excluded_foreign_current_location" in statuses:
        return "excluded_foreign_current_location", False
    if "target_location" in statuses:
        return "target_location", True
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
    current_location_lines: list[str] = []
    current_location_classifications: set[str] = set()

    for signal in location_signals:
        signal_terms.update(signal.get("location_signal_terms", []))
        header_text = signal.get("header_location_text")
        if header_text and header_text not in header_texts:
            header_texts.append(header_text)
        current_location_line = signal.get("current_location_line")
        if (
            current_location_line
            and current_location_line not in current_location_lines
        ):
            current_location_lines.append(current_location_line)
        current_location_classification = signal.get(
            "current_location_classification"
        )
        if current_location_classification:
            current_location_classifications.add(current_location_classification)

    return {
        "location_signal_terms": sorted(signal_terms),
        "header_location_text": header_texts[0] if header_texts else "",
        "current_location_line": (
            current_location_lines[0] if current_location_lines else ""
        ),
        "current_location_lines": current_location_lines,
        "current_location_classifications": sorted(
            current_location_classifications
        ),
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
            candidate["current_location_line"] = location_metadata[
                "current_location_line"
            ]
            candidate["current_location_lines"] = location_metadata[
                "current_location_lines"
            ]
            candidate["current_location_classifications"] = location_metadata[
                "current_location_classifications"
            ]
            candidate["location_filter_displayed"] = is_displayed
            candidate["result"]["location_signal_status"] = final_status
            candidate["result"]["location_signal_terms"] = location_metadata[
                "location_signal_terms"
            ]
            candidate["result"]["header_location_text"] = location_metadata[
                "header_location_text"
            ]
            candidate["result"]["current_location_line"] = location_metadata[
                "current_location_line"
            ]
            candidate["result"]["current_location_lines"] = location_metadata[
                "current_location_lines"
            ]
            candidate["result"]["current_location_classifications"] = location_metadata[
                "current_location_classifications"
            ]
        else:
            candidate["location_signal_status"] = "not_applied"
            candidate["location_signal_terms"] = []
            candidate["header_location_text"] = ""
            candidate["current_location_line"] = ""
            candidate["current_location_lines"] = []
            candidate["current_location_classifications"] = []
            candidate["location_filter_displayed"] = True

        candidate["result"].update(
            build_candidate_quality(
                candidate["result"],
                candidate["query_sources"],
                query_plan,
            )
        )

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
                    "current_location_line": candidate["current_location_line"],
                    "current_location_lines": candidate["current_location_lines"],
                    "current_location_classifications": candidate[
                        "current_location_classifications"
                    ],
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
            "hidden_by_foreign_current_location": location_occurrence_counts[
                "excluded_foreign_current_location"
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
        "role_phrase": role_phrase,
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
            "role_phrase": query_slot.get("role_phrase"),
            "uses_stack": query_slot.get("uses_stack", []),
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
        "role_phrase": query_slot.get("role_phrase"),
        "uses_stack": query_slot.get("uses_stack", []),
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
        domain_config = search_domain_config_for(
            normalized_request["role_family"],
            normalized_request["technology"],
        )
        planner_queries = domain_config.get("planner", {}).get("queries", [])
        queries = [
            build_query_slot(
                query_config["id"],
                query_config["category"],
                query_config["purpose"],
                query_config["role_phrase"],
                location,
                stack if query_config.get("uses_selected_stack") else None,
            )
            for query_config in planner_queries
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


def snapshot_slug(value: object) -> str:
    compact_value = compact_spaces(str(value or "")).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", compact_value).strip("-")
    return slug or "unknown"


def structured_search_snapshot_filename(
    normalized_request: dict,
    timestamp: datetime,
) -> str:
    timestamp_part = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")
    role_part = snapshot_slug(normalized_request.get("role_family"))
    technology_part = snapshot_slug(normalized_request.get("technology"))
    location_part = snapshot_slug(normalized_request.get("location"))

    return (
        f"{timestamp_part}_structured-search_"
        f"{role_part}-{technology_part}-{location_part}.json"
    )


def query_result_status_summary(query_result: dict) -> dict:
    return {
        "query_id": query_result.get("query_id"),
        "category": query_result.get("category"),
        "role_phrase": query_result.get("role_phrase"),
        "uses_stack": query_result.get("uses_stack"),
        "query": query_result.get("query"),
        "ok": query_result.get("ok"),
        "raw_count": query_result.get("raw_count"),
        "response_time": query_result.get("response_time"),
        "usage": query_result.get("usage"),
        "request_id": query_result.get("request_id"),
        "error": query_result.get("error"),
    }


def build_structured_search_snapshot(
    query_plan: dict,
    query_results: list[dict],
    deduped_results: list[dict],
    report: dict,
    timestamp: datetime,
) -> dict:
    return {
        "snapshot_type": "structured-search",
        "timestamp": timestamp.isoformat(),
        "normalized_request": query_plan.get("input_snapshot"),
        "query_plan": query_plan,
        "report": report,
        "location_filter_report": report.get("location_filter_report"),
        "deduped_results": deduped_results,
        "query_results_summary": [
            query_result_status_summary(query_result)
            for query_result in query_results
        ],
        "query_results": query_results,
    }


def write_structured_search_snapshot(
    query_plan: dict,
    query_results: list[dict],
    deduped_results: list[dict],
    report: dict,
) -> Path:
    timestamp = datetime.now(timezone.utc)
    snapshot = build_structured_search_snapshot(
        query_plan,
        query_results,
        deduped_results,
        report,
        timestamp,
    )
    SEARCH_RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path = SEARCH_RUN_LOG_DIR / structured_search_snapshot_filename(
        query_plan.get("input_snapshot") or {},
        timestamp,
    )
    snapshot_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return snapshot_path


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
    try:
        write_structured_search_snapshot(
            query_plan,
            query_results,
            deduped_results,
            report,
        )
    except Exception:
        logger.warning("Failed to write structured search snapshot.", exc_info=True)

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
