from pathlib import Path
import copy
import json
import logging
import os
import re
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.domain_config import (
    AI_PLANNER_COVERAGE_NOT_CONFIGURED_WARNING,
    AI_PLANNER_COVERAGE_POLICIES,
    AI_PLANNER_COVERAGE_POLICY_VERSION,
    CANONICAL_ROLE_FAMILIES,
    CANDIDATE_QUALITY_SCORE_VERSION,
    CANDIDATE_SENIORITY_CONFIG,
    FORBIDDEN_AI_QUERY_TERMS,
    IMPLEMENTED_BACKEND_TECHNOLOGIES,
    JAVA_STACK_TERMS,
    JAVA_STACK_VALUES,
    KNOWN_BACKEND_TECHNOLOGIES,
    LOCATION_FILTER_CONFIG,
    MULTI_WAVE_DEFAULT_MAX_WAVES,
    MULTI_WAVE_DEFAULT_MIN_NEW_UNIQUE_PER_WAVE,
    MULTI_WAVE_DEFAULT_PATIENCE,
    MULTI_WAVE_MAX_ALLOWED_WAVES,
    PLANNER_MODE_AI,
    PLANNER_MODE_AI_WITH_FALLBACK,
    PLANNER_MODE_RULE_BASED,
    PLANNER_MODES,
    PROFILE_SOURCE_LINKEDIN_PUBLIC,
    PROFILE_SOURCE_VALUES,
    QUERY_PLAN_MAX_RESULTS,
    QUERY_PLAN_REPORTING_FIELDS,
    QUERY_PLANNER_VERSION,
    REVIEW_FLAG_TAXONOMY,
    SEARCH_BRIEF_STATUSES,
    SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION,
    SEARCH_BRIEF_STATUS_READY_FOR_PLANNING,
    SEARCH_DOMAIN_CONFIG,
    SEARCH_DEPTH_DEEP,
    SEARCH_DEPTH_STANDARD,
    SEARCH_DEPTH_VALUES,
    location_filter_config_for,
    search_domain_config_for,
)
from app.ai_planning import (
    ai_plan_output_assumptions,
    ai_plan_output_warnings,
    ai_planner_coverage_policy_for,
    ai_planner_coverage_policy_prompt,
    ai_query_planner_system_prompt,
    ai_query_planner_user_prompt,
    normalize_ai_text_list,
    query_has_allowed_scope_only,
    query_has_brief_signal,
    query_has_forbidden_terms,
    query_site_scopes,
    query_slot_is_stack_focused,
    query_slot_stack_terms,
    role_phrase_key,
    validate_ai_query_plan,
    validate_ai_query_plan_coverage,
)
from app.agent_tools import (
    AGENT_ACTION_BUILD_QUERY_PLAN,
    AGENT_QUERY_PLAN_ENDPOINT,
    AGENT_TOOL_APPROVAL_APPROVED,
    AGENT_TOOL_APPROVAL_NOT_REQUIRED,
    AGENT_TOOL_APPROVAL_REJECTED,
    AGENT_TOOL_APPROVAL_REQUIRED,
    AGENT_TOOLS_V0,
    EXECUTION_ACTION_MULTI_WAVE,
    EXECUTION_ACTION_SINGLE_WAVE,
    agent_tool_contract,
    execution_approval_metadata,
    validate_execution_approval,
)
from app.agent_plan import (
    AGENT_PLAN_STATUS_NEEDS_CLARIFICATION,
    AGENT_PLAN_STATUS_SUPPORTED,
    AGENT_PLAN_STATUS_UNSUPPORTED,
    agent_plan_language,
    agent_plan_needs_clarification_message,
    agent_plan_proposed_action,
    agent_plan_supported_message,
    agent_plan_unsupported_message,
    build_agent_plan_response as _build_agent_plan_response,
    build_agent_plan_response_with_wording as _build_agent_plan_response_with_wording,
    is_supported_agent_v0_baseline,
    validate_agent_query_plan_action,
)
from app.planning import (
    RuleBasedQueryPlannerV1,
    add_plan_validation_error,
    add_query_plan_fingerprint,
    build_query_slot,
    build_stack_or,
    planner_explanation_for_rule_based,
    query_plan_fingerprint,
    query_plan_fingerprint_payload,
    quote_query_value,
)
from app.schemas import (
    AIQueryPlanValidationRequest,
    AgentPlanRequest,
    AgentQueryPlanRequest,
    ExecutionApproval,
    MultiWaveStructuredSearchRequest,
    RecruiterChatMessage,
    RecruiterChatTurnRequest,
    SearchBrief,
    SearchRequest,
    StructuredSearchRequest,
)
from app.search_brief import (
    adapt_search_brief_to_structured_request,
    build_structured_request_from_brief,
    clarifying_question_for_missing_field,
    normalize_brief_stack_items,
    search_brief_fingerprint,
    search_brief_fingerprint_payload,
    search_brief_validation_response,
    validate_and_normalize_search_brief,
)
from app.search_validation import (
    add_validation_error,
    canonical_value,
    normalize_location_value,
    normalize_multi_wave_search_request,
    normalize_stack_items,
    normalize_structured_search_request,
)
from app.search_execution import (
    TAVILY_SEARCH_URL,
    run_multi_wave_query_plan_core,
    run_query_plan_wave,
    run_query_slot,
    run_tavily_query,
)
from app.search_snapshots import (
    SEARCH_RUN_LOG_DIR,
    build_structured_search_snapshot,
    query_result_status_summary,
    snapshot_slug,
    structured_search_snapshot_filename,
    write_structured_search_snapshot,
)
from app.candidate_quality import (
    build_candidate_quality,
    build_identity_score_component,
    build_location_score_component,
    build_quality_score,
    build_quality_score_penalties,
    build_role_quality,
    build_role_score_component,
    build_seniority_quality,
    build_seniority_score_component,
    build_stack_quality,
    build_stack_score_component,
    build_technology_quality,
    build_technology_score_component,
    candidate_text_sources,
    collect_seniority_evidence,
    collect_term_evidence,
    derived_role_phrases,
    find_role_match,
    merge_review_flags,
    normalize_review_flags,
    query_plan_by_id,
    query_source_stack_evidence,
    review_flag_detail,
    role_context_phrases,
    role_display_from_match,
    role_prefix_terms,
    score_component,
    seniority_display_from_evidence,
    terms_from_evidence,
)
from app.text_utils import (
    clean_headline_value,
    clean_profile_text,
    compact_spaces,
    find_term_match,
    normalize_text_list,
    normalize_text_value,
    ordered_unique,
    strip_linkedin_suffix,
    term_match_pattern,
)


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
STATIC_DIR = BASE_DIR / "static"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_RECRUITER_CHAT_MAX_COMPLETION_TOKENS = 1200
OPENAI_AI_PLANNER_MAX_COMPLETION_TOKENS = 3000
OPENAI_AGENT_WORDING_MAX_COMPLETION_TOKENS = 800
RECRUITER_CHAT_DEFAULT_PLANNER_MODE = PLANNER_MODE_RULE_BASED
RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION = "needs_clarification"
RECRUITER_CHAT_STATE_READY_FOR_PLANNING = "ready_for_planning"
RECRUITER_CHAT_STATE_REFUSED = "refused"
RECRUITER_CHAT_ALLOWED_MESSAGE_ROLES = {"assistant", "recruiter", "user"}
BRIEF_PATCH_ADD_STACK = "add_stack"
BRIEF_PATCH_REMOVE_STACK = "remove_stack"
BRIEF_PATCH_REPLACE_STACK = "replace_stack"
BRIEF_PATCH_SET_SENIORITY = "set_seniority"
BRIEF_PATCH_SET_SEARCH_DEPTH = "set_search_depth"
BRIEF_PATCH_RECONFIRM_FIELD = "reconfirm_field"
BRIEF_PATCH_UNSUPPORTED = "unsupported"
BRIEF_PATCH_NOOP = "noop"
RECRUITER_CHAT_PROHIBITED_RULES = [
    {
        "code": "direct_web_search_bypass",
        "message": "Direct web-search by the agent outside the approved backend pipeline is prohibited.",
        "patterns": [
            r"\bdirect web[- ]search\b",
            r"\boutside (the )?approved backend\b",
            r"\bwithout (the )?backend\b",
            r"в обход (backend|бекенд|бекэнда)",
            r"прям(ой|ую|ым).{0,30}web[- ]?search",
        ],
    },
    {
        "code": "linkedin_login",
        "message": "LinkedIn login is prohibited.",
        "patterns": [
            r"linkedin.{0,40}\b(log\s?in|login|sign in)\b",
            r"\b(log\s?in|login|sign in)\b.{0,40}linkedin",
            r"(зайди|войд[иу]|авторизуй|залогин).{0,40}linkedin",
            r"linkedin.{0,40}(зайди|войд[иу]|авторизуй|залогин)",
        ],
    },
    {
        "code": "linkedin_scraping_or_bypass",
        "message": "LinkedIn scraping or restriction bypass is prohibited.",
        "patterns": [
            r"\bscrap(e|ing|er)\b",
            r"\bcrawl(er|ing)?\b",
            r"\bbypass\b",
            r"restriction bypass",
            r"скрейп",
            r"парс.{0,40}linkedin",
            r"linkedin.{0,40}парс",
            r"обход.{0,40}(linkedin|огранич)",
        ],
    },
    {
        "code": "candidate_messaging",
        "message": "Candidate messaging or automatic outreach is prohibited.",
        "patterns": [
            r"\binmail\b",
            r"\bsend.{0,30}(message|dm|email).{0,40}(candidate|profile)\b",
            r"\bmessage.{0,40}(candidate|profile)\b",
            r"напиш[ии].{0,40}кандидат",
            r"отправ.{0,40}сообщ.{0,40}кандидат",
            r"свяж.{0,40}кандидат",
        ],
    },
    {
        "code": "account_actions",
        "message": "User or third-party account actions are prohibited.",
        "patterns": [
            r"\baccount action",
            r"\buse my account\b",
            r"\bmy linkedin account\b",
            r"мой.{0,30}аккаунт",
            r"через.{0,30}аккаунт",
            r"действ.{0,30}аккаунт",
        ],
    },
]
PLAN_STATUS_NEEDS_CLARIFICATION = "needs_clarification"
PLAN_STATUS_DRAFT = "draft_query_plan"
PLAN_STATUS_VALIDATED_NOT_EXECUTABLE = "validated_not_executable"
PLAN_STATUS_REJECTED = "rejected"
PLAN_STATUS_RULE_BASED_FALLBACK = "rule_based_fallback"
AGENT_WORDING_MODE_LLM_ASSISTED = "llm_assisted"
AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK = "deterministic_fallback"
AGENT_WORDING_FALLBACK_NOT_CONFIGURED = "openai_not_configured"
AGENT_WORDING_TIMEOUT_SECONDS = 8.0
AI_PLANNER_UNDER_COVERED_FALLBACK_REASON = (
    "AI plan is structurally valid, but coverage is too narrow for the baseline. "
    "Falling back to rule-based planner."
)

load_dotenv()

logger = logging.getLogger("engineers_search_engine")
app = FastAPI(title="Engineers Search POC")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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


def is_country_linkedin_profile_url(url: str, location_config: dict) -> bool:
    return (
        is_linkedin_profile_url(url)
        and linkedin_domain(url) in location_config["linkedin_domains"]
    )


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


def wave_source_from_result(query_result: dict) -> dict:
    return {
        "wave_id": query_result["wave_id"],
        "query_id": query_result["query_id"],
        "query": query_result["query"],
        "role_phrase": query_result.get("role_phrase"),
        "uses_stack": query_result.get("uses_stack", []),
    }


def append_unique_query_source(query_sources: list[dict], query_source: dict) -> None:
    if any(source["id"] == query_source["id"] for source in query_sources):
        return

    query_sources.append(query_source)


def append_unique_wave_source(wave_sources: list[dict], wave_source: dict) -> None:
    if any(
        source["wave_id"] == wave_source["wave_id"]
        and source["query_id"] == wave_source["query_id"]
        for source in wave_sources
    ):
        return

    wave_sources.append(wave_source)


