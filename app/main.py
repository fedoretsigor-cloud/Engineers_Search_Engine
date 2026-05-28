from pathlib import Path
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
    AGENT_RUNTIME_ERROR_APPROVAL_MISMATCH,
    AGENT_RUNTIME_ERROR_EXECUTION_FAILED,
    AGENT_RUNTIME_ERROR_TOOL_UNAVAILABLE,
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
from app.agent_runtime import (
    AGENT_RUNTIME_STATE_APPROVAL_PENDING,
    AGENT_RUNTIME_STATE_BLOCKED,
    AGENT_RUNTIME_STATE_ERROR,
    AGENT_RUNTIME_STATE_OBSERVED,
    AGENT_RUNTIME_TURN_MODE_EXECUTE_APPROVED,
    AGENT_RUNTIME_TURN_MODE_PREPARE,
    AgentRuntimeTurnResponse,
    AgentToolResult,
    normalize_runtime_execution_binding,
    runtime_error,
    runtime_pending_approval,
    validate_runtime_execution_approval,
)
from app.agent_plan import (
    AGENT_PLAN_STATUS_NEEDS_CLARIFICATION,
    AGENT_PLAN_STATUS_SUPPORTED,
    AGENT_PLAN_STATUS_UNSUPPORTED,
    agent_plan_needs_clarification_message,
    agent_plan_proposed_action,
    agent_plan_supported_message,
    agent_plan_unsupported_message,
    build_agent_plan_response as _build_agent_plan_response,
    build_agent_plan_response_with_wording as _build_agent_plan_response_with_wording,
    is_supported_agent_v0_baseline,
    validate_agent_query_plan_action,
)
from app.agent_messages import (
    brief_refinement_source_message,
    last_stack_item_source_message,
    localized_clarifying_question_source_message,
    query_plan_ai_validated_approval_notice,
    query_plan_fallback_approval_notice,
    query_plan_preview_approval_notice,
    query_plan_ready_approval_notice,
    query_plan_rejected_approval_notice,
    ready_for_planning_source_message,
    recruiter_chat_draft_preserved_source_message,
    recruiter_chat_near_empty_source_message,
    recruiter_chat_onboarding_source_message,
    recruiter_chat_refusal_source_message,
    refinement_requires_initial_brief_source_message,
    runtime_execution_failed_source_message,
    runtime_tool_unavailable_source_message,
    search_brief_not_ready_for_query_plan_source_message,
    unsupported_patch_source_message,
    validation_error_source_message,
)
from app.agent_response import (
    agent_response_limitations,
    agent_response_message_en,
    agent_response_message_ru,
    agent_response_next_iteration_options,
    agent_response_quality_bucket,
    agent_response_quality_distribution,
    agent_response_quality_notes,
    agent_response_signal_counts,
    agent_response_suggested_next_actions,
    agent_response_summary_facts,
    build_agent_response,
    next_iteration_option,
    next_iteration_stack_observation_threshold,
    normalize_agent_language,
    stack_term_visibility_counts,
    top_review_flag_counts,
)
from app.agent_wording import (
    AGENT_WORDING_FALLBACK_NOT_CONFIGURED,
    AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
    AGENT_WORDING_MODE_LLM_ASSISTED,
    AGENT_WORDING_TIMEOUT_SECONDS,
    AGENT_WORDING_USE_CASE_RECRUITER_CHAT_ONBOARDING,
    OPENAI_AGENT_WORDING_MAX_COMPLETION_TOKENS,
    agent_plan_wording_payload,
    agent_response_wording_payload,
    agent_wording_allowed_numbers,
    agent_wording_hard_boundaries,
    agent_wording_has_disallowed_key,
    agent_wording_has_openai_config,
    agent_wording_has_prohibited_content,
    agent_wording_language_matches,
    agent_wording_number_tokens,
    agent_wording_system_prompt,
    agent_wording_text_values,
    agent_wording_user_prompt,
    build_agent_wording_provenance,
    apply_llm_wording_to_agent_plan as _apply_llm_wording_to_agent_plan,
    apply_llm_wording_to_agent_response as _apply_llm_wording_to_agent_response,
    normalize_agent_wording_limitations,
    normalize_agent_wording_warnings,
    run_openai_json_agent_wording as _run_openai_json_agent_wording,
    validate_agent_wording_output,
    with_agent_wording_metadata,
)
from app.brief_patch import (
    BRIEF_PATCH_ADD_MUST_HAVE,
    BRIEF_PATCH_ADD_STACK,
    BRIEF_PATCH_NOOP,
    BRIEF_PATCH_RECONFIRM_FIELD,
    BRIEF_PATCH_REMOVE_MUST_HAVE,
    BRIEF_PATCH_REMOVE_STACK,
    BRIEF_PATCH_REPLACE_MUST_HAVE,
    BRIEF_PATCH_REPLACE_STACK,
    BRIEF_PATCH_SET_LOCATION,
    BRIEF_PATCH_SET_SEARCH_DEPTH,
    BRIEF_PATCH_SET_SENIORITY,
    BRIEF_PATCH_UNSUPPORTED,
    build_brief_patch,
)
from app.candidate_explanation_wording import (
    build_candidate_explanation_wording_response,
)
from app.pending_answer_interpreter import (
    PENDING_ANSWER_INTENT_ANSWER_PENDING_FIELD,
    PENDING_ANSWER_INTENT_PROVIDE_UPDATE_VALUE,
    run_openai_json_pending_answer_interpreter as _run_openai_json_pending_answer_interpreter,
    validate_pending_answer_interpreter_output,
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
    AgentRuntimeTurnRequest,
    CandidateExplanationWordingRequest,
    ExecutionApproval,
    MultiWaveStructuredSearchRequest,
    RecruiterChatIntentRequest,
    RecruiterChatMessage,
    RecruiterChatTurnRequest,
    SearchBrief,
    SearchRequest,
    StructuredSearchRequest,
)
from app.routes import RouteDependencies, create_router
from app.search_brief import (
    adapt_search_brief_to_structured_request,
    build_structured_request_from_brief,
    clarifying_question_for_missing_field as canonical_clarifying_question_for_missing_field,
    normalize_brief_stack_items,
    search_brief_fingerprint,
    search_brief_fingerprint_payload,
    search_brief_validation_response,
    validate_and_normalize_search_brief,
)
from app.search_brief_extractor import (
    apply_requirement_search_signal_resolution_to_draft,
    run_openai_json_search_brief_extractor as _run_openai_json_search_brief_extractor,
    validate_search_brief_extractor_output,
)
from app.search_brief_refinement import (
    normalize_refinement_must_have_value,
    run_openai_json_search_brief_refinement_interpreter as _run_openai_json_search_brief_refinement_interpreter,
    validate_search_brief_refinement_output,
)
from app.search_validation import (
    add_validation_error,
    canonical_value,
    normalize_freeform_label,
    normalize_location_value,
    normalize_search_location_value,
    normalize_multi_wave_search_request,
    normalize_role_family_value,
    normalize_stack_item_value,
    normalize_structured_search_request,
    normalize_technology_value,
)
from app.search_execution import (
    PHASE9_PROVIDER_ORDER,
    TAVILY_SEARCH_URL,
    provider_breakdown_from_query_results,
    run_provider_expansion_query_plan,
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
    collect_seniority_evidence,
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
)
from app.text_utils import (
    clean_headline_value,
    clean_profile_text,
    compact_spaces,
    contains_cyrillic_text,
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
OPENAI_RECRUITER_INTENT_MAX_COMPLETION_TOKENS = 500
OPENAI_STACK_SIGNAL_CLASSIFIER_MAX_COMPLETION_TOKENS = 500
RECRUITER_CHAT_DEFAULT_PLANNER_MODE = PLANNER_MODE_RULE_BASED
RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION = "needs_clarification"
RECRUITER_CHAT_STATE_READY_FOR_PLANNING = "ready_for_planning"
RECRUITER_CHAT_STATE_REFUSED = "refused"
RECRUITER_CHAT_ALLOWED_MESSAGE_ROLES = {"assistant", "recruiter", "user"}
RECRUITER_INTENT_CANDIDATE_SEARCH = "candidate_search"
RECRUITER_INTENT_SMALL_TALK = "small_talk"
RECRUITER_INTENT_OFF_TOPIC = "off_topic"
RECRUITER_INTENT_UNCLEAR = "unclear"
RECRUITER_INTENT_PROHIBITED = "prohibited"
RECRUITER_INTENT_RESTART = "restart"
RECRUITER_ROLE_DOMAIN_IT_SOFTWARE = "it_software"
RECRUITER_ROLE_DOMAIN_NON_IT = "non_it"
RECRUITER_ROLE_DOMAIN_AMBIGUOUS = "ambiguous"
RECRUITER_ROLE_DOMAIN_UNKNOWN = "unknown"
RECRUITER_ROLE_SUPPORT_SUPPORTED = "supported"
RECRUITER_ROLE_SUPPORT_UNSUPPORTED = "unsupported"
RECRUITER_ROLE_SUPPORT_AMBIGUOUS = "ambiguous"
RECRUITER_ROLE_SUPPORT_NOISE = "noise"
RECRUITER_ROLE_SUPPORT_UNKNOWN = "unknown"
RECRUITER_PENDING_INTENT_CONFIRM = "confirm"
RECRUITER_PENDING_INTENT_REFINE = "refine"
RECRUITER_PENDING_INTENT_REJECT = "reject"
RECRUITER_PENDING_INTENT_UNCLEAR = "unclear"
RECRUITER_HYPOTHESIS_INTENT_CONFIRM = "confirm"
RECRUITER_HYPOTHESIS_INTENT_REJECT = "reject"
RECRUITER_HYPOTHESIS_INTENT_REFINE = "refine"
RECRUITER_HYPOTHESIS_INTENT_UNCLEAR = "unclear"
RECRUITER_UPDATE_INTENT_SELECT_FIELD = "select_field"
RECRUITER_UPDATE_INTENT_PROVIDE_VALUE = "provide_value"
RECRUITER_UPDATE_INTENT_CANCEL = "cancel"
RECRUITER_UPDATE_INTENT_UNCLEAR = "unclear"
RECRUITER_FIELD_INTENT_FIELD_EXPLANATION = "field_explanation"
RECRUITER_FIELD_INTENT_NOT_FIELD_EXPLANATION = "not_field_explanation"
RECRUITER_FIELD_INTENT_ANSWERS_PENDING_FIELD = "answers_pending_field"
RECRUITER_FIELD_INTENT_ANSWERS_DIFFERENT_FIELD = "answers_different_field"
RECRUITER_FIELD_INTENT_REPEATS_EXISTING_VALUE = "repeats_existing_value"
RECRUITER_FIELD_INTENT_UNSUPPORTED_VALUE = "unsupported_value"
RECRUITER_FIELD_INTENT_AMBIGUOUS = "ambiguous"
RECRUITER_FIELD_INTENT_NOISE = "noise"
RECRUITER_FIELD_INTENT_UNCLEAR = "unclear"
RECRUITER_INTENT_CONFIDENCE_HIGH = "high"
RECRUITER_INTENT_CONFIDENCE_MEDIUM = "medium"
RECRUITER_INTENT_CONFIDENCE_LOW = "low"
RECRUITER_INTENT_PROMPT_VERSION = "phase_8_8_recruiter_intent_prompt_v1"
RECRUITER_INTENT_VALIDATOR_VERSION = "phase_8_8_recruiter_intent_validator_v1"
STACK_SIGNAL_CLASSIFIER_PROMPT_VERSION = "phase_9_6_stack_signal_classifier_v1"
STACK_SIGNAL_CLASSIFIER_VALIDATOR_VERSION = "phase_9_6_stack_signal_classifier_validator_v1"
RECRUITER_CHAT_WORDING_USE_CASE_CONVERSATION = "recruiter_chat_conversation"
RECRUITER_SEARCH_BRIEF_FIELDS = {
    "role_family",
    "technology",
    "stack",
    "location",
    "seniority",
    "search_depth",
    "profile_sources",
}
RECRUITER_CHAT_PROHIBITED_RULES = [
    {
        "code": "direct_web_search_bypass",
        "message": "Direct web-search by the agent outside the approved backend pipeline is prohibited.",
        "patterns": [
            r"\bdirect web[- ]search\b",
            r"\bdirect (google|web) search\b",
            r"\bdirect linkedin search\b",
            r"\b(search|google).{0,40}(directly|outside|instead of the app)\b",
            r"\bgoogle\b.{0,40}\bdirectly\b",
            r"\boutside (the )?approved backend\b",
            r"\bwithout (the )?backend\b",
            r"в обход (backend|бекенд|бекэнда)",
            r"прям(ой|ую|ым).{0,30}web[- ]?search",
            r"поищ.{0,40}(напрямую|в google|в гугл)",
        ],
    },
    {
        "code": "profile_opening_or_reading",
        "message": "Opening or reading LinkedIn profiles directly is prohibited.",
        "patterns": [
            r"\b(open|read|inspect|visit).{0,40}(profile|profiles|linkedin)\b",
            r"\b(profile|profiles|linkedin).{0,40}(open|read|inspect|visit)\b",
            r"(открой|прочитай|посмотри).{0,40}(профил|linkedin)",
            r"(профил|linkedin).{0,40}(открой|прочитай|посмотри)",
        ],
    },
    {
        "code": "private_contact_harvesting",
        "message": "Harvesting private candidate contact details is prohibited.",
        "patterns": [
            r"\b(collect|gather|find|get|extract).{0,40}(email|emails|phone|phones|telephone|contact|contacts)\b",
            r"\b(email|emails|phone|phones|telephone|contact|contacts).{0,40}(candidate|profile|linkedin)\b",
            r"(собери|найди|достань|извлеки).{0,40}(email|емейл|почт|телефон|контакт)",
            r"(email|емейл|почт|телефон|контакт).{0,40}(кандидат|профил|linkedin)",
        ],
    },
    {
        "code": "linkedin_login",
        "message": "LinkedIn login is prohibited.",
        "patterns": [
            r"linkedin.{0,40}\b(log\s?in|log\s+into|login|sign in)\b",
            r"\b(log\s?in|log\s+into|login|sign in)\b.{0,40}linkedin",
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
            r"\bmessage.{0,40}(candidate|candidates|profile|profiles)\b",
            r"\b(candidate|candidates).{0,40}(message|dm|email)\b",
            r"\bautomatic.{0,30}(outreach|message|messaging|email)\b",
            r"напиш[ии].{0,40}кандидат",
            r"отправ.{0,40}сообщ.{0,40}кандидат",
            r"свяж.{0,40}кандидат",
        ],
    },
    {
        "code": "autonomous_execution",
        "message": "Autonomous search execution without explicit approval is prohibited.",
        "patterns": [
            r"\brun.{0,40}search.{0,40}without.{0,20}(asking|approval|approve|confirmation)\b",
            r"\bsearch.{0,40}without.{0,20}(asking|approval|approve|confirmation)\b",
            r"\bwithout asking me\b",
            r"\bwithout approval\b",
            r"\bautonomously\b",
            r"\bautomatic.{0,30}search\b",
            r"запуст.{0,40}поиск.{0,40}без.{0,20}(апрув|одобр|подтверж|спрос)",
            r"без.{0,20}(апрув|одобр|подтверж|спрос).{0,40}поиск",
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
    r"academy|analyst|architect|backend|business|college|company|consultant|"
    r"data|developer|education|engineer|frontend|full[- ]?stack|hibernate|"
    r"inc|institute|java|kafka|lead|llc|ltd|manager|middle|polytechnic|"
    r"programmer|python|reporting|school|senior|software|solutions|spring|"
    r"sql|systems|technologies|technology|university"
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
        "provider": result.get("provider"),
        "provider_query_id": result.get("provider_query_id"),
        "provider_page": result.get("page"),
        "provider_rank": result.get("rank"),
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
        "provider": query_result.get("provider", "tavily"),
        "provider_query_id": query_result.get("provider_query_id"),
        "provider_page": query_result.get("provider_page"),
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
    query_source_key = (
        query_source.get("id"),
        query_source.get("provider", "tavily"),
        query_source.get("provider_query_id"),
        query_source.get("provider_page"),
    )
    if any(
        (
            source.get("id"),
            source.get("provider", "tavily"),
            source.get("provider_query_id"),
            source.get("provider_page"),
        )
        == query_source_key
        for source in query_sources
    ):
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
            "provider": query_result.get("provider", "tavily"),
            "provider_query_id": query_result.get("provider_query_id"),
            "provider_page": query_result.get("provider_page"),
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
                    "provider_sources": [query_source],
                    "wave_sources": [wave_source] if wave_source else [],
                    "location_signals": [location_signal] if location_signal else [],
                }
            else:
                current_item["result"] = choose_more_complete_result(
                    current_item["result"],
                    normalized_result,
                )
                append_unique_query_source(current_item["query_sources"], query_source)
                append_unique_query_source(
                    current_item["provider_sources"],
                    query_source,
                )
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
                "provider_sources": candidate.get("provider_sources", []),
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
            "provider_breakdown": provider_breakdown_from_query_results(
                query_contribution
            ),
            "providers": [
                provider
                for provider in PHASE9_PROVIDER_ORDER
                if any(
                    contribution.get("provider") == provider
                    for contribution in query_contribution
                )
            ],
        },
    )


async def run_openai_json_agent_wording(
    payload: dict,
) -> tuple[dict | None, str | None]:
    return await _run_openai_json_agent_wording(
        payload,
        chat_completions_url=OPENAI_CHAT_COMPLETIONS_URL,
    )


async def apply_llm_wording_to_agent_plan(
    agent_plan: dict,
    normalized_request: dict,
    language: str,
) -> dict:
    return await _apply_llm_wording_to_agent_plan(
        agent_plan,
        normalized_request,
        language,
        wording_runner=run_openai_json_agent_wording,
    )


async def apply_llm_wording_to_agent_response(agent_response: dict) -> dict:
    return await _apply_llm_wording_to_agent_response(
        agent_response,
        wording_runner=run_openai_json_agent_wording,
    )


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


def recruiter_chat_user_text(messages: list[RecruiterChatMessage]) -> str:
    return "\n".join(
        f"{normalize_text_value(message.role) or 'user'}: {message.content}"
        for message in messages
        if (normalize_text_value(message.role) or "").lower() in {"user", "recruiter"}
    )


def recruiter_chat_language(request: RecruiterChatTurnRequest) -> str:
    return "en"

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


def safe_unsupported_role_label(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    label = compact_spaces(value)
    if not label or len(label) > 48:
        return None
    if re.search(r"https?://|www\.|@|[<>]", label, flags=re.IGNORECASE):
        return None
    return label


def safe_classifier_text_value(value: object, *, max_length: int = 64) -> str | None:
    if not isinstance(value, str):
        return None
    text = compact_spaces(value)
    if not text or len(text) > max_length:
        return None
    if re.search(r"https?://|www\.|@|[<>]", text, flags=re.IGNORECASE):
        return None
    return text


def safe_optional_classifier_bool(value: object) -> tuple[bool | None, bool]:
    if value is None:
        return None, True
    if isinstance(value, bool):
        return value, True
    if isinstance(value, str):
        normalized_value = (normalize_text_value(value) or "").lower()
        if normalized_value in {"true", "yes"}:
            return True, True
        if normalized_value in {"false", "no"}:
            return False, True
        if normalized_value in {"null", "none", "unknown", "unclear", ""}:
            return None, True
    return None, False


def normalize_recruiter_search_brief_field(value: object) -> str | None:
    field_name = normalize_text_value(value)
    if not field_name:
        return None
    field_name = field_name.lower().replace("-", "_").replace(" ", "_")
    if field_name in RECRUITER_SEARCH_BRIEF_FIELDS:
        return field_name
    return None


def deterministic_non_it_role_label(text: str) -> str | None:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return None
    if re.search(r"\bdata engineer\b|\bsoftware engineer\b|\bbackend\b|\bdeveloper\b", normalized_text):
        return None
    if explicit_java_technology_signal(normalized_text) or java_stack_terms_in_text(normalized_text):
        return None

    non_it_patterns = [
        (r"\bplumber\b|сантехник", "plumber"),
        (r"\bdentist\b|стоматолог", "dentist"),
        (r"\belectrician\b|электрик", "electrician"),
        (r"\bmechanical engineer\b", "mechanical engineer"),
        (r"\baccountant\b|бухгалтер", "accountant"),
        (r"\blawyer\b|юрист", "lawyer"),
        (r"\bdoctor\b|врач", "doctor"),
    ]
    for pattern, label in non_it_patterns:
        if re.search(pattern, normalized_text, flags=re.IGNORECASE):
            return label
    return None


def recruiter_intent_default_response(
    *,
    intent: str = RECRUITER_INTENT_UNCLEAR,
    role_domain: str = RECRUITER_ROLE_DOMAIN_UNKNOWN,
    role_support_status: str = RECRUITER_ROLE_SUPPORT_UNKNOWN,
    role_label: str | None = None,
    role_reason_code: str | None = None,
    is_profession_like: bool | None = None,
    java_programmer_role: bool | None = None,
    pending_action_intent: str = RECRUITER_PENDING_INTENT_UNCLEAR,
    pending_action_reason_code: str | None = None,
    pending_hypothesis_intent: str = RECRUITER_HYPOTHESIS_INTENT_UNCLEAR,
    pending_hypothesis_reason_code: str | None = None,
    pending_update_intent: str = RECRUITER_UPDATE_INTENT_UNCLEAR,
    pending_update_reason_code: str | None = None,
    field_intent: str = RECRUITER_FIELD_INTENT_UNCLEAR,
    field: str | None = None,
    answered_field: str | None = None,
    field_value: str | None = None,
    field_reason_code: str | None = None,
    confidence: str = RECRUITER_INTENT_CONFIDENCE_LOW,
    unsupported_role_label: str | None = None,
    response_language: str | None = None,
    source: str = "deterministic_fallback",
    fallback_reason: str | None = None,
) -> dict:
    response = {
        "ok": True,
        "intent": intent,
        "role_domain": role_domain,
        "role_support_status": role_support_status,
        "role_label": role_label,
        "role_reason_code": role_reason_code,
        "is_profession_like": is_profession_like,
        "java_programmer_role": java_programmer_role,
        "pending_action_intent": pending_action_intent,
        "pending_action_reason_code": pending_action_reason_code,
        "pending_hypothesis_intent": pending_hypothesis_intent,
        "pending_hypothesis_reason_code": pending_hypothesis_reason_code,
        "pending_update_intent": pending_update_intent,
        "pending_update_reason_code": pending_update_reason_code,
        "field_intent": field_intent,
        "field": field,
        "answered_field": answered_field,
        "field_value": field_value,
        "field_reason_code": field_reason_code,
        "confidence": confidence,
        "unsupported_role_label": unsupported_role_label,
        "response_language": response_language,
        "source": source,
        "prompt_version": RECRUITER_INTENT_PROMPT_VERSION,
        "validator_version": RECRUITER_INTENT_VALIDATOR_VERSION,
    }
    if fallback_reason:
        response["fallback_reason"] = fallback_reason
    return response


def validate_recruiter_intent_output(
    llm_output: dict | None,
) -> tuple[dict | None, str | None]:
    if not isinstance(llm_output, dict):
        return None, "llm_intent_wrong_shape"

    allowed_intents = {
        RECRUITER_INTENT_CANDIDATE_SEARCH,
        RECRUITER_INTENT_SMALL_TALK,
        RECRUITER_INTENT_OFF_TOPIC,
        RECRUITER_INTENT_UNCLEAR,
        RECRUITER_INTENT_PROHIBITED,
        RECRUITER_INTENT_RESTART,
    }
    allowed_role_domains = {
        RECRUITER_ROLE_DOMAIN_IT_SOFTWARE,
        RECRUITER_ROLE_DOMAIN_NON_IT,
        RECRUITER_ROLE_DOMAIN_AMBIGUOUS,
        RECRUITER_ROLE_DOMAIN_UNKNOWN,
    }
    allowed_role_support_statuses = {
        RECRUITER_ROLE_SUPPORT_SUPPORTED,
        RECRUITER_ROLE_SUPPORT_UNSUPPORTED,
        RECRUITER_ROLE_SUPPORT_AMBIGUOUS,
        RECRUITER_ROLE_SUPPORT_NOISE,
        RECRUITER_ROLE_SUPPORT_UNKNOWN,
    }
    allowed_pending_intents = {
        RECRUITER_PENDING_INTENT_CONFIRM,
        RECRUITER_PENDING_INTENT_REFINE,
        RECRUITER_PENDING_INTENT_REJECT,
        RECRUITER_PENDING_INTENT_UNCLEAR,
    }
    allowed_hypothesis_intents = {
        RECRUITER_HYPOTHESIS_INTENT_CONFIRM,
        RECRUITER_HYPOTHESIS_INTENT_REJECT,
        RECRUITER_HYPOTHESIS_INTENT_REFINE,
        RECRUITER_HYPOTHESIS_INTENT_UNCLEAR,
    }
    allowed_update_intents = {
        RECRUITER_UPDATE_INTENT_SELECT_FIELD,
        RECRUITER_UPDATE_INTENT_PROVIDE_VALUE,
        RECRUITER_UPDATE_INTENT_CANCEL,
        RECRUITER_UPDATE_INTENT_UNCLEAR,
    }
    allowed_field_intents = {
        RECRUITER_FIELD_INTENT_FIELD_EXPLANATION,
        RECRUITER_FIELD_INTENT_NOT_FIELD_EXPLANATION,
        RECRUITER_FIELD_INTENT_ANSWERS_PENDING_FIELD,
        RECRUITER_FIELD_INTENT_ANSWERS_DIFFERENT_FIELD,
        RECRUITER_FIELD_INTENT_REPEATS_EXISTING_VALUE,
        RECRUITER_FIELD_INTENT_UNSUPPORTED_VALUE,
        RECRUITER_FIELD_INTENT_AMBIGUOUS,
        RECRUITER_FIELD_INTENT_NOISE,
        RECRUITER_FIELD_INTENT_UNCLEAR,
    }
    allowed_confidence = {
        RECRUITER_INTENT_CONFIDENCE_HIGH,
        RECRUITER_INTENT_CONFIDENCE_MEDIUM,
        RECRUITER_INTENT_CONFIDENCE_LOW,
    }

    intent = normalize_text_value(llm_output.get("intent")) or RECRUITER_INTENT_UNCLEAR
    role_domain = (
        normalize_text_value(llm_output.get("role_domain"))
        or RECRUITER_ROLE_DOMAIN_UNKNOWN
    )
    role_support_status = (
        normalize_text_value(llm_output.get("role_support_status"))
        or normalize_text_value(llm_output.get("support_status"))
        or RECRUITER_ROLE_SUPPORT_UNKNOWN
    )
    role_label = safe_classifier_text_value(llm_output.get("role_label"), max_length=64)
    role_reason_code = safe_classifier_text_value(
        llm_output.get("role_reason_code") or llm_output.get("reason_code"),
        max_length=64,
    )
    is_profession_like, valid_is_profession_like = safe_optional_classifier_bool(
        llm_output.get("is_profession_like")
    )
    if not valid_is_profession_like:
        return None, "llm_intent_invalid_is_profession_like"
    java_programmer_role, valid_java_programmer_role = safe_optional_classifier_bool(
        llm_output.get("java_programmer_role")
    )
    if not valid_java_programmer_role:
        return None, "llm_intent_invalid_java_programmer_role"
    pending_action_intent = (
        normalize_text_value(llm_output.get("pending_action_intent"))
        or RECRUITER_PENDING_INTENT_UNCLEAR
    )
    pending_action_reason_code = safe_classifier_text_value(
        llm_output.get("pending_action_reason_code"),
        max_length=64,
    )
    pending_hypothesis_intent = (
        normalize_text_value(llm_output.get("pending_hypothesis_intent"))
        or RECRUITER_HYPOTHESIS_INTENT_UNCLEAR
    )
    pending_hypothesis_reason_code = safe_classifier_text_value(
        llm_output.get("pending_hypothesis_reason_code")
        or llm_output.get("hypothesis_reason_code"),
        max_length=64,
    )
    pending_update_intent = (
        normalize_text_value(llm_output.get("pending_update_intent"))
        or RECRUITER_UPDATE_INTENT_UNCLEAR
    )
    pending_update_reason_code = safe_classifier_text_value(
        llm_output.get("pending_update_reason_code")
        or llm_output.get("update_reason_code"),
        max_length=64,
    )
    field_intent = (
        normalize_text_value(llm_output.get("field_intent"))
        or normalize_text_value(llm_output.get("field_explanation_intent"))
        or RECRUITER_FIELD_INTENT_UNCLEAR
    )
    field = normalize_recruiter_search_brief_field(llm_output.get("field"))
    answered_field = normalize_recruiter_search_brief_field(
        llm_output.get("answered_field")
    )
    field_value = safe_classifier_text_value(llm_output.get("field_value"), max_length=64)
    field_reason_code = safe_classifier_text_value(
        llm_output.get("field_reason_code"),
        max_length=64,
    )
    response_language = normalize_text_value(llm_output.get("response_language"))
    if response_language not in {None, "en", "ru"}:
        response_language = None
    confidence = (
        normalize_text_value(llm_output.get("confidence"))
        or RECRUITER_INTENT_CONFIDENCE_LOW
    )
    unsupported_role_label = safe_unsupported_role_label(
        llm_output.get("unsupported_role_label")
    )

    if intent not in allowed_intents:
        return None, "llm_intent_unknown_intent"
    if role_domain not in allowed_role_domains:
        return None, "llm_intent_unknown_role_domain"
    if role_support_status not in allowed_role_support_statuses:
        return None, "llm_intent_unknown_role_support_status"
    if pending_action_intent not in allowed_pending_intents:
        return None, "llm_intent_unknown_pending_action_intent"
    if pending_hypothesis_intent not in allowed_hypothesis_intents:
        return None, "llm_intent_unknown_pending_hypothesis_intent"
    if pending_update_intent not in allowed_update_intents:
        return None, "llm_intent_unknown_pending_update_intent"
    if field_intent not in allowed_field_intents:
        return None, "llm_intent_unknown_field_intent"
    if confidence not in allowed_confidence:
        return None, "llm_intent_unknown_confidence"
    if not unsupported_role_label and role_label:
        unsupported_role_label = role_label
    if role_domain == RECRUITER_ROLE_DOMAIN_NON_IT and not unsupported_role_label:
        return None, "llm_intent_missing_safe_role_label"
    if role_support_status in {
        RECRUITER_ROLE_SUPPORT_UNSUPPORTED,
        RECRUITER_ROLE_SUPPORT_AMBIGUOUS,
    } and role_domain != RECRUITER_ROLE_DOMAIN_UNKNOWN and not role_label:
        return None, "llm_intent_missing_role_label"
    if field_intent == RECRUITER_FIELD_INTENT_FIELD_EXPLANATION and not field:
        return None, "llm_intent_missing_field_explanation_field"
    if pending_update_intent == RECRUITER_UPDATE_INTENT_SELECT_FIELD and not field:
        return None, "llm_intent_missing_pending_update_field"
    if field_intent in {
        RECRUITER_FIELD_INTENT_ANSWERS_PENDING_FIELD,
        RECRUITER_FIELD_INTENT_ANSWERS_DIFFERENT_FIELD,
        RECRUITER_FIELD_INTENT_REPEATS_EXISTING_VALUE,
    } and not (field or answered_field):
        return None, "llm_intent_missing_answer_field"

    return recruiter_intent_default_response(
        intent=intent,
        role_domain=role_domain,
        role_support_status=role_support_status,
        role_label=role_label,
        role_reason_code=role_reason_code,
        is_profession_like=is_profession_like,
        java_programmer_role=java_programmer_role,
        pending_action_intent=pending_action_intent,
        pending_action_reason_code=pending_action_reason_code,
        pending_hypothesis_intent=pending_hypothesis_intent,
        pending_hypothesis_reason_code=pending_hypothesis_reason_code,
        pending_update_intent=pending_update_intent,
        pending_update_reason_code=pending_update_reason_code,
        field_intent=field_intent,
        field=field,
        answered_field=answered_field,
        field_value=field_value,
        field_reason_code=field_reason_code,
        confidence=confidence,
        unsupported_role_label=unsupported_role_label,
        response_language=response_language,
        source="llm_assisted",
    ), None


def recruiter_chat_intent_system_prompt() -> str:
    return (
        "You classify a recruiter's latest message for a human-approved IT sourcing "
        "assistant. Return one JSON object only. You may classify intent, role meaning, "
        "Search Brief field questions, pending-field answers, and pending-action reply "
        "intent, pending-hypothesis replies, and pending-update replies. You must not build search briefs, create "
        "queries, browse, search, access LinkedIn, message candidates, execute tools, "
        "or act on accounts."
    )


def recruiter_chat_intent_user_prompt(request: RecruiterChatIntentRequest) -> str:
    return json.dumps(
        {
            "task": "Classify only the latest recruiter message.",
            "required_output": {
                "intent": "candidate_search | small_talk | off_topic | unclear | prohibited | restart",
                "role_domain": "it_software | non_it | ambiguous | unknown",
                "role_support_status": "supported | unsupported | ambiguous | noise | unknown",
                "role_label": "short safe role/profession label or null",
                "role_reason_code": "bounded short reason code or null",
                "is_profession_like": "true | false | null",
                "java_programmer_role": "true | false | null",
                "pending_action_intent": "confirm | refine | reject | unclear",
                "pending_action_reason_code": "bounded short reason code or null",
                "pending_hypothesis_intent": "confirm | reject | refine | unclear",
                "pending_hypothesis_reason_code": "bounded short reason code or null",
                "pending_update_intent": "select_field | provide_value | cancel | unclear",
                "pending_update_reason_code": "bounded short reason code or null",
                "field_intent": (
                    "field_explanation | not_field_explanation | answers_pending_field | "
                    "answers_different_field | repeats_existing_value | unsupported_value | "
                    "ambiguous | noise | unclear"
                ),
                "field": "role_family | technology | stack | location | seniority | search_depth | profile_sources | null",
                "answered_field": "role_family | technology | stack | location | seniority | search_depth | profile_sources | null",
                "field_value": "short safe field value or null",
                "field_reason_code": "bounded short reason code or null",
                "unsupported_role_label": "short safe role label or null",
                "confidence": "high | medium | low",
                "response_language": "en | ru | null",
            },
            "latest_message": request.latest_message,
            "language_hint": request.language,
            "context": {
                "context_type": request.context_type,
                "pending_action_type": request.pending_action_type,
                "pending_field": request.pending_field,
                "pending_update_field": request.pending_update_field,
                "pending_hypothesis": request.pending_hypothesis,
                "current_brief_status": request.current_brief_status,
                "current_brief": clean_search_brief_dict(request.current_brief),
                "supported_scope": (
                    "English IT/software sourcing. The final POC supports any "
                    "IT/software role when role, main technology, location, and "
                    "1-3 stack signals are provided."
                ),
            },
            "rules": [
                "Classify clear non-IT professions such as plumber or dentist as candidate_search plus non_it.",
                "Do not classify IT/software roles such as Data Engineer, QA Automation, DevOps, Frontend Developer, Product Manager, Analyst, Software Engineer, Backend Developer, or Java Developer as non_it.",
                "Supported role means an English IT/software role, not only Java programmer roles.",
                "If a word is not a profession or role-like search target, classify it as noise or unclear.",
                "Noise or random text should use support_status noise and intent unclear.",
                "If the user asks what a Search Brief field means, set field_intent field_explanation and select the field.",
                "If context has a pending_field, classify whether the latest message answers that field, answers a different field, repeats an existing value, asks for a field explanation, or is unclear/noise.",
                "For pending action start_search, classify confirmations such as Confirm, yes, or Russian equivalents as confirm.",
                "For pending action start_search, classify change/refinement requests as refine and no/not now as reject.",
                "For pending action start_search, classify general update/edit/change intent such as 'I want to update' as refine, even without a concrete field value.",
                "Do not classify vague positive acknowledgements such as 'great' as confirm unless the message clearly asks to run or start the search.",
                "For context pending_hypothesis, classify yes/correct/right as pending_hypothesis_intent confirm only when pending_hypothesis is present.",
                "For context pending_hypothesis, classify no/not that/different as reject or refine. Do not invent field values.",
                "For context pending_update, classify allowed Search Brief field names as pending_update_intent select_field and set field.",
                "For context pending_update_value, classify replacement values only as provide_value; backend validation will apply or reject them.",
                "For context pending_update or pending_update_value, classify cancel/stop/never mind as pending_update_intent cancel.",
                "Do not use pending_update_intent or pending_hypothesis_intent outside their matching context.",
                "Classify clear start-over, restart, reset, clear current search, or begin-again requests as intent restart. This is state-management only and must not execute search.",
                "Use unclear when confidence is low.",
                "Use English response_language for this final POC.",
                "Return JSON only.",
            ],
            "hard_boundaries": [
                "No autonomous execution.",
                "No direct web-search bypass.",
                "No LinkedIn login, scraping, or restriction bypass.",
                "No candidate messaging.",
                "No account actions.",
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


async def run_openai_json_recruiter_intent(
    request: RecruiterChatIntentRequest,
) -> tuple[dict | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return None, AGENT_WORDING_FALLBACK_NOT_CONFIGURED

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": recruiter_chat_intent_system_prompt()},
            {"role": "user", "content": recruiter_chat_intent_user_prompt(request)},
        ],
        "temperature": 0,
        "max_completion_tokens": OPENAI_RECRUITER_INTENT_MAX_COMPLETION_TOKENS,
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
                json=payload,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        return None, "openai_intent_timeout"
    except httpx.HTTPStatusError as exc:
        return None, f"openai_intent_http_{exc.response.status_code}"
    except httpx.HTTPError:
        return None, "openai_intent_request_failed"

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        return None, "openai_intent_empty_content"

    try:
        parsed_content = json.loads(content)
    except json.JSONDecodeError:
        return None, "openai_intent_invalid_json"
    if not isinstance(parsed_content, dict):
        return None, "openai_intent_wrong_shape"

    return parsed_content, None


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


def explicit_backend_role_signal(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    return bool(
        re.search(
            r"\bbackend\b|\bdeveloper\b|\bengineer\b|бекенд|бэкенд|бэкэнд|разработчик|программист",
            normalized_text,
            flags=re.IGNORECASE,
        )
    )


def explicit_it_role_signal(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    return bool(
        re.search(
            r"\b(dev|developer|engineer|programmer|architect|devops|sre|qa|tester|automation|analyst|data|scientist|product manager|project manager|designer|ux|ui|security|cloud|platform|database|dba|sysadmin|administrator|software|frontend|front end|backend|back end|fullstack|full stack|mobile|ios|android|embedded|firmware|blockchain|sap|salesforce)\b",
            normalized_text,
            flags=re.IGNORECASE,
        )
    )


def explicit_java_technology_signal(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    return bool(
        (
            re.search(r"(?<![a-z0-9])java(?![a-z0-9])", normalized_text)
            or re.search(r"джава|джав[аы]", normalized_text, flags=re.IGNORECASE)
        )
        and not re.search(r"(?<![a-z0-9])javascript(?![a-z0-9])", normalized_text)
    )


def explicit_technology_signal(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    if explicit_java_technology_signal(normalized_text):
        return True
    known_terms = sorted(KNOWN_BACKEND_TECHNOLOGIES, key=len, reverse=True)
    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", normalized_text)
        for term in known_terms
    )


def explicit_ukraine_location_signal(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    return bool(
        re.search(
            r"\bukraine\b|украин|україн|київ|киев|\bkyiv\b|\bkiev\b|ukrane|ukraien|ukrain\b",
            normalized_text,
            flags=re.IGNORECASE,
        )
    )


def detect_recruiter_chat_reset_intent(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    if normalized_text in {
        "start over",
        "reset",
        "clear",
        "clear brief",
        "new search",
        "start new search",
        "restart",
        "начать заново",
        "сброс",
        "новый поиск",
    }:
        return True
    return bool(
        re.search(
            r"\b(start|begin|try|do)\s+(again|over|from scratch)\b|\bclear\s+(this|current)\s+(search|brief|summary)\b",
            normalized_text,
            flags=re.IGNORECASE,
        )
    )


def detect_recruiter_chat_explanation_intent(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    return bool(
        re.search(r"\b(explain|why|what does|what do you mean)\b", normalized_text)
        and re.search(r"\b(stack|planning|build plan|search brief)\b", normalized_text)
    )


def detect_recruiter_chat_off_topic_intent(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return False
    if has_sourcing_or_recruiter_context_signal_for_off_topic(normalized_text):
        return False

    off_topic_patterns = [
        r"\bweather\b",
        r"\bhow are you\b",
        r"\bwrite.{0,20}poem\b",
        r"\bpoem\b",
        r"\bjoke\b|\btell me.{0,20}joke\b",
        r"\border.{0,20}lunch\b|\blunch\b",
        r"\bcurrency\b|\bexchange rate\b|\bdollar rate\b",
        r"\brecommend.{0,30}restaurant\b",
        r"\brestaurant\b",
        r"\bwho is.{0,30}(president|prime minister)\b",
        r"\bus president\b",
        r"\bcurrent affairs\b",
        r"погод",
        r"курс.{0,20}(доллар|долар|usd)|доллар.{0,20}курс|долар.{0,20}курс",
        r"закаж|заказ.{0,20}обед|обед",
        r"новост|ресторан|стих|анекдот",
    ]
    return text_matches_any_pattern(normalized_text, off_topic_patterns)


def detect_recruiter_chat_small_talk_intent(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return False
    if is_greeting_only_chat_message(normalized_text) or is_near_empty_chat_message(
        normalized_text
    ):
        return False
    if has_sourcing_or_recruiter_context_signal(normalized_text):
        return False
    if is_refinement_like_chat_message(normalized_text):
        return False

    small_talk_phrases = {
        "how are you",
        "what s up",
        "whats up",
        "what is up",
        "sup",
        "how s it going",
        "are you there",
        "you there",
        "thanks",
        "thank you",
        "thanks a lot",
        "thank you very much",
        "thank you so much",
        "thanks for help",
        "thanks for your help",
        "как дела",
        "ты тут",
        "спасибо",
        "спасибо большое",
        "спс",
        "благодарю",
        "благодарю за помощь",
    }
    if normalized_text in small_talk_phrases:
        return True

    gratitude_patterns = [
        r"^(thanks|thank you) (a lot|very much|so much|for help|for your help)$",
        r"^(спасибо|спс|благодарю) (большое|за помощь)$",
    ]
    return text_matches_any_pattern(normalized_text, gratitude_patterns)


def deterministic_pending_action_intent(text: str, pending_action_type: str | None) -> str:
    if pending_action_type != "start_search":
        return RECRUITER_PENDING_INTENT_UNCLEAR

    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return RECRUITER_PENDING_INTENT_UNCLEAR

    confirmation_phrases = {
        "confirm",
        "confirmed",
        "i confirm",
        "yes confirm",
        "yes confirmed",
        "yes",
        "y",
        "ok",
        "okay",
        "go ahead",
        "proceed",
        "run it",
        "run search",
        "start",
        "start search",
        "да",
        "ок",
        "окей",
        "подтверждаю",
        "да подтверждаю",
        "подтверждаю запуск",
        "запускай",
        "старт",
    }
    if normalized_text in confirmation_phrases:
        return RECRUITER_PENDING_INTENT_CONFIRM

    if re.search(r"\b(confirm|confirmed)\b", normalized_text):
        return RECRUITER_PENDING_INTENT_CONFIRM
    if re.search(r"подтвержд|запускай|старт", normalized_text, flags=re.IGNORECASE):
        return RECRUITER_PENDING_INTENT_CONFIRM

    rejection_phrases = {
        "no",
        "not now",
        "stop",
        "cancel",
        "нет",
        "не сейчас",
        "отмена",
        "стоп",
    }
    if normalized_text in rejection_phrases:
        return RECRUITER_PENDING_INTENT_REJECT

    if re.search(r"\b(change|refine|edit|adjust|replace|add|remove|without|wait)\b", normalized_text):
        return RECRUITER_PENDING_INTENT_REFINE
    if re.search(r"измени|поменяй|уточни|добавь|убери|без|подожди", normalized_text, flags=re.IGNORECASE):
        return RECRUITER_PENDING_INTENT_REFINE

    return RECRUITER_PENDING_INTENT_UNCLEAR


def deterministic_pending_hypothesis_intent(
    text: str,
    pending_hypothesis: dict | None,
) -> str:
    if not pending_hypothesis:
        return RECRUITER_HYPOTHESIS_INTENT_UNCLEAR

    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return RECRUITER_HYPOTHESIS_INTENT_UNCLEAR

    confirmation_phrases = {
        "yes",
        "y",
        "ok",
        "okay",
        "correct",
        "right",
        "exactly",
        "that is correct",
        "yes correct",
        "yes that is right",
        "да",
        "ок",
        "окей",
        "верно",
        "правильно",
        "да верно",
        "да правильно",
        "подтверждаю",
    }
    if normalized_text in confirmation_phrases:
        return RECRUITER_HYPOTHESIS_INTENT_CONFIRM

    rejection_phrases = {
        "no",
        "nope",
        "not that",
        "wrong",
        "different",
        "нет",
        "не то",
        "неверно",
        "не правильно",
        "другая",
        "другое",
    }
    if normalized_text in rejection_phrases:
        return RECRUITER_HYPOTHESIS_INTENT_REJECT

    if re.search(r"\b(change|update|edit|instead|actually)\b", normalized_text):
        return RECRUITER_HYPOTHESIS_INTENT_REFINE
    if re.search(r"измен|помен|вместо|на самом деле", normalized_text, flags=re.IGNORECASE):
        return RECRUITER_HYPOTHESIS_INTENT_REFINE

    return RECRUITER_HYPOTHESIS_INTENT_UNCLEAR


def deterministic_pending_update_intent(
    text: str,
    context_type: str | None,
    pending_update_field: str | None,
) -> tuple[str, str | None]:
    if context_type not in {"pending_update", "pending_update_value"} and not pending_update_field:
        return RECRUITER_UPDATE_INTENT_UNCLEAR, None

    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return RECRUITER_UPDATE_INTENT_UNCLEAR, None

    cancel_phrases = {
        "cancel",
        "stop",
        "nevermind",
        "never mind",
        "no changes",
        "отмена",
        "стоп",
        "не надо",
        "без изменений",
    }
    if normalized_text in cancel_phrases:
        return RECRUITER_UPDATE_INTENT_CANCEL, None

    if pending_update_field or context_type == "pending_update_value":
        return RECRUITER_UPDATE_INTENT_PROVIDE_VALUE, pending_update_field

    field_patterns = [
        ("role_family", r"\b(role|role family|position|job title)\b|роль|позици"),
        ("technology", r"\b(technology|main technology|language|programming language)\b|технолог"),
        ("stack", r"\b(stack|spring|kafka|aws|hibernate|docker|kubernetes|postgresql|microservices|rest)\b|стек"),
        ("location", r"\b(location|country|city|place)\b|локац|город|страна"),
        ("seniority", r"\b(seniority|level|senior|middle|junior|lead)\b|уров|сеньор|мидл|джун"),
        ("search_depth", r"\b(depth|search depth|deep|standard)\b|глубин"),
        ("profile_sources", r"\b(source|sources|profile source|linkedin)\b|источник"),
    ]
    for field_name, pattern in field_patterns:
        if re.search(pattern, normalized_text, flags=re.IGNORECASE):
            return RECRUITER_UPDATE_INTENT_SELECT_FIELD, field_name

    return RECRUITER_UPDATE_INTENT_UNCLEAR, None


def deterministic_recruiter_intent(
    request: RecruiterChatIntentRequest,
    *,
    fallback_reason: str | None = None,
) -> dict:
    text = request.latest_message
    pending_action_intent = deterministic_pending_action_intent(
        text,
        request.pending_action_type,
    )
    pending_hypothesis_intent = deterministic_pending_hypothesis_intent(
        text,
        request.pending_hypothesis,
    )
    pending_update_intent, pending_update_field = deterministic_pending_update_intent(
        text,
        request.context_type,
        request.pending_update_field,
    )
    unsupported_role_label = deterministic_non_it_role_label(text)

    if detect_recruiter_chat_prohibited_requests(text):
        return recruiter_intent_default_response(
            intent=RECRUITER_INTENT_PROHIBITED,
            role_domain=RECRUITER_ROLE_DOMAIN_UNKNOWN,
            pending_action_intent=pending_action_intent,
            pending_hypothesis_intent=pending_hypothesis_intent,
            pending_update_intent=pending_update_intent,
            field=pending_update_field,
            confidence=RECRUITER_INTENT_CONFIDENCE_HIGH,
            fallback_reason=fallback_reason,
        )

    if detect_recruiter_chat_reset_intent(text):
        return recruiter_intent_default_response(
            intent=RECRUITER_INTENT_RESTART,
            role_domain=RECRUITER_ROLE_DOMAIN_UNKNOWN,
            pending_action_intent=pending_action_intent,
            pending_hypothesis_intent=pending_hypothesis_intent,
            pending_update_intent=pending_update_intent,
            field=pending_update_field,
            confidence=RECRUITER_INTENT_CONFIDENCE_HIGH,
            fallback_reason=fallback_reason,
        )

    if unsupported_role_label:
        return recruiter_intent_default_response(
            intent=RECRUITER_INTENT_CANDIDATE_SEARCH,
            role_domain=RECRUITER_ROLE_DOMAIN_NON_IT,
            role_support_status=RECRUITER_ROLE_SUPPORT_UNSUPPORTED,
            role_label=unsupported_role_label,
            is_profession_like=True,
            java_programmer_role=False,
            pending_action_intent=pending_action_intent,
            pending_hypothesis_intent=pending_hypothesis_intent,
            pending_update_intent=pending_update_intent,
            field=pending_update_field,
            confidence=RECRUITER_INTENT_CONFIDENCE_HIGH,
            unsupported_role_label=unsupported_role_label,
            fallback_reason=fallback_reason,
        )

    if pending_hypothesis_intent != RECRUITER_HYPOTHESIS_INTENT_UNCLEAR:
        return recruiter_intent_default_response(
            intent=RECRUITER_INTENT_CANDIDATE_SEARCH,
            role_domain=RECRUITER_ROLE_DOMAIN_UNKNOWN,
            pending_action_intent=pending_action_intent,
            pending_hypothesis_intent=pending_hypothesis_intent,
            confidence=RECRUITER_INTENT_CONFIDENCE_HIGH,
            fallback_reason=fallback_reason,
        )

    if pending_update_intent != RECRUITER_UPDATE_INTENT_UNCLEAR:
        return recruiter_intent_default_response(
            intent=RECRUITER_INTENT_CANDIDATE_SEARCH,
            role_domain=RECRUITER_ROLE_DOMAIN_UNKNOWN,
            pending_action_intent=pending_action_intent,
            pending_update_intent=pending_update_intent,
            field=pending_update_field,
            confidence=RECRUITER_INTENT_CONFIDENCE_HIGH,
            fallback_reason=fallback_reason,
        )

    if pending_action_intent != RECRUITER_PENDING_INTENT_UNCLEAR:
        return recruiter_intent_default_response(
            intent=RECRUITER_INTENT_CANDIDATE_SEARCH,
            role_domain=RECRUITER_ROLE_DOMAIN_UNKNOWN,
            pending_action_intent=pending_action_intent,
            pending_hypothesis_intent=pending_hypothesis_intent,
            pending_update_intent=pending_update_intent,
            field=pending_update_field,
            confidence=RECRUITER_INTENT_CONFIDENCE_HIGH,
            fallback_reason=fallback_reason,
        )

    if detect_recruiter_chat_small_talk_intent(text) or is_greeting_only_chat_message(text):
        return recruiter_intent_default_response(
            intent=RECRUITER_INTENT_SMALL_TALK,
            role_domain=RECRUITER_ROLE_DOMAIN_UNKNOWN,
            pending_action_intent=pending_action_intent,
            pending_hypothesis_intent=pending_hypothesis_intent,
            pending_update_intent=pending_update_intent,
            field=pending_update_field,
            confidence=RECRUITER_INTENT_CONFIDENCE_HIGH,
            fallback_reason=fallback_reason,
        )

    if detect_recruiter_chat_off_topic_intent(text):
        return recruiter_intent_default_response(
            intent=RECRUITER_INTENT_OFF_TOPIC,
            role_domain=RECRUITER_ROLE_DOMAIN_UNKNOWN,
            pending_action_intent=pending_action_intent,
            pending_hypothesis_intent=pending_hypothesis_intent,
            pending_update_intent=pending_update_intent,
            field=pending_update_field,
            confidence=RECRUITER_INTENT_CONFIDENCE_HIGH,
            fallback_reason=fallback_reason,
        )

    if detect_recruiter_chat_unclear_request(text):
        return recruiter_intent_default_response(
            intent=RECRUITER_INTENT_UNCLEAR,
            role_domain=RECRUITER_ROLE_DOMAIN_UNKNOWN,
            pending_action_intent=pending_action_intent,
            pending_hypothesis_intent=pending_hypothesis_intent,
            pending_update_intent=pending_update_intent,
            field=pending_update_field,
            confidence=RECRUITER_INTENT_CONFIDENCE_HIGH,
            fallback_reason=fallback_reason,
        )

    role_domain = RECRUITER_ROLE_DOMAIN_UNKNOWN
    role_support_status = RECRUITER_ROLE_SUPPORT_UNKNOWN
    is_profession_like: bool | None = None
    java_programmer_role: bool | None = None
    if has_sourcing_or_recruiter_context_signal(text):
        role_domain = (
            RECRUITER_ROLE_DOMAIN_IT_SOFTWARE
            if (
                explicit_it_role_signal(text)
                or explicit_technology_signal(text)
                or java_stack_terms_in_text(text)
            )
            else RECRUITER_ROLE_DOMAIN_UNKNOWN
        )
        if role_domain == RECRUITER_ROLE_DOMAIN_IT_SOFTWARE:
            role_support_status = (
                RECRUITER_ROLE_SUPPORT_SUPPORTED
                if explicit_technology_signal(text)
                and explicit_it_role_signal(text)
                else RECRUITER_ROLE_SUPPORT_UNKNOWN
            )
            is_profession_like = explicit_it_role_signal(text)
            java_programmer_role = role_support_status == RECRUITER_ROLE_SUPPORT_SUPPORTED

    return recruiter_intent_default_response(
        intent=(
            RECRUITER_INTENT_CANDIDATE_SEARCH
            if has_sourcing_or_recruiter_context_signal(text)
            else RECRUITER_INTENT_UNCLEAR
        ),
        role_domain=role_domain,
        role_support_status=role_support_status,
        is_profession_like=is_profession_like,
        java_programmer_role=java_programmer_role,
        pending_action_intent=pending_action_intent,
        pending_hypothesis_intent=pending_hypothesis_intent,
        pending_update_intent=pending_update_intent,
        field=pending_update_field,
        confidence=RECRUITER_INTENT_CONFIDENCE_MEDIUM,
        fallback_reason=fallback_reason,
    )


def should_use_recruiter_intent_classifier(
    request: RecruiterChatIntentRequest,
) -> bool:
    text = request.latest_message
    if request.context_type == "pending_action" or request.pending_action_type:
        return True
    if request.context_type == "pending_hypothesis" or request.pending_hypothesis:
        return True
    if request.context_type in {"pending_update", "pending_update_value"}:
        return True
    if request.pending_update_field:
        return True
    if request.context_type == "pending_field" or request.pending_field:
        return True
    if detect_recruiter_chat_prohibited_requests(text):
        return False
    if explicit_it_role_signal(text) and explicit_technology_signal(text):
        return False
    if deterministic_non_it_role_label(text):
        return True
    normalized_text = normalized_chat_control_text(text)
    return bool(
        normalized_text
        and (
            detect_recruiter_chat_small_talk_intent(text)
            or detect_recruiter_chat_unclear_request(text)
            or detect_recruiter_chat_off_topic_intent(text)
            or re.search(r"\b(role|told you|i said)\b|роль|говорил|сказал", normalized_text)
            or not has_sourcing_or_recruiter_context_signal(text)
        )
    )


async def classify_recruiter_chat_intent_response(
    request: RecruiterChatIntentRequest,
) -> dict:
    deterministic_fast_path = deterministic_recruiter_intent(request)
    if deterministic_fast_path["confidence"] == RECRUITER_INTENT_CONFIDENCE_HIGH:
        if (
            deterministic_fast_path.get("intent") == RECRUITER_INTENT_UNCLEAR
            and should_use_recruiter_intent_classifier(request)
        ):
            pass
        else:
            return deterministic_fast_path

    if not should_use_recruiter_intent_classifier(request):
        deterministic_fast_path["fallback_reason"] = "classifier_not_needed"
        return deterministic_fast_path

    llm_output, error = await run_openai_json_recruiter_intent(request)
    if error or llm_output is None:
        return deterministic_recruiter_intent(
            request,
            fallback_reason=error or "openai_intent_empty_output",
        )

    validated_output, validation_error = validate_recruiter_intent_output(llm_output)
    if validation_error or validated_output is None:
        return deterministic_recruiter_intent(
            request,
            fallback_reason=validation_error or "llm_intent_invalid",
        )

    if validated_output["confidence"] == RECRUITER_INTENT_CONFIDENCE_LOW:
        return deterministic_recruiter_intent(
            request,
            fallback_reason="llm_intent_low_confidence",
        )

    return validated_output


def detect_recruiter_chat_unclear_request(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return False
    if has_sourcing_or_recruiter_context_signal(normalized_text):
        return False
    if is_greeting_only_chat_message(normalized_text):
        return False
    if detect_recruiter_chat_off_topic_intent(normalized_text):
        return False

    compact_text = re.sub(r"\s+", "", normalized_text)
    if len(compact_text) < 6:
        return False

    if re.search(r"([a-zа-яіїєґ]{1,3})\1{2,}", compact_text, flags=re.IGNORECASE):
        return True
    if re.search(r"([a-zа-яіїєґ])([a-zа-яіїєґ])\1\2\1\2", compact_text, flags=re.IGNORECASE):
        return True

    tokens = re.findall(r"[a-zа-яіїєґ]+", normalized_text, flags=re.IGNORECASE)
    if not tokens:
        return True
    if len(tokens) == 1 and len(tokens[0]) >= 10:
        vowels = re.findall(r"[aeiouyаеёиоуыэюяіїє]", tokens[0], flags=re.IGNORECASE)
        if len(vowels) / max(len(tokens[0]), 1) < 0.25:
            return True

    known_short_words = {
        "what",
        "which",
        "who",
        "how",
        "why",
        "какая",
        "какой",
        "что",
        "кто",
        "как",
        "почему",
    }
    return len(tokens) <= 2 and all(token not in known_short_words for token in tokens)


def detect_recruiter_chat_ambiguity_or_contradiction(
    text: str,
    language: str = "en",
) -> dict | None:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return None

    return None

    stack_terms = java_stack_terms_in_text(normalized_text)
    has_role = explicit_backend_role_signal(normalized_text)
    has_java = explicit_java_technology_signal(normalized_text)
    has_ukraine = explicit_ukraine_location_signal(normalized_text)

    if stack_terms and has_ukraine and not (has_role and has_java):
        if language == "ru":
            return {
                "code": "missing_role_or_technology",
                "message": (
                    "Вижу локацию и Java стек-сигналы, но перед поиском нужна "
                    "целевая роль и основная технология. Ищем Backend Developer с Java?"
                ),
            }
        return {
            "code": "missing_role_or_technology",
            "message": (
                "I see location and Java stack signals, but I still need the target "
                "role and main technology before planning. Are we looking for "
                "Backend Developer with Java?"
            ),
        }

    if len(stack_terms) > 3:
        return {
            "code": "too_many_stack_terms",
            "message": (
                "The current flow supports 1-3 Java stack signals. Which three "
                "should be the priority for this search?"
            ),
        }

    if re.search(r"\b(two roles|multiple roles)\b", normalized_text) or (
        re.search(r"\bjava\b", normalized_text)
        and re.search(r"\bpython\b", normalized_text)
        and re.search(r"\bpoland\b", normalized_text)
    ):
        return {
            "code": "multiple_roles_or_markets",
            "message": (
                "Let's handle one supported search first: Backend Developer with "
                "Java in Ukraine. Should I proceed with that one?"
            ),
        }

    if re.search(r"\bjava\b", normalized_text) and re.search(r"\bpython\b", normalized_text):
        return {
            "code": "conflicting_technology",
            "message": "Please choose one main technology for this search: Java or Python.",
        }

    if re.search(r"\bukraine\b", normalized_text) and re.search(
        r"\b(prague|praha|czechia|czech republic)\b",
        normalized_text,
    ):
        return {
            "code": "conflicting_location",
            "message": (
                "Please clarify the target location. Should candidates be in "
                "Ukraine, or should the current location be Prague/Czechia?"
            ),
        }

    if re.search(r"\bspring\b", normalized_text) and re.search(
        r"\b(no|without|exclude)\b.{0,20}\bspring\b|\bspring\b.{0,20}\b(no|without|exclude)\b",
        normalized_text,
    ):
        return {
            "code": "conflicting_stack",
            "message": "Please clarify whether Spring is required or should be excluded.",
        }

    if re.search(r"\b(deep search|run deep)\b", normalized_text) and re.search(
        r"\b(do not search|don't search|without search|no search)\b",
        normalized_text,
    ):
        return {
            "code": "conflicting_execution_intent",
            "message": (
                "You asked for deep search and also asked not to search. Should I "
                "only prepare the brief and plan, without running search?"
            ),
        }

    return None


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


def stack_signal_candidate_terms_from_text(text: str) -> list[str]:
    normalized_text = normalize_text_value(text)
    if not normalized_text:
        return []

    cleaned_text = re.sub(
        r"^\s*(?:please\s+)?(?:use|set|change|replace|update|make|stack|stack\s+is|stack\s*:|with|preferably)\s+",
        "",
        normalized_text,
        flags=re.IGNORECASE,
    )
    parts = re.split(r"\s*,\s*|\s*&\s*|\s+\band\s+", cleaned_text, flags=re.IGNORECASE)
    terms: list[str] = []
    for part in parts:
        term = compact_spaces(part).strip(" .,:;\"'")
        if not term:
            continue
        if term.lower() in {"stack", "technology", "tech", "signal", "signals"}:
            continue
        if term not in terms:
            terms.append(term)
    return terms


def normalize_stack_signal_candidates(text: str) -> tuple[list[str], str | None]:
    raw_terms = stack_signal_candidate_terms_from_text(text)
    if not raw_terms:
        return [], "stack_signal_missing"
    if len(raw_terms) > 3:
        return [], "stack_signal_too_many_terms"

    normalized_terms: list[str] = []
    for term in raw_terms:
        normalized_term, term_error = normalize_stack_item_value(term)
        if term_error or not normalized_term:
            return [], term_error or "stack_signal_invalid"
        if agent_wording_has_prohibited_content(normalized_term):
            return [], "stack_signal_prohibited_content"
        if normalized_term not in normalized_terms:
            normalized_terms.append(normalized_term)

    if len(normalized_terms) > 3:
        return [], "stack_signal_too_many_terms"
    return normalized_terms, None


def deterministic_known_stack_signal_terms(terms: list[str]) -> list[str] | None:
    if not terms:
        return None

    known_values = {
        **JAVA_STACK_VALUES,
        **KNOWN_BACKEND_TECHNOLOGIES,
        **{value.lower(): value for value in JAVA_STACK_TERMS},
        **{value.lower(): value for value in KNOWN_BACKEND_TECHNOLOGIES.values()},
    }
    normalized_terms: list[str] = []
    for term in terms:
        canonical_term = canonical_value(term, known_values)
        if not canonical_term:
            return None
        normalized_term, term_error = normalize_stack_item_value(canonical_term)
        if term_error or not normalized_term:
            return None
        if normalized_term not in normalized_terms:
            normalized_terms.append(normalized_term)
    return normalized_terms


def stack_signal_context_value(current_brief: SearchBrief | dict | None, field: str) -> str | None:
    if current_brief is None:
        return None
    if isinstance(current_brief, dict):
        return normalize_text_value(current_brief.get(field))
    return normalize_text_value(getattr(current_brief, field, None))


def stack_signal_classifier_system_prompt() -> str:
    return (
        "You classify bounded recruiter-provided stack signals for an IT/software "
        "candidate search assistant. Return JSON only. You may only classify and "
        "normalize the supplied stack terms. Do not create search queries, browse, "
        "search, access LinkedIn, execute tools, approve searches, mutate role or "
        "location, message candidates, or act on accounts."
    )


def stack_signal_classifier_user_prompt(
    terms: list[str],
    current_brief: SearchBrief | dict | None,
) -> str:
    return json.dumps(
        {
            "task": "Classify whether each supplied term is an English IT/software stack signal.",
            "required_output": {
                "accepted_terms": [
                    {
                        "input": "exact supplied term",
                        "normalized": "safe normalized display label",
                        "reason_code": "programming_language | framework | tool | platform | database | cloud | qa_tool | methodology | other_it",
                    }
                ],
                "rejected_terms": [
                    {
                        "input": "exact supplied term",
                        "reason_code": "non_it | noise | unsafe | not_english | too_broad | unclear",
                    }
                ],
                "confidence": "high | medium | low",
            },
            "terms": terms,
            "context": {
                "role_family": stack_signal_context_value(current_brief, "role_family"),
                "technology": stack_signal_context_value(current_brief, "technology"),
                "location": stack_signal_context_value(current_brief, "location"),
            },
            "rules": [
                "Accept English IT/software stack signals, including programming languages, frameworks, libraries, tools, platforms, cloud services, QA tools, databases, methodologies, and related technologies.",
                "Reject non-IT terms, random text, URLs, instructions, account actions, outreach requests, and non-English terms.",
                "Normalize labels conservatively without inventing new terms.",
                "Every supplied term must appear exactly once across accepted_terms or rejected_terms.",
                "Do not add terms that were not supplied.",
                "Use confidence low if unsure.",
                "Return JSON only.",
            ],
            "hard_boundaries": [
                "No autonomous execution.",
                "No query generation.",
                "No direct web-search bypass.",
                "No LinkedIn login, scraping, or restriction bypass.",
                "No candidate messaging.",
                "No account actions.",
            ],
            "prompt_version": STACK_SIGNAL_CLASSIFIER_PROMPT_VERSION,
        },
        ensure_ascii=False,
        indent=2,
    )


async def run_openai_json_stack_signal_classifier(
    terms: list[str],
    current_brief: SearchBrief | dict | None = None,
) -> tuple[dict | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return None, AGENT_WORDING_FALLBACK_NOT_CONFIGURED

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": stack_signal_classifier_system_prompt()},
            {"role": "user", "content": stack_signal_classifier_user_prompt(terms, current_brief)},
        ],
        "temperature": 0,
        "max_completion_tokens": OPENAI_STACK_SIGNAL_CLASSIFIER_MAX_COMPLETION_TOKENS,
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
                json=payload,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        return None, "openai_stack_signal_timeout"
    except httpx.HTTPStatusError as exc:
        return None, f"openai_stack_signal_http_{exc.response.status_code}"
    except httpx.HTTPError:
        return None, "openai_stack_signal_request_failed"

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        return None, "openai_stack_signal_empty_content"

    try:
        parsed_content = json.loads(content)
    except json.JSONDecodeError:
        return None, "openai_stack_signal_invalid_json"
    if not isinstance(parsed_content, dict):
        return None, "openai_stack_signal_wrong_shape"

    return parsed_content, None


def normalize_stack_signal_output_entry(entry: object) -> tuple[str | None, str | None, str | None]:
    if isinstance(entry, str):
        raw_input = normalize_text_value(entry)
        normalized_value = raw_input
        reason_code = None
    elif isinstance(entry, dict):
        raw_input = normalize_text_value(
            entry.get("input") or entry.get("term") or entry.get("raw")
        )
        normalized_value = normalize_text_value(
            entry.get("normalized") or entry.get("value") or raw_input
        )
        reason_code = safe_classifier_text_value(
            entry.get("reason_code") or entry.get("reason"),
            max_length=64,
        )
    else:
        return None, None, None
    return raw_input, normalized_value, reason_code


def validate_stack_signal_classifier_output(
    llm_output: dict | None,
    terms: list[str],
) -> tuple[dict | None, str | None]:
    if not isinstance(llm_output, dict):
        return None, "llm_stack_signal_wrong_shape"

    allowed_keys = {"accepted_terms", "rejected_terms", "confidence"}
    if any(key not in allowed_keys for key in llm_output):
        return None, "llm_stack_signal_unknown_fields"

    confidence = normalize_text_value(llm_output.get("confidence")) or RECRUITER_INTENT_CONFIDENCE_LOW
    if confidence not in {
        RECRUITER_INTENT_CONFIDENCE_HIGH,
        RECRUITER_INTENT_CONFIDENCE_MEDIUM,
        RECRUITER_INTENT_CONFIDENCE_LOW,
    }:
        return None, "llm_stack_signal_unknown_confidence"
    if confidence == RECRUITER_INTENT_CONFIDENCE_LOW:
        return None, "llm_stack_signal_low_confidence"

    accepted_source = llm_output.get("accepted_terms")
    rejected_source = llm_output.get("rejected_terms")
    if not isinstance(accepted_source, list) or not isinstance(rejected_source, list):
        return None, "llm_stack_signal_terms_not_lists"

    candidate_keys = {
        (normalize_text_value(term) or "").lower(): term
        for term in terms
        if normalize_text_value(term)
    }
    seen_keys: set[str] = set()
    accepted_terms: list[str] = []
    rejected_terms: list[dict[str, str]] = []

    for entry in accepted_source:
        raw_input, normalized_value, reason_code = normalize_stack_signal_output_entry(entry)
        input_key = (raw_input or normalized_value or "").lower()
        if input_key not in candidate_keys or input_key in seen_keys:
            return None, "llm_stack_signal_accepted_term_mismatch"
        normalized_term, term_error = normalize_stack_item_value(normalized_value)
        if term_error or not normalized_term:
            return None, "llm_stack_signal_invalid_accepted_term"
        if agent_wording_has_prohibited_content(normalized_term):
            return None, "llm_stack_signal_unsafe_accepted_term"
        seen_keys.add(input_key)
        if normalized_term not in accepted_terms:
            accepted_terms.append(normalized_term)

    for entry in rejected_source:
        raw_input, normalized_value, reason_code = normalize_stack_signal_output_entry(entry)
        input_key = (raw_input or normalized_value or "").lower()
        if input_key not in candidate_keys or input_key in seen_keys:
            return None, "llm_stack_signal_rejected_term_mismatch"
        seen_keys.add(input_key)
        rejected_terms.append(
            {
                "input": candidate_keys[input_key],
                "reason_code": reason_code or "rejected",
            }
        )

    if seen_keys != set(candidate_keys):
        return None, "llm_stack_signal_missing_terms"
    if len(accepted_terms) > 3:
        return None, "llm_stack_signal_too_many_accepted_terms"

    return {
        "accepted_terms": accepted_terms,
        "rejected_terms": rejected_terms,
        "confidence": confidence,
        "prompt_version": STACK_SIGNAL_CLASSIFIER_PROMPT_VERSION,
        "validator_version": STACK_SIGNAL_CLASSIFIER_VALIDATOR_VERSION,
    }, None


async def classify_stack_signal_terms_from_message(
    text: str,
    current_brief: SearchBrief | dict | None = None,
) -> tuple[list[str], str | None]:
    candidate_terms, candidate_error = normalize_stack_signal_candidates(text)
    if candidate_error:
        return [], candidate_error

    deterministic_terms = deterministic_known_stack_signal_terms(candidate_terms)
    if deterministic_terms:
        return deterministic_terms, None

    llm_output, llm_error = await run_openai_json_stack_signal_classifier(
        candidate_terms,
        current_brief,
    )
    if llm_error or llm_output is None:
        return [], llm_error or "llm_stack_signal_unavailable"

    validated_output, validation_error = validate_stack_signal_classifier_output(
        llm_output,
        candidate_terms,
    )
    if validation_error or validated_output is None:
        return [], validation_error or "llm_stack_signal_invalid"
    if validated_output["rejected_terms"]:
        return [], "llm_stack_signal_rejected_terms"
    if not validated_output["accepted_terms"]:
        return [], "llm_stack_signal_no_accepted_terms"

    return validated_output["accepted_terms"], None


def clean_pending_answer_brief_context(
    current_brief: SearchBrief | dict | None,
) -> dict:
    if isinstance(current_brief, SearchBrief):
        return clean_search_brief_dict(current_brief)
    if isinstance(current_brief, dict):
        return {
            key: value
            for key, value in current_brief.items()
            if value is not None and value != []
        }
    return {}


async def run_openai_json_pending_answer_interpreter(
    *,
    latest_message: str,
    language: str,
    expected_field: str | None = None,
    pending_update_field: str | None = None,
    current_brief: SearchBrief | dict | None = None,
) -> tuple[dict | None, str | None]:
    return await _run_openai_json_pending_answer_interpreter(
        latest_message=latest_message,
        language=language,
        expected_field=expected_field,
        pending_update_field=pending_update_field,
        current_brief=clean_pending_answer_brief_context(current_brief),
        chat_completions_url=OPENAI_CHAT_COMPLETIONS_URL,
    )


async def run_openai_json_search_brief_extractor(
    *,
    latest_message: str,
    language: str,
    previous_brief: dict | None = None,
) -> tuple[dict | None, str | None]:
    return await _run_openai_json_search_brief_extractor(
        latest_message=latest_message,
        language=language,
        previous_brief=previous_brief,
        chat_completions_url=OPENAI_CHAT_COMPLETIONS_URL,
    )


async def run_openai_json_search_brief_refinement_interpreter(
    *,
    latest_message: str,
    language: str,
    current_brief: SearchBrief | dict | None = None,
) -> tuple[dict | None, str | None]:
    return await _run_openai_json_search_brief_refinement_interpreter(
        latest_message=latest_message,
        language=language,
        current_brief=clean_pending_answer_brief_context(current_brief),
        chat_completions_url=OPENAI_CHAT_COMPLETIONS_URL,
    )


async def classify_pending_answer_interpreter_from_message(
    *,
    text: str,
    language: str,
    expected_field: str | None = None,
    pending_update_field: str | None = None,
    current_brief: SearchBrief | dict | None = None,
) -> tuple[dict | None, str | None]:
    llm_output, llm_error = await run_openai_json_pending_answer_interpreter(
        latest_message=text,
        language=language,
        expected_field=expected_field,
        pending_update_field=pending_update_field,
        current_brief=current_brief,
    )
    if llm_error or llm_output is None:
        return None, llm_error or "pending_answer_interpreter_unavailable"

    return validate_pending_answer_interpreter_output(
        llm_output,
        expected_field=expected_field,
        pending_update_field=pending_update_field,
    )


async def stack_terms_from_pending_answer_interpreter(
    interpreter_result: dict | None,
    current_brief: SearchBrief | dict | None,
) -> list[str]:
    if not interpreter_result:
        return []
    if interpreter_result.get("field") != "stack":
        return []
    if interpreter_result.get("intent") not in {
        PENDING_ANSWER_INTENT_ANSWER_PENDING_FIELD,
        PENDING_ANSWER_INTENT_PROVIDE_UPDATE_VALUE,
    }:
        return []
    raw_terms = interpreter_result.get("values") or []
    if not raw_terms:
        return []
    stack_terms, _ = await classify_stack_signal_terms_from_message(
        ", ".join(raw_terms),
        current_brief,
    )
    return stack_terms[:3]


UNSUPPORTED_REFINEMENT_PATTERNS = [
]

LEGACY_UNSUPPORTED_REFINEMENT_PATTERNS = [
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
        r"\bchange\b",
        r"\bupdate\b",
        r"\bset\b",
        r"\bmake\b",
        r"\bi meant\b",
        r"\binstead\b",
        r"\blocation\b",
        r"\bcountry\b",
        r"\bcity\b",
        r"\bregion\b",
        r"\bremote\b",
        r"\brole\b",
        r"\btechnology\b",
        r"\bmust[- ]?have\b",
        r"\bdomain\b",
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
            "Уточни, что именно изменить в текущей search summary."
            if language == "ru"
            else "Please clarify what to change in the current search summary."
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
    return recruiter_chat_refusal_source_message(language)


def localized_clarifying_question_for_missing_field(field: str, language: str) -> str:
    return localized_clarifying_question_source_message(field, language)


def one_clarifying_question(normalized_brief: dict, language: str) -> str | None:
    missing_fields = normalized_brief.get("missing_fields") or []
    questions = normalized_brief.get("clarifying_questions") or []
    if missing_fields:
        generic_questions = {
            canonical_clarifying_question_for_missing_field(field)
            for field in missing_fields
        }
        for question in questions:
            if question and question not in generic_questions:
                return question
        return localized_clarifying_question_for_missing_field(missing_fields[0], language)

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
    return ready_for_planning_source_message(language)


def validation_error_message(errors: list[dict[str, str]], language: str) -> str:
    return validation_error_source_message(errors, language)


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

    if re.search(r"\bbackend\b|бекенд|бэкенд|бэкэнд|разработчик|программист", lowered_text):
        hints["role_family"] = "Backend Developer"

    if (
        re.search(r"\bjava\b|джава|джав[аы]", lowered_text)
        and not re.search(r"\bjavascript\b", lowered_text)
    ):
        hints["technology"] = "Java"
        hints["must_have"] = ["Java"]

    stack = java_stack_terms_in_text(lowered_text)
    typo_stack_aliases = {
        "sping": "Spring",
        "sprng": "Spring",
        "kafak": "Kafka",
        "kafkaa": "Kafka",
    }
    for alias, canonical_stack_item in typo_stack_aliases.items():
        if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", lowered_text):
            if canonical_stack_item not in stack:
                stack.append(canonical_stack_item)

    if stack:
        hints["stack"] = stack[:3]
        hints["nice_to_have"] = stack[:3]

    if re.search(r"\bukraine\b|украин|україн|київ|киев|\bkyiv\b|\bkiev\b", lowered_text):
        hints["location"] = "Ukraine"

    if re.search(r"ukrane|ukraien|ukrain\b", lowered_text):
        hints["location"] = "Ukraine"

    if re.search(r"\bdeep\b|глубок", lowered_text):
        hints["search_depth"] = SEARCH_DEPTH_DEEP

    return hints


SEARCH_BRIEF_STRING_FIELDS = {
    "source_text",
    "brief_status",
    "role_family",
    "technology",
    "location",
    "seniority",
    "search_depth",
    "notes",
}
SEARCH_BRIEF_LIST_FIELDS = {
    "stack",
    "must_have",
    "nice_to_have",
    "exclusions",
    "profile_sources",
    "missing_fields",
    "clarifying_questions",
    "assumptions",
}


def sanitize_chat_draft_field(field_name: str, value: object) -> object | None:
    if value is None:
        return None

    if field_name in SEARCH_BRIEF_STRING_FIELDS:
        if isinstance(value, str):
            return normalize_text_value(value)
        return None

    if field_name in SEARCH_BRIEF_LIST_FIELDS:
        if not isinstance(value, list):
            return None
        return [
            normalize_text_value(item)
            for item in value
            if isinstance(item, str) and normalize_text_value(item)
        ]

    return value


def should_merge_chat_brief_field(
    field_name: str,
    value: object,
    current_value: object,
) -> bool:
    if not current_value:
        return True

    if field_name == "role_family" and isinstance(value, str):
        _, errors = normalize_role_family_value(value)
        return not errors

    if field_name == "technology" and isinstance(value, str):
        _, errors = normalize_technology_value(value)
        return not errors

    if field_name == "location" and isinstance(value, str):
        return bool(normalize_location_value(value))

    return True


def merge_chat_draft_brief(
    existing_brief: SearchBrief | None,
    llm_draft: dict,
    source_text: str,
    evidence_text: str | None = None,
) -> tuple[SearchBrief | None, list[dict[str, str]]]:
    merged = clean_search_brief_dict(existing_brief)
    deterministic_hints = deterministic_chat_brief_hints(evidence_text or source_text)
    explicit_stack = deterministic_hints.get("stack") or []

    for field_name, value in deterministic_hints.items():
        if value is not None and value != []:
            merged[field_name] = value

    for field_name, value in llm_draft.items():
        value = sanitize_chat_draft_field(field_name, value)
        if value is None:
            continue
        if isinstance(value, str) and not normalize_text_value(value):
            continue
        if isinstance(value, list) and not value:
            continue
        if field_name in {"stack", "nice_to_have"}:
            normalized_stack_value, _ = normalize_brief_stack_items(value)
            value = (
                [
                    stack_item
                    for stack_item in normalized_stack_value
                    if stack_item in explicit_stack
                ]
                if explicit_stack
                else normalized_stack_value
            )
            if not value:
                continue
        if not should_merge_chat_brief_field(field_name, value, merged.get(field_name)):
            continue
        merged[field_name] = value

    if "source_text" not in merged:
        merged["source_text"] = source_text
    elif evidence_text is not None:
        merged["source_text"] = source_text
    if "search_depth" not in merged:
        merged["search_depth"] = SEARCH_DEPTH_STANDARD
    if "profile_sources" not in merged:
        merged["profile_sources"] = [PROFILE_SOURCE_LINKEDIN_PUBLIC]

    merged, _ = apply_requirement_search_signal_resolution_to_draft(merged)

    if merged.get("stack"):
        synced_stack, _ = normalize_brief_stack_items(merged["stack"])
        merged["stack"] = synced_stack
        merged["nice_to_have"] = synced_stack

    try:
        return SearchBrief(**merged), []
    except ValidationError as exc:
        return None, [
            {
                "field": f"draft_brief.{'.'.join(str(part) for part in error.get('loc', [])) or 'value'}",
                "message": "I could not safely normalize that request. Please clarify the role, main technology, location, and 1-3 stack signals.",
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
                    "role_family": "explicit English IT/software role/title/family or null",
                    "technology": "explicit main technology or null",
                    "stack": ["up to 3 explicitly requested stack signals"],
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
                "role_family": "Any English IT/software role.",
                "implemented_technology": "Any English main software technology.",
                "known_backend_technologies": sorted(KNOWN_BACKEND_TECHNOLOGIES.values()),
                "known_java_stack_examples": JAVA_STACK_TERMS,
                "search_depth": sorted(SEARCH_DEPTH_VALUES),
                "profile_sources": [PROFILE_SOURCE_LINKEDIN_PUBLIC],
            },
            "rules": [
                "Return one JSON object only.",
                "Do not invent hard constraints that the recruiter did not provide.",
                "If location, stack, role, or technology is missing, leave it null or empty.",
                "Keep the recruiter's target IT/software role as role_family; do not force it to Backend Developer.",
                "Set search_depth to standard unless the recruiter asks for deep search.",
                "Use profile_sources ['linkedin_public'] unless the user explicitly asks otherwise.",
                "Use English field values only.",
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


def recruiter_chat_greeting_count(messages: list[RecruiterChatMessage]) -> int:
    return sum(
        1
        for message in messages
        if (normalize_text_value(message.role) or "").lower() in {"user", "recruiter"}
        and is_greeting_only_chat_message(message.content)
    )


def has_sourcing_or_recruiter_context_signal(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return False

    if (
        explicit_it_role_signal(normalized_text)
        or explicit_technology_signal(normalized_text)
        or explicit_ukraine_location_signal(normalized_text)
        or bool(java_stack_terms_in_text(normalized_text))
    ):
        return True

    recruiter_context_patterns = [
        r"\b(find|search|source|sourcing|hire|hiring|recruit|recruiter|candidate|candidates|vacancy|job)\b",
        r"найд|ищем|поиск|сорсинг|рекрут|кандидат|ваканси|зарплат|компенсац|релокац|найм",
    ]
    return text_matches_any_pattern(normalized_text, recruiter_context_patterns)


def has_sourcing_or_recruiter_context_signal_for_off_topic(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return False

    if (
        explicit_it_role_signal(normalized_text)
        or explicit_technology_signal(normalized_text)
        or bool(java_stack_terms_in_text(normalized_text))
    ):
        return True

    recruiter_context_patterns = [
        r"\b(find|search|source|sourcing|hire|hiring|recruit|recruiter|candidate|candidates|vacancy|job)\b",
        r"найд|ищем|поиск|сорсинг|рекрут|кандидат|ваканси|зарплат|компенсац|релокац|найм",
    ]
    return text_matches_any_pattern(normalized_text, recruiter_context_patterns)


def recruiter_chat_onboarding_wording_payload(
    request: RecruiterChatTurnRequest,
    language: str,
    deterministic_message: str,
) -> dict:
    context = current_brief_validation_context(request.draft_brief)
    normalized_brief = context.get("normalized_brief") or {}
    has_draft = bool(request.draft_brief)

    return {
        "wording_use_case": AGENT_WORDING_USE_CASE_RECRUITER_CHAT_ONBOARDING,
        "message_type": "onboarding",
        "language": language,
        "deterministic_message": deterministic_message,
        "greeting_count": recruiter_chat_greeting_count(request.messages),
        "has_current_or_draft_search_brief": has_draft,
        "current_brief_status": normalized_brief.get("brief_status") if has_draft else None,
        "required_inputs": [
            "role",
            "main technology",
            "location",
            "1-3 stack signals",
        ],
        "allowed_meaning": (
            "Greet or re-greet the recruiter and ask for role, main technology, "
            "location, and 1-3 stack signals. If a draft brief exists, say it is "
            "preserved without changing its values."
        ),
        "forbidden_claims": [
            "search started",
            "results exist",
            "LinkedIn opened or inspected",
            "candidate messaging",
            "approval bypass",
            "autonomous execution",
        ],
        "allowed_numbers": ["1", "3"],
    }


def onboarding_wording_provenance(
    language: str,
    wording_mode: str,
    fallback_reason: str | None = None,
    no_call_reason: str | None = None,
    model: str | None = None,
) -> dict[str, str]:
    return build_agent_wording_provenance(
        message_type=AGENT_WORDING_USE_CASE_RECRUITER_CHAT_ONBOARDING,
        language=language,
        wording_mode=wording_mode,
        fallback_reason=fallback_reason,
        no_call_reason=no_call_reason,
        model=model,
    )


def validate_onboarding_wording_output(
    llm_output: dict,
    language: str,
) -> tuple[str | None, list[str], str | None]:
    validated_output, error = validate_agent_wording_output(
        llm_output,
        language=language,
        allowed_numbers={"1", "3"},
        wording_use_case=AGENT_WORDING_USE_CASE_RECRUITER_CHAT_ONBOARDING,
        existing_limitation_kinds=set(),
    )
    if error:
        return None, [], error

    message = validated_output["message"]
    if len(message) > 360:
        return None, [], "llm_output_too_long"
    if re.search(r"<[^>]+>", message):
        return None, [], "llm_output_html_not_allowed"

    return message, validated_output.get("warnings") or [], None


async def apply_llm_wording_to_recruiter_chat_onboarding(
    request: RecruiterChatTurnRequest,
    language: str,
    deterministic_message: str,
) -> tuple[str, dict[str, str], list[str]]:
    if not agent_wording_has_openai_config():
        return (
            deterministic_message,
            onboarding_wording_provenance(
                language,
                AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
                fallback_reason=AGENT_WORDING_FALLBACK_NOT_CONFIGURED,
                no_call_reason=AGENT_WORDING_FALLBACK_NOT_CONFIGURED,
            ),
            [],
        )

    payload = recruiter_chat_onboarding_wording_payload(
        request,
        language,
        deterministic_message,
    )
    llm_output, error = await run_openai_json_agent_wording(payload)
    if error or llm_output is None:
        return (
            deterministic_message,
            onboarding_wording_provenance(
                language,
                AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
                fallback_reason=error or "openai_onboarding_wording_failed",
            ),
            [],
        )

    message, warnings, validation_error = validate_onboarding_wording_output(
        llm_output,
        language,
    )
    if validation_error or not message:
        return (
            deterministic_message,
            onboarding_wording_provenance(
                language,
                AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
                fallback_reason=validation_error or "llm_output_invalid",
                model=os.getenv("OPENAI_MODEL"),
            ),
            [],
        )

    return (
        message,
        onboarding_wording_provenance(
            language,
            AGENT_WORDING_MODE_LLM_ASSISTED,
            model=os.getenv("OPENAI_MODEL"),
        ),
        warnings,
    )


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
    clear_brief: bool = False,
    wording_provenance: dict | None = None,
    llm_warnings: list[str] | None = None,
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
            assistant_message = None
        else:
            assistant_message = validation_error_message(validation_errors, language)

    build_plan_action = None
    if can_build_plan:
        build_plan_action = {
            "label": "Prepare search",
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
        "clear_brief": clear_brief,
        "wording_provenance": wording_provenance,
        "llm_warnings": llm_warnings or [],
    }


def recruiter_chat_onboarding_message(language: str) -> str:
    return recruiter_chat_onboarding_source_message(language)


def recruiter_chat_near_empty_message(language: str) -> str:
    return recruiter_chat_near_empty_source_message(language)


def recruiter_chat_draft_preserved_message(
    normalized_brief: dict,
    language: str,
    fallback_message: str,
) -> str:
    next_question = one_clarifying_question(normalized_brief, language)
    return recruiter_chat_draft_preserved_source_message(
        normalized_brief,
        language,
        fallback_message,
        next_question,
    )


def build_recruiter_chat_onboarding_response(
    request: RecruiterChatTurnRequest,
    language: str,
    planner_mode: str,
    assistant_message: str,
    wording_provenance: dict | None = None,
    llm_warnings: list[str] | None = None,
) -> dict:
    if not request.draft_brief:
        return build_recruiter_chat_response(
            ok=True,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            assistant_message=assistant_message,
            planner_mode=planner_mode,
            wording_provenance=wording_provenance,
            llm_warnings=llm_warnings,
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
        wording_provenance=wording_provenance,
        llm_warnings=llm_warnings,
    )


def build_recruiter_chat_preserve_current_brief_response(
    request: RecruiterChatTurnRequest,
    language: str,
    planner_mode: str,
    assistant_message: str,
    wording_provenance: dict | None = None,
    llm_warnings: list[str] | None = None,
) -> dict:
    context = current_brief_context_for_language(request.draft_brief, language)
    return build_recruiter_chat_response(
        ok=context["ok"],
        state=context["state"],
        language=language,
        normalized_brief=context["normalized_brief"],
        validation_errors=context["errors"],
        next_question=context["next_question"],
        planner_mode=planner_mode,
        assistant_message=assistant_message,
        brief_changed=False,
        stale_state_should_clear=False,
        wording_provenance=wording_provenance,
        llm_warnings=llm_warnings,
    )


def recruiter_chat_small_talk_prefix(text: str, language: str) -> str:
    normalized_text = normalized_chat_control_text(text)
    gratitude_phrases = {
        "thanks",
        "thank you",
        "thanks a lot",
        "thank you very much",
        "thank you so much",
        "thanks for help",
        "thanks for your help",
        "спасибо",
        "спасибо большое",
        "спс",
        "благодарю",
        "благодарю за помощь",
    }
    if normalized_text in gratitude_phrases:
        if language == "ru":
            return "Пожалуйста."
        return "You're welcome."

    if language == "ru":
        return "Я на связи и готов помочь."
    return "I'm here and ready to help."


def recruiter_chat_small_talk_message(
    request: RecruiterChatTurnRequest,
    text: str,
    language: str,
) -> str:
    prefix = recruiter_chat_small_talk_prefix(text, language)
    context = current_brief_context_for_language(request.draft_brief, language)
    normalized_brief = context.get("normalized_brief") or {}
    next_question = context.get("next_question")

    if normalized_brief.get("brief_status") == SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        if language == "ru":
            return (
                f"{prefix} Текущая сводка поиска готова. "
                "Можем продолжить или уточнить параметры."
            )
        return (
            f"{prefix} The current search summary is still ready. "
            "We can continue or adjust the details."
        )

    if next_question:
        return f"{prefix} {next_question}"

    if language == "ru":
        return (
            f"{prefix} Расскажи, кого ищем: роль, основная технология, "
            "локация и 1-3 сигнала стека."
        )
    return (
        f"{prefix} Tell me who we should find: role, main technology, "
        "location, and 1-3 stack signals."
    )


def recruiter_chat_off_topic_message(language: str) -> str:
    if language == "ru":
        return (
            "Я не смогу помочь с этой темой здесь, но могу помочь с поиском кандидатов: "
            "напиши, кого ищем, основную технологию, локацию и 1-3 сигнала стека."
        )
    return (
        "I cannot help with that topic here, but I can help with candidate search: "
        "tell me the role, main technology, location, and 1-3 stack signals."
    )


def recruiter_chat_unclear_request_message(language: str) -> str:
    if language == "ru":
        return (
            "Извини, я не понял запрос. Я могу помочь с поиском кандидатов: напиши, "
            "кого ищем, основную технологию, локацию и 1-3 сигнала стека."
        )
    return (
        "Sorry, I did not understand the request. I can help with candidate search: "
        "tell me the role, main technology, location, and 1-3 stack signals."
    )


def recruiter_chat_unsupported_role_message(language: str, role_label: str | None) -> str:
    role_context = f' "{role_label}"' if role_label else ""
    if language == "ru":
        return (
            f"Текущая версия помогает с IT/software candidate search;{role_context} "
            "вне поддерживаемой области. Напиши IT-роль, основную технологию, "
            "локацию и 1-3 сигнала стека."
        )
    return (
        f'This version helps with IT/software candidate search;{role_context} '
        "is outside the supported search scope. Tell me an IT role, main "
        "technology, location, and 1-3 stack signals."
    )


def recruiter_chat_unsupported_it_role_message(language: str, role_label: str | None) -> str:
    role_context = f' "{role_label}"' if role_label else ""
    if language == "ru":
        return (
            f"Понял{role_context} как IT/software роль, но текущий flow поддерживает "
            "только Java programmer / Backend Developer search. Если ищем Java-разработчика, "
            "напиши роль, локацию и 1-3 stack signals."
        )
    return (
        f"I understand{role_context} as an IT/software role. Tell me the main "
        "technology, location, and 1-3 stack signals."
    )


def recruiter_chat_ambiguous_role_message(language: str, role_label: str | None) -> str:
    role_context = f' "{role_label}"' if role_label else " that role"
    if language == "ru":
        return (
            f"Понял{role_context} как role-like запрос, но нужно уточнить: "
            "это Java programmer / Backend Developer search или другая роль?"
        )
    return (
        f"I understand{role_context} as role-like, but it is ambiguous. "
        "Tell me the target IT role, main technology, location, and 1-3 stack signals."
    )


def recruiter_chat_noise_role_message(language: str) -> str:
    if language == "ru":
        return (
            "Это не похоже на роль или поисковый запрос. Напиши, кого ищем: "
            "Java-разработчик, локация и 1-3 stack signals."
        )
    return (
        "That does not look like a candidate-search role request. Tell me the target "
        "IT role, main technology, location, and 1-3 stack signals."
    )


def recruiter_chat_field_explanation_message(field: str, language: str) -> str:
    explanations = {
        "role_family": {
            "en": "Role family means the broad type of role to search for, for example Backend Developer.",
            "ru": "Role family означает общий тип роли для поиска, например Backend Developer.",
        },
        "technology": {
            "en": "Technology means the main programming technology, for example Java.",
            "ru": "Technology означает основную технологию кандидата, например Java.",
        },
        "stack": {
            "en": "Stack means 1-3 supporting technologies to prefer, for example Spring, Kafka, or AWS.",
            "ru": "Stack означает 1-3 дополнительные технологии, например Spring, Kafka или AWS.",
        },
        "location": {
            "en": "Location means the target candidate location, for example Ukraine.",
            "ru": "Location означает целевую локацию кандидатов, например Ukraine.",
        },
        "seniority": {
            "en": "Seniority means the optional experience level, for example Senior, Middle, or Lead.",
            "ru": "Seniority означает желаемый уровень опыта, например Senior, Middle или Lead.",
        },
        "search_depth": {
            "en": "Search depth controls how broad the prepared search should be; standard is the default.",
            "ru": "Search depth задает ширину поиска; standard используется по умолчанию.",
        },
        "profile_sources": {
            "en": "Profile sources means the allowed public profile source; this flow currently uses public LinkedIn profiles.",
            "ru": "Profile sources означает разрешенный публичный источник профилей; сейчас это public LinkedIn profiles.",
        },
    }
    field_explanations = explanations.get(field, explanations["role_family"])
    return field_explanations.get(language, field_explanations["en"])


def recruiter_chat_pending_field_mismatch_message(
    *,
    pending_field: str,
    answered_field: str | None,
    value: str | None,
    language: str,
    repeated: bool = False,
) -> str:
    value_label = value or "That"
    if pending_field == "technology" and answered_field == "stack":
        if language == "ru":
            prefix = (
                f"{value_label} уже есть в stack."
                if repeated
                else f"{value_label} понял как stack signal."
            )
            return (
                f"{prefix} Теперь нужна основная технология кандидата. "
                "Для текущего supported flow это Java."
            )
        prefix = (
            f"{value_label} is already captured as a stack signal."
            if repeated
            else f"{value_label} is a stack signal."
        )
        return (
            f"{prefix} I still need the main programming technology. "
            "For the current supported flow, use Java."
        )

    if pending_field == "stack" and answered_field == "technology":
        if language == "ru":
            return (
                f"{value_label} понял как основную технологию. Теперь нужны 1-3 stack signals, "
                "например Spring, Kafka или AWS."
            )
        return (
            f"{value_label} is the main technology. I still need 1-3 stack signals, "
            "for example Spring, Kafka, or AWS."
        )

    if pending_field == "location" and answered_field == "stack":
        if language == "ru":
            return (
                f"{value_label} понял как stack signal. Теперь нужна локация, например Ukraine."
            )
        return f"{value_label} is a stack signal. I still need the target location, for example Ukraine."

    if pending_field == "role_family" and answered_field == "stack":
        if language == "ru":
            return (
                f"{value_label} понял как stack signal. Теперь нужна целевая роль, например Backend Developer."
            )
        return f"{value_label} is a stack signal. I still need the target role, for example Backend Developer."

    if language == "ru":
        return (
            f"{value_label} похоже на {answered_field or 'другое поле'}, "
            f"но сейчас нужно уточнить {pending_field}."
        )
    return (
        f"{value_label} looks like {answered_field or 'a different field'}, "
        f"but I still need {pending_field}."
    )


def recruiter_chat_conversation_wording_payload(
    *,
    message_type: str,
    language: str,
    latest_user_text: str,
    deterministic_message: str,
    request: RecruiterChatTurnRequest,
) -> dict:
    context = current_brief_validation_context(request.draft_brief)
    normalized_brief = context.get("normalized_brief") or {}
    payload = {
        "wording_use_case": RECRUITER_CHAT_WORDING_USE_CASE_CONVERSATION,
        "message_type": message_type,
        "language": language,
        "latest_user_message": latest_user_text[:500],
        "deterministic_message": deterministic_message,
        "current_search_state": normalized_brief.get("brief_status") or "none",
        "allowed_meaning": [
            "Answer only the current safe chat turn.",
            "Preserve the current search summary and pending action state.",
            "Gently guide the recruiter back to candidate search when useful.",
        ],
        "forbidden_claims": [
            "search started",
            "results exist",
            "LinkedIn opened or inspected",
            "candidate messaging",
            "approval bypass",
            "autonomous execution",
        ],
        "hard_boundaries": agent_wording_hard_boundaries(),
    }
    payload["allowed_numbers"] = sorted(
        agent_wording_allowed_numbers(payload) | {"1", "3"}
    )
    return payload


def recruiter_chat_conversation_wording_has_disallowed_visible_content(text: str) -> bool:
    disallowed_patterns = [
        r"\bbuild\s+plan\b",
        r"\bprepare\s+search\b",
        r"\bsearch\s+plan\b",
        r"\bqueryplan\b",
        r"\bbackend\s+planner\b",
        r"\bfingerprint\b",
        r"\bruntime\b",
        r"\bapproval\b",
        r"\btavily\b",
        r"\bopenai\b",
        r"\blinkedin\b.{0,40}\b(opened|viewed|visited|checked|inspected)\b",
    ]
    return any(re.search(pattern, text or "", re.IGNORECASE) for pattern in disallowed_patterns)


def validate_recruiter_chat_conversation_wording_output(
    llm_output: dict,
    *,
    language: str,
    allowed_numbers: set[str],
) -> tuple[str | None, list[str], str | None]:
    validated_output, error = validate_agent_wording_output(
        llm_output,
        language=language,
        allowed_numbers=allowed_numbers,
        wording_use_case=RECRUITER_CHAT_WORDING_USE_CASE_CONVERSATION,
        existing_limitation_kinds=set(),
    )
    if error:
        return None, [], error

    message = validated_output["message"]
    if len(message) > 360:
        return None, [], "llm_output_too_long"
    if "\n" in message or "\r" in message:
        return None, [], "llm_output_multiline_not_allowed"
    if recruiter_chat_conversation_wording_has_disallowed_visible_content(message):
        return None, [], "llm_output_conversation_disallowed_visible_content"
    return message, validated_output.get("warnings") or [], None


async def apply_llm_wording_to_recruiter_chat_conversation(
    *,
    request: RecruiterChatTurnRequest,
    language: str,
    latest_user_text: str,
    deterministic_message: str,
    message_type: str,
) -> tuple[str, dict[str, str], list[str]]:
    if not agent_wording_has_openai_config():
        return (
            deterministic_message,
            build_agent_wording_provenance(
                message_type=message_type,
                language=language,
                wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
                fallback_reason=AGENT_WORDING_FALLBACK_NOT_CONFIGURED,
                no_call_reason=AGENT_WORDING_FALLBACK_NOT_CONFIGURED,
            ),
            [],
        )

    payload = recruiter_chat_conversation_wording_payload(
        message_type=message_type,
        language=language,
        latest_user_text=latest_user_text,
        deterministic_message=deterministic_message,
        request=request,
    )
    model = normalize_text_value(os.getenv("OPENAI_MODEL") or "") or None
    llm_output, error = await run_openai_json_agent_wording(payload)
    if error or llm_output is None:
        return (
            deterministic_message,
            build_agent_wording_provenance(
                message_type=message_type,
                language=language,
                wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
                fallback_reason=error or "openai_conversation_wording_failed",
                model=model,
            ),
            [],
        )

    message, warnings, validation_error = (
        validate_recruiter_chat_conversation_wording_output(
            llm_output,
            language=language,
            allowed_numbers=set(payload["allowed_numbers"]),
        )
    )
    if validation_error or not message:
        return (
            deterministic_message,
            build_agent_wording_provenance(
                message_type=message_type,
                language=language,
                wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
                fallback_reason=validation_error or "llm_output_invalid",
                model=model,
            ),
            [],
        )

    return (
        message,
        build_agent_wording_provenance(
            message_type=message_type,
            language=language,
            wording_mode=AGENT_WORDING_MODE_LLM_ASSISTED,
            model=model,
        ),
        warnings,
    )


def recruiter_chat_stack_explanation_message(language: str) -> str:
    if language == "ru":
        return (
            "Stack нужен, чтобы собрать конкретную Java/Ukraine search summary и "
            "не запускать слишком широкий поиск. Для текущего flow выбери 1-3 "
            "сигнала, например Spring, Kafka, AWS, Docker или Kubernetes."
        )
    return (
        "Stack is required so the search summary is specific enough before planning. "
        "Choose 1-3 signals such as Spring, Kafka, AWS, Docker, React, or Kubernetes."
    )


def recruiter_chat_reset_message(language: str) -> str:
    if language == "ru":
        return "Текущая search summary очищена. Напиши новый sourcing request."
    return "The current search summary is cleared. Tell me the new sourcing request."


def build_recruiter_chat_restart_response(
    request: RecruiterChatTurnRequest,
    language: str,
    planner_mode: str,
) -> dict:
    return build_recruiter_chat_response(
        ok=True,
        state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
        language=language,
        assistant_message=recruiter_chat_reset_message(language),
        planner_mode=planner_mode,
        brief_changed=bool(request.draft_brief),
        stale_state_should_clear=False,
        clear_brief=True,
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


def normalized_field_value_has_evidence(value: object, text: str) -> bool:
    if not value:
        return False
    values = value if isinstance(value, list) else [value]
    normalized_text = normalized_chat_control_text(text)
    for item in values:
        item_text = normalize_text_value(str(item))
        if not item_text:
            continue
        candidate_terms = [item_text]
        item_key = item_text.lower()
        for alias, canonical_value in JAVA_STACK_VALUES.items():
            if canonical_value.lower() == item_key:
                candidate_terms.append(alias)
        for alias, canonical_value in KNOWN_BACKEND_TECHNOLOGIES.items():
            if canonical_value.lower() == item_key:
                candidate_terms.append(alias)

        for candidate_term in candidate_terms:
            if candidate_term.lower() in text.lower():
                return True
            pattern = term_match_pattern(candidate_term.lower())
            if re.search(pattern, normalized_text, flags=re.IGNORECASE):
                return True
    return False


def search_brief_readiness_evidence(
    *,
    normalized_brief: dict,
    latest_user_text: str,
    user_text: str,
    existing_brief: SearchBrief | None,
) -> dict:
    if normalized_brief.get("brief_status") != SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        return {"ready_evidence": "sufficient", "missing_evidence": [], "reason": None}

    existing_context = current_brief_validation_context(existing_brief)
    existing_normalized = existing_context.get("normalized_brief") or {}
    existing_is_ready = (
        existing_context.get("ok")
        and existing_normalized.get("brief_status") == SEARCH_BRIEF_STATUS_READY_FOR_PLANNING
    )
    if (
        existing_is_ready
        and normalized_brief_state_payload(existing_normalized)
        == normalized_brief_state_payload(normalized_brief)
    ):
        return {
            "ready_evidence": "sufficient",
            "missing_evidence": [],
            "reason": "unchanged_existing_ready_brief",
        }

    combined_user_text = f"{user_text}\n{latest_user_text}"
    existing_payload = normalized_brief_state_payload(existing_normalized)
    candidate_payload = normalized_brief_state_payload(normalized_brief)

    field_evidence = {
        "role_family": normalized_field_value_has_evidence(
            normalized_brief.get("role_family"),
            combined_user_text,
        ) or explicit_it_role_signal(combined_user_text),
        "technology": normalized_field_value_has_evidence(
            normalized_brief.get("technology"),
            combined_user_text,
        ) or explicit_technology_signal(combined_user_text),
        "location": normalized_field_value_has_evidence(
            normalized_brief.get("location"),
            combined_user_text,
        ) or explicit_ukraine_location_signal(combined_user_text),
        "stack": normalized_field_value_has_evidence(
            normalized_brief.get("stack") or [],
            combined_user_text,
        ),
    }
    if existing_is_ready:
        for field_name in field_evidence:
            if existing_payload.get(field_name) == candidate_payload.get(field_name):
                field_evidence[field_name] = True

    missing_evidence = [
        field_name
        for field_name in ("role_family", "technology", "location", "stack")
        if not field_evidence[field_name]
    ]
    latest_has_sourcing_signal = has_sourcing_or_recruiter_context_signal(latest_user_text)
    latest_is_noise = detect_recruiter_chat_unclear_request(latest_user_text)

    if missing_evidence:
        reason = "weak_llm_only_field"
        if latest_is_noise and not latest_has_sourcing_signal:
            reason = "noisy_latest_turn"
        elif not has_sourcing_or_recruiter_context_signal(combined_user_text):
            reason = "no_sourcing_signal"
        return {
            "ready_evidence": "insufficient",
            "missing_evidence": missing_evidence,
            "reason": reason,
        }

    return {"ready_evidence": "sufficient", "missing_evidence": [], "reason": None}


def downgraded_brief_for_insufficient_evidence(
    normalized_brief: dict,
    missing_evidence: list[str],
) -> dict:
    downgraded = dict(normalized_brief)
    downgraded["brief_status"] = SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION
    downgraded["missing_fields"] = missing_evidence
    downgraded["clarifying_questions"] = []
    if "role_family" in missing_evidence:
        downgraded["role_family"] = None
    if "technology" in missing_evidence:
        downgraded["technology"] = None
        downgraded["must_have"] = []
    if "location" in missing_evidence:
        downgraded["location"] = None
    if "stack" in missing_evidence:
        downgraded["stack"] = []
        downgraded["nice_to_have"] = []
    return downgraded


def refinement_requires_initial_brief_message(language: str) -> str:
    return refinement_requires_initial_brief_source_message(language)


def unsupported_patch_message(language: str) -> str:
    return unsupported_patch_source_message(language)


def last_stack_item_message(language: str) -> str:
    return last_stack_item_source_message(language)


def brief_patch_operation_label(operation_name: str, language: str) -> str:
    labels = {
        "ru": {
            BRIEF_PATCH_ADD_STACK: "добавил stack",
            BRIEF_PATCH_REMOVE_STACK: "удалил stack",
            BRIEF_PATCH_REPLACE_STACK: "обновил stack",
            BRIEF_PATCH_SET_SENIORITY: "обновил seniority",
            BRIEF_PATCH_SET_SEARCH_DEPTH: "обновил глубину поиска",
            BRIEF_PATCH_SET_LOCATION: "обновил локацию",
        },
        "en": {
            BRIEF_PATCH_ADD_STACK: "added stack",
            BRIEF_PATCH_REMOVE_STACK: "removed stack",
            BRIEF_PATCH_REPLACE_STACK: "updated stack",
            BRIEF_PATCH_ADD_MUST_HAVE: "added must-have",
            BRIEF_PATCH_REMOVE_MUST_HAVE: "removed must-have",
            BRIEF_PATCH_REPLACE_MUST_HAVE: "updated must-have",
            BRIEF_PATCH_SET_SENIORITY: "updated seniority",
            BRIEF_PATCH_SET_SEARCH_DEPTH: "updated search depth",
            BRIEF_PATCH_SET_LOCATION: "updated location",
        },
    }
    return labels.get(language, labels["en"]).get(
        operation_name,
        operation_name.replace("_", " "),
    )


def patch_success_message(
    patch: dict,
    language: str,
    changed: bool,
    next_question: str | None = None,
) -> str:
    operations = patch.get("operations") or []
    operation_labels = [
        brief_patch_operation_label(operation.get("operation", "update"), language)
        for operation in operations
        if operation.get("operation") not in {BRIEF_PATCH_NOOP, BRIEF_PATCH_RECONFIRM_FIELD}
    ]
    action_summary = ", ".join(operation_labels) if operation_labels else (
        "обновил" if language == "ru" else "updated"
    )

    if changed and next_question:
        if language == "ru":
            return f"Обновил search summary ({action_summary}). {next_question}"
        return f"Updated the search summary ({action_summary}). {next_question}"

    return brief_refinement_source_message(language, changed, action_summary)


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
                "Patch contains unsupported values for the current final POC flow.",
            )
        ], unsupported_patch_message(language)

    candidate = clean_search_brief_dict(request.draft_brief)
    current_stack, current_stack_errors = normalize_brief_stack_items(candidate.get("stack"))
    if current_stack_errors:
        if candidate.get("stack"):
            return None, None, False, current_stack_errors, validation_error_message(current_stack_errors, language)
        current_stack = []

    next_stack = current_stack[:]
    current_must_have = normalize_text_list(candidate.get("must_have"))
    next_must_have = current_must_have[:]
    changed = False
    stack_touched = False
    must_have_touched = False

    for operation in operations:
        operation_name = operation.get("operation")

        if operation_name == BRIEF_PATCH_ADD_STACK:
            stack_item, stack_item_error = normalize_stack_item_value(operation.get("value"))
            if stack_item_error:
                return None, None, False, [
                    patch_validation_error("stack", "invalid_stack_item", stack_item_error)
                ], validation_error_message([], language)
            if stack_item and stack_item not in next_stack:
                next_stack.append(stack_item)
                changed = True
                stack_touched = True
            continue

        if operation_name == BRIEF_PATCH_REMOVE_STACK:
            stack_item, _ = normalize_stack_item_value(operation.get("value"))
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

        if operation_name == BRIEF_PATCH_SET_LOCATION:
            location = normalize_location_value(operation.get("value"))
            if location and location != normalize_location_value(
                candidate.get("location")
            ):
                candidate["location"] = location
                changed = True
            continue

        if operation_name == BRIEF_PATCH_ADD_MUST_HAVE:
            must_have, must_have_error = normalize_refinement_must_have_value(
                operation.get("value")
            )
            if must_have_error or not must_have:
                return None, None, False, [
                    patch_validation_error(
                        "must_have",
                        "invalid_must_have_item",
                        must_have_error or "Invalid must-have item.",
                    )
                ], validation_error_message([], language)
            if must_have.lower() not in {item.lower() for item in next_must_have}:
                next_must_have.append(must_have)
                changed = True
                must_have_touched = True
            continue

        if operation_name == BRIEF_PATCH_REMOVE_MUST_HAVE:
            must_have, must_have_error = normalize_refinement_must_have_value(
                operation.get("value")
            )
            if must_have_error or not must_have:
                return None, None, False, [
                    patch_validation_error(
                        "must_have",
                        "invalid_must_have_item",
                        must_have_error or "Invalid must-have item.",
                    )
                ], validation_error_message([], language)
            lowered_must_have = must_have.lower()
            filtered_must_have = [
                item
                for item in next_must_have
                if item.lower() != lowered_must_have
            ]
            if filtered_must_have != next_must_have:
                next_must_have = filtered_must_have
                changed = True
                must_have_touched = True
            continue

        if operation_name == BRIEF_PATCH_REPLACE_MUST_HAVE:
            raw_values = operation.get("values") or []
            if not isinstance(raw_values, list):
                return None, None, False, [
                    patch_validation_error(
                        "must_have",
                        "invalid_must_have_values",
                        "Must-have replacement must be a list.",
                    )
                ], validation_error_message([], language)
            replacement_must_have: list[str] = []
            for raw_value in raw_values:
                must_have, must_have_error = normalize_refinement_must_have_value(
                    raw_value
                )
                if must_have_error or not must_have:
                    return None, None, False, [
                        patch_validation_error(
                            "must_have",
                            "invalid_must_have_item",
                            must_have_error or "Invalid must-have item.",
                        )
                    ], validation_error_message([], language)
                if must_have.lower() not in {
                    item.lower() for item in replacement_must_have
                }:
                    replacement_must_have.append(must_have)
            if next_must_have != replacement_must_have:
                next_must_have = replacement_must_have
                changed = True
                must_have_touched = True
            continue

        if operation_name == BRIEF_PATCH_RECONFIRM_FIELD:
            field_name = operation.get("field")
            value = operation.get("value")
            if field_name == "technology":
                technology, technology_errors = normalize_technology_value(value)
                if technology_errors or not technology:
                    return None, None, False, technology_errors, validation_error_message(
                        technology_errors,
                        language,
                    )
                if technology != normalize_text_value(candidate.get("technology")):
                    candidate["technology"] = technology
                    candidate["must_have"] = [technology]
                    changed = True
            elif field_name == "role_family":
                role_family, role_errors = normalize_role_family_value(value)
                if role_errors or not role_family:
                    return None, None, False, role_errors, validation_error_message(
                        role_errors,
                        language,
                    )
                if role_family != normalize_text_value(candidate.get("role_family")):
                    candidate["role_family"] = role_family
                    changed = True
            continue

        if operation_name == BRIEF_PATCH_NOOP:
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

    if must_have_touched:
        candidate["must_have"] = next_must_have

    if changed:
        candidate["source_text"] = chat_text

    if "search_depth" not in candidate:
        candidate["search_depth"] = SEARCH_DEPTH_STANDARD
    if "profile_sources" not in candidate:
        candidate["profile_sources"] = [PROFILE_SOURCE_LINKEDIN_PUBLIC]

    candidate, requirement_signals_changed = (
        apply_requirement_search_signal_resolution_to_draft(candidate)
    )
    changed = changed or requirement_signals_changed

    try:
        candidate_brief = SearchBrief(**candidate)
    except ValidationError as exc:
        return None, None, False, [
            {
                "field": "brief_patch",
                "message": f"Updated search summary is invalid: {error['msg']}",
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

    if changed and state == RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION and next_question:
        message = patch_success_message(
            patch,
            language,
            changed,
            next_question=next_question,
        )
        patch["assistant_message"] = message

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


def pending_clarification_field(
    request: RecruiterChatTurnRequest,
    language: str = "en",
) -> str | None:
    if not request.draft_brief:
        return None

    context = current_brief_context_for_language(request.draft_brief, language)
    normalized_brief = context.get("normalized_brief") or {}
    missing_fields = normalized_brief.get("missing_fields") or []
    if not missing_fields:
        return None
    return missing_fields[0]


async def pending_stack_clarification_patch_from_message(
    request: RecruiterChatTurnRequest,
    text: str,
    language: str = "en",
) -> dict | None:
    if pending_clarification_field(request, language) != "stack":
        return None

    stack_terms: list[str] = []
    candidate_terms, candidate_error = normalize_stack_signal_candidates(text)
    if not candidate_error:
        stack_terms = deterministic_known_stack_signal_terms(candidate_terms)

    should_use_semantic_interpreter = bool(
        candidate_error
        or any(re.search(r"\s", term.strip()) for term in candidate_terms)
    )

    if not stack_terms:
        if should_use_semantic_interpreter:
            interpreter_result, _ = await classify_pending_answer_interpreter_from_message(
                text=text,
                language=language,
                expected_field="stack",
                current_brief=request.draft_brief,
            )
            stack_terms = await stack_terms_from_pending_answer_interpreter(
                interpreter_result,
                request.draft_brief,
            )
        if not stack_terms and not candidate_error and not should_use_semantic_interpreter:
            stack_terms, _ = await classify_stack_signal_terms_from_message(
                text,
                request.draft_brief,
            )
    if not stack_terms:
        return None

    return build_brief_patch(
        source_message=text,
        operations=[
            {
                "operation": BRIEF_PATCH_REPLACE_STACK,
                "field": "stack",
                "values": stack_terms[:3],
            }
        ],
        requires_clarification=False,
    )


def pending_location_candidate_text(text: str) -> str | None:
    candidate = normalize_text_value(text)
    if not candidate:
        return None

    prefix_pattern = (
        r"^\s*(?:please\s+)?"
        r"(?:(?:use|set|change|replace|update|make)\s+)?"
        r"(?:(?:the\s+)?(?:target\s+)?(?:location|country|city|region)\s*"
        r"(?:is|to|as|:)?\s*|(?:in|from)\s+)"
    )
    for _ in range(2):
        next_candidate = re.sub(prefix_pattern, "", candidate, flags=re.IGNORECASE)
        next_candidate = compact_spaces(next_candidate).strip(" .,:;\"'")
        if next_candidate == candidate:
            break
        candidate = next_candidate

    return candidate or None


def location_candidate_is_obviously_not_location(value: str) -> bool:
    normalized_value = normalized_chat_control_text(value)
    if not normalized_value:
        return True

    if normalized_value in {
        "yes",
        "no",
        "ok",
        "okay",
        "great",
        "good",
        "sure",
        "confirm",
        "confirmed",
        "update",
        "change",
        "location",
        "country",
        "city",
        "region",
        "skip",
        "none",
        "n a",
        "na",
        "not sure",
        "i dont know",
        "i do not know",
    }:
        return True

    if explicit_technology_signal(value):
        return True
    if deterministic_known_stack_signal_terms([value]):
        return True
    if explicit_it_role_signal(value):
        return True
    return bool(
        re.search(
            r"\b(skill|skills|stack|technology|tech|role|profession|"
            r"developer|engineer|automation|tester|qa|software)\b",
            normalized_value,
            flags=re.IGNORECASE,
        )
    )


def normalize_pending_location_value(value: str) -> tuple[str | None, str | None]:
    candidate = pending_location_candidate_text(value)
    if not candidate:
        return None, "location_missing"
    if location_candidate_is_obviously_not_location(candidate):
        return None, "location_not_location"

    location, errors = normalize_search_location_value(candidate)
    if errors or not location:
        return None, "location_invalid"
    if location_candidate_is_obviously_not_location(location):
        return None, "location_not_location"

    return location, None


async def pending_location_clarification_patch_from_message(
    request: RecruiterChatTurnRequest,
    text: str,
    language: str = "en",
) -> dict | None:
    if pending_clarification_field(request, language) != "location":
        return None

    location = deterministic_chat_brief_hints(text).get("location")
    if not location:
        candidate = pending_location_candidate_text(text)
        token_count = len(re.findall(r"[A-Za-z0-9]+", candidate or ""))
        if token_count <= 2:
            location, _ = normalize_pending_location_value(text)
    if not location:
        interpreter_result, _ = await classify_pending_answer_interpreter_from_message(
            text=text,
            language=language,
            expected_field="location",
            current_brief=request.draft_brief,
        )
        if (
            interpreter_result
            and interpreter_result.get("field") == "location"
            and interpreter_result.get("intent") == PENDING_ANSWER_INTENT_ANSWER_PENDING_FIELD
            and interpreter_result.get("values")
        ):
            location = interpreter_result["values"][0]
    if not location:
        return None

    return build_brief_patch(
        source_message=text,
        operations=[
            {
                "operation": BRIEF_PATCH_SET_LOCATION,
                "field": "location",
                "value": location,
            }
        ],
        requires_clarification=False,
    )


def pending_location_unsupported_answer_from_message(
    request: RecruiterChatTurnRequest,
    text: str,
) -> bool:
    if pending_clarification_field(request) != "location":
        return False

    return any(
        operation.get("field") == "location"
        for operation in unsupported_refinement_operations(text)
    )


def pending_location_unsupported_answer_message(language: str) -> str:
    if language == "ru":
        return (
            "Текущий Java/Ukraine baseline поддерживает только Украину как локацию. "
            "Укажи Украину или город в Украине, например Киев."
        )
    return (
        "Use an English target location."
    )


def pending_clarification_unrecognized_answer_field(
    request: RecruiterChatTurnRequest,
    text: str,
    language: str,
) -> str | None:
    field = pending_clarification_field(request, language)
    if not field:
        return None
    if field not in {"location", "stack"}:
        return None

    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return field if text.strip() else None

    if field == "location":
        location = deterministic_chat_brief_hints(text).get("location")
        if not location:
            location, _ = normalize_pending_location_value(text)
        if location:
            return None
    if field == "stack" and java_stack_terms_in_text(normalized_text):
        return None

    if deterministic_brief_patch_from_message(text, language) is not None:
        return None

    return field


def pending_clarification_unrecognized_answer_message(field: str, language: str) -> str:
    if field == "location":
        if language == "ru":
            return (
                "Не распознал локацию. Для текущего baseline укажи Украину "
                "или город в Украине, например Киев."
            )
        return (
            "That does not look like an English target location. Use a country, "
            "city, region, or Remote, for example Spain, Germany, Poland, "
            "Madrid, or Remote."
        )

    if field == "stack":
        if language == "ru":
            return (
                "Не распознал поддерживаемые Java стек-сигналы. Укажи 1-3 сигнала, "
                "например Spring, Kafka, AWS или Hibernate."
            )
        return (
            "That does not look like an English IT/software stack signal. Use 1-3 "
            "English stack signals, for example Java, Playwright, Selenium, Spring, "
            "AWS, or Kubernetes."
        )

    return recruiter_chat_unclear_request_message(language)


def latest_user_and_prior_context(
    messages: list[RecruiterChatMessage],
) -> tuple[int | None, RecruiterChatMessage | None, RecruiterChatMessage | None]:
    latest_user_index: int | None = None
    for index in range(len(messages) - 1, -1, -1):
        role = (normalize_text_value(messages[index].role) or "").lower()
        if role in {"user", "recruiter"}:
            latest_user_index = index
            break

    if latest_user_index is None:
        return None, None, None

    prior_assistant: RecruiterChatMessage | None = None
    prior_user: RecruiterChatMessage | None = None
    for index in range(latest_user_index - 1, -1, -1):
        role = (normalize_text_value(messages[index].role) or "").lower()
        if prior_assistant is None and role == "assistant":
            prior_assistant = messages[index]
            continue
        if prior_assistant is not None and role in {"user", "recruiter"}:
            prior_user = messages[index]
            break

    return latest_user_index, prior_assistant, prior_user


def is_backend_java_hypothesis_question(text: str) -> bool:
    normalized_text = normalized_chat_control_text(text)
    if not normalized_text:
        return False
    return bool(
        "backend developer" in normalized_text
        and "java" in normalized_text
        and (
            "are we looking" in normalized_text
            or "looking for" in normalized_text
            or "should the search target" in normalized_text
            or "ищем" in normalized_text
        )
    )


def extract_pending_backend_java_hypothesis(
    request: RecruiterChatTurnRequest,
    language: str,
) -> dict | None:
    _, prior_assistant, prior_user = latest_user_and_prior_context(request.messages)
    if prior_assistant is None or prior_user is None:
        return None
    if not is_backend_java_hypothesis_question(prior_assistant.content):
        return None

    prior_user_text = prior_user.content
    hints = deterministic_chat_brief_hints(prior_user_text)
    if hints.get("technology") != "Java" or hints.get("location") != "Ukraine":
        return None
    if not hints.get("stack"):
        return None

    ambiguity = detect_recruiter_chat_ambiguity_or_contradiction(
        prior_user_text,
        language,
    )
    if not ambiguity or ambiguity.get("code") != "missing_role_or_technology":
        return None

    stack = list(hints.get("stack") or [])[:3]
    return {
        "source_text": prior_user_text,
        "role_family": "Backend Developer",
        "technology": "Java",
        "stack": stack,
        "location": "Ukraine",
        "must_have": ["Java"],
        "nice_to_have": stack,
        "search_depth": hints.get("search_depth") or SEARCH_DEPTH_STANDARD,
        "profile_sources": hints.get("profile_sources")
        or [PROFILE_SOURCE_LINKEDIN_PUBLIC],
    }


def build_pending_hypothesis_confirmation_response(
    request: RecruiterChatTurnRequest,
    language: str,
    planner_mode: str,
    pending_hypothesis: dict,
) -> dict:
    try:
        candidate_brief = SearchBrief(
            source_text=pending_hypothesis["source_text"],
            brief_status=SEARCH_BRIEF_STATUS_READY_FOR_PLANNING,
            role_family=pending_hypothesis["role_family"],
            technology=pending_hypothesis["technology"],
            stack=pending_hypothesis.get("stack") or [],
            location=pending_hypothesis["location"],
            must_have=pending_hypothesis.get("must_have") or ["Java"],
            nice_to_have=pending_hypothesis.get("nice_to_have") or [],
            search_depth=pending_hypothesis.get("search_depth") or SEARCH_DEPTH_STANDARD,
            profile_sources=pending_hypothesis.get("profile_sources")
            or [PROFILE_SOURCE_LINKEDIN_PUBLIC],
        )
    except ValidationError as exc:
        errors = [
            {
                "field": f"pending_hypothesis.{'.'.join(str(part) for part in error.get('loc', [])) or 'value'}",
                "message": "I could not safely confirm that search hypothesis. Please restate the role, main technology, location, and 1-3 stack signals.",
            }
            for error in exc.errors()
        ]
        return build_recruiter_chat_response(
            ok=False,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            validation_errors=errors,
            planner_mode=planner_mode,
        )

    candidate_response = search_brief_validation_response(candidate_brief)
    normalized_brief = candidate_response["normalized_brief"]
    validation_errors = candidate_response["errors"]
    next_question = one_clarifying_question(normalized_brief, language)
    state = RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION
    ok = not validation_errors
    if ok and normalized_brief["brief_status"] == SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        state = RECRUITER_CHAT_STATE_READY_FOR_PLANNING

    existing_payload = normalized_brief_state_payload(
        current_brief_context_for_language(request.draft_brief, language)["normalized_brief"]
    )
    candidate_payload = normalized_brief_state_payload(normalized_brief)
    brief_changed = existing_payload != candidate_payload

    return build_recruiter_chat_response(
        ok=ok,
        state=state,
        language=language,
        normalized_brief=normalized_brief,
        validation_errors=validation_errors,
        next_question=next_question,
        planner_mode=planner_mode,
        brief_changed=brief_changed,
        stale_state_should_clear=brief_changed,
    )


def pending_hypothesis_reject_message(language: str) -> str:
    if language == "ru":
        return "Понял. Уточни целевую роль и основную технологию для поиска."
    return "Understood. Tell me the target role and main technology for the search."


def pending_hypothesis_unclear_message(language: str) -> str:
    if language == "ru":
        return "Подтверди, пожалуйста: ищем Backend Developer с Java, или нужно изменить роль/технологию?"
    return "Please confirm: are we looking for Backend Developer with Java, or should we change the role/technology?"


def pending_update_field_question(field: str, language: str) -> str:
    if field == "location":
        if language == "ru":
            return "Какую локацию использовать?"
        return "What location should I use?"
    if field == "stack":
        if language == "ru":
            return "Какие 1-3 stack signals использовать?"
        return "Which 1-3 stack signals should I use?"
    if field == "technology":
        if language == "ru":
            return "Какую основную технологию использовать? В текущем flow поддерживается Java."
        return "What main technology should I use?"
    if field == "role_family":
        if language == "ru":
            return "Какую целевую роль использовать? Например, Backend Developer."
        return "What target role should I use? For example, Backend Developer."
    if field == "seniority":
        if language == "ru":
            return "Какой seniority использовать: Junior, Middle, Senior или Lead?"
        return "What seniority should I use: Junior, Middle, Senior, or Lead?"
    if field == "search_depth":
        if language == "ru":
            return "Какую глубину поиска использовать: standard или deep?"
        return "What search depth should I use: standard or deep?"
    if language == "ru":
        return "Какое поле в search summary нужно изменить?"
    return "Which search summary field should I update?"


def pending_update_cancel_message(language: str) -> str:
    if language == "ru":
        return "Ок, оставляю текущую search summary без изменений."
    return "Ok, I will keep the current search summary unchanged."


def pending_update_unknown_field_message(language: str) -> str:
    if language == "ru":
        return "Укажи поле, которое нужно изменить: role, technology, stack, location, seniority или depth."
    return "Tell me which field to update: role, technology, stack, location, seniority, or depth."


async def pending_interpreter_patch_for_field(
    field: str,
    text: str,
    language: str,
    current_brief: SearchBrief | dict | None = None,
) -> dict | None:
    interpreter_result, _ = await classify_pending_answer_interpreter_from_message(
        text=text,
        language=language,
        expected_field=field,
        pending_update_field=field,
        current_brief=current_brief,
    )
    if not interpreter_result:
        return None
    if interpreter_result.get("intent") not in {
        PENDING_ANSWER_INTENT_ANSWER_PENDING_FIELD,
        PENDING_ANSWER_INTENT_PROVIDE_UPDATE_VALUE,
    }:
        return None
    if interpreter_result.get("field") != field:
        return None

    values = interpreter_result.get("values") or []
    if not values:
        return None

    if field == "stack":
        stack_terms = await stack_terms_from_pending_answer_interpreter(
            interpreter_result,
            current_brief,
        )
        if not stack_terms:
            return None
        return build_brief_patch(
            source_message=text,
            operations=[
                {
                    "operation": BRIEF_PATCH_REPLACE_STACK,
                    "field": "stack",
                    "values": stack_terms[:3],
                }
            ],
            requires_clarification=False,
        )

    if field == "location":
        return build_brief_patch(
            source_message=text,
            operations=[
                {
                    "operation": BRIEF_PATCH_SET_LOCATION,
                    "field": "location",
                    "value": values[0],
                }
            ],
            requires_clarification=False,
        )

    if field == "technology":
        operation = BRIEF_PATCH_RECONFIRM_FIELD
    elif field == "role_family":
        operation = BRIEF_PATCH_RECONFIRM_FIELD
    elif field == "seniority":
        operation = BRIEF_PATCH_SET_SENIORITY
    elif field == "search_depth":
        operation = BRIEF_PATCH_SET_SEARCH_DEPTH
    else:
        return None

    return build_brief_patch(
        source_message=text,
        operations=[
            {
                "operation": operation,
                "field": field,
                "value": values[0],
            }
        ],
        requires_clarification=False,
    )


async def pending_update_field_patch_from_message(
    field: str,
    text: str,
    language: str,
    current_brief: SearchBrief | dict | None = None,
) -> tuple[dict | None, str | None]:
    if field == "location":
        location = deterministic_chat_brief_hints(text).get("location")
        if not location:
            candidate = pending_location_candidate_text(text)
            token_count = len(re.findall(r"[A-Za-z0-9]+", candidate or ""))
            if token_count <= 2:
                location, _ = normalize_pending_location_value(text)
        if location:
            return build_brief_patch(
                source_message=text,
                operations=[
                    {
                        "operation": BRIEF_PATCH_SET_LOCATION,
                        "field": "location",
                        "value": location,
                    }
                ],
                requires_clarification=False,
            ), None
        interpreter_patch = await pending_interpreter_patch_for_field(
            "location",
            text,
            language,
            current_brief,
        )
        if interpreter_patch is not None:
            return interpreter_patch, None
        return None, pending_clarification_unrecognized_answer_message("location", language)

    if field == "stack":
        stack_terms: list[str] = []
        candidate_terms, candidate_error = normalize_stack_signal_candidates(text)
        if not candidate_error:
            stack_terms = deterministic_known_stack_signal_terms(candidate_terms)
        should_use_semantic_interpreter = bool(
            candidate_error
            or any(re.search(r"\s", term.strip()) for term in candidate_terms)
        )
        if not stack_terms and should_use_semantic_interpreter:
            interpreter_patch = await pending_interpreter_patch_for_field(
                "stack",
                text,
                language,
                current_brief,
            )
            if interpreter_patch is not None:
                return interpreter_patch, None
        if not stack_terms and not candidate_error and not should_use_semantic_interpreter:
            stack_terms, _ = await classify_stack_signal_terms_from_message(
                text,
                current_brief,
            )
        if stack_terms:
            return build_brief_patch(
                source_message=text,
                operations=[
                    {
                        "operation": BRIEF_PATCH_REPLACE_STACK,
                        "field": "stack",
                        "values": stack_terms[:3],
                    }
                ],
                requires_clarification=False,
            ), None
        return None, pending_clarification_unrecognized_answer_message("stack", language)

    if field == "technology":
        technology, technology_errors = normalize_technology_value(text)
        if technology and not technology_errors:
            return build_brief_patch(
                source_message=text,
                operations=[
                    {
                        "operation": BRIEF_PATCH_RECONFIRM_FIELD,
                        "field": "technology",
                        "value": technology,
                    }
                ],
                requires_clarification=False,
            ), None
        interpreter_patch = await pending_interpreter_patch_for_field(
            "technology",
            text,
            language,
            current_brief,
        )
        if interpreter_patch is not None:
            return interpreter_patch, None
        return None, pending_update_field_question("technology", language)

    if field == "role_family":
        role_family, role_errors = normalize_role_family_value(text)
        if role_family and not role_errors:
            return build_brief_patch(
                source_message=text,
                operations=[
                    {
                        "operation": BRIEF_PATCH_RECONFIRM_FIELD,
                        "field": "role_family",
                        "value": role_family,
                    }
                ],
                requires_clarification=False,
            ), None
        interpreter_patch = await pending_interpreter_patch_for_field(
            "role_family",
            text,
            language,
            current_brief,
        )
        if interpreter_patch is not None:
            return interpreter_patch, None
        return None, pending_update_field_question("role_family", language)

    if field == "seniority":
        seniority = detected_seniority_value(text)
        if seniority:
            return build_brief_patch(
                source_message=text,
                operations=[
                    {
                        "operation": BRIEF_PATCH_SET_SENIORITY,
                        "field": "seniority",
                        "value": seniority,
                    }
                ],
                requires_clarification=False,
            ), None
        interpreter_patch = await pending_interpreter_patch_for_field(
            "seniority",
            text,
            language,
            current_brief,
        )
        if interpreter_patch is not None:
            return interpreter_patch, None
        return None, pending_update_field_question("seniority", language)

    if field == "search_depth":
        search_depth = detected_search_depth_value(text)
        if search_depth:
            return build_brief_patch(
                source_message=text,
                operations=[
                    {
                        "operation": BRIEF_PATCH_SET_SEARCH_DEPTH,
                        "field": "search_depth",
                        "value": search_depth,
                    }
                ],
                requires_clarification=False,
            ), None
        interpreter_patch = await pending_interpreter_patch_for_field(
            "search_depth",
            text,
            language,
            current_brief,
        )
        if interpreter_patch is not None:
            return interpreter_patch, None
        return None, pending_update_field_question("search_depth", language)

    return None, pending_update_unknown_field_message(language)


def search_brief_refinement_unavailable_message(language: str) -> str:
    if language == "ru":
        return "Please clarify what to change in the current search summary."
    return "Please clarify what to change in the current search summary."


async def search_brief_refinement_patch_from_message(
    request: RecruiterChatTurnRequest,
    text: str,
    language: str,
) -> tuple[dict | None, str | None]:
    if not request.draft_brief:
        return None, None
    if not is_refinement_like_chat_message(text):
        return None, None

    llm_output, llm_error = await run_openai_json_search_brief_refinement_interpreter(
        latest_message=text,
        language=language,
        current_brief=request.draft_brief,
    )
    if llm_error or llm_output is None:
        return None, search_brief_refinement_unavailable_message(language)

    refinement_result, refinement_errors = validate_search_brief_refinement_output(
        llm_output,
        source_message=text,
    )
    if refinement_errors or refinement_result is None:
        return None, search_brief_refinement_unavailable_message(language)

    patch = refinement_result["patch"]
    if patch.get("requires_clarification"):
        return None, search_brief_refinement_unavailable_message(language)
    return patch, None


async def pending_clarification_response_if_any(
    request: RecruiterChatTurnRequest,
    language: str,
    planner_mode: str,
    latest_user_text: str,
    chat_text: str,
) -> dict | None:
    pending_stack_patch = await pending_stack_clarification_patch_from_message(
        request,
        latest_user_text,
        language,
    )
    if pending_stack_patch is not None:
        return build_recruiter_chat_refinement_response(
            request,
            language,
            planner_mode,
            pending_stack_patch,
            chat_text,
        )

    pending_location_patch = await pending_location_clarification_patch_from_message(
        request,
        latest_user_text,
        language,
    )
    if pending_location_patch is not None:
        return build_recruiter_chat_refinement_response(
            request,
            language,
            planner_mode,
            pending_location_patch,
            chat_text,
        )

    if pending_location_unsupported_answer_from_message(request, latest_user_text):
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            pending_location_unsupported_answer_message(language),
        )

    brief_patch = deterministic_brief_patch_from_message(latest_user_text, language)
    if brief_patch is not None and brief_patch.get("operations"):
        return build_recruiter_chat_refinement_response(
            request,
            language,
            planner_mode,
            brief_patch,
            chat_text,
        )

    if not pending_clarification_field(request, language):
        refinement_patch, refinement_message = await search_brief_refinement_patch_from_message(
            request,
            latest_user_text,
            language,
        )
        if refinement_patch is not None:
            return build_recruiter_chat_refinement_response(
                request,
                language,
                planner_mode,
                refinement_patch,
                chat_text,
            )
        if refinement_message:
            return build_recruiter_chat_preserve_current_brief_response(
                request,
                language,
                planner_mode,
                refinement_message,
            )

    if brief_patch is not None:
        return build_recruiter_chat_refinement_response(
            request,
            language,
            planner_mode,
            brief_patch,
            chat_text,
        )

    unrecognized_field = pending_clarification_unrecognized_answer_field(
        request,
        latest_user_text,
        language,
    )
    if unrecognized_field:
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            pending_clarification_unrecognized_answer_message(
                unrecognized_field,
                language,
            ),
        )

    return None


async def build_recruiter_chat_validated_brief_turn_response(
    *,
    request: RecruiterChatTurnRequest,
    language: str,
    planner_mode: str,
    normalized_brief: dict,
    validation_errors: list[dict[str, str]],
    latest_user_text: str,
    user_text: str,
    brief_changed: bool,
) -> dict:
    next_question = one_clarifying_question(normalized_brief, language)
    readiness_evidence = search_brief_readiness_evidence(
        normalized_brief=normalized_brief,
        latest_user_text=latest_user_text,
        user_text=user_text,
        existing_brief=request.draft_brief,
    )
    if readiness_evidence["ready_evidence"] == "insufficient":
        missing_evidence = readiness_evidence.get("missing_evidence") or []
        if (
            readiness_evidence.get("reason") in {"noisy_latest_turn", "no_sourcing_signal"}
            and not has_sourcing_or_recruiter_context_signal(user_text)
        ):
            deterministic_message = recruiter_chat_unclear_request_message(language)
            assistant_message, wording_provenance, llm_warnings = (
                await apply_llm_wording_to_recruiter_chat_conversation(
                    request=request,
                    language=language,
                    latest_user_text=latest_user_text,
                    deterministic_message=deterministic_message,
                    message_type="unclear",
                )
            )
            return build_recruiter_chat_preserve_current_brief_response(
                request,
                language,
                planner_mode,
                assistant_message,
                wording_provenance,
                llm_warnings,
            )

        downgraded_brief = downgraded_brief_for_insufficient_evidence(
            normalized_brief,
            missing_evidence,
        )
        return build_recruiter_chat_response(
            ok=True,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            normalized_brief=downgraded_brief,
            validation_errors=[],
            next_question=one_clarifying_question(downgraded_brief, language),
            planner_mode=planner_mode,
            brief_changed=brief_changed,
            stale_state_should_clear=brief_changed,
        )

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

    latest_user_text = latest_recruiter_chat_user_text(request.messages)
    chat_text = recruiter_chat_text(request.messages)
    user_text = recruiter_chat_user_text(request.messages)
    if contains_cyrillic_text(chat_text) or contains_cyrillic_text(clean_search_brief_dict(request.draft_brief)):
        return build_recruiter_chat_response(
            ok=False,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language="en",
            validation_errors=[
                {
                    "field": "messages",
                    "message": "This POC accepts English input only.",
                }
            ],
            planner_mode=planner_mode,
        )

    prohibited_errors = detect_recruiter_chat_prohibited_requests(latest_user_text)
    if prohibited_errors:
        return build_recruiter_chat_response(
            ok=False,
            state=RECRUITER_CHAT_STATE_REFUSED,
            language=language,
            validation_errors=prohibited_errors,
            planner_mode=planner_mode,
            stale_state_should_clear=True,
        )

    if detect_recruiter_chat_reset_intent(latest_user_text):
        return build_recruiter_chat_restart_response(request, language, planner_mode)

    if is_greeting_only_chat_message(latest_user_text):
        onboarding_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_onboarding(
                request,
                language,
                recruiter_chat_onboarding_message(language),
            )
        )
        return build_recruiter_chat_onboarding_response(
            request,
            language,
            planner_mode,
            onboarding_message,
            wording_provenance,
            llm_warnings,
        )

    if is_near_empty_chat_message(latest_user_text) and not (
        request.draft_brief and latest_user_text.strip()
    ):
        onboarding_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_onboarding(
                request,
                language,
                recruiter_chat_near_empty_message(language),
            )
        )
        return build_recruiter_chat_onboarding_response(
            request,
            language,
            planner_mode,
            onboarding_message,
            wording_provenance,
            llm_warnings,
        )

    if detect_recruiter_chat_explanation_intent(latest_user_text):
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            recruiter_chat_stack_explanation_message(language),
        )

    pending_update_field = normalize_recruiter_search_brief_field(
        request.pending_update_field
    )
    if request.pending_update_field and not pending_update_field:
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            pending_update_unknown_field_message(language),
        )

    if pending_update_field:
        if not request.draft_brief:
            return build_recruiter_chat_response(
                ok=True,
                state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
                language=language,
                assistant_message=refinement_requires_initial_brief_message(language),
                planner_mode=planner_mode,
            )

        pending_update_patch, pending_update_message = (
            await pending_update_field_patch_from_message(
                pending_update_field,
                latest_user_text,
                language,
                request.draft_brief,
            )
        )
        if pending_update_patch is not None:
            return build_recruiter_chat_refinement_response(
                request,
                language,
                planner_mode,
                pending_update_patch,
                chat_text,
            )

        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            pending_update_message or pending_update_field_question(
                pending_update_field,
                language,
            ),
        )

    pending_hypothesis = extract_pending_backend_java_hypothesis(request, language)
    if pending_hypothesis:
        hypothesis_intent_request = RecruiterChatIntentRequest(
            latest_message=latest_user_text,
            language=language,
            context_type="pending_hypothesis",
            pending_hypothesis=pending_hypothesis,
            current_brief_status=(
                current_brief_validation_context(request.draft_brief)
                .get("normalized_brief")
                or {}
            ).get("brief_status"),
            current_brief=request.draft_brief,
        )
        hypothesis_decision = await classify_recruiter_chat_intent_response(
            hypothesis_intent_request
        )
        if (
            hypothesis_decision.get("intent") == RECRUITER_INTENT_RESTART
            and hypothesis_decision.get("confidence")
            in {RECRUITER_INTENT_CONFIDENCE_HIGH, RECRUITER_INTENT_CONFIDENCE_MEDIUM}
        ):
            return build_recruiter_chat_restart_response(request, language, planner_mode)
        hypothesis_intent = hypothesis_decision.get("pending_hypothesis_intent")
        hypothesis_confidence = hypothesis_decision.get("confidence")
        if hypothesis_confidence in {
            RECRUITER_INTENT_CONFIDENCE_HIGH,
            RECRUITER_INTENT_CONFIDENCE_MEDIUM,
        }:
            if hypothesis_intent == RECRUITER_HYPOTHESIS_INTENT_CONFIRM:
                return build_pending_hypothesis_confirmation_response(
                    request,
                    language,
                    planner_mode,
                    pending_hypothesis,
                )
            if hypothesis_intent in {
                RECRUITER_HYPOTHESIS_INTENT_REJECT,
                RECRUITER_HYPOTHESIS_INTENT_REFINE,
            }:
                return build_recruiter_chat_preserve_current_brief_response(
                    request,
                    language,
                    planner_mode,
                    pending_hypothesis_reject_message(language),
                )

        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            pending_hypothesis_unclear_message(language),
        )

    current_pending_field = pending_clarification_field(request, language)
    intent_request = RecruiterChatIntentRequest(
        latest_message=latest_user_text,
        language=language,
        context_type="recruiter_chat",
        pending_field=current_pending_field,
        current_brief_status=(
            current_brief_validation_context(request.draft_brief)
            .get("normalized_brief")
            or {}
        ).get("brief_status"),
        current_brief=request.draft_brief,
    )
    intent_decision = None
    if should_use_recruiter_intent_classifier(intent_request):
        intent_decision = await classify_recruiter_chat_intent_response(intent_request)

    if (
        intent_decision
        and intent_decision.get("intent") == RECRUITER_INTENT_RESTART
        and intent_decision.get("confidence")
        in {RECRUITER_INTENT_CONFIDENCE_HIGH, RECRUITER_INTENT_CONFIDENCE_MEDIUM}
    ):
        return build_recruiter_chat_restart_response(request, language, planner_mode)

    if (
        intent_decision
        and intent_decision.get("field_intent")
        == RECRUITER_FIELD_INTENT_FIELD_EXPLANATION
        and intent_decision.get("field")
        and intent_decision.get("confidence")
        in {RECRUITER_INTENT_CONFIDENCE_HIGH, RECRUITER_INTENT_CONFIDENCE_MEDIUM}
    ):
        deterministic_message = recruiter_chat_field_explanation_message(
            intent_decision["field"],
            intent_decision.get("response_language") or language,
        )
        assistant_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_conversation(
                request=request,
                language=intent_decision.get("response_language") or language,
                latest_user_text=latest_user_text,
                deterministic_message=deterministic_message,
                message_type="field_explanation",
            )
        )
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            intent_decision.get("response_language") or language,
            planner_mode,
            assistant_message,
            wording_provenance,
            llm_warnings,
        )

    if (
        intent_decision
        and current_pending_field
        and intent_decision.get("field_intent")
        in {
            RECRUITER_FIELD_INTENT_ANSWERS_DIFFERENT_FIELD,
            RECRUITER_FIELD_INTENT_REPEATS_EXISTING_VALUE,
        }
        and intent_decision.get("confidence")
        in {RECRUITER_INTENT_CONFIDENCE_HIGH, RECRUITER_INTENT_CONFIDENCE_MEDIUM}
    ):
        answered_field = intent_decision.get("answered_field") or intent_decision.get("field")
        if answered_field and answered_field != current_pending_field:
            deterministic_message = recruiter_chat_pending_field_mismatch_message(
                pending_field=current_pending_field,
                answered_field=answered_field,
                value=intent_decision.get("field_value") or latest_user_text,
                language=intent_decision.get("response_language") or language,
                repeated=(
                    intent_decision.get("field_intent")
                    == RECRUITER_FIELD_INTENT_REPEATS_EXISTING_VALUE
                ),
            )
            assistant_message, wording_provenance, llm_warnings = (
                await apply_llm_wording_to_recruiter_chat_conversation(
                    request=request,
                    language=intent_decision.get("response_language") or language,
                    latest_user_text=latest_user_text,
                    deterministic_message=deterministic_message,
                    message_type="pending_field_mismatch",
                )
            )
            return build_recruiter_chat_preserve_current_brief_response(
                request,
                intent_decision.get("response_language") or language,
                planner_mode,
                assistant_message,
                wording_provenance,
                llm_warnings,
            )

    if (
        request.draft_brief
        and current_pending_field
        and not (
            intent_decision
            and intent_decision.get("intent")
            in {RECRUITER_INTENT_SMALL_TALK, RECRUITER_INTENT_OFF_TOPIC}
        )
    ):
        pending_response = await pending_clarification_response_if_any(
            request,
            language,
            planner_mode,
            latest_user_text,
            chat_text,
        )
        if pending_response is not None:
            return pending_response

    if (
        intent_decision
        and intent_decision.get("role_domain") == RECRUITER_ROLE_DOMAIN_NON_IT
        and intent_decision.get("confidence") == RECRUITER_INTENT_CONFIDENCE_HIGH
    ):
        deterministic_message = recruiter_chat_unsupported_role_message(
            language,
            intent_decision.get("unsupported_role_label"),
        )
        assistant_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_conversation(
                request=request,
                language=language,
                latest_user_text=latest_user_text,
                deterministic_message=deterministic_message,
                message_type="unsupported_non_it_role",
            )
        )
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            assistant_message,
            wording_provenance,
            llm_warnings,
        )

    if (
        intent_decision
        and request.draft_brief
        and intent_decision.get("role_domain") == RECRUITER_ROLE_DOMAIN_IT_SOFTWARE
        and intent_decision.get("role_label")
        and not explicit_technology_signal(latest_user_text)
        and not java_stack_terms_in_text(latest_user_text)
        and not explicit_ukraine_location_signal(latest_user_text)
    ):
        role_label = normalize_freeform_label(str(intent_decision["role_label"]))
        partial_brief = {
            "source_text": chat_text,
            "brief_status": SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION,
            "role_family": role_label,
            "technology": None,
            "stack": [],
            "location": None,
            "seniority": None,
            "must_have": [],
            "nice_to_have": [],
            "exclusions": [],
            "search_depth": SEARCH_DEPTH_STANDARD,
            "profile_sources": ["linkedin_public"],
            "notes": None,
            "missing_fields": ["technology", "location", "stack"],
            "clarifying_questions": [],
            "assumptions": [],
        }
        return build_recruiter_chat_response(
            ok=True,
            state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
            language=language,
            normalized_brief=partial_brief,
            next_question=one_clarifying_question(partial_brief, language),
            planner_mode=planner_mode,
            brief_changed=True,
            stale_state_should_clear=True,
        )

    if (
        intent_decision
        and request.draft_brief
        and intent_decision.get("role_domain") == RECRUITER_ROLE_DOMAIN_IT_SOFTWARE
        and intent_decision.get("role_support_status")
        == RECRUITER_ROLE_SUPPORT_UNSUPPORTED
        and intent_decision.get("confidence")
        in {RECRUITER_INTENT_CONFIDENCE_HIGH, RECRUITER_INTENT_CONFIDENCE_MEDIUM}
    ):
        deterministic_message = recruiter_chat_unsupported_it_role_message(
            language,
            intent_decision.get("role_label") or intent_decision.get("unsupported_role_label"),
        )
        assistant_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_conversation(
                request=request,
                language=language,
                latest_user_text=latest_user_text,
                deterministic_message=deterministic_message,
                message_type="unsupported_it_role",
            )
        )
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            assistant_message,
            wording_provenance,
            llm_warnings,
        )

    if (
        intent_decision
        and request.draft_brief
        and intent_decision.get("role_support_status")
        == RECRUITER_ROLE_SUPPORT_AMBIGUOUS
        and intent_decision.get("confidence")
        in {RECRUITER_INTENT_CONFIDENCE_HIGH, RECRUITER_INTENT_CONFIDENCE_MEDIUM}
    ):
        deterministic_message = recruiter_chat_ambiguous_role_message(
            language,
            intent_decision.get("role_label"),
        )
        assistant_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_conversation(
                request=request,
                language=language,
                latest_user_text=latest_user_text,
                deterministic_message=deterministic_message,
                message_type="ambiguous_role",
            )
        )
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            assistant_message,
            wording_provenance,
            llm_warnings,
        )

    if (
        intent_decision
        and intent_decision.get("role_support_status") == RECRUITER_ROLE_SUPPORT_NOISE
        and intent_decision.get("confidence") == RECRUITER_INTENT_CONFIDENCE_HIGH
    ):
        deterministic_message = recruiter_chat_noise_role_message(language)
        assistant_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_conversation(
                request=request,
                language=language,
                latest_user_text=latest_user_text,
                deterministic_message=deterministic_message,
                message_type="noise",
            )
        )
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            assistant_message,
            wording_provenance,
            llm_warnings,
        )

    if (
        intent_decision
        and intent_decision.get("intent") == RECRUITER_INTENT_SMALL_TALK
        and intent_decision.get("confidence") in {
            RECRUITER_INTENT_CONFIDENCE_HIGH,
            RECRUITER_INTENT_CONFIDENCE_MEDIUM,
        }
    ):
        deterministic_message = recruiter_chat_small_talk_message(
            request,
            latest_user_text,
            language,
        )
        assistant_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_conversation(
                request=request,
                language=language,
                latest_user_text=latest_user_text,
                deterministic_message=deterministic_message,
                message_type="small_talk",
            )
        )
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            assistant_message,
            wording_provenance,
            llm_warnings,
        )

    if (
        intent_decision
        and intent_decision.get("intent") == RECRUITER_INTENT_OFF_TOPIC
        and intent_decision.get("confidence") in {
            RECRUITER_INTENT_CONFIDENCE_HIGH,
            RECRUITER_INTENT_CONFIDENCE_MEDIUM,
        }
    ):
        deterministic_message = recruiter_chat_off_topic_message(language)
        assistant_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_conversation(
                request=request,
                language=language,
                latest_user_text=latest_user_text,
                deterministic_message=deterministic_message,
                message_type="off_topic",
            )
        )
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            assistant_message,
            wording_provenance,
            llm_warnings,
        )

    if (
        intent_decision
        and intent_decision.get("intent") == RECRUITER_INTENT_UNCLEAR
        and intent_decision.get("confidence") == RECRUITER_INTENT_CONFIDENCE_HIGH
        and not (request.draft_brief and is_refinement_like_chat_message(latest_user_text))
    ):
        deterministic_message = recruiter_chat_unclear_request_message(language)
        assistant_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_conversation(
                request=request,
                language=language,
                latest_user_text=latest_user_text,
                deterministic_message=deterministic_message,
                message_type="unclear",
            )
        )
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            assistant_message,
            wording_provenance,
            llm_warnings,
        )

    if detect_recruiter_chat_small_talk_intent(latest_user_text):
        deterministic_message = recruiter_chat_small_talk_message(
            request,
            latest_user_text,
            language,
        )
        assistant_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_conversation(
                request=request,
                language=language,
                latest_user_text=latest_user_text,
                deterministic_message=deterministic_message,
                message_type="small_talk",
            )
        )
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            assistant_message,
            wording_provenance,
            llm_warnings,
        )

    if detect_recruiter_chat_off_topic_intent(latest_user_text):
        deterministic_message = recruiter_chat_off_topic_message(language)
        assistant_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_conversation(
                request=request,
                language=language,
                latest_user_text=latest_user_text,
                deterministic_message=deterministic_message,
                message_type="off_topic",
            )
        )
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            assistant_message,
            wording_provenance,
            llm_warnings,
        )

    if request.draft_brief:
        pending_response = await pending_clarification_response_if_any(
            request,
            language,
            planner_mode,
            latest_user_text,
            chat_text,
        )
        if pending_response is not None:
            return pending_response

    if detect_recruiter_chat_unclear_request(latest_user_text) and not (
        request.draft_brief and is_refinement_like_chat_message(latest_user_text)
    ):
        deterministic_message = recruiter_chat_unclear_request_message(language)
        assistant_message, wording_provenance, llm_warnings = (
            await apply_llm_wording_to_recruiter_chat_conversation(
                request=request,
                language=language,
                latest_user_text=latest_user_text,
                deterministic_message=deterministic_message,
                message_type="unclear",
            )
        )
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            assistant_message,
            wording_provenance,
            llm_warnings,
        )

    ambiguity = detect_recruiter_chat_ambiguity_or_contradiction(latest_user_text, language)
    if ambiguity:
        return build_recruiter_chat_preserve_current_brief_response(
            request,
            language,
            planner_mode,
            ambiguity["message"],
        )

    if not request.draft_brief:
        extractor_output, extractor_error = await run_openai_json_search_brief_extractor(
            latest_message=latest_user_text,
            language=language,
            previous_brief=None,
        )
        if extractor_error or extractor_output is None:
            return build_recruiter_chat_response(
                ok=False,
                state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
                language=language,
                validation_errors=[
                    {
                        "field": "search_brief_extractor",
                        "message": extractor_error
                        or "Search Brief extractor returned no output.",
                    }
                ],
                planner_mode=planner_mode,
            )

        extractor_validation, extractor_validation_errors = (
            validate_search_brief_extractor_output(extractor_output)
        )
        if extractor_validation_errors or extractor_validation is None:
            return build_recruiter_chat_response(
                ok=False,
                state=RECRUITER_CHAT_STATE_NEEDS_CLARIFICATION,
                language=language,
                validation_errors=extractor_validation_errors,
                planner_mode=planner_mode,
            )

        normalized_brief = extractor_validation["normalized_brief"]
        brief_changed = normalized_brief_state_payload(
            current_brief_context_for_language(request.draft_brief, language)[
                "normalized_brief"
            ]
        ) != normalized_brief_state_payload(normalized_brief)
        return await build_recruiter_chat_validated_brief_turn_response(
            request=request,
            language=language,
            planner_mode=planner_mode,
            normalized_brief=normalized_brief,
            validation_errors=[],
            latest_user_text=latest_user_text,
            user_text=user_text,
            brief_changed=brief_changed,
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
        evidence_text=user_text,
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
    brief_changed = normalized_brief_state_payload(
        current_brief_context_for_language(request.draft_brief, language)["normalized_brief"]
    ) != normalized_brief_state_payload(normalized_brief)

    return await build_recruiter_chat_validated_brief_turn_response(
        request=request,
        language=language,
        planner_mode=planner_mode,
        normalized_brief=normalized_brief,
        validation_errors=validation_errors,
        latest_user_text=latest_user_text,
        user_text=user_text,
        brief_changed=brief_changed,
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
        "approval_notice": query_plan_ready_approval_notice(),
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
        "approval_notice": query_plan_fallback_approval_notice(),
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
        "approval_notice": query_plan_rejected_approval_notice(),
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
        "approval_notice": query_plan_ai_validated_approval_notice(),
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
            "approval_notice": query_plan_rejected_approval_notice(),
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


async def run_phase9_provider_expansion(query_plan: dict) -> list[dict]:
    return await run_provider_expansion_query_plan(query_plan)


async def extend_query_results_with_phase9_providers(
    query_plan: dict,
    query_results: list[dict],
) -> list[dict]:
    try:
        provider_query_results = await run_phase9_provider_expansion(query_plan)
    except Exception:
        logger.warning("Phase 9 provider expansion failed.", exc_info=True)
        provider_query_results = []

    if not provider_query_results:
        return query_results

    return [*query_results, *provider_query_results]


def mark_multi_provider_report(
    query_plan: dict,
    report: dict,
    query_results: list[dict],
    *,
    base_mode: str,
) -> dict:
    providers = report.get("providers") or []
    provider_breakdown = report.get("provider_breakdown") or {}
    report.update(
        {
            "provider_mode": "multi_provider",
            "base_mode": base_mode,
            "mode": base_mode,
            "query_plan_queries": len(query_plan.get("queries", [])),
            "query_attempts": len(query_results),
            "queries_total": len(query_results),
            "providers": providers,
            "provider_breakdown": provider_breakdown,
            "provider_limits": {
                "serper_pages": 1,
                "serpapi_google_pages": 5,
                "serpapi_bing_pages": 5,
            },
        }
    )
    return report


def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "engineers-search-engine",
        "phase": "phase-9-5-final-poc",
    }


def validate_structured_search(request: StructuredSearchRequest) -> dict:
    normalized_request, errors = normalize_structured_search_request(request)

    if errors:
        return {"ok": False, "errors": errors}

    return {"ok": True, "normalized_request": normalized_request}


def validate_search_brief_endpoint(request: SearchBrief) -> dict:
    return search_brief_validation_response(request)


async def create_recruiter_chat_turn(request: RecruiterChatTurnRequest) -> dict:
    return await recruiter_chat_turn_response(request)


async def classify_recruiter_chat_intent(
    request: RecruiterChatIntentRequest,
) -> dict:
    if contains_cyrillic_text(request.latest_message):
        return recruiter_intent_default_response(
            intent=RECRUITER_INTENT_UNCLEAR,
            role_domain=RECRUITER_ROLE_DOMAIN_UNKNOWN,
            role_support_status=RECRUITER_ROLE_SUPPORT_UNKNOWN,
            confidence=RECRUITER_INTENT_CONFIDENCE_HIGH,
            response_language="en",
            fallback_reason="english_only",
        )
    return await classify_recruiter_chat_intent_response(request)


async def create_agent_plan(request: AgentPlanRequest) -> dict:
    return await build_agent_plan_response_with_wording(request)


def get_agent_tools() -> dict:
    return {"ok": True, "agent_tools": agent_tool_contract()}


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


def runtime_blocked_response(errors: list[dict[str, str]]) -> dict:
    return AgentRuntimeTurnResponse(
        ok=False,
        runtime_state=AGENT_RUNTIME_STATE_BLOCKED,
        errors=errors,
    ).to_dict()


def runtime_search_observations(search_response: dict) -> list[dict]:
    report = search_response.get("report") or {}
    if not isinstance(report, dict):
        return []

    return [
        {
            "type": "search_report_counts",
            "queries_total": report.get("queries_total"),
            "queries_succeeded": report.get("queries_succeeded"),
            "raw_total": report.get("raw_total"),
            "unique_profiles": report.get("unique_profiles"),
            "hidden_by_profile_filter": report.get("hidden_by_profile_filter"),
            "hidden_by_location_filter": report.get("hidden_by_location_filter"),
        }
    ]


async def execute_single_wave_structured_search_response(
    request: StructuredSearchRequest,
    query_plan: dict,
    execution_approval: dict,
) -> dict:
    query_results = await run_query_plan_wave(query_plan)
    query_results = await extend_query_results_with_phase9_providers(
        query_plan,
        query_results,
    )
    successful_queries = sum(1 for result in query_results if result["ok"])
    deduped_results, report = build_deduped_results_and_report(
        query_plan,
        query_results,
    )
    report = mark_multi_provider_report(
        query_plan,
        report,
        query_results,
        base_mode="single_wave",
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


async def execute_multi_wave_structured_search_response(
    request: MultiWaveStructuredSearchRequest,
    query_plan: dict,
    settings: dict,
    execution_approval: dict,
) -> dict:
    deduped_results, report, query_results = await run_multi_wave_query_plan(
        query_plan,
        settings,
    )
    base_multi_wave_report = report
    query_results = await extend_query_results_with_phase9_providers(
        query_plan,
        query_results,
    )
    deduped_results, report = build_deduped_results_and_report(
        query_plan,
        query_results,
        include_wave_sources=True,
    )
    report.update(
        {
            "experimental": True,
            "multi_wave_settings": settings,
            "waves_run": base_multi_wave_report.get("waves_run"),
            "planned_max_waves": base_multi_wave_report.get(
                "planned_max_waves",
                settings["max_waves"],
            ),
            "stop_reason": base_multi_wave_report.get("stop_reason"),
            "unique_profiles_per_wave": base_multi_wave_report.get(
                "unique_profiles_per_wave",
                [],
            ),
            "new_unique_profiles_per_wave": base_multi_wave_report.get(
                "new_unique_profiles_per_wave",
                [],
            ),
            "cumulative_unique_profiles": base_multi_wave_report.get(
                "cumulative_unique_profiles",
                [],
            ),
            "duplicates_across_waves": base_multi_wave_report.get(
                "duplicates_across_waves",
                0,
            ),
            "wave_reports": base_multi_wave_report.get("wave_reports", []),
        }
    )
    report = mark_multi_provider_report(
        query_plan,
        report,
        query_results,
        base_mode="multi_wave",
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


async def create_agent_runtime_turn(request: AgentRuntimeTurnRequest) -> dict:
    binding, binding_errors = normalize_runtime_execution_binding(request)
    if binding_errors:
        return runtime_blocked_response(binding_errors)

    assert binding is not None

    if request.turn_mode == AGENT_RUNTIME_TURN_MODE_PREPARE:
        if not os.getenv("TAVILY_API_KEY"):
            return runtime_blocked_response(
                [
                    runtime_error(
                        "tavily_api_key",
                        AGENT_RUNTIME_ERROR_TOOL_UNAVAILABLE,
                        runtime_tool_unavailable_source_message(),
                    )
                ]
            )

        pending_approval = runtime_pending_approval(binding.tool_call)
        return AgentRuntimeTurnResponse(
            ok=True,
            runtime_state=AGENT_RUNTIME_STATE_APPROVAL_PENDING,
            tool_calls=[binding.tool_call.to_dict()],
            pending_approvals=[pending_approval],
        ).to_dict()

    if request.turn_mode != AGENT_RUNTIME_TURN_MODE_EXECUTE_APPROVED:
        return runtime_blocked_response(
            [
                runtime_error(
                    "turn_mode",
                    AGENT_RUNTIME_ERROR_APPROVAL_MISMATCH,
                    "Unsupported runtime turn mode.",
                )
            ]
        )

    approval_errors = validate_runtime_execution_approval(
        request.runtime_approval,
        binding,
    )
    if approval_errors:
        return runtime_blocked_response(approval_errors)

    if not os.getenv("TAVILY_API_KEY"):
        return runtime_blocked_response(
            [
                runtime_error(
                    "tavily_api_key",
                    AGENT_RUNTIME_ERROR_TOOL_UNAVAILABLE,
                    runtime_tool_unavailable_source_message(),
                )
            ]
        )

    legacy_approval_request = ExecutionApproval(
        approval_status=AGENT_TOOL_APPROVAL_APPROVED,
        approved_action=binding.tool_name,
        approved_planner_mode=PLANNER_MODE_RULE_BASED,
        approved_query_count=len(binding.query_plan.get("queries", [])),
        approved_plan_fingerprint=query_plan_fingerprint(binding.query_plan),
    )
    execution_approval, legacy_approval_errors = validate_execution_approval(
        legacy_approval_request,
        binding.tool_name,
        binding.query_plan,
    )
    if legacy_approval_errors:
        return runtime_blocked_response(
            [
                runtime_error(
                    error.get("field", "execution_approval"),
                    AGENT_RUNTIME_ERROR_APPROVAL_MISMATCH,
                    error.get("message", "Search execution could not be confirmed."),
                )
                for error in legacy_approval_errors
            ]
        )

    try:
        if binding.tool_name == EXECUTION_ACTION_MULTI_WAVE:
            assert binding.settings is not None
            search_request = MultiWaveStructuredSearchRequest(
                **binding.runtime_tool_input,
                execution_approval=legacy_approval_request,
                agent_language=request.agent_language,
            )
            search_response = await execute_multi_wave_structured_search_response(
                search_request,
                binding.query_plan,
                binding.settings,
                execution_approval,
            )
        else:
            search_request = StructuredSearchRequest(
                **binding.normalized_request,
                execution_approval=legacy_approval_request,
                agent_language=request.agent_language,
            )
            search_response = await execute_single_wave_structured_search_response(
                search_request,
                binding.query_plan,
                execution_approval,
            )
    except Exception:
        logger.warning("Agent runtime execution failed.", exc_info=True)
        return AgentRuntimeTurnResponse(
            ok=False,
            runtime_state=AGENT_RUNTIME_STATE_ERROR,
            tool_calls=[binding.tool_call.to_dict()],
            tool_results=[
                AgentToolResult(
                    tool_call_id=binding.tool_call.tool_call_id,
                    tool_name=binding.tool_name,
                    ok=False,
                    errors=[
                        runtime_error(
                            "runtime_execution",
                            AGENT_RUNTIME_ERROR_EXECUTION_FAILED,
                            runtime_execution_failed_source_message(),
                        )
                    ],
                ).to_dict()
            ],
        ).to_dict()

    observations = runtime_search_observations(search_response)
    tool_result = AgentToolResult(
        tool_call_id=binding.tool_call.tool_call_id,
        tool_name=binding.tool_name,
        ok=bool(search_response.get("ok")),
        result=search_response,
        errors=search_response.get("errors", []),
        observations=observations,
    )
    return AgentRuntimeTurnResponse(
        ok=bool(search_response.get("ok")),
        runtime_state=(
            AGENT_RUNTIME_STATE_OBSERVED
            if not search_response.get("errors")
            else AGENT_RUNTIME_STATE_ERROR
        ),
        tool_calls=[binding.tool_call.to_dict()],
        tool_results=[tool_result.to_dict()],
        messages=[],
    ).to_dict()


async def create_candidate_explanation_wording(
    request: CandidateExplanationWordingRequest,
) -> dict:
    return await build_candidate_explanation_wording_response(request.model_dump())


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
                    "message": search_brief_not_ready_for_query_plan_source_message(),
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
        "approval_notice": query_plan_preview_approval_notice(),
    }


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
                    "message": runtime_tool_unavailable_source_message(),
                }
            ],
        }

    query_results = await run_query_plan_wave(query_plan)
    query_results = await extend_query_results_with_phase9_providers(
        query_plan,
        query_results,
    )

    successful_queries = sum(1 for result in query_results if result["ok"])
    deduped_results, report = build_deduped_results_and_report(
        query_plan,
        query_results,
    )
    report = mark_multi_provider_report(
        query_plan,
        report,
        query_results,
        base_mode="single_wave",
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
                    "message": runtime_tool_unavailable_source_message(),
                }
            ],
        }

    deduped_results, report, query_results = await run_multi_wave_query_plan(
        query_plan,
        settings,
    )
    base_multi_wave_report = report
    query_results = await extend_query_results_with_phase9_providers(
        query_plan,
        query_results,
    )
    deduped_results, report = build_deduped_results_and_report(
        query_plan,
        query_results,
        include_wave_sources=True,
    )
    report.update(
        {
            "experimental": True,
            "multi_wave_settings": settings,
            "waves_run": base_multi_wave_report.get("waves_run"),
            "planned_max_waves": base_multi_wave_report.get(
                "planned_max_waves",
                settings["max_waves"],
            ),
            "stop_reason": base_multi_wave_report.get("stop_reason"),
            "unique_profiles_per_wave": base_multi_wave_report.get(
                "unique_profiles_per_wave",
                [],
            ),
            "new_unique_profiles_per_wave": base_multi_wave_report.get(
                "new_unique_profiles_per_wave",
                [],
            ),
            "cumulative_unique_profiles": base_multi_wave_report.get(
                "cumulative_unique_profiles",
                [],
            ),
            "duplicates_across_waves": base_multi_wave_report.get(
                "duplicates_across_waves",
                0,
            ),
            "wave_reports": base_multi_wave_report.get("wave_reports", []),
        }
    )
    report = mark_multi_provider_report(
        query_plan,
        report,
        query_results,
        base_mode="multi_wave",
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


app.include_router(
    create_router(
        RouteDependencies(
            index=index,
            health=health,
            validate_structured_search=validate_structured_search,
            validate_search_brief_endpoint=validate_search_brief_endpoint,
            create_recruiter_chat_turn=create_recruiter_chat_turn,
            classify_recruiter_chat_intent=classify_recruiter_chat_intent,
            create_agent_plan=create_agent_plan,
            get_agent_tools=get_agent_tools,
            create_query_plan=create_query_plan,
            create_agent_query_plan=create_agent_query_plan,
            create_agent_runtime_turn=create_agent_runtime_turn,
            create_candidate_explanation_wording=create_candidate_explanation_wording,
            validate_ai_query_plan_endpoint=validate_ai_query_plan_endpoint,
            structured_search=structured_search,
            structured_search_multi_wave=structured_search_multi_wave,
            search=search,
        ),
        STATIC_DIR,
    )
)
