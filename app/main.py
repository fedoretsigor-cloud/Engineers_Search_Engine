from pathlib import Path
import copy
from datetime import datetime, timezone
import hashlib
import html
import json
import logging
import os
import re
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
STATIC_DIR = BASE_DIR / "static"
SEARCH_RUN_LOG_DIR = PROJECT_DIR / "logs" / "search-runs"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
QUERY_PLANNER_VERSION = "rule_based_v1"
QUERY_PLAN_MAX_RESULTS = 20
CANDIDATE_QUALITY_SCORE_VERSION = "candidate_quality_v1"
MULTI_WAVE_DEFAULT_MAX_WAVES = 5
MULTI_WAVE_MAX_ALLOWED_WAVES = 7
MULTI_WAVE_DEFAULT_MIN_NEW_UNIQUE_PER_WAVE = 3
MULTI_WAVE_DEFAULT_PATIENCE = 2
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_RECRUITER_CHAT_MAX_COMPLETION_TOKENS = 1200
OPENAI_AI_PLANNER_MAX_COMPLETION_TOKENS = 3000
OPENAI_AGENT_WORDING_MAX_COMPLETION_TOKENS = 800
SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION = "needs_clarification"
SEARCH_BRIEF_STATUS_READY_FOR_PLANNING = "ready_for_planning"
SEARCH_BRIEF_STATUSES = {
    SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION,
    SEARCH_BRIEF_STATUS_READY_FOR_PLANNING,
}
SEARCH_DEPTH_STANDARD = "standard"
SEARCH_DEPTH_DEEP = "deep"
SEARCH_DEPTH_VALUES = {SEARCH_DEPTH_STANDARD, SEARCH_DEPTH_DEEP}
PROFILE_SOURCE_LINKEDIN_PUBLIC = "linkedin_public"
PROFILE_SOURCE_VALUES = {PROFILE_SOURCE_LINKEDIN_PUBLIC}
PLANNER_MODE_RULE_BASED = "rule_based"
PLANNER_MODE_AI = "ai"
PLANNER_MODE_AI_WITH_FALLBACK = "ai_with_fallback"
PLANNER_MODES = {
    PLANNER_MODE_RULE_BASED,
    PLANNER_MODE_AI,
    PLANNER_MODE_AI_WITH_FALLBACK,
}
RECRUITER_CHAT_DEFAULT_PLANNER_MODE = PLANNER_MODE_RULE_BASED
RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION = "needs_clarification"
RECRUITER_CHAT_STATE_READY_FOR_PLANNING = "ready_for_planning"
RECRUITER_CHAT_STATE_REFUSED = "refused"
RECRUITER_CHAT_ALLOWED_MESSAGE_ROLES = {"assistant", "recruiter", "user"}
EXECUTION_ACTION_SINGLE_WAVE = "run_single_wave_search"
EXECUTION_ACTION_MULTI_WAVE = "run_multi_wave_search"
FORBIDDEN_AI_QUERY_TERMS = [
    "linkedin.com/login",
    "login",
    "password",
    "scrape",
    "scraping",
    "crawler",
    "bypass",
    "restriction bypass",
    "inmail",
    "send message",
    "message candidate",
    "contact candidate",
    "account",
]
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
AGENT_TOOL_APPROVAL_NOT_REQUIRED = "not_required"
AGENT_TOOL_APPROVAL_REQUIRED = "required"
AGENT_TOOL_APPROVAL_APPROVED = "approved"
AGENT_TOOL_APPROVAL_REJECTED = "rejected"
AGENT_PLAN_STATUS_SUPPORTED = "supported"
AGENT_PLAN_STATUS_NEEDS_CLARIFICATION = "needs_clarification"
AGENT_PLAN_STATUS_UNSUPPORTED = "unsupported"
AGENT_ACTION_BUILD_QUERY_PLAN = "build_query_plan"
AGENT_QUERY_PLAN_ENDPOINT = "/api/agent/query-plan"
AGENT_WORDING_MODE_LLM_ASSISTED = "llm_assisted"
AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK = "deterministic_fallback"
AGENT_WORDING_FALLBACK_NOT_CONFIGURED = "openai_not_configured"
AGENT_WORDING_TIMEOUT_SECONDS = 8.0
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
AI_PLANNER_COVERAGE_POLICY_VERSION = "ai_planner_coverage_policy_v0"
AI_PLANNER_COVERAGE_NOT_CONFIGURED_WARNING = (
    "coverage_policy_not_configured: Strict AI planner coverage policy is not "
    "configured for this brief."
)
AI_PLANNER_UNDER_COVERED_FALLBACK_REASON = (
    "AI plan is structurally valid, but coverage is too narrow for the baseline. "
    "Falling back to rule-based planner."
)
AI_PLANNER_COVERAGE_POLICIES = [
    {
        "policy_id": "java_backend_ukraine_standard_v0",
        "policy_version": AI_PLANNER_COVERAGE_POLICY_VERSION,
        "role_family": "Backend Developer",
        "technology": "Java",
        "location": "Ukraine",
        "search_depth": SEARCH_DEPTH_STANDARD,
        "expected_query_count": 10,
        "role_based_min": 6,
        "stack_focused_min": 4,
        "min_role_phrase_diversity": 5,
        "max_ai_plan_revision_attempts": 1,
    }
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
CANDIDATE_SENIORITY_CONFIG = {
    "junior": {
        "display": "Junior",
        "terms": ["Junior", "Jr", "Trainee", "Intern"],
    },
    "middle": {
        "display": "Middle",
        "terms": ["Middle", "Mid", "Mid-level"],
    },
    "senior": {
        "display": "Senior",
        "terms": ["Senior", "Sr"],
    },
    "leadership": {
        "display": "Lead",
        "terms": ["Team Lead", "Tech Lead", "Lead"],
    },
}
REVIEW_FLAG_TAXONOMY = {
    "role_missing": {
        "category": "role",
        "severity": "medium",
        "label": "Role not confirmed",
        "description": "Target or similar role was not found in candidate public text.",
        "affects_quality_score": True,
        "score_penalty_group": "role_fit",
    },
    "role_similar_only": {
        "category": "role",
        "severity": "low",
        "label": "Similar role only",
        "description": "Candidate role looks close, but it is not a direct target-role phrase.",
        "affects_quality_score": True,
        "score_penalty_group": "role_fit",
    },
    "role_from_snippet_only": {
        "category": "role",
        "severity": "low",
        "label": "Role from snippet",
        "description": "Role evidence was found only in lower-confidence snippet text.",
        "affects_quality_score": True,
        "score_penalty_group": "low_confidence_source",
    },
    "technology_missing": {
        "category": "technology",
        "severity": "medium",
        "label": "Technology not confirmed",
        "description": "Selected technology was not directly found in candidate public text.",
        "affects_quality_score": True,
        "score_penalty_group": "technology_fit",
    },
    "technology_related_only": {
        "category": "technology",
        "severity": "low",
        "label": "Related technology only",
        "description": "Only a configured related technology signal was found.",
        "affects_quality_score": True,
        "score_penalty_group": "technology_fit",
    },
    "technology_ambiguous": {
        "category": "technology",
        "severity": "high",
        "label": "Technology ambiguous",
        "description": "Technology evidence may indicate a false positive.",
        "affects_quality_score": True,
        "score_penalty_group": "technology_false_positive",
    },
    "possible_technology_false_positive": {
        "category": "technology",
        "severity": "high",
        "label": "Possible technology false positive",
        "description": "Candidate text includes an exclude term that can look like the selected technology.",
        "affects_quality_score": True,
        "score_penalty_group": "technology_false_positive",
    },
    "selected_stack_missing": {
        "category": "stack",
        "severity": "medium",
        "label": "Stack not confirmed",
        "description": "Selected stack was not directly found in candidate public text.",
        "affects_quality_score": True,
        "score_penalty_group": "stack_fit",
    },
    "stack_from_query_source_only": {
        "category": "stack",
        "severity": "low",
        "label": "Stack only from query source",
        "description": "Candidate came from a stack-focused OR query, but no specific stack term was directly observed.",
        "affects_quality_score": True,
        "score_penalty_group": "stack_fit",
    },
    "stack_related_only": {
        "category": "stack",
        "severity": "low",
        "label": "Related stack only",
        "description": "Only a configured related stack signal was found.",
        "affects_quality_score": True,
        "score_penalty_group": "stack_fit",
    },
    "seniority_missing": {
        "category": "seniority",
        "severity": "info",
        "label": "Seniority not found",
        "description": "Seniority was not found in candidate public text.",
        "affects_quality_score": False,
        "score_penalty_group": None,
    },
    "seniority_ambiguous": {
        "category": "seniority",
        "severity": "low",
        "label": "Seniority ambiguous",
        "description": "Multiple seniority signals were found and should be reviewed.",
        "affects_quality_score": True,
        "score_penalty_group": "low_confidence_seniority",
    },
    "seniority_from_snippet_only": {
        "category": "seniority",
        "severity": "low",
        "label": "Seniority from snippet",
        "description": "Seniority was found only in lower-confidence snippet text.",
        "affects_quality_score": True,
        "score_penalty_group": "low_confidence_source",
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


class ExecutionApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_status: str | None = None
    approved_action: str | None = None
    approved_planner_mode: str | None = None
    approved_query_count: int | None = None
    approved_plan_fingerprint: str | None = None


class StructuredSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_family: str | None = None
    technology: str | None = None
    stack: list[str] | None = None
    location: str | None = None
    linkedin_profiles_only: bool | None = None
    location_filter_enabled: bool | None = None
    execution_approval: ExecutionApproval | None = None
    agent_language: str | None = None


class MultiWaveStructuredSearchRequest(StructuredSearchRequest):
    max_waves: int | None = None
    min_new_unique_per_wave: int | None = None
    patience: int | None = None


class SearchBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_text: str | None = None
    brief_status: str | None = None
    role_family: str | None = None
    technology: str | None = None
    stack: list[str] | None = None
    location: str | None = None
    seniority: str | None = None
    must_have: list[str] | None = None
    nice_to_have: list[str] | None = None
    exclusions: list[str] | None = None
    search_depth: str | None = None
    profile_sources: list[str] | None = None
    notes: str | None = None
    missing_fields: list[str] | None = None
    clarifying_questions: list[str] | None = None
    assumptions: list[str] | None = None


class AgentQueryPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    planner_mode: str = PLANNER_MODE_RULE_BASED
    search_brief: SearchBrief
    agent_plan_brief_fingerprint: str | None = None
    agent_plan_action: dict | None = None


class AgentPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search_brief: SearchBrief
    language: str | None = None


class AIQueryPlanValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search_brief: SearchBrief
    draft_query_plan: dict | None = None


class RecruiterChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    content: str = Field(..., min_length=1)


class RecruiterChatTurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[RecruiterChatMessage] = Field(default_factory=list)
    draft_brief: SearchBrief | None = None
    language: str | None = None
    planner_mode: str | None = None


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


def collect_seniority_evidence(
    sources: list[dict[str, str]],
    seniority_config: dict,
) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    seen_levels: set[str] = set()

    for source in sources:
        value = source["value"]
        for level, config in seniority_config.items():
            if level in seen_levels:
                continue

            terms = sorted(config.get("terms", []), key=len, reverse=True)
            for term in terms:
                if find_term_match(value, term):
                    seen_levels.add(level)
                    evidence.append(
                        {
                            "term": term,
                            "level": level,
                            "display": config["display"],
                            "source": source["source"],
                            "value": value,
                        }
                    )
                    break

    return evidence


def seniority_display_from_evidence(evidence: list[dict]) -> str:
    found_levels = {item["level"] for item in evidence}
    experience_order = ["junior", "middle", "senior"]
    experience_levels = [
        level for level in experience_order if level in found_levels
    ]
    has_leadership = "leadership" in found_levels

    display_parts: list[str] = []
    if experience_levels:
        highest_experience_level = experience_levels[-1]
        display_parts.append(
            CANDIDATE_SENIORITY_CONFIG[highest_experience_level]["display"]
        )
    if has_leadership:
        display_parts.append(CANDIDATE_SENIORITY_CONFIG["leadership"]["display"])

    return " ".join(display_parts) if display_parts else "n/a"


def build_seniority_quality(result: dict) -> dict:
    sources = candidate_text_sources(result)
    seniority_evidence = collect_seniority_evidence(
        sources,
        CANDIDATE_SENIORITY_CONFIG,
    )

    if not seniority_evidence:
        return {
            "seniority_display": "n/a",
            "seniority_fit": "missing",
            "seniority_evidence": [],
            "review_flags": ["seniority_missing"],
        }

    found_levels = {item["level"] for item in seniority_evidence}
    experience_levels = found_levels.intersection({"junior", "middle", "senior"})
    review_flags: list[str] = []
    if len(experience_levels) > 1:
        review_flags.append("seniority_ambiguous")
    if all(item["source"] not in {"headline", "title"} for item in seniority_evidence):
        review_flags.append("seniority_from_snippet_only")

    return {
        "seniority_display": seniority_display_from_evidence(seniority_evidence),
        "seniority_fit": "ambiguous" if "seniority_ambiguous" in review_flags else "found",
        "seniority_evidence": seniority_evidence,
        "review_flags": review_flags,
    }


def merge_review_flags(existing_flags: list[str], new_flags: list[str]) -> list[str]:
    return ordered_unique(existing_flags + new_flags)


def review_flag_detail(flag_code: str) -> dict:
    flag_config = REVIEW_FLAG_TAXONOMY.get(flag_code)
    if not flag_config:
        return {
            "code": flag_code,
            "category": "unknown",
            "severity": "info",
            "label": flag_code.replace("_", " ").title(),
            "description": "Unknown review flag preserved for compatibility.",
            "affects_quality_score": False,
            "score_penalty_group": None,
        }

    return {"code": flag_code, **flag_config}


def normalize_review_flags(review_flags: list[str]) -> tuple[list[str], list[dict]]:
    unique_flags = ordered_unique(review_flags)
    known_flags = [
        flag_code for flag_code in REVIEW_FLAG_TAXONOMY if flag_code in unique_flags
    ]
    unknown_flags = [
        flag_code for flag_code in unique_flags if flag_code not in REVIEW_FLAG_TAXONOMY
    ]
    normalized_flags = known_flags + unknown_flags
    return normalized_flags, [review_flag_detail(flag) for flag in normalized_flags]


def score_component(
    component: str,
    points: int,
    max_points: int,
    status: str,
    reason: str,
    optional: bool = False,
) -> dict:
    return {
        "component": component,
        "points": points,
        "max_points": max_points,
        "status": status,
        "reason": reason,
        "optional": optional,
    }


def build_location_score_component(result: dict) -> dict:
    status = result.get("location_signal_status") or "not_applied"
    if status == "not_applied":
        return score_component(
            "location",
            0,
            0,
            "not_evaluated",
            "Location filter was not evaluated.",
        )

    score_by_status = {
        "target_location": (
            25,
            "Current-location text contains the target location.",
        ),
        "rescued_header_location": (
            20,
            "Header/location text supports the target location.",
        ),
        "country_domain": (
            16,
            "Country-specific LinkedIn domain supports the target location.",
        ),
    }
    points, reason = score_by_status.get(
        status,
        (0, "Location confidence is weak or not displayed by the filter."),
    )
    return score_component("location", points, 25, status, reason)


def build_role_score_component(result: dict) -> dict:
    role_fit = result.get("role_fit") or "missing_role"
    score_by_fit = {
        "target_or_close_role": (
            25,
            "Target or close role matched candidate text.",
        ),
        "similar_role": (
            16,
            "Similar role matched candidate text.",
        ),
    }
    points, reason = score_by_fit.get(
        role_fit,
        (0, "Target or similar role was not confirmed."),
    )
    return score_component("role", points, 25, role_fit, reason)


def build_technology_score_component(result: dict) -> dict:
    technology_fit = result.get("technology_fit") or "missing"
    score_by_fit = {
        "exact": (
            20,
            "Selected technology was directly found.",
        ),
        "related_only": (
            10,
            "Only a configured related technology was found.",
        ),
    }
    points, reason = score_by_fit.get(
        technology_fit,
        (0, "Selected technology was not confidently confirmed."),
    )
    return score_component("technology", points, 20, technology_fit, reason)


def build_stack_score_component(result: dict) -> dict:
    stack_fit = result.get("stack_fit") or "missing"
    score_by_fit = {
        "selected_stack_found": (
            20,
            "Selected stack was directly found in candidate text.",
        ),
        "related_stack_only": (
            8,
            "Only configured related stack evidence was found.",
        ),
        "stack_query_source_only": (
            6,
            "Candidate came from a stack-focused query, but no specific OR term was directly observed.",
        ),
    }
    points, reason = score_by_fit.get(
        stack_fit,
        (0, "Selected stack was not directly confirmed."),
    )
    return score_component("stack", points, 20, stack_fit, reason)


def build_identity_score_component(result: dict) -> dict:
    name_found = bool(result.get("name") and result.get("name") != "unknown")
    headline_found = bool(result.get("headline") and result.get("headline") != "n/a")
    points = (3 if name_found else 0) + (2 if headline_found else 0)
    return score_component(
        "identity",
        points,
        5,
        "complete" if points == 5 else "partial",
        "Candidate name/headline extraction completeness.",
    )


def build_seniority_score_component(result: dict) -> dict:
    seniority_fit = result.get("seniority_fit") or "missing"
    score_by_fit = {
        "found": (
            5,
            "Seniority signal was found as a bonus signal.",
        ),
        "ambiguous": (
            2,
            "Seniority signal was found but needs review.",
        ),
    }
    points, reason = score_by_fit.get(
        seniority_fit,
        (0, "Seniority was not found and is not penalized without a requirement."),
    )
    return score_component("seniority", points, 5, seniority_fit, reason, optional=True)


def build_quality_score_penalties(result: dict) -> list[dict]:
    review_flag_details = result.get("review_flag_details") or []
    penalty_by_group = {
        "technology_false_positive": {
            "points": -10,
            "reason": "Technology evidence may be a false positive.",
        },
        "low_confidence_source": {
            "points": -3,
            "reason": "Important evidence came only from lower-confidence snippet text.",
        },
        "low_confidence_seniority": {
            "points": -2,
            "reason": "Seniority evidence is ambiguous.",
        },
    }
    applied_groups: set[str] = set()
    penalties: list[dict] = []

    for flag_detail in review_flag_details:
        group = flag_detail.get("score_penalty_group")
        if group not in penalty_by_group or group in applied_groups:
            continue

        applied_groups.add(group)
        penalty_config = penalty_by_group[group]
        penalties.append(
            {
                "flag": flag_detail["code"],
                "group": group,
                "points": penalty_config["points"],
                "reason": penalty_config["reason"],
            }
        )

    return penalties


def build_quality_score(result: dict) -> dict:
    breakdown = [
        build_location_score_component(result),
        build_role_score_component(result),
        build_technology_score_component(result),
        build_stack_score_component(result),
        build_identity_score_component(result),
        build_seniority_score_component(result),
    ]
    required_components = [item for item in breakdown if not item.get("optional")]
    optional_components = [item for item in breakdown if item.get("optional")]
    available_points = sum(item["max_points"] for item in required_components)
    earned_points = sum(item["points"] for item in required_components)
    optional_points = sum(item["points"] for item in optional_components)
    base_score = round((earned_points / available_points) * 95) if available_points else 0
    penalties = build_quality_score_penalties(result)
    penalty_points = sum(item["points"] for item in penalties)
    quality_score = min(100, max(0, base_score + optional_points + penalty_points))

    return {
        "quality_score": quality_score,
        "quality_score_version": CANDIDATE_QUALITY_SCORE_VERSION,
        "quality_score_breakdown": breakdown,
        "quality_score_penalties": penalties,
    }


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
        build_seniority_quality(result),
    ):
        review_flags = merge_review_flags(
            review_flags,
            quality_part.pop("review_flags", []),
        )
        quality.update(quality_part)

    normalized_flags, flag_details = normalize_review_flags(review_flags)
    quality["review_flags"] = normalized_flags
    quality["review_flag_details"] = flag_details
    quality.update(build_quality_score({**result, **quality}))
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
        "step: review the strongest candidates first; if coverage feels narrow, "
        "consider multi-wave or adjust the stack through the normal approval flow."
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
        "\u0441\u043d\u0430\u0447\u0430\u043b\u0430 \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c "
        "\u0441\u0438\u043b\u044c\u043d\u044b\u0445 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432; "
        "\u0435\u0441\u043b\u0438 coverage \u0443\u0437\u043a\u0438\u0439, "
        "\u0440\u0430\u0441\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c multi-wave "
        "\u0438\u043b\u0438 \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c stack "
        "\u0447\u0435\u0440\u0435\u0437 \u043e\u0431\u044b\u0447\u043d\u044b\u0439 approval flow."
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
    mode = summary_facts.get("mode")
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
        if mode != "multi_wave":
            actions.append(
                {
                    "label": "\u0420\u0430\u0441\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c multi-wave",
                    "description": (
                        "\u0417\u0430\u043f\u0443\u0441\u043a \u0432\u043e\u0437\u043c\u043e\u0436\u0435\u043d "
                        "\u0442\u043e\u043b\u044c\u043a\u043e \u0447\u0435\u0440\u0435\u0437 "
                        "\u044f\u0432\u043d\u044b\u0439 approval gate."
                    ),
                    "executable": False,
                }
            )
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
    if mode != "multi_wave":
        actions.append(
            {
                "label": "Consider multi-wave",
                "description": (
                    "A new run must still go through the explicit approval gate."
                ),
                "executable": False,
            }
        )
    return actions


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


def canonical_value(value: str | None, allowed_values: dict[str, str]) -> str | None:
    if value is None:
        return None

    normalized_key = value.strip().lower()
    if not normalized_key:
        return None

    return allowed_values.get(normalized_key)


def normalize_location_value(value: str | None) -> str | None:
    normalized_value = normalize_text_value(value)
    if not normalized_value:
        return None

    normalized_key = normalized_value.lower()
    if re.search(r"^укра(и|ї)н", normalized_key) or normalized_key == "ukraine":
        return "Ukraine"

    return normalized_value


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

    location = normalize_location_value(request.location) or ""
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


def normalize_multi_wave_search_request(
    request: MultiWaveStructuredSearchRequest,
) -> tuple[dict | None, dict | None, list[dict[str, str]]]:
    normalized_request, errors = normalize_structured_search_request(request)

    max_waves = (
        MULTI_WAVE_DEFAULT_MAX_WAVES
        if request.max_waves is None
        else request.max_waves
    )
    min_new_unique_per_wave = (
        MULTI_WAVE_DEFAULT_MIN_NEW_UNIQUE_PER_WAVE
        if request.min_new_unique_per_wave is None
        else request.min_new_unique_per_wave
    )
    patience = (
        MULTI_WAVE_DEFAULT_PATIENCE
        if request.patience is None
        else request.patience
    )

    if max_waves < 1 or max_waves > MULTI_WAVE_MAX_ALLOWED_WAVES:
        add_validation_error(
            errors,
            "max_waves",
            f"max_waves must be between 1 and {MULTI_WAVE_MAX_ALLOWED_WAVES}.",
        )
    if min_new_unique_per_wave < 0:
        add_validation_error(
            errors,
            "min_new_unique_per_wave",
            "min_new_unique_per_wave must be 0 or greater.",
        )
    if patience < 1:
        add_validation_error(errors, "patience", "patience must be 1 or greater.")

    if errors:
        return None, None, errors

    return (
        normalized_request,
        {
            "max_waves": max_waves,
            "max_allowed_waves": MULTI_WAVE_MAX_ALLOWED_WAVES,
            "min_new_unique_per_wave": min_new_unique_per_wave,
            "patience": patience,
        },
        errors,
    )


def normalize_text_value(value: str | None) -> str | None:
    normalized_value = compact_spaces(value or "")
    return normalized_value or None


def normalize_text_list(values: list[str] | None) -> list[str]:
    if not values:
        return []

    normalized_values: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        normalized_value = normalize_text_value(value)
        if not normalized_value:
            continue
        value_key = normalized_value.lower()
        if value_key in seen_values:
            continue
        seen_values.add(value_key)
        normalized_values.append(normalized_value)

    return normalized_values


def clarifying_question_for_missing_field(field: str) -> str:
    questions = {
        "role_family": "What role family should the search target?",
        "technology": "What main technology should the candidate have?",
        "stack": (
            "Which Java stack signals are important for this search: "
            "Spring, Kafka, AWS, Hibernate, or something else?"
        ),
        "location": "What target location should the search use?",
        "search_depth": "Should this be a standard or deep search?",
        "profile_sources": "Which public profile source should be used?",
    }
    return questions.get(field, f"Please clarify {field}.")


def normalize_brief_stack_items(
    stack: list[str] | None,
) -> tuple[list[str], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    normalized_stack: list[str] = []
    seen_stack_values: set[str] = set()

    for item in stack or []:
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


def build_structured_request_from_brief(normalized_brief: dict) -> StructuredSearchRequest:
    return StructuredSearchRequest(
        role_family=normalized_brief.get("role_family"),
        technology=normalized_brief.get("technology"),
        stack=normalized_brief.get("stack") or [],
        location=normalized_brief.get("location"),
        linkedin_profiles_only=True,
        location_filter_enabled=(
            location_filter_config_for(normalized_brief.get("location") or "") is not None
        ),
    )


def validate_and_normalize_search_brief(
    brief: SearchBrief,
) -> tuple[dict, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []

    brief_status = normalize_text_value(brief.brief_status)
    if not brief_status:
        brief_status = SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION
    if brief_status not in SEARCH_BRIEF_STATUSES:
        add_validation_error(errors, "brief_status", "Unsupported brief status.")
        brief_status = SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION

    role_family = canonical_value(brief.role_family, CANONICAL_ROLE_FAMILIES)
    if brief.role_family and not role_family:
        add_validation_error(errors, "role_family", "Unsupported role family.")

    technology = canonical_value(brief.technology, KNOWN_BACKEND_TECHNOLOGIES)
    if brief.technology and not technology:
        add_validation_error(errors, "technology", "Unsupported technology.")
    elif technology and technology not in IMPLEMENTED_BACKEND_TECHNOLOGIES:
        add_validation_error(
            errors,
            "technology",
            "Technology is known but planner is not implemented yet.",
        )

    location = normalize_location_value(brief.location)
    if location and not location_filter_config_for(location):
        add_validation_error(errors, "location", "Location is not supported yet.")

    search_depth = normalize_text_value(brief.search_depth) or SEARCH_DEPTH_STANDARD
    if search_depth not in SEARCH_DEPTH_VALUES:
        add_validation_error(errors, "search_depth", "Unsupported search depth.")
        search_depth = SEARCH_DEPTH_STANDARD

    profile_sources = normalize_text_list(brief.profile_sources) or [
        PROFILE_SOURCE_LINKEDIN_PUBLIC
    ]
    unsupported_profile_sources = [
        source for source in profile_sources if source not in PROFILE_SOURCE_VALUES
    ]
    if unsupported_profile_sources:
        add_validation_error(errors, "profile_sources", "Unsupported profile source.")

    normalized_stack, stack_errors = normalize_brief_stack_items(brief.stack)
    errors.extend(stack_errors)

    missing_fields: set[str] = set()
    required_for_planning = [
        "role_family",
        "technology",
        "stack",
        "location",
        "search_depth",
        "profile_sources",
    ]
    field_values = {
        "role_family": role_family,
        "technology": technology,
        "stack": normalized_stack,
        "location": location,
        "search_depth": search_depth,
        "profile_sources": profile_sources,
    }

    for field in required_for_planning:
        value = field_values[field]
        if not value:
            missing_fields.add(field)

    clarifying_questions = []
    if missing_fields:
        clarifying_questions = normalize_text_list(brief.clarifying_questions)
        for field in sorted(missing_fields):
            question = clarifying_question_for_missing_field(field)
            if question not in clarifying_questions:
                clarifying_questions.append(question)

    if missing_fields:
        brief_status = SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION
    elif brief_status == SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION:
        brief_status = SEARCH_BRIEF_STATUS_READY_FOR_PLANNING

    normalized_brief = {
        "source_text": normalize_text_value(brief.source_text),
        "brief_status": brief_status,
        "role_family": role_family,
        "technology": technology,
        "stack": normalized_stack,
        "location": location,
        "seniority": normalize_text_value(brief.seniority),
        "must_have": normalize_text_list(brief.must_have),
        "nice_to_have": normalize_text_list(brief.nice_to_have),
        "exclusions": normalize_text_list(brief.exclusions),
        "search_depth": search_depth,
        "profile_sources": profile_sources,
        "notes": normalize_text_value(brief.notes),
        "missing_fields": sorted(missing_fields),
        "clarifying_questions": clarifying_questions,
        "assumptions": normalize_text_list(brief.assumptions),
    }

    return normalized_brief, errors


def adapt_search_brief_to_structured_request(
    normalized_brief: dict,
) -> tuple[dict | None, list[dict[str, str]]]:
    if normalized_brief.get("brief_status") != SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        return None, [
            {
                "field": "brief_status",
                "message": "Search Brief needs clarification before planning.",
            }
        ]

    structured_request = build_structured_request_from_brief(normalized_brief)
    return normalize_structured_search_request(structured_request)


def search_brief_validation_response(brief: SearchBrief) -> dict:
    normalized_brief, errors = validate_and_normalize_search_brief(brief)
    adapted_request = None
    adapter_errors: list[dict[str, str]] = []

    if not errors and normalized_brief["brief_status"] == SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        adapted_request, adapter_errors = adapt_search_brief_to_structured_request(
            normalized_brief
        )

    all_errors = errors + adapter_errors

    return {
        "ok": not all_errors,
        "normalized_brief": normalized_brief,
        "errors": all_errors,
        "missing_fields": normalized_brief.get("missing_fields", []),
        "clarifying_questions": normalized_brief.get("clarifying_questions", []),
        "adapted_structured_request": adapted_request,
    }


def search_brief_fingerprint_payload(normalized_brief: dict) -> dict:
    return {
        "source_text": normalized_brief.get("source_text"),
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
        "notes": normalized_brief.get("notes"),
        "missing_fields": normalized_brief.get("missing_fields") or [],
        "clarifying_questions": normalized_brief.get("clarifying_questions") or [],
        "assumptions": normalized_brief.get("assumptions") or [],
    }


def search_brief_fingerprint(normalized_brief: dict) -> str:
    payload = json.dumps(
        search_brief_fingerprint_payload(normalized_brief),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def agent_plan_language(language: str | None, normalized_brief: dict | None = None) -> str:
    normalized_language = (normalize_text_value(language) or "").lower()
    if normalized_language.startswith(("ru", "\u0440\u0443\u0441")):
        return "ru"
    if normalized_language.startswith(("en", "\u0430\u043d\u0433\u043b")):
        return "en"

    source_text = (normalized_brief or {}).get("source_text") or ""
    if re.search(r"[\u0400-\u04ff]", source_text):
        return "ru"

    return "en"


def agent_plan_proposed_action() -> dict:
    return {
        "action": AGENT_ACTION_BUILD_QUERY_PLAN,
        "endpoint": AGENT_QUERY_PLAN_ENDPOINT,
        "planner_mode": PLANNER_MODE_RULE_BASED,
        "requires_approval": False,
    }


def is_supported_agent_v0_baseline(
    normalized_brief: dict,
    normalized_request: dict | None,
) -> bool:
    if not normalized_request:
        return False

    return (
        normalized_request.get("role_family") == "Backend Developer"
        and normalized_request.get("technology") == "Java"
        and normalized_request.get("location") == "Ukraine"
        and bool(normalized_request.get("stack"))
        and (normalized_brief.get("search_depth") or SEARCH_DEPTH_STANDARD)
        == SEARCH_DEPTH_STANDARD
    )


def agent_plan_supported_message(language: str, normalized_request: dict) -> str:
    stack_text = ", ".join(normalized_request.get("stack") or []) or "n/a"
    if language == "ru":
        return (
            "\u042f \u043f\u043e\u043d\u044f\u043b \u0437\u0430\u0434\u0430\u0447\u0443: "
            "\u0438\u0449\u0435\u043c Backend Developer \u0441 Java \u0432 "
            f"\u0423\u043a\u0440\u0430\u0438\u043d\u0435, stack: {stack_text}. "
            "\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 "
            "\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u044b\u0439 "
            "\u0448\u0430\u0433 - Build Plan \u0447\u0435\u0440\u0435\u0437 "
            "approved backend planner. \u041f\u043e\u0438\u0441\u043a "
            "\u043d\u0435 \u0437\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u0441\u044f "
            "\u0431\u0435\u0437 approval."
        )

    return (
        "I understood the task: find Backend Developer profiles with Java in "
        f"Ukraine, stack: {stack_text}. The next safe step is Build Plan through "
        "the approved backend planner. Search will not run without approval."
    )


def agent_plan_needs_clarification_message(language: str) -> str:
    if language == "ru":
        return (
            "\u041c\u043d\u0435 \u043d\u0443\u0436\u0435\u043d stack, "
            "\u0447\u0442\u043e\u0431\u044b \u0441\u043e\u0437\u0434\u0430\u0442\u044c "
            "Agent Plan \u0434\u043b\u044f Java/Ukraine baseline."
        )

    return "I need the missing stack before I can create an Agent Plan."


def agent_plan_unsupported_message(language: str) -> str:
    if language == "ru":
        return (
            "Agent v0 \u043f\u043e\u043a\u0430 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u0442 "
            "\u0442\u043e\u043b\u044c\u043a\u043e Backend Developer with Java in Ukraine."
        )

    return "Agent v0 currently supports only Backend Developer with Java in Ukraine."


def build_agent_plan_response(request: AgentPlanRequest) -> dict:
    brief_response = search_brief_validation_response(request.search_brief)
    normalized_brief = brief_response["normalized_brief"]
    language = agent_plan_language(request.language, normalized_brief)

    if brief_response["errors"]:
        return {
            "ok": False,
            "agent_plan_status": AGENT_PLAN_STATUS_NEEDS_CLARIFICATION,
            "agent_plan": None,
            "message": validation_error_message(brief_response["errors"], language),
            "normalized_brief": normalized_brief,
            "adapted_structured_request": None,
            "missing_fields": brief_response["missing_fields"],
            "clarifying_questions": brief_response["clarifying_questions"],
            "errors": brief_response["errors"],
            "validation_errors": brief_response["errors"],
        }

    if normalized_brief["brief_status"] != SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        return {
            "ok": True,
            "agent_plan_status": AGENT_PLAN_STATUS_NEEDS_CLARIFICATION,
            "agent_plan": None,
            "message": agent_plan_needs_clarification_message(language),
            "normalized_brief": normalized_brief,
            "adapted_structured_request": None,
            "missing_fields": normalized_brief.get("missing_fields", []),
            "clarifying_questions": normalized_brief.get("clarifying_questions", []),
            "errors": [],
            "validation_errors": [],
        }

    normalized_request = brief_response["adapted_structured_request"]
    if not is_supported_agent_v0_baseline(normalized_brief, normalized_request):
        return {
            "ok": True,
            "agent_plan_status": AGENT_PLAN_STATUS_UNSUPPORTED,
            "agent_plan": None,
            "message": agent_plan_unsupported_message(language),
            "normalized_brief": normalized_brief,
            "adapted_structured_request": normalized_request,
            "missing_fields": [],
            "clarifying_questions": [],
            "errors": [],
            "validation_errors": [],
        }

    fingerprint = search_brief_fingerprint(normalized_brief)
    message = agent_plan_supported_message(language, normalized_request)
    agent_plan = {
        "brief_fingerprint": fingerprint,
        "input_snapshot": normalized_brief,
        "message": message,
        "proposed_action": agent_plan_proposed_action(),
    }

    return {
        "ok": True,
        "agent_plan_status": AGENT_PLAN_STATUS_SUPPORTED,
        "agent_plan": agent_plan,
        "message": message,
        "normalized_brief": normalized_brief,
        "adapted_structured_request": normalized_request,
        "missing_fields": [],
        "clarifying_questions": [],
        "errors": [],
        "validation_errors": [],
    }


async def build_agent_plan_response_with_wording(request: AgentPlanRequest) -> dict:
    response = build_agent_plan_response(request)
    agent_plan = response.get("agent_plan")
    normalized_request = response.get("adapted_structured_request")

    if (
        response.get("ok") is True
        and response.get("agent_plan_status") == AGENT_PLAN_STATUS_SUPPORTED
        and isinstance(agent_plan, dict)
        and isinstance(normalized_request, dict)
    ):
        language = agent_plan_language(request.language, response.get("normalized_brief"))
        worded_agent_plan = await apply_llm_wording_to_agent_plan(
            agent_plan,
            normalized_request,
            language,
        )
        response["agent_plan"] = worded_agent_plan
        response["message"] = worded_agent_plan["message"]

    return response


def validate_agent_query_plan_action(
    request: AgentQueryPlanRequest,
    normalized_brief: dict,
    normalized_request: dict,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    action = request.agent_plan_action
    fingerprint = request.agent_plan_brief_fingerprint

    expected_fingerprint = search_brief_fingerprint(normalized_brief)
    if not fingerprint:
        add_plan_validation_error(
            errors,
            "agent_plan_brief_fingerprint",
            "missing_agent_plan_fingerprint",
            "Build Plan requires the current Agent Plan fingerprint.",
        )
    elif fingerprint != expected_fingerprint:
        add_plan_validation_error(
            errors,
            "agent_plan_brief_fingerprint",
            "stale_or_mismatched_agent_plan_fingerprint",
            "Agent Plan fingerprint does not match the current Search Brief.",
        )

    if not isinstance(action, dict):
        add_plan_validation_error(
            errors,
            "agent_plan_action",
            "missing_agent_plan_action",
            "Build Plan requires a supported Agent Plan proposed_action.",
        )
        return errors

    expected_action = agent_plan_proposed_action()
    for field, expected_value in expected_action.items():
        if action.get(field) != expected_value:
            add_plan_validation_error(
                errors,
                f"agent_plan_action.{field}",
                "unsupported_agent_plan_action",
                "Build Plan proposed_action is not supported.",
            )

    if action.get("planner_mode") != request.planner_mode:
        add_plan_validation_error(
            errors,
            "agent_plan_action.planner_mode",
            "mismatched_agent_plan_planner_mode",
            "Agent Plan planner_mode must match the Build Plan request.",
        )

    if not is_supported_agent_v0_baseline(normalized_brief, normalized_request):
        add_plan_validation_error(
            errors,
            "agent_plan_action",
            "unsupported_agent_v0_baseline",
            "Agent v0 currently supports only Backend Developer with Java in Ukraine.",
        )

    return errors


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
    }


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

    if validation_errors:
        return build_recruiter_chat_response(
            ok=False,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            normalized_brief=normalized_brief,
            validation_errors=validation_errors,
            next_question=next_question,
            planner_mode=planner_mode,
        )

    if normalized_brief["brief_status"] != SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        return build_recruiter_chat_response(
            ok=True,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            normalized_brief=normalized_brief,
            next_question=next_question,
            planner_mode=planner_mode,
        )

    return build_recruiter_chat_response(
        ok=True,
        state=RECRUITER_CHAT_STATE_READY_FOR_PLANNING,
        language=language,
        normalized_brief=normalized_brief,
        planner_mode=planner_mode,
    )


AGENT_TOOLS_V0 = {
    "validate_search_brief": {
        "requires_approval": False,
        "description": "Validate and normalize Search Brief v0.",
    },
    "adapt_brief_to_structured_request": {
        "requires_approval": False,
        "description": "Adapt a ready Search Brief into StructuredSearchRequest.",
    },
    "build_query_plan": {
        "requires_approval": False,
        "description": "Build a QueryPlan without executing search.",
    },
    "validate_query_plan": {
        "requires_approval": False,
        "description": "Validate a QueryPlan deterministically before execution.",
    },
    "run_single_wave_search": {
        "requires_approval": True,
        "description": "Run single-wave Tavily search through the backend pipeline.",
    },
    "run_multi_wave_search": {
        "requires_approval": True,
        "description": "Run explicit multi-wave search through the backend pipeline.",
    },
    "analyze_candidate_quality": {
        "requires_approval": False,
        "description": "Analyze already returned candidate quality signals.",
    },
    "summarize_search_results": {
        "requires_approval": False,
        "description": "Summarize already available report and result data.",
    },
    "suggest_next_iteration": {
        "requires_approval": False,
        "description": "Suggest the next sourcing iteration without executing it.",
    },
}


def agent_tool_contract() -> dict:
    return {
        "tools": AGENT_TOOLS_V0,
        "approval_statuses": [
            AGENT_TOOL_APPROVAL_NOT_REQUIRED,
            AGENT_TOOL_APPROVAL_REQUIRED,
            AGENT_TOOL_APPROVAL_APPROVED,
            AGENT_TOOL_APPROVAL_REJECTED,
        ],
        "absolute_boundaries": [
            "no_direct_web_search_bypass",
            "no_linkedin_login",
            "no_linkedin_scraping_or_bypass",
            "no_automatic_candidate_messaging",
            "no_account_actions",
        ],
    }


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


async def run_query_plan_wave(
    query_plan: dict,
    wave_id: int | None = None,
) -> list[dict]:
    query_results = []

    for query_slot in query_plan["queries"]:
        query_result = await run_query_slot(query_slot)
        if wave_id is not None:
            query_result["wave_id"] = wave_id
        query_results.append(query_result)

    return query_results


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


def query_plan_fingerprint_payload(query_plan: dict) -> dict:
    return {
        "planner_version": query_plan.get("planner_version"),
        "planner_mode": query_plan.get("planner_mode", PLANNER_MODE_RULE_BASED),
        "input_snapshot": query_plan.get("input_snapshot"),
        "queries": query_plan.get("queries"),
        "filters": query_plan.get("filters"),
        "execution": query_plan.get("execution"),
        "reporting": query_plan.get("reporting"),
    }


def query_plan_fingerprint(query_plan: dict) -> str:
    payload = json.dumps(
        query_plan_fingerprint_payload(query_plan),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def add_query_plan_fingerprint(query_plan: dict) -> dict:
    return {
        **query_plan,
        "plan_fingerprint": query_plan_fingerprint(query_plan),
    }


def execution_approval_metadata(
    approval: ExecutionApproval,
    expected_action: str,
    query_plan: dict,
) -> dict:
    return {
        "approval_status": approval.approval_status,
        "approved_action": approval.approved_action,
        "approved_planner_mode": approval.approved_planner_mode,
        "approved_query_count": approval.approved_query_count,
        "approved_plan_fingerprint": approval.approved_plan_fingerprint,
        "expected_action": expected_action,
        "current_plan_fingerprint": query_plan_fingerprint(query_plan),
        "current_query_count": len(query_plan.get("queries", [])),
        "execution_allowed": True,
    }


def validate_execution_approval(
    approval: ExecutionApproval | None,
    expected_action: str,
    query_plan: dict,
) -> tuple[dict | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    current_fingerprint = query_plan_fingerprint(query_plan)
    current_query_count = len(query_plan.get("queries", []))

    if approval is None:
        add_plan_validation_error(
            errors,
            "execution_approval",
            "missing_execution_approval",
            "Tavily execution requires explicit approval for the visible QueryPlan.",
        )
        return None, errors

    if approval.approval_status != AGENT_TOOL_APPROVAL_APPROVED:
        add_plan_validation_error(
            errors,
            "execution_approval.approval_status",
            "approval_not_approved",
            "Execution approval status must be approved.",
        )

    if approval.approved_action != expected_action:
        add_plan_validation_error(
            errors,
            "execution_approval.approved_action",
            "wrong_execution_action",
            f"Approval must be for {expected_action}.",
        )

    if approval.approved_planner_mode != PLANNER_MODE_RULE_BASED:
        add_plan_validation_error(
            errors,
            "execution_approval.approved_planner_mode",
            "unsupported_execution_planner_mode",
            "Only rule_based QueryPlan execution is supported in this phase.",
        )

    if approval.approved_query_count != current_query_count:
        add_plan_validation_error(
            errors,
            "execution_approval.approved_query_count",
            "stale_or_mismatched_query_count",
            "Approved query count does not match the current QueryPlan.",
        )

    if approval.approved_plan_fingerprint != current_fingerprint:
        add_plan_validation_error(
            errors,
            "execution_approval.approved_plan_fingerprint",
            "stale_or_mismatched_plan_fingerprint",
            "Approved plan fingerprint does not match the current QueryPlan.",
        )

    if errors:
        return None, errors

    return execution_approval_metadata(approval, expected_action, query_plan), []


def planner_explanation_for_rule_based() -> str:
    return "Using tested Java Backend rule-based planner baseline."


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


def ai_planner_coverage_policy_for(
    normalized_brief: dict,
    normalized_request: dict,
) -> dict | None:
    search_depth = normalized_brief.get("search_depth") or SEARCH_DEPTH_STANDARD

    for policy in AI_PLANNER_COVERAGE_POLICIES:
        if (
            normalized_request.get("role_family") == policy["role_family"]
            and normalized_request.get("technology") == policy["technology"]
            and (normalized_request.get("location") or "").strip().lower()
            == policy["location"].lower()
            and search_depth == policy["search_depth"]
        ):
            policy_copy = dict(policy)
            policy_copy["selected_stack"] = normalized_request.get("stack", [])
            return policy_copy

    return None


def ai_planner_coverage_policy_prompt(
    coverage_policy: dict | None,
    normalized_request: dict,
) -> dict:
    if not coverage_policy:
        return {
            "configured": False,
            "warning": AI_PLANNER_COVERAGE_NOT_CONFIGURED_WARNING,
        }

    expected_plan = RuleBasedQueryPlannerV1().build(normalized_request)
    return {
        "configured": True,
        "policy_id": coverage_policy["policy_id"],
        "policy_version": coverage_policy["policy_version"],
        "expected_query_count": coverage_policy["expected_query_count"],
        "required_shape": {
            "role_based_min": coverage_policy["role_based_min"],
            "stack_focused_min": coverage_policy["stack_focused_min"],
            "min_role_phrase_diversity": coverage_policy[
                "min_role_phrase_diversity"
            ],
        },
        "selected_stack": coverage_policy.get("selected_stack", []),
        "max_ai_plan_revision_attempts": coverage_policy[
            "max_ai_plan_revision_attempts"
        ],
        "query_slot_blueprint": [
            {
                "id": query["id"],
                "category": query["category"],
                "purpose": query["purpose"],
                "role_phrase": query["role_phrase"],
                "uses_stack": query.get("uses_stack", []),
                "query": query["query"],
                "max_results": query["max_results"],
            }
            for query in expected_plan.get("queries", [])
        ],
    }


def normalize_ai_text_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []

    return [str(value) for value in values if str(value or "").strip()]


def ai_plan_output_warnings(ai_output: dict | None) -> list[str]:
    if not isinstance(ai_output, dict):
        return []

    return normalize_ai_text_list(ai_output.get("warnings", []))


def ai_plan_output_assumptions(ai_output: dict | None) -> list[str]:
    if not isinstance(ai_output, dict):
        return []

    return normalize_ai_text_list(ai_output.get("assumptions", []))


def ai_query_planner_system_prompt() -> str:
    return (
        "You are an AI Query Planner for a recruiter sourcing search engine. "
        "Return only valid JSON. You may propose a draft QueryPlan, but you must not "
        "execute searches, browse the web, scrape LinkedIn, log in to LinkedIn, send "
        "messages, or act on accounts. Build LinkedIn public profile X-ray queries only "
        "inside the approved QueryPlan contract."
    )


def ai_query_planner_user_prompt(
    normalized_brief: dict,
    normalized_request: dict,
    repair_feedback: list[dict[str, str]] | None = None,
    previous_draft_plan: dict | None = None,
) -> str:
    coverage_policy = ai_planner_coverage_policy_for(
        normalized_brief,
        normalized_request,
    )
    coverage_policy_prompt = ai_planner_coverage_policy_prompt(
        coverage_policy,
        normalized_request,
    )
    is_repair = bool(repair_feedback)
    task = (
        "Repair the previous draft QueryPlan using the coverage feedback."
        if is_repair
        else "Create a draft QueryPlan for recruiter sourcing."
    )

    return json.dumps(
        {
            "task": task,
            "required_output": {
                "planner_version": "ai_query_planner_v0",
                "planner_mode": "ai",
                "explanation": "Short explanation of the planning logic.",
                "draft_query_plan": {
                    "planner_version": "ai_query_planner_v0",
                    "planner_mode": "ai",
                    "input_snapshot": normalized_request,
                    "queries": coverage_policy_prompt.get("query_slot_blueprint")
                    or [
                        {
                            "id": "Q01",
                            "category": "role_based",
                            "purpose": "Why this query exists.",
                            "role_phrase": "Role phrase used in query.",
                            "query": "site:linkedin.com/in AND \"Role\" AND \"Location\"",
                            "uses_stack": [],
                            "max_results": QUERY_PLAN_MAX_RESULTS,
                        }
                    ],
                    "filters": {
                        "linkedin_profiles_only": normalized_request[
                            "linkedin_profiles_only"
                        ],
                        "location_filter_enabled": normalized_request[
                            "location_filter_enabled"
                        ],
                    },
                    "execution": {
                        "mode": "sequential",
                        "max_results_per_query": QUERY_PLAN_MAX_RESULTS,
                    },
                    "reporting": QUERY_PLAN_REPORTING_FIELDS,
                },
                "warnings": [],
                "assumptions": [],
            },
            "search_brief": normalized_brief,
            "normalized_structured_request": normalized_request,
            "coverage_policy": coverage_policy_prompt,
            "repair_feedback": repair_feedback or [],
            "previous_draft_query_plan": previous_draft_plan if is_repair else None,
            "hard_limits": {
                "max_queries": 10,
                "expected_queries_when_coverage_policy_configured": coverage_policy_prompt.get(
                    "expected_query_count"
                ),
                "max_results_per_query": QUERY_PLAN_MAX_RESULTS,
                "allowed_source_scope": "site:linkedin.com/in",
                "allowed_profile_sources": [PROFILE_SOURCE_LINKEDIN_PUBLIC],
                "default_planner_remains": PLANNER_MODE_RULE_BASED,
            },
            "coverage_rules": [
                "If coverage_policy.configured is true, return exactly the expected query count.",
                "For the Java Backend Ukraine standard policy, return exactly 10 query slots.",
                "Use role-based coverage plus stack-focused coverage; do not collapse the plan to one broad query.",
                "For the Java Backend Ukraine standard policy, target at least 6 role-based slots and 4 stack-focused slots.",
                "Use diverse role phrases instead of repeating the same phrase across all slots.",
                "If selected stack terms are present, stack-focused slots must include those terms in the query text and uses_stack.",
            ],
            "safety_rules": [
                "Every query must include site:linkedin.com/in.",
                "Every query must include the target location.",
                "Every query must include the main technology signal from the brief.",
                "Every query must include a role signal from the brief or policy blueprint.",
                "Do not include arbitrary domains.",
                "Do not include LinkedIn login, scraping, bypass, messaging, or account-action behavior.",
                "Do not change filters, scoring, dedupe, location filtering, or execution behavior.",
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


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


def add_plan_validation_error(
    errors: list[dict[str, str]],
    field: str,
    code: str,
    message: str,
) -> None:
    errors.append({"field": field, "code": code, "message": message})


def query_site_scopes(query: str) -> list[str]:
    return re.findall(r"(?i)\bsite:([^\s)]+)", query or "")


def query_has_forbidden_terms(query: str) -> bool:
    lowered_query = (query or "").lower()
    return any(term in lowered_query for term in FORBIDDEN_AI_QUERY_TERMS)


def query_has_allowed_scope_only(query: str) -> bool:
    scopes = [scope.lower().strip('"') for scope in query_site_scopes(query)]
    return bool(scopes) and all(scope == "linkedin.com/in" for scope in scopes)


def query_has_brief_signal(query: str, normalized_request: dict) -> bool:
    technology = normalized_request.get("technology")
    role_family = normalized_request.get("role_family")
    if technology and find_term_match(query, technology):
        return True
    if role_family and all(
        find_term_match(query, term)
        for term in re.findall(r"[A-Za-z][A-Za-z+#.]*", role_family)
    ):
        return True
    return False


def validate_ai_query_plan(
    draft_plan: dict | None,
    normalized_brief: dict,
    normalized_request: dict,
) -> tuple[dict | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    if not isinstance(draft_plan, dict):
        add_plan_validation_error(
            errors,
            "draft_query_plan",
            "invalid_plan_shape",
            "AI draft plan must be an object.",
        )
        return None, errors

    for field in [
        "planner_version",
        "planner_mode",
        "input_snapshot",
        "queries",
        "filters",
        "execution",
        "reporting",
    ]:
        if field not in draft_plan:
            add_plan_validation_error(
                errors,
                field,
                "missing_required_field",
                f"QueryPlan is missing {field}.",
            )

    queries = draft_plan.get("queries")
    if not isinstance(queries, list) or not queries:
        add_plan_validation_error(
            errors,
            "queries",
            "invalid_queries",
            "QueryPlan must contain at least one query.",
        )
        queries = []

    if len(queries) > 10:
        add_plan_validation_error(
            errors,
            "queries",
            "too_many_queries",
            "Standard AI QueryPlan must not exceed 10 queries.",
        )

    planner_mode = draft_plan.get("planner_mode")
    if planner_mode != PLANNER_MODE_AI:
        add_plan_validation_error(
            errors,
            "planner_mode",
            "invalid_planner_mode",
            "AI QueryPlan must declare planner_mode as ai.",
        )

    seen_query_ids: set[str] = set()
    for index, query_slot in enumerate(queries):
        field_prefix = f"queries[{index}]"
        if not isinstance(query_slot, dict):
            add_plan_validation_error(
                errors,
                field_prefix,
                "invalid_query_slot",
                "Query slot must be an object.",
            )
            continue

        for field in [
            "id",
            "category",
            "purpose",
            "role_phrase",
            "query",
            "uses_stack",
            "max_results",
        ]:
            if field not in query_slot:
                add_plan_validation_error(
                    errors,
                    f"{field_prefix}.{field}",
                    "missing_required_field",
                    f"Query slot is missing {field}.",
                )

        query_id = query_slot.get("id")
        if query_id in seen_query_ids:
            add_plan_validation_error(
                errors,
                f"{field_prefix}.id",
                "duplicate_query_id",
                "Query IDs must be unique.",
            )
        elif query_id:
            seen_query_ids.add(query_id)

        query = query_slot.get("query") or ""
        if not query:
            add_plan_validation_error(
                errors,
                f"{field_prefix}.query",
                "empty_query",
                "Query string must not be empty.",
            )
        else:
            if not query_has_allowed_scope_only(query):
                add_plan_validation_error(
                    errors,
                    f"{field_prefix}.query",
                    "invalid_source_scope",
                    "Query must use only site:linkedin.com/in.",
                )
            if query_has_forbidden_terms(query):
                add_plan_validation_error(
                    errors,
                    f"{field_prefix}.query",
                    "forbidden_query_behavior",
                    "Query contains forbidden behavior terms.",
                )
            location = normalized_request.get("location")
            if location and not find_term_match(query, location):
                add_plan_validation_error(
                    errors,
                    f"{field_prefix}.query",
                    "missing_target_location",
                    f"Query does not include target location {location}.",
                )
            if not query_has_brief_signal(query, normalized_request):
                add_plan_validation_error(
                    errors,
                    f"{field_prefix}.query",
                    "missing_role_or_technology_signal",
                    "Query must include a role or technology signal from the brief.",
                )

        max_results = query_slot.get("max_results")
        if not isinstance(max_results, int) or max_results > QUERY_PLAN_MAX_RESULTS:
            add_plan_validation_error(
                errors,
                f"{field_prefix}.max_results",
                "invalid_max_results",
                f"max_results must be an integer no greater than {QUERY_PLAN_MAX_RESULTS}.",
            )

        uses_stack = query_slot.get("uses_stack")
        if uses_stack is not None and not isinstance(uses_stack, list):
            add_plan_validation_error(
                errors,
                f"{field_prefix}.uses_stack",
                "invalid_uses_stack",
                "uses_stack must be a list.",
            )

    filters = draft_plan.get("filters") or {}
    if filters:
        if filters.get("linkedin_profiles_only") is False:
            add_plan_validation_error(
                errors,
                "filters.linkedin_profiles_only",
                "filter_override_not_allowed",
                "AI plan must not disable LinkedIn profiles only filter.",
            )
        if filters.get("location_filter_enabled") is False:
            add_plan_validation_error(
                errors,
                "filters.location_filter_enabled",
                "filter_override_not_allowed",
                "AI plan must not disable location filter.",
            )

    execution = draft_plan.get("execution") or {}
    if execution and execution.get("mode") not in {None, "sequential"}:
        add_plan_validation_error(
            errors,
            "execution.mode",
            "unsupported_execution_mode",
            "AI plan execution mode must remain sequential.",
        )

    if errors:
        return None, errors

    validated_plan = {
        **draft_plan,
        "planner_version": draft_plan.get("planner_version") or "ai_query_planner_v0",
        "planner_mode": PLANNER_MODE_AI,
        "input_snapshot": normalized_request,
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

    return validated_plan, []


def role_phrase_key(value: object) -> str:
    return compact_spaces(str(value or "")).lower()


def query_slot_stack_terms(query_slot: dict, selected_stack: list[str]) -> list[str]:
    query = query_slot.get("query") or ""
    uses_stack = query_slot.get("uses_stack")
    if not isinstance(uses_stack, list):
        uses_stack = []

    matched_terms = []
    for stack_term in selected_stack:
        if stack_term in uses_stack and find_term_match(query, stack_term):
            matched_terms.append(stack_term)

    return matched_terms


def query_slot_is_stack_focused(query_slot: dict, selected_stack: list[str]) -> bool:
    return bool(query_slot_stack_terms(query_slot, selected_stack))


def validate_ai_query_plan_coverage(
    query_plan: dict,
    normalized_brief: dict,
    normalized_request: dict,
) -> tuple[list[dict[str, str]], list[str], dict | None]:
    coverage_policy = ai_planner_coverage_policy_for(
        normalized_brief,
        normalized_request,
    )
    if not coverage_policy:
        return [], [AI_PLANNER_COVERAGE_NOT_CONFIGURED_WARNING], None

    errors: list[dict[str, str]] = []
    queries = [
        query
        for query in query_plan.get("queries", [])
        if isinstance(query, dict)
    ]
    selected_stack = coverage_policy.get("selected_stack", [])
    expected_query_count = coverage_policy["expected_query_count"]

    if len(queries) != expected_query_count:
        add_plan_validation_error(
            errors,
            "coverage.query_count",
            "undercovered_query_count",
            (
                f"AI plan returned {len(queries)} queries, but coverage policy "
                f"requires exactly {expected_query_count} queries."
            ),
        )

    stack_focused_queries = [
        query for query in queries if query_slot_is_stack_focused(query, selected_stack)
    ]
    stack_focused_query_ids = {id(query) for query in stack_focused_queries}
    role_based_queries = [
        query for query in queries if id(query) not in stack_focused_query_ids
    ]

    if len(role_based_queries) < coverage_policy["role_based_min"]:
        add_plan_validation_error(
            errors,
            "coverage.role_based",
            "missing_role_based_coverage",
            (
                f"AI plan has {len(role_based_queries)} role-based queries, but "
                f"coverage policy requires at least {coverage_policy['role_based_min']}."
            ),
        )

    if selected_stack and len(stack_focused_queries) < coverage_policy["stack_focused_min"]:
        add_plan_validation_error(
            errors,
            "coverage.stack_focused",
            "missing_stack_focused_coverage",
            (
                f"AI plan has {len(stack_focused_queries)} stack-focused queries, but "
                f"coverage policy requires at least {coverage_policy['stack_focused_min']}."
            ),
        )

    role_phrase_count = len(
        {
            role_phrase_key(query.get("role_phrase"))
            for query in queries
            if role_phrase_key(query.get("role_phrase"))
        }
    )
    if role_phrase_count < coverage_policy["min_role_phrase_diversity"]:
        add_plan_validation_error(
            errors,
            "coverage.role_phrase_diversity",
            "insufficient_role_phrase_diversity",
            (
                f"AI plan has {role_phrase_count} distinct role phrases, but "
                "coverage policy requires at least "
                f"{coverage_policy['min_role_phrase_diversity']}."
            ),
        )

    technology = normalized_request.get("technology")
    if technology:
        missing_technology_indexes = [
            str(index + 1)
            for index, query in enumerate(queries)
            if not find_term_match(query.get("query") or "", technology)
        ]
        if missing_technology_indexes:
            add_plan_validation_error(
                errors,
                "coverage.technology",
                "missing_technology_signal",
                (
                    "AI plan has queries without the required technology signal: "
                    + ", ".join(missing_technology_indexes)
                    + "."
                ),
            )

    location = normalized_request.get("location")
    if location:
        missing_location_indexes = [
            str(index + 1)
            for index, query in enumerate(queries)
            if not find_term_match(query.get("query") or "", location)
        ]
        if missing_location_indexes:
            add_plan_validation_error(
                errors,
                "coverage.location",
                "missing_target_location",
                (
                    "AI plan has queries without the required target location: "
                    + ", ".join(missing_location_indexes)
                    + "."
                ),
            )

    if selected_stack:
        stack_terms_seen = {
            term
            for query in stack_focused_queries
            for term in query_slot_stack_terms(query, selected_stack)
        }
        missing_stack_terms = [
            term for term in selected_stack if term not in stack_terms_seen
        ]
        if missing_stack_terms:
            add_plan_validation_error(
                errors,
                "coverage.stack_terms",
                "missing_selected_stack_terms",
                (
                    "AI plan stack-focused queries did not cover selected stack terms: "
                    + ", ".join(missing_stack_terms)
                    + "."
                ),
            )

    return errors, [], coverage_policy


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


def snapshot_slug(value: object) -> str:
    compact_value = compact_spaces(str(value or "")).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", compact_value).strip("-")
    return slug or "unknown"


def structured_search_snapshot_filename(
    normalized_request: dict,
    timestamp: datetime,
    snapshot_type: str = "structured-search",
) -> str:
    timestamp_part = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")
    role_part = snapshot_slug(normalized_request.get("role_family"))
    technology_part = snapshot_slug(normalized_request.get("technology"))
    location_part = snapshot_slug(normalized_request.get("location"))

    return (
        f"{timestamp_part}_{snapshot_type}_"
        f"{role_part}-{technology_part}-{location_part}.json"
    )


def query_result_status_summary(query_result: dict) -> dict:
    summary = {
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
    if "wave_id" in query_result:
        summary["wave_id"] = query_result["wave_id"]

    return summary


def build_structured_search_snapshot(
    query_plan: dict,
    query_results: list[dict],
    deduped_results: list[dict],
    report: dict,
    timestamp: datetime,
    snapshot_type: str = "structured-search",
    execution_approval: dict | None = None,
) -> dict:
    return {
        "snapshot_type": snapshot_type,
        "timestamp": timestamp.isoformat(),
        "normalized_request": query_plan.get("input_snapshot"),
        "query_plan": add_query_plan_fingerprint(query_plan),
        "plan_fingerprint": query_plan_fingerprint(query_plan),
        "execution_approval": execution_approval,
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
    snapshot_type: str = "structured-search",
    execution_approval: dict | None = None,
) -> Path:
    timestamp = datetime.now(timezone.utc)
    snapshot = build_structured_search_snapshot(
        query_plan,
        query_results,
        deduped_results,
        report,
        timestamp,
        snapshot_type,
        execution_approval,
    )
    SEARCH_RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path = SEARCH_RUN_LOG_DIR / structured_search_snapshot_filename(
        query_plan.get("input_snapshot") or {},
        timestamp,
        snapshot_type,
    )
    snapshot_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return snapshot_path


async def run_multi_wave_query_plan(
    query_plan: dict,
    settings: dict,
) -> tuple[list[dict], dict, list[dict]]:
    all_query_results: list[dict] = []
    wave_reports: list[dict] = []
    cumulative_unique_urls: set[str] = set()
    low_gain_streak = 0
    stop_reason = "max_waves_reached"

    for wave_id in range(1, settings["max_waves"] + 1):
        wave_query_results = await run_query_plan_wave(query_plan, wave_id)
        all_query_results.extend(wave_query_results)

        wave_deduped_results, wave_report = build_deduped_results_and_report(
            query_plan,
            wave_query_results,
            include_wave_sources=True,
        )
        wave_unique_urls = {
            result["normalized_url"] for result in wave_deduped_results
        }
        new_unique_urls = wave_unique_urls - cumulative_unique_urls
        duplicates_across_waves = len(wave_unique_urls & cumulative_unique_urls)
        cumulative_unique_urls.update(wave_unique_urls)

        new_unique_count = len(new_unique_urls)
        if new_unique_count < settings["min_new_unique_per_wave"]:
            low_gain_streak += 1
        else:
            low_gain_streak = 0

        wave_reports.append(
            {
                "wave_id": wave_id,
                "queries_succeeded": wave_report["queries_succeeded"],
                "queries_failed": wave_report["queries_failed"],
                "raw_total": wave_report["raw_total"],
                "displayed": wave_report["displayed"],
                "unique_profiles": wave_report["unique_profiles"],
                "new_unique_profiles": new_unique_count,
                "cumulative_unique_profiles": len(cumulative_unique_urls),
                "duplicates_across_waves": duplicates_across_waves,
                "hidden_by_profile_filter": wave_report[
                    "hidden_by_profile_filter"
                ],
                "hidden_by_location_filter": wave_report[
                    "hidden_by_location_filter"
                ],
                "hidden_by_foreign_current_location": wave_report[
                    "hidden_by_foreign_current_location"
                ],
            }
        )

        if low_gain_streak >= settings["patience"]:
            stop_reason = "low_incremental_gain"
            break

    deduped_results, report = build_deduped_results_and_report(
        query_plan,
        all_query_results,
        include_wave_sources=True,
    )
    report["queries_total"] = len(all_query_results)
    report.update(
        {
            "experimental": True,
            "mode": "multi_wave",
            "multi_wave_settings": settings,
            "waves_run": len(wave_reports),
            "planned_max_waves": settings["max_waves"],
            "stop_reason": stop_reason,
            "queries_executed": len(all_query_results),
            "unique_profiles_per_wave": [
                wave["unique_profiles"] for wave in wave_reports
            ],
            "new_unique_profiles_per_wave": [
                wave["new_unique_profiles"] for wave in wave_reports
            ],
            "cumulative_unique_profiles": [
                wave["cumulative_unique_profiles"] for wave in wave_reports
            ],
            "duplicates_across_waves": sum(
                wave["duplicates_across_waves"] for wave in wave_reports
            ),
            "wave_reports": wave_reports,
        }
    )

    return deduped_results, report, all_query_results


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
