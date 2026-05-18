import hashlib
import json

from app.domain_config import (
    CANONICAL_ROLE_FAMILIES,
    IMPLEMENTED_BACKEND_TECHNOLOGIES,
    JAVA_STACK_VALUES,
    KNOWN_BACKEND_TECHNOLOGIES,
    PROFILE_SOURCE_LINKEDIN_PUBLIC,
    PROFILE_SOURCE_VALUES,
    SEARCH_BRIEF_STATUSES,
    SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION,
    SEARCH_BRIEF_STATUS_READY_FOR_PLANNING,
    SEARCH_DEPTH_STANDARD,
    SEARCH_DEPTH_VALUES,
    location_filter_config_for,
)
from app.schemas import SearchBrief, StructuredSearchRequest
from app.search_validation import (
    add_validation_error,
    canonical_value,
    normalize_location_value,
    normalize_structured_search_request,
)
from app.text_utils import normalize_text_list, normalize_text_value


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
        search_depth=normalized_brief.get("search_depth") or SEARCH_DEPTH_STANDARD,
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