def match_config_terms(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if find_term_match(text, term)]


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
    include_wave_sources: bool = False,
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
        if "wave_id" in query_result:
            contribution["wave_id"] = query_result["wave_id"]

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
            wave_source = (
                wave_source_from_result(query_result)
                if include_wave_sources and "wave_id" in query_result
                else None
            )
            current_item = candidates_by_url.get(normalized_url)
            if current_item is None:
                candidates_by_url[normalized_url] = {
                    "normalized_url": normalized_url,
                    "result": normalized_result,
                    "query_sources": [query_source],
                    "wave_sources": [wave_source] if wave_source else [],
                    "location_signals": [location_signal] if location_signal else [],
                }
            else:
                current_item["result"] = choose_more_complete_result(
                    current_item["result"],
                    normalized_result,
                )
                append_unique_query_source(current_item["query_sources"], query_source)
                if wave_source:
                    append_unique_wave_source(current_item["wave_sources"], wave_source)
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
            deduped_item = {
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
            if include_wave_sources:
                deduped_item["wave_sources"] = candidate.get("wave_sources", [])
            deduped_results.append(deduped_item)

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


def normalize_agent_language(value: str | None) -> str:
    return agent_plan_language(value, None)


def agent_response_quality_bucket(score: object) -> str:
    try:
        score_value = int(score)
    except (TypeError, ValueError):
        score_value = 0

    if score_value >= 80:
        return "strong"
    if score_value >= 60:
        return "review"
    return "weak"


def agent_response_quality_distribution(deduped_results: list[dict]) -> dict:
    distribution = {"strong": 0, "review": 0, "weak": 0}
    for item in deduped_results:
        result = item.get("result") or {}
        distribution[agent_response_quality_bucket(result.get("quality_score"))] += 1
    return distribution


def agent_response_signal_counts(deduped_results: list[dict]) -> dict:
    counts = {
        "target_or_close_role": 0,
        "exact_technology": 0,
        "selected_stack_visible": 0,
        "selected_stack_not_visible": 0,
        "seniority_not_visible": 0,
        "role_missing": 0,
        "technology_missing": 0,
        "target_location": 0,
        "weak_location": 0,
        "unknown_location": 0,
    }

    for item in deduped_results:
        result = item.get("result") or {}
        flags = set(result.get("review_flags") or [])
        location_status = (
            result.get("location_signal_status")
            or item.get("location_signal_status")
            or ""
        )

        if result.get("role_fit") == "target_or_close_role":
            counts["target_or_close_role"] += 1
        if result.get("technology_fit") == "exact":
            counts["exact_technology"] += 1
        if result.get("stack_fit") == "selected_stack_found":
            counts["selected_stack_visible"] += 1
        if "selected_stack_missing" in flags:
            counts["selected_stack_not_visible"] += 1
        if "seniority_missing" in flags:
            counts["seniority_not_visible"] += 1
        if "role_missing" in flags:
            counts["role_missing"] += 1
        if "technology_missing" in flags:
            counts["technology_missing"] += 1
        if location_status in {"target_location", "country_domain"}:
            counts["target_location"] += 1
        if location_status == "weak_history_only":
            counts["weak_location"] += 1
        if location_status == "unknown_non_country_domain":
            counts["unknown_location"] += 1

    return counts


def top_review_flag_counts(
    deduped_results: list[dict],
    limit: int = 5,
) -> list[dict[str, int | str]]:
    flag_counts: dict[str, int] = {}
    for item in deduped_results:
        result = item.get("result") or {}
        for flag in result.get("review_flags") or []:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

    return [
        {"flag": flag, "count": count}
        for flag, count in sorted(
            flag_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[:limit]
    ]


def agent_response_summary_facts(
    query_plan: dict,
    report: dict,
    deduped_results: list[dict],
) -> dict:
    input_snapshot = query_plan.get("input_snapshot") or {}
    return {
        "mode": report.get("mode", "single_wave"),
        "candidate_count": report.get("unique_profiles", len(deduped_results)),
        "raw_total": report.get("raw_total", 0),
        "displayed": report.get("displayed", 0),
        "queries_succeeded": report.get("queries_succeeded", 0),
        "queries_total": report.get("queries_total", len(query_plan.get("queries", []))),
        "quality_distribution": agent_response_quality_distribution(deduped_results),
        "strong_signal_counts": agent_response_signal_counts(deduped_results),
        "top_review_flags": top_review_flag_counts(deduped_results),
        "input_snapshot": input_snapshot,
    }


def agent_response_message_en(summary_facts: dict) -> str:
    quality = summary_facts["quality_distribution"]
    signals = summary_facts["strong_signal_counts"]
    candidate_count = summary_facts["candidate_count"]
    raw_total = summary_facts["raw_total"]
    queries_succeeded = summary_facts["queries_succeeded"]
    queries_total = summary_facts["queries_total"]

    return (
        f"Search completed: {candidate_count} unique candidates from {raw_total} "
        f"raw results, with {queries_succeeded}/{queries_total} queries succeeded. "
        f"Quality buckets: {quality['strong']} strong, {quality['review']} review, "
        f"{quality['weak']} weak. Strongest signals: exact Java evidence on "
        f"{signals['exact_technology']} candidates and target-role evidence on "
        f"{signals['target_or_close_role']} candidates. Main limitations: selected "
        f"stack was not visible in public snippets for "
        f"{signals['selected_stack_not_visible']} candidates, and seniority was not "
        f"visible for {signals['seniority_not_visible']} candidates. Suggested next "
        "step: review the strongest candidates first, then choose a non-executable "
        "next iteration option if the brief should change."
    )


def agent_response_message_ru(summary_facts: dict) -> str:
    quality = summary_facts["quality_distribution"]
    signals = summary_facts["strong_signal_counts"]
    candidate_count = summary_facts["candidate_count"]
    raw_total = summary_facts["raw_total"]
    queries_succeeded = summary_facts["queries_succeeded"]
    queries_total = summary_facts["queries_total"]

    return (
        f"\u041f\u043e\u0438\u0441\u043a \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d: {candidate_count} "
        f"\u0443\u043d\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u0445 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432 "
        f"\u0438\u0437 {raw_total} raw results, \u0443\u0441\u043f\u0435\u0448\u043d\u043e "
        f"{queries_succeeded}/{queries_total} \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432. "
        f"Quality buckets: {quality['strong']} strong, {quality['review']} review, "
        f"{quality['weak']} weak. \u0421\u0438\u043b\u044c\u043d\u044b\u0435 "
        f"\u0441\u0438\u0433\u043d\u0430\u043b\u044b: Java \u0432\u0438\u0434\u0435\u043d "
        f"\u0443 {signals['exact_technology']} \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432, "
        f"\u0446\u0435\u043b\u0435\u0432\u0430\u044f \u0440\u043e\u043b\u044c "
        f"\u0432\u0438\u0434\u043d\u0430 \u0443 {signals['target_or_close_role']}. "
        f"\u041e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u044f: selected stack "
        f"\u043d\u0435 \u0432\u0438\u0434\u0435\u043d \u0432 public snippets "
        f"\u0443 {signals['selected_stack_not_visible']} \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432, "
        f"seniority \u043d\u0435 \u0432\u0438\u0434\u0435\u043d \u0443 "
        f"{signals['seniority_not_visible']}. \u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 "
        "\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u044b\u0439 \u0448\u0430\u0433: "
        "\u043f\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c "
        "\u0441\u0438\u043b\u044c\u043d\u044b\u0445 "
        "\u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432 \u0438 "
        "\u0432\u044b\u0431\u0440\u0430\u0442\u044c \u043e\u0434\u043d\u0443 "
        "\u0438\u0437 non-executable next iteration options "
        "\u043d\u0438\u0436\u0435, \u0435\u0441\u043b\u0438 Search Brief "
        "\u043d\u0443\u0436\u043d\u043e \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c."
    )


def agent_response_quality_notes(
    language: str,
    summary_facts: dict,
) -> list[dict[str, object]]:
    quality = summary_facts["quality_distribution"]
    signals = summary_facts["strong_signal_counts"]

    if language == "ru":
        return [
            {
                "kind": "quality_distribution",
                "message": (
                    f"Quality buckets: {quality['strong']} strong, "
                    f"{quality['review']} review, {quality['weak']} weak."
                ),
                "facts": quality,
            },
            {
                "kind": "signals",
                "message": (
                    "Java \u0438 \u0440\u043e\u043b\u044c \u0441\u0447\u0438\u0442\u0430\u044e\u0442\u0441\u044f "
                    "\u0441\u0438\u043b\u044c\u043d\u044b\u043c\u0438 \u0442\u043e\u043b\u044c\u043a\u043e "
                    "\u043a\u043e\u0433\u0434\u0430 \u043e\u043d\u0438 \u0432\u0438\u0434\u043d\u044b "
                    "\u0432 public profile text."
                ),
                "facts": signals,
            },
        ]

    return [
        {
            "kind": "quality_distribution",
            "message": (
                f"Quality buckets: {quality['strong']} strong, "
                f"{quality['review']} review, {quality['weak']} weak."
            ),
            "facts": quality,
        },
        {
            "kind": "signals",
            "message": (
                "Java and role signals count as strong only when visible in "
                "public profile text."
            ),
            "facts": signals,
        },
    ]


def agent_response_limitations(language: str, summary_facts: dict) -> list[dict[str, object]]:
    signals = summary_facts["strong_signal_counts"]
    if language == "ru":
        return [
            {
                "kind": "public_snippets",
                "message": (
                    "\u041e\u0442\u0432\u0435\u0442 \u043e\u0441\u043d\u043e\u0432\u0430\u043d "
                    "\u0442\u043e\u043b\u044c\u043a\u043e \u043d\u0430 public snippets "
                    "\u0438 \u0434\u0430\u043d\u043d\u044b\u0445, \u0443\u0436\u0435 "
                    "\u0432\u0435\u0440\u043d\u0443\u0442\u044b\u0445 backend."
                ),
            },
            {
                "kind": "stack_visibility",
                "message": (
                    "Selected stack \u043d\u0435 \u0432\u0438\u0434\u0435\u043d "
                    f"\u0432 public snippets \u0443 {signals['selected_stack_not_visible']} "
                    "\u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432; "
                    "\u044d\u0442\u043e \u043d\u0435 \u0434\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0435\u0442, "
                    "\u0447\u0442\u043e \u0443 \u043d\u0438\u0445 \u043d\u0435\u0442 "
                    "\u044d\u0442\u043e\u0433\u043e stack."
                ),
            },
            {
                "kind": "seniority_visibility",
                "message": (
                    "Seniority \u043d\u0435 \u0432\u0438\u0434\u0435\u043d "
                    f"\u0443 {signals['seniority_not_visible']} "
                    "\u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432."
                ),
            },
        ]

    return [
        {
            "kind": "public_snippets",
            "message": (
                "This response is based only on public snippets and data already "
                "returned by the backend."
            ),
        },
        {
            "kind": "stack_visibility",
            "message": (
                "Selected stack is not visible in public snippets for "
                f"{signals['selected_stack_not_visible']} candidates; this does "
                "not prove they lack that stack."
            ),
        },
        {
            "kind": "seniority_visibility",
            "message": (
                f"Seniority is not visible for {signals['seniority_not_visible']} "
                "candidates."
            ),
        },
    ]


def agent_response_suggested_next_actions(
    language: str,
    summary_facts: dict,
) -> list[dict[str, object]]:
    if language == "ru":
        actions = [
            {
                "label": "\u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c top candidates",
                "description": (
                    "\u041d\u0430\u0447\u0430\u0442\u044c \u0441 strong bucket "
                    "\u0438 \u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c "
                    "\u043f\u0440\u043e\u0444\u0438\u043b\u0438 \u0432\u0440\u0443\u0447\u043d\u0443\u044e."
                ),
                "executable": False,
            },
            {
                "label": "\u0423\u0442\u043e\u0447\u043d\u0438\u0442\u044c stack",
                "description": (
                    "\u0415\u0441\u043b\u0438 stack \u0432 snippets "
                    "\u0432\u0438\u0434\u0435\u043d \u0441\u043b\u0430\u0431\u043e, "
                    "\u043c\u043e\u0436\u043d\u043e \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c "
                    "\u0438\u043b\u0438 \u0441\u0443\u0437\u0438\u0442\u044c stack."
                ),
                "executable": False,
            },
        ]
        return actions

    actions = [
        {
            "label": "Review top candidates",
            "description": "Start with the strong bucket and manually inspect profiles.",
            "executable": False,
        },
        {
            "label": "Adjust stack",
            "description": (
                "If stack visibility is weak in snippets, consider narrowing or "
                "changing selected stack terms."
            ),
            "executable": False,
        },
    ]
    return actions


def next_iteration_option(
    option_id: str,
    label: str,
    reason: str,
    operations: list[dict],
    *,
    requires_clarification: bool = False,
) -> dict[str, object]:
    return {
        "id": option_id,
        "label": label,
        "reason": reason,
        "proposed_brief_patch": build_brief_patch(
            source_message=f"next_iteration_option:{option_id}",
            operations=operations,
            requires_clarification=requires_clarification,
        ),
        "requires_approval_before_execution": True,
        "is_executable_now": False,
    }


def stack_term_visibility_counts(
    deduped_results: list[dict],
    stack_terms: list[str],
) -> dict[str, int]:
    counts = {term: 0 for term in stack_terms}
    if not stack_terms:
        return counts

    for item in deduped_results:
        result = item.get("result") or {}
        sources = candidate_text_sources(result)
        evidence = collect_term_evidence(sources, stack_terms)
        for term in terms_from_evidence(evidence, stack_terms):
            counts[term] += 1

    return counts


def next_iteration_stack_observation_threshold(candidate_count: int) -> int:
    if candidate_count <= 0:
        return 2
    return max(2, min(5, (candidate_count + 11) // 12))


def agent_response_next_iteration_options(
    query_plan: dict,
    summary_facts: dict,
    deduped_results: list[dict],
) -> list[dict[str, object]]:
    input_snapshot = (
        query_plan.get("input_snapshot")
        or summary_facts.get("input_snapshot")
        or {}
    )
    candidate_count = int(summary_facts.get("candidate_count") or 0)
    quality = summary_facts.get("quality_distribution") or {}
    signals = summary_facts.get("strong_signal_counts") or {}
    selected_stack = input_snapshot.get("stack") or []
    search_depth = input_snapshot.get("search_depth") or SEARCH_DEPTH_STANDARD
    mode = summary_facts.get("mode")
    domain_config = search_domain_config_for(
        input_snapshot.get("role_family") or "",
        input_snapshot.get("technology") or "",
    )
    allowed_stack = (
        domain_config.get("quality", {})
        .get("stack", {})
        .get("allowed_terms", [])
    )
    selected_stack = [term for term in selected_stack if term in allowed_stack]
    selected_counts = stack_term_visibility_counts(deduped_results, selected_stack)
    unselected_stack = [term for term in allowed_stack if term not in selected_stack]
    unselected_counts = stack_term_visibility_counts(deduped_results, unselected_stack)
    options: list[dict[str, object]] = []

    strong_count = int(quality.get("strong") or 0)
    if strong_count:
        options.append(
            next_iteration_option(
                "review_high_quality_candidates",
                "Review high-quality candidates first",
                (
                    f"{strong_count} candidates are in the strong quality bucket. "
                    "This is a review-focus suggestion only and does not change the Search Brief."
                ),
                [
                    {
                        "operation": BRIEF_PATCH_NOOP,
                        "field": "review_focus",
                        "value": "high_quality_candidates",
                    }
                ],
            )
        )

    visible_selected_stack = [
        term for term in selected_stack if selected_counts.get(term, 0) > 0
    ]
    missing_selected_stack = [
        term for term in selected_stack if selected_counts.get(term, 0) == 0
    ]
    if (
        len(selected_stack) > 1
        and visible_selected_stack
        and missing_selected_stack
        and visible_selected_stack != selected_stack
    ):
        options.append(
            next_iteration_option(
                "narrow_to_visible_selected_stack",
                "Narrow stack to visible selected terms",
                (
                    "Current results directly show "
                    f"{', '.join(visible_selected_stack)}, while "
                    f"{', '.join(missing_selected_stack)} is not visible in returned snippets."
                ),
                [
                    {
                        "operation": BRIEF_PATCH_REPLACE_STACK,
                        "field": "stack",
                        "values": visible_selected_stack[:3],
                    }
                ],
            )
        )

    observation_threshold = next_iteration_stack_observation_threshold(candidate_count)
    observed_unselected_stack = [
        (term, count)
        for term, count in unselected_counts.items()
        if count >= observation_threshold
    ]
    observed_unselected_stack.sort(key=lambda item: (-item[1], item[0]))
    if selected_stack and len(selected_stack) < 3 and observed_unselected_stack:
        term, count = observed_unselected_stack[0]
        options.append(
            next_iteration_option(
                "broaden_with_observed_stack",
                f"Broaden stack with {term}",
                (
                    f"{term} is visible in {count} returned candidates but is not "
                    "part of the selected stack."
                ),
                [
                    {
                        "operation": BRIEF_PATCH_ADD_STACK,
                        "field": "stack",
                        "value": term,
                    }
                ],
            )
        )

    if (
        selected_stack
        and not visible_selected_stack
        and int(signals.get("selected_stack_not_visible") or 0) > 0
    ):
        options.append(
            next_iteration_option(
                "clarify_stack_preference",
                "Clarify stack preference",
                (
                    "Selected stack is not directly visible in the returned public snippets. "
                    "The safest next step is to ask whether to keep or replace it."
                ),
                [
                    {
                        "operation": BRIEF_PATCH_RECONFIRM_FIELD,
                        "field": "stack",
                        "value": "current",
                    }
                ],
                requires_clarification=True,
            )
        )

    if search_depth != SEARCH_DEPTH_DEEP and mode != "multi_wave":
        options.append(
            next_iteration_option(
                "try_deep_search_depth",
                "Try deep search depth",
                (
                    "The current Search Brief uses standard depth. Deep depth is "
                    "a brief-level change that still requires Build Plan and approval."
                ),
                [
                    {
                        "operation": BRIEF_PATCH_SET_SEARCH_DEPTH,
                        "field": "search_depth",
                        "value": SEARCH_DEPTH_DEEP,
                    }
                ],
            )
        )

    return options[:4]


def build_agent_response(
    query_plan: dict,
    report: dict,
    deduped_results: list[dict],
    language: str | None = None,
) -> dict:
    normalized_language = normalize_agent_language(language)
    summary_facts = agent_response_summary_facts(
        query_plan,
        report,
        deduped_results,
    )
    message = (
        agent_response_message_ru(summary_facts)
        if normalized_language == "ru"
        else agent_response_message_en(summary_facts)
    )

    return {
        "message": message,
        "summary_facts": summary_facts,
        "quality_notes": agent_response_quality_notes(
            normalized_language,
            summary_facts,
        ),
        "limitations": agent_response_limitations(
            normalized_language,
            summary_facts,
        ),
        "suggested_next_actions": agent_response_suggested_next_actions(
            normalized_language,
            summary_facts,
        ),
        "next_iteration_options": agent_response_next_iteration_options(
            query_plan,
            summary_facts,
            deduped_results,
        ),
        "language": normalized_language,
        "source": "backend_returned_search_data",
        "requires_approval_for_execution": True,
    }


def agent_wording_hard_boundaries() -> list[str]:
    return [
        "No web search by the wording helper.",
        "No direct web-search by the agent outside the approved backend pipeline.",
        "No LinkedIn login.",
        "No LinkedIn scraping or restriction bypass.",
        "No candidate messaging or automatic outreach.",
        "No user or third-party account actions.",
        "No autonomous execution.",
        "Do not change facts, counts, actions, filters, scoring, location logic, dedupe, planner behavior, fingerprints, or approval state.",
        "Do not invent candidates or claim direct LinkedIn inspection.",
    ]


def agent_wording_system_prompt() -> str:
    return (
        "You are a bounded wording helper for a human-approved recruiting agent. "
        "Return one valid JSON object only. Your only job is to make the provided "
        "deterministic Agent Plan or Agent Response text clearer and more natural. "
        "You must not browse, search, call tools, access LinkedIn, log in, scrape, "
        "message candidates, act on accounts, change facts, change counts, change "
        "actions, change approval rules, or create executable next steps."
    )


def agent_wording_user_prompt(payload: dict) -> str:
    return json.dumps(
        {
            "task": "Rewrite only allowed user-facing text fields.",
            "required_output_shape": {
                "message": "string",
                "warnings": ["optional short strings"],
                "limitations": [
                    {
                        "kind": "existing limitation kind only",
                        "message": "optional rewritten limitation message",
                    }
                ],
            },
            "rules": [
                "Return JSON only.",
                "Use the requested language.",
                "Use only facts present in the payload.",
                "Do not add numbers outside allowed_numbers.",
                "Do not include query text.",
                "Do not create or change suggested_next_actions.",
                "Do not make any next step executable.",
                "Do not repeat prohibited behavior as a capability.",
            ],
            "payload": payload,
        },
        ensure_ascii=False,
        indent=2,
    )


def agent_wording_has_openai_config() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_MODEL"))


async def run_openai_json_agent_wording(
    payload: dict,
) -> tuple[dict | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return None, AGENT_WORDING_FALLBACK_NOT_CONFIGURED

    request_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": agent_wording_system_prompt()},
            {"role": "user", "content": agent_wording_user_prompt(payload)},
        ],
        "temperature": 0.2,
        "max_completion_tokens": OPENAI_AGENT_WORDING_MAX_COMPLETION_TOKENS,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=AGENT_WORDING_TIMEOUT_SECONDS) as client:
            response = await client.post(
                os.getenv("OPENAI_CHAT_COMPLETIONS_URL", OPENAI_CHAT_COMPLETIONS_URL),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=request_payload,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        return None, "openai_wording_timeout"
    except httpx.HTTPStatusError as exc:
        return None, f"openai_wording_http_{exc.response.status_code}"
    except httpx.HTTPError:
        return None, "openai_wording_request_failed"

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        return None, "openai_wording_empty_content"

    try:
        parsed_content = json.loads(content)
    except json.JSONDecodeError:
        return None, "openai_wording_invalid_json"
    if not isinstance(parsed_content, dict):
        return None, "openai_wording_wrong_shape"

    return parsed_content, None


def agent_wording_number_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(
            r"(?<![A-Za-z0-9_])-?\d+(?:\.\d+)?(?![A-Za-z0-9_])",
            value or "",
        )
    }


def agent_wording_allowed_numbers(value: object) -> set[str]:
    numbers: set[str] = set()
    if isinstance(value, bool) or value is None:
        return numbers
    if isinstance(value, int):
        numbers.add(str(value))
        return numbers
    if isinstance(value, float):
        numbers.add(str(value))
        if value.is_integer():
            numbers.add(str(int(value)))
        return numbers
    if isinstance(value, str):
        return agent_wording_number_tokens(value)
    if isinstance(value, list):
        for item in value:
            numbers.update(agent_wording_allowed_numbers(item))
        return numbers
    if isinstance(value, dict):
        for item in value.values():
            numbers.update(agent_wording_allowed_numbers(item))
        return numbers
    return numbers


def agent_wording_text_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(agent_wording_text_values(item))
        return values
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(agent_wording_text_values(item))
        return values
    return []


def agent_wording_has_disallowed_key(value: object) -> bool:
    disallowed_keys = {
        "summary_facts",
        "quality_notes",
        "suggested_next_actions",
        "proposed_action",
        "brief_fingerprint",
        "plan_fingerprint",
        "fingerprint",
        "counts",
        "approval_state",
        "approval_required",
        "requires_approval",
        "executable",
        "planner_mode",
        "filters",
        "scoring",
        "dedupe",
        "location_logic",
        "query",
        "queries",
        "query_plan",
        "candidate",
        "candidates",
        "url",
        "urls",
    }

    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in disallowed_keys:
                return True
            if agent_wording_has_disallowed_key(item):
                return True
    if isinstance(value, list):
        return any(agent_wording_has_disallowed_key(item) for item in value)
    return False


def agent_wording_language_matches(text: str, language: str) -> bool:
    has_cyrillic = bool(re.search(r"[\u0400-\u04ff]", text or ""))
    if language == "ru":
        return has_cyrillic
    return not has_cyrillic


def agent_wording_has_prohibited_content(text: str) -> bool:
    prohibited_patterns = [
        r"\bsite:linkedin\.com\b",
        r"\bdirect\s+web[- ]search\b",
        r"\bsearched\s+linkedin\s+directly\b",
        r"\blinkedin.{0,40}\b(log\s?in|login|sign in)\b",
        r"\b(log\s?in|login|sign in)\b.{0,40}linkedin",
        r"\b(scrape|scraping|scraper|crawl|crawler|bypass)\b",
        r"\binmail\b",
        r"\bsend.{0,30}(message|dm|email).{0,40}(candidate|profile)\b",
        r"\bmessage.{0,40}(candidate|profile)\b",
        r"\bcontact.{0,40}(candidate|profile)\b",
        r"\b(use|used).{0,30}(my|user|recruiter).{0,30}account\b",
        r"\bi\s+(will|can|am going to)\s+(run|execute|search|contact|message|scrape|log in)\b",
        r"\bi\s+(ran|executed|searched|contacted|messaged|scraped|logged in)\b",
        r"\bperfect\s+candidates?\b",
        r"\bguarantee(d|s)?\b",
        r"\u044f\s+(\u0437\u0430\u043f\u0443\u0449\u0443|\u0437\u0430\u043f\u0443\u0441\u0442\u0438\u043b|\u043d\u0430\u043f\u0438\u0441\u0430\u043b|\u0441\u0432\u044f\u0437\u0430\u043b\u0441\u044f)",
        r"\u0441\u043a\u0440\u0435\u0439\u043f|\u043f\u0430\u0440\u0441.{0,40}linkedin",
        r"\u0432\u043e\u0439\u0434.{0,40}linkedin|linkedin.{0,40}\u0432\u043e\u0439\u0434",
        r"\u0430\u043a\u043a\u0430\u0443\u043d\u0442",
        r"\u0433\u0430\u0440\u0430\u043d\u0442\u0438\u0440|\u0438\u0434\u0435\u0430\u043b\u044c\u043d",
    ]
    return any(re.search(pattern, text or "", re.IGNORECASE) for pattern in prohibited_patterns)


def normalize_agent_wording_warnings(value: object) -> list[str] | None:
    if value is None:
        return []
    if not isinstance(value, list):
        return None

    warnings: list[str] = []
    for item in value[:5]:
        if not isinstance(item, str):
            return None
        normalized_item = normalize_text_value(item)
        if normalized_item:
            warnings.append(normalized_item)
    return warnings


def normalize_agent_wording_limitations(value: object) -> list[dict[str, str]] | None:
    if value is None:
        return []
    if not isinstance(value, list):
        return None

    limitations: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            return None
        kind = normalize_text_value(str(item.get("kind") or ""))
        message = normalize_text_value(str(item.get("message") or ""))
        if not kind or not message:
            return None
        limitations.append({"kind": kind, "message": message})
    return limitations


def validate_agent_wording_output(
    llm_output: dict,
    *,
    language: str,
    allowed_numbers: set[str],
    existing_limitation_kinds: set[str] | None = None,
) -> tuple[dict | None, str | None]:
    if agent_wording_has_disallowed_key(llm_output):
        return None, "llm_output_disallowed_fields"

    allowed_keys = {"message", "warnings", "limitations"}
    if any(key not in allowed_keys for key in llm_output):
        return None, "llm_output_unknown_fields"

    message_value = llm_output.get("message")
    if not isinstance(message_value, str):
        return None, "llm_output_missing_message"
    message = normalize_text_value(message_value)
    if not message:
        return None, "llm_output_missing_message"

    warnings = normalize_agent_wording_warnings(llm_output.get("warnings"))
    if warnings is None:
        return None, "llm_output_invalid_warnings"

    limitations = normalize_agent_wording_limitations(llm_output.get("limitations"))
    if limitations is None:
        return None, "llm_output_invalid_limitations"

    if existing_limitation_kinds is not None:
        for limitation in limitations:
            if limitation["kind"] not in existing_limitation_kinds:
                return None, "llm_output_new_limitation_kind"

    combined_text = "\n".join(
        [message] + warnings + [limitation["message"] for limitation in limitations]
    )
    if not agent_wording_language_matches(combined_text, language):
        return None, "llm_output_wrong_language"
    if agent_wording_has_prohibited_content(combined_text):
        return None, "llm_output_unsafe_content"

    output_numbers = agent_wording_number_tokens(combined_text)
    if not output_numbers.issubset(allowed_numbers):
        return None, "llm_output_disallowed_numbers"

    return {
        "message": message,
        "warnings": warnings,
        "limitations": limitations,
    }, None


def with_agent_wording_metadata(
    value: dict,
    *,
    wording_mode: str,
    fallback_reason: str | None = None,
    llm_warnings: list[str] | None = None,
) -> dict:
    updated_value = copy.deepcopy(value)
    updated_value["wording_mode"] = wording_mode
    updated_value["fallback_reason"] = fallback_reason
    updated_value["llm_warnings"] = llm_warnings or []
    return updated_value


def agent_plan_wording_payload(
    agent_plan: dict,
    normalized_request: dict,
    language: str,
) -> dict:
    payload = {
        "wording_use_case": "agent_plan",
        "language": language,
        "deterministic_message": agent_plan.get("message"),
        "normalized_brief": agent_plan.get("input_snapshot") or {},
        "normalized_structured_request": normalized_request,
        "proposed_action": agent_plan.get("proposed_action") or {},
        "approval_requirement": {
            "build_plan_requires_approval": False,
            "search_execution_requires_explicit_approval": True,
        },
        "hard_boundaries": agent_wording_hard_boundaries(),
    }
    payload["allowed_numbers"] = sorted(agent_wording_allowed_numbers(payload))
    return payload


def agent_response_wording_payload(agent_response: dict) -> dict:
    payload = {
        "wording_use_case": "agent_response",
        "language": agent_response.get("language"),
        "deterministic_message": agent_response.get("message"),
        "summary_facts": agent_response.get("summary_facts") or {},
        "quality_notes": agent_response.get("quality_notes") or [],
        "limitations": agent_response.get("limitations") or [],
        "suggested_next_actions": agent_response.get("suggested_next_actions") or [],
        "requires_approval_for_execution": agent_response.get(
            "requires_approval_for_execution"
        ),
        "hard_boundaries": agent_wording_hard_boundaries(),
    }
    payload["allowed_numbers"] = sorted(agent_wording_allowed_numbers(payload))
    return payload


async def apply_llm_wording_to_agent_plan(
    agent_plan: dict,
    normalized_request: dict,
    language: str,
) -> dict:
    if not agent_wording_has_openai_config():
        return with_agent_wording_metadata(
            agent_plan,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=AGENT_WORDING_FALLBACK_NOT_CONFIGURED,
        )

    payload = agent_plan_wording_payload(agent_plan, normalized_request, language)
    llm_output, fallback_reason = await run_openai_json_agent_wording(payload)
    if fallback_reason or llm_output is None:
        return with_agent_wording_metadata(
            agent_plan,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=fallback_reason or "openai_wording_empty_output",
        )

    validated_output, validation_reason = validate_agent_wording_output(
        llm_output,
        language=language,
        allowed_numbers=set(payload["allowed_numbers"]),
    )
    if validation_reason or validated_output is None:
        return with_agent_wording_metadata(
            agent_plan,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=validation_reason or "llm_output_invalid",
        )

    updated_agent_plan = with_agent_wording_metadata(
        agent_plan,
        wording_mode=AGENT_WORDING_MODE_LLM_ASSISTED,
        llm_warnings=validated_output["warnings"],
    )
    updated_agent_plan["message"] = validated_output["message"]
    return updated_agent_plan


async def apply_llm_wording_to_agent_response(agent_response: dict) -> dict:
    if not agent_wording_has_openai_config():
        return with_agent_wording_metadata(
            agent_response,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=AGENT_WORDING_FALLBACK_NOT_CONFIGURED,
        )

    payload = agent_response_wording_payload(agent_response)
    existing_limitation_kinds = {
        str(item.get("kind"))
        for item in agent_response.get("limitations") or []
        if isinstance(item, dict) and item.get("kind")
    }
    llm_output, fallback_reason = await run_openai_json_agent_wording(payload)
    if fallback_reason or llm_output is None:
        return with_agent_wording_metadata(
            agent_response,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=fallback_reason or "openai_wording_empty_output",
        )

    validated_output, validation_reason = validate_agent_wording_output(
        llm_output,
        language=agent_response.get("language") or "en",
        allowed_numbers=set(payload["allowed_numbers"]),
        existing_limitation_kinds=existing_limitation_kinds,
    )
    if validation_reason or validated_output is None:
        return with_agent_wording_metadata(
            agent_response,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=validation_reason or "llm_output_invalid",
        )

    updated_agent_response = with_agent_wording_metadata(
        agent_response,
        wording_mode=AGENT_WORDING_MODE_LLM_ASSISTED,
        llm_warnings=validated_output["warnings"],
    )
    updated_agent_response["message"] = validated_output["message"]

    if validated_output["limitations"]:
        limitation_messages = {
            item["kind"]: item["message"]
            for item in validated_output["limitations"]
        }
        updated_limitations = []
        for limitation in updated_agent_response.get("limitations") or []:
            updated_limitation = dict(limitation)
            kind = updated_limitation.get("kind")
            if kind in limitation_messages:
                updated_limitation["message"] = limitation_messages[kind]
            updated_limitations.append(updated_limitation)
        updated_agent_response["limitations"] = updated_limitations

    return updated_agent_response


def build_agent_plan_response(request: AgentPlanRequest) -> dict:
    return _build_agent_plan_response(
        request,
        validation_error_formatter=validation_error_message,
    )


async def build_agent_plan_response_with_wording(request: AgentPlanRequest) -> dict:
    return await _build_agent_plan_response_with_wording(
        request,
        validation_error_formatter=validation_error_message,
        wording_applier=apply_llm_wording_to_agent_plan,
    )


def recruiter_chat_text(messages: list[RecruiterChatMessage]) -> str:
    return "\n".join(
        f"{normalize_text_value(message.role) or 'user'}: {message.content}"
        for message in messages
    )


def recruiter_chat_language(request: RecruiterChatTurnRequest) -> str:
    language = (normalize_text_value(request.language) or "").lower()
    if language.startswith(("ru", "рус")):
        return "ru"
    if language.startswith(("en", "англ")):
        return "en"

    text = recruiter_chat_text(request.messages)
    if re.search(r"[А-Яа-яЁёІіЇїЄє]", text):
        return "ru"

    return "en"


def latest_recruiter_chat_user_text(messages: list[RecruiterChatMessage]) -> str:
    for message in reversed(messages):
        role = (normalize_text_value(message.role) or "").lower()
        if role in {"user", "recruiter"}:
            return message.content

    if messages:
        return messages[-1].content

    return ""


def normalized_chat_control_text(text: str) -> str:
    lowered_text = (normalize_text_value(text) or "").lower()
    cleaned_text = re.sub(r"[\"'`“”‘’()\[\]{}<>]+", " ", lowered_text)
    cleaned_text = re.sub(r"[\s,!.?;:…/\\|+-]+", " ", cleaned_text)
    return compact_spaces(cleaned_text)


def is_greeting_only_chat_message(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return False

    greetings = {
        "hi",
        "hello",
        "hey",
        "hello there",
        "good morning",
        "good afternoon",
        "good evening",
        "привет",
        "приветствую",
        "здравствуй",
        "здравствуйте",
        "добрый день",
        "доброе утро",
        "добрый вечер",
    }
    return normalized_text in greetings


def is_near_empty_chat_message(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return True

    return len(normalized_text) <= 1


def text_matches_any_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def split_refinement_segments(text: str) -> list[str]:
    normalized_text = normalized_chat_control_text(text)
    return [
        segment.strip()
        for segment in re.split(r"\b(?:and|but|и|но)\b|[,;]+", normalized_text)
        if segment.strip()
    ]


def java_stack_terms_in_text(text: str) -> list[str]:
    lowered_text = (normalize_text_value(text) or "").lower()
    stack_terms: list[str] = []
    occupied_spans: list[tuple[int, int]] = []

    stack_aliases = sorted(JAVA_STACK_VALUES.items(), key=lambda item: len(item[0]), reverse=True)
    for alias, canonical_stack_item in stack_aliases:
        pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
        for match in re.finditer(pattern, lowered_text):
            span = match.span()
            if any(span[0] < end and start < span[1] for start, end in occupied_spans):
                continue
            occupied_spans.append(span)
            if canonical_stack_item not in stack_terms:
                stack_terms.append(canonical_stack_item)
            break

    return stack_terms


UNSUPPORTED_REFINEMENT_PATTERNS = [
    (r"(?<![a-z0-9])react(?![a-z0-9])", "stack", "React"),
    (r"(?<![a-z0-9])javascript(?![a-z0-9])", "technology", "JavaScript"),
    (r"(?<![a-z0-9])python(?![a-z0-9])", "technology", "Python"),
    (r"(?<![a-z0-9])node(?:\.js|js| js)(?![a-z0-9])", "technology", "Node.js"),
    (r"(?<![a-z0-9])c#(?![a-z0-9])", "technology", "C#"),
    (r"(?<![a-z0-9])go(?:lang)?(?![a-z0-9])", "technology", "Go"),
    (r"(?<![a-z0-9])php(?![a-z0-9])", "technology", "PHP"),
    (r"(?<![a-z0-9])poland(?![a-z0-9])|польш", "location", "Poland"),
    (r"(?<![a-z0-9])germany(?![a-z0-9])|герман", "location", "Germany"),
    (r"(?<![a-z0-9])frontend(?![a-z0-9])|фронтенд", "role_family", "Frontend Developer"),
    (r"(?<![a-z0-9])devops(?![a-z0-9])", "role_family", "DevOps"),
]


def unsupported_refinement_operations(text: str) -> list[dict]:
    lowered_text = (normalize_text_value(text) or "").lower()
    operations: list[dict] = []
    seen_values: set[tuple[str, str]] = set()

    for pattern, field_name, value in UNSUPPORTED_REFINEMENT_PATTERNS:
        if not re.search(pattern, lowered_text, flags=re.IGNORECASE):
            continue
        value_key = (field_name, value)
        if value_key in seen_values:
            continue
        seen_values.add(value_key)
        operations.append(
            {
                "operation": BRIEF_PATCH_UNSUPPORTED,
                "field": field_name,
                "value": value,
                "reason": "Unsupported value for the current Java/Ukraine flow.",
            }
        )

    return operations


ADD_REFINEMENT_PATTERNS = [
    r"\badd\b",
    r"\binclude\b",
    r"добав",
]
REMOVE_REFINEMENT_PATTERNS = [
    r"\bremove\b",
    r"\bdrop\b",
    r"\bexclude\b",
    r"\bwithout\b",
    r"\bno\b",
    r"убер",
    r"удал",
    r"исключ",
    r"\bбез\b",
]
REPLACE_REFINEMENT_PATTERNS = [
    r"\bonly\b",
    r"\breplace\b",
    r"остав.*только",
    r"\bтолько\b",
    r"замен",
]
REFINEMENT_INTENT_PATTERNS = (
    ADD_REFINEMENT_PATTERNS
    + REMOVE_REFINEMENT_PATTERNS
    + REPLACE_REFINEMENT_PATTERNS
    + [
        r"\bsenior\b",
        r"\bmiddle\b",
        r"\bjunior\b",
        r"\blead\b",
        r"сеньор|сениор|старш",
        r"мидл|middle",
        r"джун|junior",
        r"\bdeep\b|глубок",
        r"\bstandard\b|стандарт|обычн",
        r"\bищем\b",
    ]
)


def is_refinement_like_chat_message(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return False

    return (
        text_matches_any_pattern(normalized_text, REFINEMENT_INTENT_PATTERNS)
        or bool(unsupported_refinement_operations(normalized_text))
    )


def detected_seniority_value(text: str) -> str | None:
    lowered_text = normalized_chat_control_text(text)
    seniority_patterns = [
        (r"\blead\b|лид", "Lead"),
        (r"\bsenior\b|сеньор|сениор|старш", "Senior"),
        (r"\bmiddle\b|\bmid\b|мидл", "Middle"),
        (r"\bjunior\b|\bjun\b|джун", "Junior"),
    ]
    for pattern, value in seniority_patterns:
        if re.search(pattern, lowered_text, flags=re.IGNORECASE):
            return value
    return None


def detected_search_depth_value(text: str) -> str | None:
    lowered_text = normalized_chat_control_text(text)
    if re.search(r"\bdeep\b|глубок", lowered_text, flags=re.IGNORECASE):
        return SEARCH_DEPTH_DEEP
    if re.search(r"\bstandard\b|стандарт|обычн", lowered_text, flags=re.IGNORECASE):
        return SEARCH_DEPTH_STANDARD
    return None


def build_brief_patch(
    *,
    source_message: str,
    operations: list[dict],
    requires_clarification: bool = False,
    assistant_message: str | None = None,
) -> dict:
    return {
        "operations": operations,
        "source_message": source_message,
        "requires_clarification": requires_clarification,
        "assistant_message": assistant_message,
    }


def deterministic_brief_patch_from_message(
    text: str,
    language: str,
) -> dict | None:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return None

    operations: list[dict] = []

    replace_intent = text_matches_any_pattern(normalized_text, REPLACE_REFINEMENT_PATTERNS)
    if replace_intent:
        stack_terms = java_stack_terms_in_text(normalized_text)
        if stack_terms:
            operations.append(
                {
                    "operation": BRIEF_PATCH_REPLACE_STACK,
                    "field": "stack",
                    "values": stack_terms,
                }
            )
        operations.extend(unsupported_refinement_operations(normalized_text))
    else:
        for segment in split_refinement_segments(normalized_text):
            segment_stack_terms = java_stack_terms_in_text(segment)
            segment_unsupported_operations = unsupported_refinement_operations(segment)
            has_add_intent = text_matches_any_pattern(segment, ADD_REFINEMENT_PATTERNS)
            has_remove_intent = text_matches_any_pattern(segment, REMOVE_REFINEMENT_PATTERNS)

            if has_remove_intent:
                for stack_item in segment_stack_terms:
                    operations.append(
                        {
                            "operation": BRIEF_PATCH_REMOVE_STACK,
                            "field": "stack",
                            "value": stack_item,
                        }
                    )
                operations.extend(segment_unsupported_operations)
                continue

            if has_add_intent:
                for stack_item in segment_stack_terms:
                    operations.append(
                        {
                            "operation": BRIEF_PATCH_ADD_STACK,
                            "field": "stack",
                            "value": stack_item,
                        }
                    )
                operations.extend(segment_unsupported_operations)

    seniority = detected_seniority_value(normalized_text)
    if seniority:
        operations.append(
            {
                "operation": BRIEF_PATCH_SET_SENIORITY,
                "field": "seniority",
                "value": seniority,
            }
        )

    search_depth = detected_search_depth_value(normalized_text)
    if search_depth:
        operations.append(
            {
                "operation": BRIEF_PATCH_SET_SEARCH_DEPTH,
                "field": "search_depth",
                "value": search_depth,
            }
        )

    if (
        not operations
        and re.search(r"\b(java|ukraine|backend)\b|украин|україн", normalized_text)
        and re.search(r"\b(yes|same|correct|keep|ok)\b|да|верно|подтверж|оставим", normalized_text)
    ):
        operations.append(
            {
                "operation": BRIEF_PATCH_RECONFIRM_FIELD,
                "field": "search_brief",
                "value": "current",
            }
        )

    if not operations and is_refinement_like_chat_message(normalized_text):
        message = (
            "Уточни, что именно изменить в текущем Search Brief."
            if language == "ru"
            else "Please clarify what to change in the current Search Brief."
        )
        return build_brief_patch(
            source_message=text,
            operations=[],
            requires_clarification=True,
            assistant_message=message,
        )

    if not operations:
        return None

    requires_clarification = any(
        operation.get("operation") == BRIEF_PATCH_UNSUPPORTED
        for operation in operations
    )
    return build_brief_patch(
        source_message=text,
        operations=operations,
        requires_clarification=requires_clarification,
    )


def validate_recruiter_chat_messages(
    messages: list[RecruiterChatMessage],
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if not messages:
        add_validation_error(errors, "messages", "At least one chat message is required.")
        return errors

    for index, message in enumerate(messages):
        role = (normalize_text_value(message.role) or "").lower()
        if role not in RECRUITER_CHAT_ALLOWED_MESSAGE_ROLES:
            add_validation_error(
                errors,
                f"messages[{index}].role",
                "Unsupported chat message role.",
            )

    return errors


def detect_recruiter_chat_prohibited_requests(
    text: str,
) -> list[dict[str, str]]:
    normalized_text = compact_spaces(text).lower()
    detections: list[dict[str, str]] = []
    seen_codes: set[str] = set()

    for rule in RECRUITER_CHAT_PROHIBITED_RULES:
        for pattern in rule["patterns"]:
            if not re.search(pattern, normalized_text, flags=re.IGNORECASE):
                continue
            if rule["code"] in seen_codes:
                break
            seen_codes.add(rule["code"])
            detections.append(
                {
                    "field": "messages",
                    "code": rule["code"],
                    "message": rule["message"],
                }
            )
            break

    return detections


def recruiter_chat_refusal_message(language: str) -> str:
    if language == "ru":
        return (
            "Я не могу выполнять LinkedIn login, scraping, обход ограничений, "
            "автоматические сообщения кандидатам, действия с аккаунтами или "
            "прямой web-search в обход backend. Могу помочь сформировать Search Brief "
            "для approved backend pipeline."
        )

    return (
        "I cannot perform LinkedIn login, scraping, restriction bypass, automatic "
        "candidate messaging, account actions, or direct web-search outside the "
        "approved backend pipeline. I can help turn the request into a Search Brief."
    )


def localized_clarifying_question_for_missing_field(field: str, language: str) -> str:
    if language != "ru":
        return clarifying_question_for_missing_field(field)

    questions = {
        "role_family": "Какую роль ищем?",
        "technology": "Какая основная технология должна быть у кандидата?",
        "stack": (
            "Какие Java stack сигналы важны: Spring, Kafka, AWS, Hibernate "
            "или что-то другое?"
        ),
        "location": "В какой локации ищем кандидатов?",
        "search_depth": "Делаем standard или deep search?",
        "profile_sources": "Какие публичные источники профилей использовать?",
    }
    return questions.get(field, f"Уточни, пожалуйста, поле {field}.")


def one_clarifying_question(normalized_brief: dict, language: str) -> str | None:
    missing_fields = normalized_brief.get("missing_fields") or []
    if missing_fields:
        return localized_clarifying_question_for_missing_field(missing_fields[0], language)

    questions = normalized_brief.get("clarifying_questions") or []
    return questions[0] if questions else None


def build_search_brief_summary(normalized_brief: dict) -> dict:
    return {
        "role_family": normalized_brief.get("role_family"),
        "technology": normalized_brief.get("technology"),
        "stack": normalized_brief.get("stack") or [],
        "location": normalized_brief.get("location"),
        "seniority": normalized_brief.get("seniority") or "n/a",
        "search_depth": normalized_brief.get("search_depth"),
        "profile_sources": normalized_brief.get("profile_sources") or [],
        "assumptions": normalized_brief.get("assumptions") or [],
    }


def ready_for_planning_message(language: str) -> str:
    if language == "ru":
        return "Search Brief собран. Проверь summary и нажми Build Plan."

    return "Search Brief is ready. Review the summary and click Build Plan."


def validation_error_message(errors: list[dict[str, str]], language: str) -> str:
    if not errors:
        return ""

    message = errors[0].get("message", "Validation error.")
    if language == "ru":
        return f"Нужно уточнить brief: {message}"

    return f"The brief needs clarification: {message}"


def clean_search_brief_dict(brief: SearchBrief | None) -> dict:
    if not brief:
        return {}

    return {
        key: value
        for key, value in brief.model_dump().items()
        if value is not None and value != []
    }


def extract_chat_draft_brief(ai_output: dict) -> dict:
    draft_source = ai_output.get("draft_brief")
    if not isinstance(draft_source, dict):
        draft_source = ai_output

    draft: dict = {}
    for field_name in SearchBrief.model_fields:
        if field_name in draft_source:
            draft[field_name] = draft_source[field_name]

    top_level_assumptions = ai_output.get("assumptions")
    if "assumptions" not in draft and isinstance(top_level_assumptions, list):
        draft["assumptions"] = top_level_assumptions

    return draft


def deterministic_chat_brief_hints(source_text: str) -> dict:
    lowered_text = source_text.lower()
    hints: dict = {
        "source_text": source_text,
        "search_depth": SEARCH_DEPTH_STANDARD,
        "profile_sources": [PROFILE_SOURCE_LINKEDIN_PUBLIC],
    }

    if re.search(r"\bbackend\b|бекенд|бэкенд", lowered_text):
        hints["role_family"] = "Backend Developer"

    if re.search(r"\bjava\b", lowered_text) and not re.search(r"\bjavascript\b", lowered_text):
        hints["technology"] = "Java"
        hints["must_have"] = ["Java"]

    stack: list[str] = []
    for alias, canonical_stack_item in JAVA_STACK_VALUES.items():
        if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", lowered_text):
            if canonical_stack_item not in stack:
                stack.append(canonical_stack_item)
    if stack:
        hints["stack"] = stack[:3]
        hints["nice_to_have"] = stack[:3]

    if re.search(r"\bukraine\b|украин|україн|київ|киев|\bkyiv\b|\bkiev\b", lowered_text):
        hints["location"] = "Ukraine"

    if re.search(r"\bdeep\b|глубок", lowered_text):
        hints["search_depth"] = SEARCH_DEPTH_DEEP

    return hints


def should_merge_chat_brief_field(
    field_name: str,
    value: object,
    current_value: object,
) -> bool:
    if not current_value:
        return True

    if field_name == "role_family" and isinstance(value, str):
        return canonical_value(value, CANONICAL_ROLE_FAMILIES) is not None

    if field_name == "technology" and isinstance(value, str):
        return canonical_value(value, KNOWN_BACKEND_TECHNOLOGIES) is not None

    if field_name == "location" and isinstance(value, str):
        normalized_location = normalize_location_value(value)
        return bool(
            normalized_location and location_filter_config_for(normalized_location)
        )

    return True


def merge_chat_draft_brief(
    existing_brief: SearchBrief | None,
    llm_draft: dict,
    source_text: str,
) -> tuple[SearchBrief | None, list[dict[str, str]]]:
    merged = clean_search_brief_dict(existing_brief)

    for field_name, value in deterministic_chat_brief_hints(source_text).items():
        if value is not None and value != []:
            merged[field_name] = value

    for field_name, value in llm_draft.items():
        if value is None:
            continue
        if isinstance(value, str) and not normalize_text_value(value):
            continue
        if isinstance(value, list) and not value:
            continue
        if not should_merge_chat_brief_field(field_name, value, merged.get(field_name)):
            continue
        merged[field_name] = value

    if "source_text" not in merged:
        merged["source_text"] = source_text
    if "search_depth" not in merged:
        merged["search_depth"] = SEARCH_DEPTH_STANDARD
    if "profile_sources" not in merged:
        merged["profile_sources"] = [PROFILE_SOURCE_LINKEDIN_PUBLIC]

    try:
        return SearchBrief(**merged), []
    except ValidationError as exc:
        return None, [
            {
                "field": "draft_brief",
                "message": f"Chat draft brief is invalid: {error['msg']}",
            }
            for error in exc.errors()
        ]


def recruiter_chat_brief_system_prompt() -> str:
    return (
        "You are a recruiter chat-to-Search-Brief adapter. Return only valid JSON. "
        "Your only job is to convert chat messages into a draft SearchBrief. Do not "
        "build QueryPlans, do not execute searches, do not call tools, do not browse "
        "the web, do not scrape LinkedIn, do not log in to LinkedIn, do not send "
        "messages, and do not act on accounts."
    )


def recruiter_chat_brief_user_prompt(request: RecruiterChatTurnRequest) -> str:
    messages = [
        {
            "role": (normalize_text_value(message.role) or "user").lower(),
            "content": message.content,
        }
        for message in request.messages
    ]

    return json.dumps(
        {
            "task": "Extract or update a draft SearchBrief from the recruiter chat turn.",
            "required_output": {
                "draft_brief": {
                    "source_text": "Combined recruiter request text.",
                    "brief_status": "needs_clarification or ready_for_planning",
                    "role_family": "Backend Developer or null",
                    "technology": "Java or another explicitly requested backend technology",
                    "stack": ["up to 3 Java stack values"],
                    "location": "Target location string or null",
                    "seniority": "Optional seniority or null",
                    "must_have": [],
                    "nice_to_have": [],
                    "exclusions": [],
                    "search_depth": "standard or deep",
                    "profile_sources": ["linkedin_public"],
                    "notes": None,
                    "missing_fields": [],
                    "clarifying_questions": [],
                    "assumptions": [],
                },
                "assistant_message": "Short user-facing message, no more than one sentence.",
                "assumptions": [],
            },
            "messages": messages,
            "previous_draft_brief": clean_search_brief_dict(request.draft_brief),
            "language_hint": request.language,
            "supported_values": {
                "role_family": ["Backend Developer"],
                "implemented_technology": ["Java"],
                "known_backend_technologies": sorted(KNOWN_BACKEND_TECHNOLOGIES.values()),
                "java_stack": JAVA_STACK_TERMS,
                "search_depth": sorted(SEARCH_DEPTH_VALUES),
                "profile_sources": [PROFILE_SOURCE_LINKEDIN_PUBLIC],
            },
            "rules": [
                "Return one JSON object only.",
                "Do not invent hard constraints that the recruiter did not provide.",
                "If location, stack, role, or technology is missing, leave it null or empty.",
                "Map Java backend/software engineer intent to role_family Backend Developer.",
                "Set search_depth to standard unless the recruiter asks for deep search.",
                "Use profile_sources ['linkedin_public'] unless the user explicitly asks otherwise.",
                "Never include target_titles; planner owns title generation later.",
            ],
            "hard_boundaries": [
                "No direct web-search by the agent outside the approved backend pipeline.",
                "No LinkedIn login.",
                "No LinkedIn scraping or restriction bypass.",
                "No candidate messaging or automatic outreach.",
                "No user or third-party account actions.",
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


async def run_openai_json_recruiter_chat(
    request: RecruiterChatTurnRequest,
) -> tuple[dict | None, list[dict[str, str]]]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key:
        return None, [{"field": "openai_api_key", "message": "OPENAI_API_KEY is not configured."}]
    if not model:
        return None, [{"field": "openai_model", "message": "OPENAI_MODEL is not configured."}]

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": recruiter_chat_brief_system_prompt()},
            {"role": "user", "content": recruiter_chat_brief_user_prompt(request)},
        ],
        "temperature": 0.1,
        "max_completion_tokens": OPENAI_RECRUITER_CHAT_MAX_COMPLETION_TOKENS,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                os.getenv("OPENAI_CHAT_COMPLETIONS_URL", OPENAI_CHAT_COMPLETIONS_URL),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return None, [
            {
                "field": "openai",
                "message": (
                    "OpenAI recruiter chat request failed with status "
                    f"{exc.response.status_code}."
                ),
            }
        ]
    except httpx.HTTPError:
        return None, [{"field": "openai", "message": "OpenAI recruiter chat request failed."}]

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        return None, [{"field": "openai", "message": "OpenAI recruiter chat returned no content."}]

    try:
        parsed_content = json.loads(content)
    except json.JSONDecodeError:
        return None, [{"field": "openai", "message": "OpenAI recruiter chat returned invalid JSON."}]
    if not isinstance(parsed_content, dict):
        return None, [
            {
                "field": "openai",
                "message": "OpenAI recruiter chat returned JSON that is not an object.",
            }
        ]

    return parsed_content, []


def build_recruiter_chat_response(
    *,
    ok: bool,
    state: str,
    language: str,
    normalized_brief: dict | None = None,
    validation_errors: list[dict[str, str]] | None = None,
    next_question: str | None = None,
    planner_mode: str = RECRUITER_CHAT_DEFAULT_PLANNER_MODE,
    assistant_message: str | None = None,
    brief_patch: dict | None = None,
    brief_changed: bool = False,
    stale_state_should_clear: bool = False,
) -> dict:
    normalized_brief = normalized_brief or {}
    validation_errors = validation_errors or []
    can_build_plan = ok and state == RECRUITER_CHAT_STATE_READY_FOR_PLANNING
    summary = build_search_brief_summary(normalized_brief) if normalized_brief else None

    if assistant_message is None:
        if state == RECRUITER_CHAT_STATE_REFUSED:
            assistant_message = recruiter_chat_refusal_message(language)
        elif next_question:
            assistant_message = next_question
        elif can_build_plan:
            assistant_message = ready_for_planning_message(language)
        else:
            assistant_message = validation_error_message(validation_errors, language)

    build_plan_action = None
    if can_build_plan:
        build_plan_action = {
            "label": "Build Plan",
            "method": "POST",
            "endpoint": AGENT_QUERY_PLAN_ENDPOINT,
            "planner_mode": planner_mode,
            "search_brief": normalized_brief,
        }

    return {
        "ok": ok,
        "state": state,
        "language": language,
        "assistant_message": assistant_message,
        "next_question": next_question,
        "normalized_brief": normalized_brief or None,
        "summary": summary,
        "missing_fields": normalized_brief.get("missing_fields", []),
        "assumptions": normalized_brief.get("assumptions", []),
        "validation_errors": validation_errors,
        "recommended_planner_mode": planner_mode,
        "can_build_plan": can_build_plan,
        "build_plan_action": build_plan_action,
        "brief_patch": brief_patch,
        "brief_changed": brief_changed,
        "stale_state_should_clear": stale_state_should_clear,
    }


def recruiter_chat_onboarding_message(language: str) -> str:
    if language == "ru":
        return (
            "Привет. Расскажи, кого ищем: роль, основная технология, локация "
            "и 1-3 сигнала стека."
        )

    return (
        "Hi. Tell me who we should find: role, main technology, location, "
        "and 1-3 stack signals."
    )


def recruiter_chat_near_empty_message(language: str) -> str:
    if language == "ru":
        return (
            "Напиши, пожалуйста, кого ищем: роль, основная технология, локация "
            "и 1-3 сигнала стека."
        )

    return (
        "Please tell me who we should find: role, main technology, location, "
        "and 1-3 stack signals."
    )


def recruiter_chat_draft_preserved_message(
    normalized_brief: dict,
    language: str,
    fallback_message: str,
) -> str:
    if normalized_brief.get("brief_status") == SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        if language == "ru":
            return "Привет. Текущий Search Brief сохранен и готов к Build Plan."
        return "Hi. The current Search Brief is still saved and ready for Build Plan."

    next_question = one_clarifying_question(normalized_brief, language)
    if next_question:
        if language == "ru":
            return f"Текущий Search Brief сохранен. {next_question}"
        return f"The current Search Brief is still saved. {next_question}"

    return fallback_message


def build_recruiter_chat_onboarding_response(
    request: RecruiterChatTurnRequest,
    language: str,
    planner_mode: str,
    assistant_message: str,
) -> dict:
    if not request.draft_brief:
        return build_recruiter_chat_response(
            ok=True,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            assistant_message=assistant_message,
            planner_mode=planner_mode,
        )

    brief_response = search_brief_validation_response(request.draft_brief)
    normalized_brief = brief_response["normalized_brief"]
    validation_errors = brief_response["errors"]
    next_question = one_clarifying_question(normalized_brief, language)
    state = RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION
    ok = not validation_errors

    if ok and normalized_brief["brief_status"] == SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        state = RECRUITER_CHAT_STATE_READY_FOR_PLANNING

    return build_recruiter_chat_response(
        ok=ok,
        state=state,
        language=language,
        normalized_brief=normalized_brief,
        validation_errors=validation_errors,
        next_question=next_question,
        planner_mode=planner_mode,
        assistant_message=recruiter_chat_draft_preserved_message(
            normalized_brief,
            language,
            assistant_message,
        ),
    )


def patch_validation_error(field: str, code: str, message: str) -> dict[str, str]:
    return {
        "field": field,
        "code": code,
        "message": message,
    }


def normalized_brief_state_payload(normalized_brief: dict | None) -> dict:
    normalized_brief = normalized_brief or {}
    return {
        "brief_status": normalized_brief.get("brief_status"),
        "role_family": normalized_brief.get("role_family"),
        "technology": normalized_brief.get("technology"),
        "stack": normalized_brief.get("stack") or [],
        "location": normalized_brief.get("location"),
        "seniority": normalized_brief.get("seniority"),
        "must_have": normalized_brief.get("must_have") or [],
        "nice_to_have": normalized_brief.get("nice_to_have") or [],
        "exclusions": normalized_brief.get("exclusions") or [],
        "search_depth": normalized_brief.get("search_depth"),
        "profile_sources": normalized_brief.get("profile_sources") or [],
    }


def current_brief_validation_context(brief: SearchBrief | None) -> dict:
    if not brief:
        return {
            "ok": True,
            "state": RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            "normalized_brief": None,
            "errors": [],
            "next_question": None,
        }

    brief_response = search_brief_validation_response(brief)
    normalized_brief = brief_response["normalized_brief"]
    validation_errors = brief_response["errors"]
    state = RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION
    if not validation_errors and normalized_brief["brief_status"] == SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        state = RECRUITER_CHAT_STATE_READY_FOR_PLANNING

    return {
        "ok": not validation_errors,
        "state": state,
        "normalized_brief": normalized_brief,
        "errors": validation_errors,
        "next_question": None,
    }


def current_brief_context_for_language(
    brief: SearchBrief | None,
    language: str,
) -> dict:
    context = current_brief_validation_context(brief)
    normalized_brief = context.get("normalized_brief")
    if normalized_brief:
        context["next_question"] = one_clarifying_question(normalized_brief, language)
    return context


def refinement_requires_initial_brief_message(language: str) -> str:
    if language == "ru":
        return (
            "Сначала соберем initial Search Brief: роль, основная технология, "
            "локация и 1-3 stack сигнала."
        )
    return (
        "Let's collect the initial Search Brief first: role, main technology, "
        "location, and 1-3 stack signals."
    )


def unsupported_patch_message(language: str) -> str:
    if language == "ru":
        return (
            "Это изменение вне текущего Java/Ukraine flow. Уточни изменение "
            "в рамках Backend Developer, Java, Ukraine и поддержанного Java stack."
        )
    return (
        "That change is outside the current Java/Ukraine flow. Please refine it "
        "within Backend Developer, Java, Ukraine, and the supported Java stack."
    )


def last_stack_item_message(language: str) -> str:
    if language == "ru":
        return (
            "Нельзя убрать последний stack item без замены. Выбери replacement "
            "из поддержанного Java stack."
        )
    return (
        "I cannot remove the last stack item without a replacement. Choose a "
        "replacement from the supported Java stack."
    )


def patch_success_message(patch: dict, language: str, changed: bool) -> str:
    if not changed:
        if language == "ru":
            return "Search Brief не изменился. Текущий план можно оставить."
        return "Search Brief did not change. The current plan can stay as is."

    operations = patch.get("operations") or []
    operation_labels = [
        operation.get("operation", "update").replace("_", " ")
        for operation in operations
        if operation.get("operation") not in {BRIEF_PATCH_NOOP, BRIEF_PATCH_RECONFIRM_FIELD}
    ]
    action_summary = ", ".join(operation_labels) if operation_labels else "updated"

    if language == "ru":
        return f"Обновил Search Brief ({action_summary}). Нужно заново построить план."
    return f"Updated the Search Brief ({action_summary}). Build a new plan before search."


def build_recruiter_chat_patch_response(
    *,
    request: RecruiterChatTurnRequest,
    language: str,
    planner_mode: str,
    patch: dict,
    assistant_message: str,
    validation_errors: list[dict[str, str]] | None = None,
) -> dict:
    context = current_brief_context_for_language(request.draft_brief, language)
    return build_recruiter_chat_response(
        ok=context["ok"],
        state=context["state"],
        language=language,
        normalized_brief=context["normalized_brief"],
        validation_errors=validation_errors or [],
        next_question=context["next_question"],
        planner_mode=planner_mode,
        assistant_message=assistant_message,
        brief_patch=patch,
        brief_changed=False,
        stale_state_should_clear=False,
    )


def apply_brief_patch_to_draft(
    request: RecruiterChatTurnRequest,
    patch: dict,
    chat_text: str,
    language: str,
) -> tuple[SearchBrief | None, dict | None, bool, list[dict[str, str]], str]:
    operations = patch.get("operations") or []
    if any(operation.get("operation") == BRIEF_PATCH_UNSUPPORTED for operation in operations):
        patch["requires_clarification"] = True
        return None, None, False, [
            patch_validation_error(
                "brief_patch.operations",
                "unsupported_patch_operation",
                "Patch contains unsupported values for the current Java/Ukraine flow.",
            )
        ], unsupported_patch_message(language)

    candidate = clean_search_brief_dict(request.draft_brief)
    current_stack, current_stack_errors = normalize_brief_stack_items(candidate.get("stack"))
    if current_stack_errors:
        return None, None, False, current_stack_errors, validation_error_message(current_stack_errors, language)

    next_stack = current_stack[:]
    changed = False
    stack_touched = False

    for operation in operations:
        operation_name = operation.get("operation")

        if operation_name == BRIEF_PATCH_ADD_STACK:
            stack_item = canonical_value(operation.get("value"), JAVA_STACK_VALUES)
            if stack_item and stack_item not in next_stack:
                next_stack.append(stack_item)
                changed = True
                stack_touched = True
            continue

        if operation_name == BRIEF_PATCH_REMOVE_STACK:
            stack_item = canonical_value(operation.get("value"), JAVA_STACK_VALUES)
            if stack_item and stack_item in next_stack:
                next_stack.remove(stack_item)
                changed = True
                stack_touched = True
            continue

        if operation_name == BRIEF_PATCH_REPLACE_STACK:
            replacement_stack, replacement_errors = normalize_brief_stack_items(
                operation.get("values")
            )
            if replacement_errors:
                return None, None, False, replacement_errors, validation_error_message(
                    replacement_errors,
                    language,
                )
            if next_stack != replacement_stack:
                next_stack = replacement_stack
                changed = True
                stack_touched = True
            continue

        if operation_name == BRIEF_PATCH_SET_SENIORITY:
            seniority = normalize_text_value(operation.get("value"))
            if seniority and seniority != normalize_text_value(candidate.get("seniority")):
                candidate["seniority"] = seniority
                changed = True
            continue

        if operation_name == BRIEF_PATCH_SET_SEARCH_DEPTH:
            search_depth = normalize_text_value(operation.get("value"))
            if search_depth in SEARCH_DEPTH_VALUES and search_depth != (
                normalize_text_value(candidate.get("search_depth")) or SEARCH_DEPTH_STANDARD
            ):
                candidate["search_depth"] = search_depth
                changed = True
            continue

        if operation_name in {BRIEF_PATCH_RECONFIRM_FIELD, BRIEF_PATCH_NOOP}:
            continue

    if stack_touched and not next_stack:
        patch["requires_clarification"] = True
        return None, None, False, [
            patch_validation_error(
                "stack",
                "last_stack_item_requires_replacement",
                "Removing the last stack item requires a replacement.",
            )
        ], last_stack_item_message(language)

    if stack_touched:
        candidate["stack"] = next_stack
        candidate["nice_to_have"] = next_stack

    if changed:
        candidate["source_text"] = chat_text

    if "search_depth" not in candidate:
        candidate["search_depth"] = SEARCH_DEPTH_STANDARD
    if "profile_sources" not in candidate:
        candidate["profile_sources"] = [PROFILE_SOURCE_LINKEDIN_PUBLIC]

    try:
        candidate_brief = SearchBrief(**candidate)
    except ValidationError as exc:
        return None, None, False, [
            {
                "field": "brief_patch",
                "message": f"Patched Search Brief is invalid: {error['msg']}",
            }
            for error in exc.errors()
        ], validation_error_message([], language)

    candidate_response = search_brief_validation_response(candidate_brief)
    candidate_errors = candidate_response["errors"]
    if candidate_errors:
        patch["requires_clarification"] = True
        return None, None, False, candidate_errors, validation_error_message(
            candidate_errors,
            language,
        )

    existing_context = current_brief_context_for_language(request.draft_brief, language)
    existing_payload = normalized_brief_state_payload(existing_context["normalized_brief"])
    candidate_payload = normalized_brief_state_payload(candidate_response["normalized_brief"])
    changed = changed and existing_payload != candidate_payload

    return (
        candidate_brief,
        candidate_response["normalized_brief"],
        changed,
        [],
        patch_success_message(patch, language, changed),
    )


def build_recruiter_chat_refinement_response(
    request: RecruiterChatTurnRequest,
    language: str,
    planner_mode: str,
    patch: dict,
    chat_text: str,
) -> dict:
    if not request.draft_brief:
        patch["requires_clarification"] = True
        message = refinement_requires_initial_brief_message(language)
        patch["assistant_message"] = message
        return build_recruiter_chat_response(
            ok=True,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            assistant_message=message,
            planner_mode=planner_mode,
            brief_patch=patch,
            brief_changed=False,
            stale_state_should_clear=False,
        )

    if patch.get("requires_clarification"):
        message = patch.get("assistant_message") or unsupported_patch_message(language)
        patch["assistant_message"] = message
        return build_recruiter_chat_patch_response(
            request=request,
            language=language,
            planner_mode=planner_mode,
            patch=patch,
            assistant_message=message,
            validation_errors=[
                patch_validation_error(
                    "brief_patch.operations",
                    "patch_requires_clarification",
                    message,
                )
            ],
        )

    candidate_brief, normalized_brief, changed, patch_errors, message = apply_brief_patch_to_draft(
        request,
        patch,
        chat_text,
        language,
    )
    if patch_errors or candidate_brief is None or normalized_brief is None:
        patch["assistant_message"] = message
        return build_recruiter_chat_patch_response(
            request=request,
            language=language,
            planner_mode=planner_mode,
            patch=patch,
            assistant_message=message,
            validation_errors=patch_errors,
        )

    patch["assistant_message"] = message
    next_question = one_clarifying_question(normalized_brief, language)
    state = RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION
    if normalized_brief["brief_status"] == SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        state = RECRUITER_CHAT_STATE_READY_FOR_PLANNING

    return build_recruiter_chat_response(
        ok=True,
        state=state,
        language=language,
        normalized_brief=normalized_brief,
        validation_errors=[],
        next_question=next_question,
        planner_mode=planner_mode,
        assistant_message=message,
        brief_patch=patch,
        brief_changed=changed,
        stale_state_should_clear=changed,
    )


async def recruiter_chat_turn_response(request: RecruiterChatTurnRequest) -> dict:
    language = recruiter_chat_language(request)
    planner_mode = request.planner_mode or RECRUITER_CHAT_DEFAULT_PLANNER_MODE

    if planner_mode not in PLANNER_MODES:
        return build_recruiter_chat_response(
            ok=False,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            validation_errors=[
                {
                    "field": "planner_mode",
                    "message": "Unsupported planner mode.",
                }
            ],
            planner_mode=RECRUITER_CHAT_DEFAULT_PLANNER_MODE,
        )

    message_errors = validate_recruiter_chat_messages(request.messages)
    if message_errors:
        return build_recruiter_chat_response(
            ok=False,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            validation_errors=message_errors,
            planner_mode=planner_mode,
        )

    chat_text = recruiter_chat_text(request.messages)
    prohibited_errors = detect_recruiter_chat_prohibited_requests(chat_text)
    if prohibited_errors:
        return build_recruiter_chat_response(
            ok=False,
            state=RECRUITER_CHAT_STATE_REFUSED,
            language=language,
            validation_errors=prohibited_errors,
            planner_mode=planner_mode,
        )

    latest_user_text = latest_recruiter_chat_user_text(request.messages)
    if is_greeting_only_chat_message(latest_user_text):
        return build_recruiter_chat_onboarding_response(
            request,
            language,
            planner_mode,
            recruiter_chat_onboarding_message(language),
        )

    if is_near_empty_chat_message(latest_user_text):
        return build_recruiter_chat_onboarding_response(
            request,
            language,
            planner_mode,
            recruiter_chat_near_empty_message(language),
        )

    brief_patch = deterministic_brief_patch_from_message(latest_user_text, language)
    if brief_patch is not None:
        return build_recruiter_chat_refinement_response(
            request,
            language,
            planner_mode,
            brief_patch,
            chat_text,
        )

    ai_output, ai_errors = await run_openai_json_recruiter_chat(request)
    if ai_errors or ai_output is None:
        return build_recruiter_chat_response(
            ok=False,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            validation_errors=ai_errors,
            planner_mode=planner_mode,
        )

    brief, draft_errors = merge_chat_draft_brief(
        request.draft_brief,
        extract_chat_draft_brief(ai_output),
        chat_text,
    )
    if draft_errors or brief is None:
        return build_recruiter_chat_response(
            ok=False,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            validation_errors=draft_errors,
            planner_mode=planner_mode,
        )

    brief_response = search_brief_validation_response(brief)
    normalized_brief = brief_response["normalized_brief"]
    validation_errors = brief_response["errors"]
    next_question = one_clarifying_question(normalized_brief, language)
    brief_changed = normalized_brief_state_payload(
        current_brief_context_for_language(request.draft_brief, language)["normalized_brief"]
    ) != normalized_brief_state_payload(normalized_brief)

    if validation_errors:
        return build_recruiter_chat_response(
            ok=False,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            normalized_brief=normalized_brief,
            validation_errors=validation_errors,
            next_question=next_question,
            planner_mode=planner_mode,
            brief_changed=brief_changed,
            stale_state_should_clear=brief_changed,
        )

    if normalized_brief["brief_status"] != SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        return build_recruiter_chat_response(
            ok=True,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            normalized_brief=normalized_brief,
            next_question=next_question,
            planner_mode=planner_mode,
            brief_changed=brief_changed,
            stale_state_should_clear=brief_changed,
        )

    return build_recruiter_chat_response(
        ok=True,
        state=RECRUITER_CHAT_STATE_READY_FOR_PLANNING,
        language=language,
        normalized_brief=normalized_brief,
        planner_mode=planner_mode,
        brief_changed=brief_changed,
        stale_state_should_clear=brief_changed,
    )


def build_agent_rule_based_plan_response(
    normalized_brief: dict,
    normalized_request: dict,
) -> dict:
    query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
    plan_fingerprint = query_plan_fingerprint(query_plan)
    return {
        "ok": True,
        "planner_mode": PLANNER_MODE_RULE_BASED,
        "plan_status": PLAN_STATUS_VALIDATED_NOT_EXECUTABLE,
        "execution_allowed": False,
        "normalized_brief": normalized_brief,
        "adapted_structured_request": normalized_request,
        "explanation": planner_explanation_for_rule_based(),
        "query_plan": add_query_plan_fingerprint(query_plan),
        "plan_fingerprint": plan_fingerprint,
        "draft_query_plan": None,
        "validation_errors": [],
        "warnings": [],
        "assumptions": normalized_brief.get("assumptions", []),
        "approval_required": False,
        "execution_approval_required": True,
        "approval_notice": (
            "Search plan is ready. Review the queries before running search."
        ),
    }


def build_rule_based_fallback_response(
    normalized_brief: dict,
    normalized_request: dict,
    fallback_reason: str,
    validation_errors: list[dict] | None = None,
    warnings: list[str] | None = None,
    draft_query_plan: dict | None = None,
    coverage_policy: dict | None = None,
    repair_attempts: int = 0,
) -> dict:
    query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
    plan_fingerprint = query_plan_fingerprint(query_plan)
    return {
        "ok": True,
        "planner_mode": PLAN_STATUS_RULE_BASED_FALLBACK,
        "plan_status": PLAN_STATUS_RULE_BASED_FALLBACK,
        "execution_allowed": False,
        "normalized_brief": normalized_brief,
        "adapted_structured_request": normalized_request,
        "explanation": planner_explanation_for_rule_based(),
        "fallback_reason": fallback_reason,
        "query_plan": add_query_plan_fingerprint(query_plan),
        "plan_fingerprint": plan_fingerprint,
        "draft_query_plan": draft_query_plan,
        "validation_errors": validation_errors or [],
        "warnings": warnings or [],
        "assumptions": normalized_brief.get("assumptions", []),
        "coverage_policy": coverage_policy,
        "repair_attempts": repair_attempts,
        "approval_required": False,
        "execution_approval_required": True,
        "approval_notice": (
            "Fallback search plan is ready. Review the queries before running search."
        ),
    }


async def run_openai_json_planner(
    normalized_brief: dict,
    normalized_request: dict,
    repair_feedback: list[dict[str, str]] | None = None,
    previous_draft_plan: dict | None = None,
) -> tuple[dict | None, list[dict[str, str]]]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key:
        return None, [{"field": "openai_api_key", "message": "OPENAI_API_KEY is not configured."}]
    if not model:
        return None, [{"field": "openai_model", "message": "OPENAI_MODEL is not configured."}]

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": ai_query_planner_system_prompt()},
            {
                "role": "user",
                "content": ai_query_planner_user_prompt(
                    normalized_brief,
                    normalized_request,
                    repair_feedback=repair_feedback,
                    previous_draft_plan=previous_draft_plan,
                ),
            },
        ],
        "temperature": 0.2,
        "max_completion_tokens": OPENAI_AI_PLANNER_MAX_COMPLETION_TOKENS,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                os.getenv("OPENAI_CHAT_COMPLETIONS_URL", OPENAI_CHAT_COMPLETIONS_URL),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return None, [
            {
                "field": "openai",
                "message": f"OpenAI planner request failed with status {exc.response.status_code}.",
            }
        ]
    except httpx.HTTPError:
        return None, [{"field": "openai", "message": "OpenAI planner request failed."}]

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        return None, [{"field": "openai", "message": "OpenAI planner returned no content."}]

    try:
        parsed_content = json.loads(content)
    except json.JSONDecodeError:
        return None, [{"field": "openai", "message": "OpenAI planner returned invalid JSON."}]
    if not isinstance(parsed_content, dict):
        return None, [{"field": "openai", "message": "OpenAI planner returned JSON that is not an object."}]

    return parsed_content, []


def merge_warning_lists(*warning_lists: list[str]) -> list[str]:
    merged_warnings: list[str] = []
    seen_warnings: set[str] = set()

    for warning_list in warning_lists:
        for warning in warning_list:
            if warning and warning not in seen_warnings:
                seen_warnings.add(warning)
                merged_warnings.append(warning)

    return merged_warnings


def build_ai_plan_rejected_response(
    normalized_brief: dict,
    normalized_request: dict,
    ai_output: dict | None,
    draft_plan: dict | None,
    validation_errors: list[dict[str, str]],
    fallback_reason: str,
    warnings: list[str] | None = None,
    coverage_policy: dict | None = None,
    repair_attempts: int = 0,
) -> dict:
    fallback_query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
    return {
        "ok": False,
        "planner_mode": PLANNER_MODE_AI,
        "plan_status": PLAN_STATUS_REJECTED,
        "execution_allowed": False,
        "normalized_brief": normalized_brief,
        "adapted_structured_request": normalized_request,
        "explanation": ai_output.get("explanation") if isinstance(ai_output, dict) else None,
        "draft_query_plan": draft_plan,
        "validation_errors": validation_errors,
        "errors": validation_errors,
        "warnings": merge_warning_lists(
            ai_plan_output_warnings(ai_output),
            warnings or [],
        ),
        "assumptions": ai_plan_output_assumptions(ai_output),
        "coverage_policy": coverage_policy,
        "repair_attempts": repair_attempts,
        "fallback_available": True,
        "fallback_reason": fallback_reason,
        "fallback_query_plan": add_query_plan_fingerprint(fallback_query_plan),
        "fallback_plan_fingerprint": query_plan_fingerprint(fallback_query_plan),
        "approval_required": False,
        "execution_approval_required": True,
        "approval_notice": "A fallback plan is available but not executed. Search execution requires approval.",
    }


def build_valid_ai_plan_response(
    normalized_brief: dict,
    normalized_request: dict,
    ai_output: dict,
    draft_plan: dict,
    validated_plan: dict,
    warnings: list[str],
    coverage_policy: dict | None = None,
    repair_attempts: int = 0,
) -> dict:
    plan_fingerprint = query_plan_fingerprint(validated_plan)

    return {
        "ok": True,
        "planner_mode": PLANNER_MODE_AI,
        "plan_status": PLAN_STATUS_VALIDATED_NOT_EXECUTABLE,
        "execution_allowed": False,
        "normalized_brief": normalized_brief,
        "adapted_structured_request": normalized_request,
        "explanation": ai_output.get("explanation"),
        "query_plan": add_query_plan_fingerprint(validated_plan),
        "plan_fingerprint": plan_fingerprint,
        "draft_query_plan": draft_plan,
        "validation_errors": [],
        "warnings": merge_warning_lists(
            ai_plan_output_warnings(ai_output),
            warnings,
        ),
        "assumptions": ai_plan_output_assumptions(ai_output),
        "coverage_policy": coverage_policy,
        "repair_attempts": repair_attempts,
        "approval_required": False,
        "execution_approval_required": True,
        "approval_notice": "This AI plan is validated but not executed yet. Search execution requires approval.",
    }


async def build_ai_query_plan_response(
    normalized_brief: dict,
    normalized_request: dict,
    planner_mode: str,
) -> dict:
    ai_output, ai_errors = await run_openai_json_planner(
        normalized_brief,
        normalized_request,
    )
    if ai_errors:
        fallback_query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
        if planner_mode == PLANNER_MODE_AI_WITH_FALLBACK:
            return build_rule_based_fallback_response(
                normalized_brief,
                normalized_request,
                "AI planner request failed.",
                ai_errors,
            )
        return {
            "ok": False,
            "planner_mode": PLANNER_MODE_AI,
            "plan_status": PLAN_STATUS_REJECTED,
            "execution_allowed": False,
            "normalized_brief": normalized_brief,
            "adapted_structured_request": normalized_request,
            "errors": ai_errors,
            "validation_errors": ai_errors,
            "fallback_available": True,
            "fallback_reason": "AI planner request failed.",
            "fallback_query_plan": add_query_plan_fingerprint(fallback_query_plan),
            "fallback_plan_fingerprint": query_plan_fingerprint(fallback_query_plan),
            "approval_required": False,
            "execution_approval_required": True,
            "approval_notice": "A fallback plan is available but not executed. Search execution requires approval.",
        }

    draft_plan = ai_output.get("draft_query_plan") if isinstance(ai_output, dict) else None
    validated_plan, validation_errors = validate_ai_query_plan(
        draft_plan,
        normalized_brief,
        normalized_request,
    )
    if validation_errors:
        if planner_mode == PLANNER_MODE_AI_WITH_FALLBACK:
            return build_rule_based_fallback_response(
                normalized_brief,
                normalized_request,
                "AI plan failed validation.",
                validation_errors,
                warnings=ai_plan_output_warnings(ai_output),
                draft_query_plan=draft_plan,
            )
        return build_ai_plan_rejected_response(
            normalized_brief,
            normalized_request,
            ai_output,
            draft_plan,
            validation_errors,
            "AI plan failed validation.",
        )

    coverage_errors, coverage_warnings, coverage_policy = validate_ai_query_plan_coverage(
        validated_plan,
        normalized_brief,
        normalized_request,
    )
    if coverage_errors:
        if planner_mode == PLANNER_MODE_AI_WITH_FALLBACK and coverage_policy:
            repair_output, repair_errors = await run_openai_json_planner(
                normalized_brief,
                normalized_request,
                repair_feedback=coverage_errors,
                previous_draft_plan=draft_plan,
            )
            repair_draft_plan = (
                repair_output.get("draft_query_plan")
                if isinstance(repair_output, dict)
                else None
            )
            if repair_errors:
                return build_rule_based_fallback_response(
                    normalized_brief,
                    normalized_request,
                    "AI plan failed coverage quality and repair request failed.",
                    coverage_errors + repair_errors,
                    warnings=coverage_warnings,
                    draft_query_plan=draft_plan,
                    coverage_policy=coverage_policy,
                    repair_attempts=1,
                )

            repaired_plan, repair_validation_errors = validate_ai_query_plan(
                repair_draft_plan,
                normalized_brief,
                normalized_request,
            )
            if repair_validation_errors:
                return build_rule_based_fallback_response(
                    normalized_brief,
                    normalized_request,
                    "AI repaired plan failed validation.",
                    repair_validation_errors,
                    warnings=merge_warning_lists(
                        coverage_warnings,
                        ai_plan_output_warnings(repair_output),
                    ),
                    draft_query_plan=repair_draft_plan,
                    coverage_policy=coverage_policy,
                    repair_attempts=1,
                )

            (
                repair_coverage_errors,
                repair_coverage_warnings,
                repair_coverage_policy,
            ) = validate_ai_query_plan_coverage(
                repaired_plan,
                normalized_brief,
                normalized_request,
            )
            repair_warnings = merge_warning_lists(
                coverage_warnings,
                repair_coverage_warnings,
                ["AI plan required one coverage repair attempt."],
            )
            if repair_coverage_errors:
                return build_rule_based_fallback_response(
                    normalized_brief,
                    normalized_request,
                    "AI plan failed coverage quality after one repair attempt.",
                    repair_coverage_errors,
                    warnings=merge_warning_lists(
                        repair_warnings,
                        ai_plan_output_warnings(repair_output),
                    ),
                    draft_query_plan=repair_draft_plan,
                    coverage_policy=repair_coverage_policy or coverage_policy,
                    repair_attempts=1,
                )

            return build_valid_ai_plan_response(
                normalized_brief,
                normalized_request,
                repair_output,
                repair_draft_plan,
                repaired_plan,
                repair_warnings,
                coverage_policy=repair_coverage_policy or coverage_policy,
                repair_attempts=1,
            )

        if planner_mode == PLANNER_MODE_AI_WITH_FALLBACK:
            return build_rule_based_fallback_response(
                normalized_brief,
                normalized_request,
                AI_PLANNER_UNDER_COVERED_FALLBACK_REASON,
                coverage_errors,
                warnings=coverage_warnings,
                draft_query_plan=draft_plan,
                coverage_policy=coverage_policy,
            )

        return build_ai_plan_rejected_response(
            normalized_brief,
            normalized_request,
            ai_output,
            draft_plan,
            coverage_errors,
            AI_PLANNER_UNDER_COVERED_FALLBACK_REASON,
            warnings=coverage_warnings,
            coverage_policy=coverage_policy,
        )

    return build_valid_ai_plan_response(
        normalized_brief,
        normalized_request,
        ai_output,
        draft_plan,
        validated_plan,
        coverage_warnings,
        coverage_policy=coverage_policy,
    )


async def run_multi_wave_query_plan(
    query_plan: dict,
    settings: dict,
) -> tuple[list[dict], dict, list[dict]]:
    return await run_multi_wave_query_plan_core(
        query_plan,
        settings,
        run_query_plan_wave,
        build_deduped_results_and_report,
    )


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


@app.post("/api/search-brief/validate")
def validate_search_brief_endpoint(request: SearchBrief) -> dict:
    return search_brief_validation_response(request)


@app.post("/api/recruiter-chat/turn")
async def create_recruiter_chat_turn(request: RecruiterChatTurnRequest) -> dict:
    return await recruiter_chat_turn_response(request)


@app.post("/api/agent/plan")
async def create_agent_plan(request: AgentPlanRequest) -> dict:
    return await build_agent_plan_response_with_wording(request)


@app.get("/api/agent/tools")
def get_agent_tools() -> dict:
    return {"ok": True, "agent_tools": agent_tool_contract()}


@app.post("/api/query-plan")
def create_query_plan(request: StructuredSearchRequest) -> dict:
    normalized_request, errors = normalize_structured_search_request(request)

    if errors:
        return {"ok": False, "errors": errors}

    query_plan = RuleBasedQueryPlannerV1().build(normalized_request)

    return {
        "ok": True,
        "query_plan": add_query_plan_fingerprint(query_plan),
        "plan_fingerprint": query_plan_fingerprint(query_plan),
    }


@app.post("/api/agent/query-plan")
async def create_agent_query_plan(request: AgentQueryPlanRequest) -> dict:
    planner_mode = request.planner_mode
    if planner_mode not in PLANNER_MODES:
        return {
            "ok": False,
            "errors": [
                {
                    "field": "planner_mode",
                    "message": "Unsupported planner mode.",
                }
            ],
        }

    brief_response = search_brief_validation_response(request.search_brief)
    normalized_brief = brief_response["normalized_brief"]
    if brief_response["errors"]:
        return {
            "ok": False,
            "planner_mode": planner_mode,
            "plan_status": PLAN_STATUS_REJECTED,
            "execution_allowed": False,
            "normalized_brief": normalized_brief,
            "errors": brief_response["errors"],
            "validation_errors": brief_response["errors"],
            "clarifying_questions": brief_response["clarifying_questions"],
        }

    if normalized_brief["brief_status"] != SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        return {
            "ok": True,
            "planner_mode": planner_mode,
            "plan_status": PLAN_STATUS_NEEDS_CLARIFICATION,
            "execution_allowed": False,
            "normalized_brief": normalized_brief,
            "adapted_structured_request": None,
            "query_plan": None,
            "validation_errors": [],
            "clarifying_questions": normalized_brief.get("clarifying_questions", []),
            "approval_required": False,
            "execution_approval_required": False,
        }

    normalized_request = brief_response["adapted_structured_request"]
    if not normalized_request:
        return {
            "ok": False,
            "planner_mode": planner_mode,
            "plan_status": PLAN_STATUS_REJECTED,
            "execution_allowed": False,
            "normalized_brief": normalized_brief,
            "errors": brief_response["errors"],
            "validation_errors": brief_response["errors"],
        }

    agent_action_errors = validate_agent_query_plan_action(
        request,
        normalized_brief,
        normalized_request,
    )
    if agent_action_errors:
        return {
            "ok": False,
            "planner_mode": planner_mode,
            "plan_status": PLAN_STATUS_REJECTED,
            "execution_allowed": False,
            "normalized_brief": normalized_brief,
            "adapted_structured_request": normalized_request,
            "query_plan": None,
            "errors": agent_action_errors,
            "validation_errors": agent_action_errors,
            "approval_required": False,
            "execution_approval_required": False,
        }

    if planner_mode == PLANNER_MODE_RULE_BASED:
        return build_agent_rule_based_plan_response(normalized_brief, normalized_request)

    return await build_ai_query_plan_response(
        normalized_brief,
        normalized_request,
        planner_mode,
    )


@app.post("/api/ai-query-plan/validate")
def validate_ai_query_plan_endpoint(request: AIQueryPlanValidationRequest) -> dict:
    brief_response = search_brief_validation_response(request.search_brief)
    normalized_brief = brief_response["normalized_brief"]
    if brief_response["errors"]:
        return {
            "ok": False,
            "plan_status": PLAN_STATUS_REJECTED,
            "execution_allowed": False,
            "normalized_brief": normalized_brief,
            "errors": brief_response["errors"],
            "validation_errors": brief_response["errors"],
        }

    normalized_request = brief_response["adapted_structured_request"]
    if not normalized_request:
        return {
            "ok": False,
            "plan_status": PLAN_STATUS_NEEDS_CLARIFICATION,
            "execution_allowed": False,
            "normalized_brief": normalized_brief,
            "errors": [
                {
                    "field": "brief_status",
                    "code": "brief_not_ready",
                    "message": "Search Brief must be ready before validating a QueryPlan.",
                }
            ],
            "validation_errors": [],
        }

    validated_plan, validation_errors = validate_ai_query_plan(
        request.draft_query_plan,
        normalized_brief,
        normalized_request,
    )
    if validation_errors:
        fallback_query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
        return {
            "ok": False,
            "plan_status": PLAN_STATUS_REJECTED,
            "execution_allowed": False,
            "normalized_brief": normalized_brief,
            "validation_errors": validation_errors,
            "fallback_available": True,
            "fallback_query_plan": add_query_plan_fingerprint(fallback_query_plan),
            "fallback_plan_fingerprint": query_plan_fingerprint(fallback_query_plan),
        }

    coverage_errors, coverage_warnings, coverage_policy = validate_ai_query_plan_coverage(
        validated_plan,
        normalized_brief,
        normalized_request,
    )
    if coverage_errors:
        fallback_query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
        return {
            "ok": False,
            "plan_status": PLAN_STATUS_REJECTED,
            "execution_allowed": False,
            "normalized_brief": normalized_brief,
            "validation_errors": coverage_errors,
            "warnings": coverage_warnings,
            "coverage_policy": coverage_policy,
            "fallback_available": True,
            "fallback_reason": AI_PLANNER_UNDER_COVERED_FALLBACK_REASON,
            "fallback_query_plan": add_query_plan_fingerprint(fallback_query_plan),
            "fallback_plan_fingerprint": query_plan_fingerprint(fallback_query_plan),
        }

    plan_fingerprint = query_plan_fingerprint(validated_plan)

    return {
        "ok": True,
        "planner_mode": PLANNER_MODE_AI,
        "plan_status": PLAN_STATUS_VALIDATED_NOT_EXECUTABLE,
        "execution_allowed": False,
        "normalized_brief": normalized_brief,
        "query_plan": add_query_plan_fingerprint(validated_plan),
        "plan_fingerprint": plan_fingerprint,
        "validation_errors": [],
        "warnings": coverage_warnings,
        "coverage_policy": coverage_policy,
        "approval_required": False,
        "execution_approval_required": True,
        "approval_notice": "This plan is not executed yet. Search execution requires approval.",
    }


@app.post("/api/structured-search")
async def structured_search(request: StructuredSearchRequest) -> dict:
    normalized_request, errors = normalize_structured_search_request(request)

    if errors:
        return {"ok": False, "errors": errors}

    query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
    execution_approval, approval_errors = validate_execution_approval(
        request.execution_approval,
        EXECUTION_ACTION_SINGLE_WAVE,
        query_plan,
    )
    if approval_errors:
        return {
            "ok": False,
            "errors": approval_errors,
            "execution_allowed": False,
            "query_plan": add_query_plan_fingerprint(query_plan),
            "plan_fingerprint": query_plan_fingerprint(query_plan),
        }

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

    query_results = await run_query_plan_wave(query_plan)

    successful_queries = sum(1 for result in query_results if result["ok"])
    deduped_results, report = build_deduped_results_and_report(
        query_plan,
        query_results,
    )
    agent_response = build_agent_response(
        query_plan,
        report,
        deduped_results,
        request.agent_language,
    )
    agent_response = await apply_llm_wording_to_agent_response(agent_response)
    try:
        write_structured_search_snapshot(
            query_plan,
            query_results,
            deduped_results,
            report,
            execution_approval=execution_approval,
        )
    except Exception:
        logger.warning("Failed to write structured search snapshot.", exc_info=True)

    return {
        "ok": successful_queries > 0,
        "query_plan": add_query_plan_fingerprint(query_plan),
        "plan_fingerprint": query_plan_fingerprint(query_plan),
        "execution_approval": execution_approval,
        "query_results": query_results,
        "deduped_results": deduped_results,
        "report": report,
        "agent_response": agent_response,
    }


@app.post("/api/structured-search/multi-wave")
async def structured_search_multi_wave(
    request: MultiWaveStructuredSearchRequest,
) -> dict:
    normalized_request, settings, errors = normalize_multi_wave_search_request(request)

    if errors:
        return {"ok": False, "errors": errors}

    query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
    execution_approval, approval_errors = validate_execution_approval(
        request.execution_approval,
        EXECUTION_ACTION_MULTI_WAVE,
        query_plan,
    )
    if approval_errors:
        return {
            "ok": False,
            "errors": approval_errors,
            "execution_allowed": False,
            "query_plan": add_query_plan_fingerprint(query_plan),
            "plan_fingerprint": query_plan_fingerprint(query_plan),
        }

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

    deduped_results, report, query_results = await run_multi_wave_query_plan(
        query_plan,
        settings,
    )
    agent_response = build_agent_response(
        query_plan,
        report,
        deduped_results,
        request.agent_language,
    )
    agent_response = await apply_llm_wording_to_agent_response(agent_response)
    try:
        write_structured_search_snapshot(
            query_plan,
            query_results,
            deduped_results,
            report,
            "structured-search-multi-wave",
            execution_approval=execution_approval,
        )
    except Exception:
        logger.warning(
            "Failed to write structured search multi-wave snapshot.",
            exc_info=True,
        )

    return {
        "ok": report["queries_succeeded"] > 0,
        "experimental": True,
        "query_plan": add_query_plan_fingerprint(query_plan),
        "plan_fingerprint": query_plan_fingerprint(query_plan),
        "execution_approval": execution_approval,
        "query_results": query_results,
        "deduped_results": deduped_results,
        "report": report,
        "agent_response": agent_response,
    }


@app.post("/api/search")
async def search(request: SearchRequest) -> dict:
    query = request.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Search query is required.")

    return {
        "ok": False,
        "errors": [
            {
                "field": "search",
                "code": "legacy_raw_search_disabled",
                "message": (
                    "Legacy raw Tavily search is disabled. "
                    "Use approval-gated structured search instead."
                ),
            }
        ],
    }
