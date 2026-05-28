import json
import os
import re

import httpx

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
    build_brief_patch,
)
from app.domain_config import SEARCH_DEPTH_DEEP, SEARCH_DEPTH_STANDARD
from app.search_brief_extractor import looks_like_domain_context
from app.search_validation import (
    normalize_role_family_value,
    normalize_search_location_value,
    normalize_stack_item_value,
    normalize_technology_value,
)
from app.text_utils import compact_spaces, contains_cyrillic_text, normalize_text_list, normalize_text_value


SEARCH_BRIEF_REFINEMENT_PROMPT_VERSION = "search_brief_refinement_v2"
SEARCH_BRIEF_REFINEMENT_VALIDATOR_VERSION = "search_brief_refinement_validator_v1"
SEARCH_BRIEF_REFINEMENT_MAX_COMPLETION_TOKENS = 700
SEARCH_BRIEF_REFINEMENT_TIMEOUT_SECONDS = 20
DEFAULT_OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

REFINEMENT_INTENT_PATCH = "patch"
REFINEMENT_INTENT_CLARIFY = "clarify"
REFINEMENT_INTENT_NOOP = "noop"
REFINEMENT_INTENT_UNSAFE = "unsafe"
REFINEMENT_INTENT_UNCLEAR = "unclear"
REFINEMENT_INTENTS = {
    REFINEMENT_INTENT_PATCH,
    REFINEMENT_INTENT_CLARIFY,
    REFINEMENT_INTENT_NOOP,
    REFINEMENT_INTENT_UNSAFE,
    REFINEMENT_INTENT_UNCLEAR,
}

REFINEMENT_CONFIDENCE_HIGH = "high"
REFINEMENT_CONFIDENCE_MEDIUM = "medium"
REFINEMENT_CONFIDENCE_LOW = "low"
REFINEMENT_CONFIDENCES = {
    REFINEMENT_CONFIDENCE_HIGH,
    REFINEMENT_CONFIDENCE_MEDIUM,
    REFINEMENT_CONFIDENCE_LOW,
}

REFINEMENT_ALLOWED_TOP_LEVEL_KEYS = {
    "schema_version",
    "intent",
    "operations",
    "confidence",
    "reason_codes",
}
REFINEMENT_ALLOWED_OPERATION_KEYS = {"operation", "field", "value", "values"}
REFINEMENT_ALLOWED_OPERATIONS = {
    BRIEF_PATCH_ADD_STACK,
    BRIEF_PATCH_REMOVE_STACK,
    BRIEF_PATCH_REPLACE_STACK,
    BRIEF_PATCH_SET_LOCATION,
    BRIEF_PATCH_RECONFIRM_FIELD,
    BRIEF_PATCH_SET_SENIORITY,
    BRIEF_PATCH_SET_SEARCH_DEPTH,
    BRIEF_PATCH_ADD_MUST_HAVE,
    BRIEF_PATCH_REMOVE_MUST_HAVE,
    BRIEF_PATCH_REPLACE_MUST_HAVE,
    BRIEF_PATCH_NOOP,
}
SAFE_REASON_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def search_brief_refinement_system_prompt() -> str:
    return (
        "You interpret a recruiter's refinement message for an existing Search Brief. "
        "Return strict JSON only. You may classify the requested Search Brief change "
        "and extract bounded values. You must not generate queries, search, browse, "
        "access LinkedIn, scrape, approve execution, message candidates, perform "
        "account actions, or persist data."
    )


def search_brief_refinement_user_prompt(
    *,
    latest_message: str,
    language: str,
    current_brief: dict | None,
) -> str:
    return json.dumps(
        {
            "task": "Interpret the latest recruiter message as a safe patch for the existing Search Brief.",
            "required_output": {
                "schema_version": SEARCH_BRIEF_REFINEMENT_PROMPT_VERSION,
                "intent": "patch | clarify | noop | unsafe | unclear",
                "operations": [
                    {
                        "operation": (
                            "add_stack | remove_stack | replace_stack | set_location | "
                            "reconfirm_field | set_seniority | set_search_depth | "
                            "add_must_have | remove_must_have | replace_must_have | noop"
                        ),
                        "field": (
                            "stack | location | role_family | technology | seniority | "
                            "search_depth | must_have"
                        ),
                        "value": "single safe value when needed",
                        "values": ["safe values when operation replaces a list"],
                    }
                ],
                "confidence": "high | medium | low",
                "reason_codes": ["short_snake_case"],
            },
            "latest_message": latest_message,
            "language": language,
            "current_brief": current_brief or {},
            "semantic_rules": [
                "Use patch only when the recruiter asked to change the existing Search Brief.",
                "For 'Java only' or 'use only Java', replace stack with Java unless the message explicitly says main technology.",
                "For 'change location to Canada' or 'make it remote', set location.",
                "For 'I meant QA, not developer', update role_family if the new role is clear.",
                "For domain/business context such as banking or fintech, use must_have operations, not technology or stack.",
                "For technical tools/frameworks/languages/platforms, use stack or technology as appropriate.",
                "Do not invent missing values.",
                "Return unclear or clarify when the requested change is ambiguous.",
                "Use unsafe for URLs, credentials, LinkedIn/account actions, scraping, outreach, or bypass instructions.",
            ],
            "hard_boundaries": [
                "No query generation.",
                "No provider calls.",
                "No direct web-search bypass.",
                "No LinkedIn login, scraping, profile automation, or restriction bypass.",
                "No candidate messaging.",
                "No user or third-party account actions.",
                "No search approval.",
                "No persistence.",
            ],
            "prompt_version": SEARCH_BRIEF_REFINEMENT_PROMPT_VERSION,
        },
        ensure_ascii=False,
        indent=2,
    )


def search_brief_refinement_openai_payload(
    *,
    model: str,
    latest_message: str,
    language: str = "en",
    current_brief: dict | None = None,
) -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": search_brief_refinement_system_prompt()},
            {
                "role": "user",
                "content": search_brief_refinement_user_prompt(
                    latest_message=latest_message,
                    language=language,
                    current_brief=current_brief,
                ),
            },
        ],
        "temperature": 0,
        "max_completion_tokens": SEARCH_BRIEF_REFINEMENT_MAX_COMPLETION_TOKENS,
        "response_format": {"type": "json_object"},
    }


async def run_openai_json_search_brief_refinement_interpreter(
    *,
    latest_message: str,
    language: str = "en",
    current_brief: dict | None = None,
    chat_completions_url: str | None = None,
) -> tuple[dict | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return None, "openai_not_configured"

    payload = search_brief_refinement_openai_payload(
        model=model,
        latest_message=latest_message,
        language=language,
        current_brief=current_brief,
    )

    try:
        async with httpx.AsyncClient(timeout=SEARCH_BRIEF_REFINEMENT_TIMEOUT_SECONDS) as client:
            response = await client.post(
                os.getenv(
                    "OPENAI_CHAT_COMPLETIONS_URL",
                    chat_completions_url or DEFAULT_OPENAI_CHAT_COMPLETIONS_URL,
                ),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        return None, "openai_search_brief_refinement_timeout"
    except httpx.HTTPStatusError as exc:
        return None, f"openai_search_brief_refinement_http_{exc.response.status_code}"
    except httpx.HTTPError:
        return None, "openai_search_brief_refinement_request_failed"

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        return None, "openai_search_brief_refinement_empty_content"

    try:
        parsed_content = json.loads(content)
    except json.JSONDecodeError:
        return None, "openai_search_brief_refinement_invalid_json"
    if not isinstance(parsed_content, dict):
        return None, "openai_search_brief_refinement_wrong_shape"

    return parsed_content, None


def safe_refinement_text_value(value: object, max_length: int = 120) -> str | None:
    if value is not None and not isinstance(value, str):
        return None
    text = normalize_text_value(value)
    if not text:
        return None
    text = compact_spaces(text).strip(" .,:;\"'")
    if not text or len(text) > max_length:
        return None
    if contains_cyrillic_text(text):
        return None
    if re.search(r"https?://|www\.|@|<|>|`|{|}|\[|\]", text, flags=re.IGNORECASE):
        return None
    return text


def normalize_refinement_must_have_value(value: object) -> tuple[str | None, str | None]:
    text = safe_refinement_text_value(value, max_length=120)
    if not text:
        return None, "search_brief_refinement_invalid_must_have"
    return text, None


def _raw_values(operation: dict, *, prefer_value: bool = False) -> list[object] | None:
    if prefer_value and "value" in operation:
        return [operation.get("value")]
    values = operation.get("values")
    if values is None and "value" in operation:
        values = [operation.get("value")]
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    if isinstance(values, list):
        return values
    return None


def _normalize_stack_values(values: list[object]) -> tuple[list[str], str | None]:
    normalized_values: list[str] = []
    for value in values:
        text = safe_refinement_text_value(value, max_length=80)
        if not text or looks_like_domain_context(text):
            return [], "search_brief_refinement_invalid_stack"
        stack_item, errors = normalize_stack_item_value(text)
        if errors or not stack_item:
            return [], "search_brief_refinement_invalid_stack"
        if stack_item not in normalized_values:
            normalized_values.append(stack_item)
    if not normalized_values:
        return [], "search_brief_refinement_missing_stack"
    if len(normalized_values) > 3:
        return [], "search_brief_refinement_too_many_stack_values"
    return normalized_values, None


def _normalize_must_have_values(values: list[object]) -> tuple[list[str], str | None]:
    normalized_values: list[str] = []
    for value in values:
        must_have, error = normalize_refinement_must_have_value(value)
        if error or not must_have:
            return [], error or "search_brief_refinement_invalid_must_have"
        if must_have.lower() not in {existing.lower() for existing in normalized_values}:
            normalized_values.append(must_have)
    if not normalized_values:
        return [], "search_brief_refinement_missing_must_have"
    if len(normalized_values) > 6:
        return [], "search_brief_refinement_too_many_must_have_values"
    return normalized_values, None


def _normalize_seniority_value(value: object) -> tuple[str | None, str | None]:
    text = (safe_refinement_text_value(value, max_length=40) or "").lower()
    aliases = {
        "jr": "Junior",
        "junior": "Junior",
        "middle": "Middle",
        "mid": "Middle",
        "senior": "Senior",
        "sr": "Senior",
        "lead": "Lead",
        "staff": "Staff",
        "principal": "Principal",
    }
    seniority = aliases.get(text)
    if not seniority:
        return None, "search_brief_refinement_invalid_seniority"
    return seniority, None


def _normalize_search_depth_value(value: object) -> tuple[str | None, str | None]:
    text = (safe_refinement_text_value(value, max_length=40) or "").lower()
    if text in {"standard", "normal", "default"}:
        return SEARCH_DEPTH_STANDARD, None
    if text in {"deep", "deeper", "expanded"}:
        return SEARCH_DEPTH_DEEP, None
    return None, "search_brief_refinement_invalid_search_depth"


def _normalize_reason_codes(value: object) -> list[str]:
    raw_codes = normalize_text_list(value)
    reason_codes: list[str] = []
    for raw_code in raw_codes[:5]:
        code = raw_code.lower().replace("-", "_").replace(" ", "_")
        if SAFE_REASON_CODE_PATTERN.match(code) and code not in reason_codes:
            reason_codes.append(code)
    return reason_codes or ["validated"]


def _validate_operation(operation: object) -> tuple[dict | None, str | None]:
    if not isinstance(operation, dict):
        return None, "search_brief_refinement_operation_wrong_shape"
    unknown_keys = set(operation) - REFINEMENT_ALLOWED_OPERATION_KEYS
    if unknown_keys:
        return None, "search_brief_refinement_operation_unknown_fields"

    operation_name = safe_refinement_text_value(operation.get("operation"), max_length=48)
    if operation_name not in REFINEMENT_ALLOWED_OPERATIONS:
        return None, "search_brief_refinement_unknown_operation"

    field = safe_refinement_text_value(operation.get("field"), max_length=48)
    if field:
        field = field.lower().replace("-", "_").replace(" ", "_")

    if operation_name == BRIEF_PATCH_NOOP:
        return {"operation": BRIEF_PATCH_NOOP, "field": field or "search_brief"}, None

    if operation_name in {
        BRIEF_PATCH_ADD_STACK,
        BRIEF_PATCH_REMOVE_STACK,
    }:
        if field != "stack":
            return None, "search_brief_refinement_field_mismatch"
        values = _raw_values(operation, prefer_value=True)
        if values is None:
            return None, "search_brief_refinement_values_wrong_shape"
        stack_values, error = _normalize_stack_values(values)
        if error:
            return None, error
        return {
            "operation": operation_name,
            "field": "stack",
            "value": stack_values[0],
        }, None

    if operation_name == BRIEF_PATCH_REPLACE_STACK:
        if field != "stack":
            return None, "search_brief_refinement_field_mismatch"
        values = _raw_values(operation)
        if values is None:
            return None, "search_brief_refinement_values_wrong_shape"
        stack_values, error = _normalize_stack_values(values)
        if error:
            return None, error
        return {
            "operation": BRIEF_PATCH_REPLACE_STACK,
            "field": "stack",
            "values": stack_values,
        }, None

    if operation_name == BRIEF_PATCH_SET_LOCATION:
        if field != "location":
            return None, "search_brief_refinement_field_mismatch"
        text = safe_refinement_text_value(operation.get("value"), max_length=80)
        location, errors = normalize_search_location_value(text)
        if errors or not location:
            return None, "search_brief_refinement_invalid_location"
        return {
            "operation": BRIEF_PATCH_SET_LOCATION,
            "field": "location",
            "value": location,
        }, None

    if operation_name == BRIEF_PATCH_RECONFIRM_FIELD:
        if field == "role_family":
            text = safe_refinement_text_value(operation.get("value"), max_length=80)
            value, errors = normalize_role_family_value(text)
            if errors or not value:
                return None, "search_brief_refinement_invalid_role"
            return {
                "operation": BRIEF_PATCH_RECONFIRM_FIELD,
                "field": "role_family",
                "value": value,
            }, None
        if field == "technology":
            text = safe_refinement_text_value(operation.get("value"), max_length=40)
            if looks_like_domain_context(text):
                return None, "search_brief_refinement_technology_is_domain"
            value, errors = normalize_technology_value(text)
            if errors or not value:
                return None, "search_brief_refinement_invalid_technology"
            return {
                "operation": BRIEF_PATCH_RECONFIRM_FIELD,
                "field": "technology",
                "value": value,
            }, None
        return None, "search_brief_refinement_field_mismatch"

    if operation_name == BRIEF_PATCH_SET_SENIORITY:
        if field != "seniority":
            return None, "search_brief_refinement_field_mismatch"
        value, error = _normalize_seniority_value(operation.get("value"))
        if error:
            return None, error
        return {
            "operation": BRIEF_PATCH_SET_SENIORITY,
            "field": "seniority",
            "value": value,
        }, None

    if operation_name == BRIEF_PATCH_SET_SEARCH_DEPTH:
        if field != "search_depth":
            return None, "search_brief_refinement_field_mismatch"
        value, error = _normalize_search_depth_value(operation.get("value"))
        if error:
            return None, error
        return {
            "operation": BRIEF_PATCH_SET_SEARCH_DEPTH,
            "field": "search_depth",
            "value": value,
        }, None

    if operation_name in {
        BRIEF_PATCH_ADD_MUST_HAVE,
        BRIEF_PATCH_REMOVE_MUST_HAVE,
    }:
        if field != "must_have":
            return None, "search_brief_refinement_field_mismatch"
        values = _raw_values(operation, prefer_value=True)
        if values is None:
            return None, "search_brief_refinement_values_wrong_shape"
        must_have_values, error = _normalize_must_have_values(values)
        if error:
            return None, error
        return {
            "operation": operation_name,
            "field": "must_have",
            "value": must_have_values[0],
        }, None

    if operation_name == BRIEF_PATCH_REPLACE_MUST_HAVE:
        if field != "must_have":
            return None, "search_brief_refinement_field_mismatch"
        values = _raw_values(operation)
        if values is None:
            return None, "search_brief_refinement_values_wrong_shape"
        must_have_values, error = _normalize_must_have_values(values)
        if error:
            return None, error
        return {
            "operation": BRIEF_PATCH_REPLACE_MUST_HAVE,
            "field": "must_have",
            "values": must_have_values,
        }, None

    return None, "search_brief_refinement_unknown_operation"


def validate_search_brief_refinement_output(
    llm_output: dict | None,
    *,
    source_message: str,
) -> tuple[dict | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    if not isinstance(llm_output, dict):
        return None, [
            {
                "field": "search_brief_refinement",
                "message": "Refinement interpreter output must be an object.",
            }
        ]

    unknown_keys = set(llm_output) - REFINEMENT_ALLOWED_TOP_LEVEL_KEYS
    if unknown_keys:
        errors.append(
            {
                "field": "search_brief_refinement",
                "message": "Refinement interpreter output contains unsupported fields.",
            }
        )

    schema_version = safe_refinement_text_value(
        llm_output.get("schema_version"),
        max_length=80,
    )
    if schema_version != SEARCH_BRIEF_REFINEMENT_PROMPT_VERSION:
        errors.append(
            {
                "field": "schema_version",
                "message": "Unsupported refinement interpreter schema version.",
            }
        )

    intent = safe_refinement_text_value(llm_output.get("intent"), max_length=40)
    if intent not in REFINEMENT_INTENTS:
        errors.append(
            {
                "field": "intent",
                "message": "Unsupported refinement intent.",
            }
        )

    confidence = safe_refinement_text_value(llm_output.get("confidence"), max_length=24)
    if confidence not in REFINEMENT_CONFIDENCES:
        errors.append(
            {
                "field": "confidence",
                "message": "Unsupported refinement confidence.",
            }
        )
    elif confidence == REFINEMENT_CONFIDENCE_LOW:
        errors.append(
            {
                "field": "confidence",
                "message": "Refinement confidence is too low.",
            }
        )

    raw_operations = llm_output.get("operations") or []
    if not isinstance(raw_operations, list):
        errors.append(
            {
                "field": "operations",
                "message": "Refinement operations must be a list.",
            }
        )
        raw_operations = []

    operations: list[dict] = []
    for raw_operation in raw_operations:
        operation, error = _validate_operation(raw_operation)
        if error:
            errors.append(
                {
                    "field": "operations",
                    "message": error,
                }
            )
            continue
        if operation:
            operations.append(operation)

    if errors:
        return None, errors

    if intent == REFINEMENT_INTENT_PATCH and not operations:
        return None, [
            {
                "field": "operations",
                "message": "Patch intent requires at least one operation.",
            }
        ]
    if intent != REFINEMENT_INTENT_PATCH and operations:
        return None, [
            {
                "field": "operations",
                "message": "Only patch intent may include operations.",
            }
        ]

    requires_clarification = intent in {
        REFINEMENT_INTENT_CLARIFY,
        REFINEMENT_INTENT_UNSAFE,
        REFINEMENT_INTENT_UNCLEAR,
    }
    patch = build_brief_patch(
        source_message=source_message,
        operations=operations,
        requires_clarification=requires_clarification,
    )
    return {
        "validator_version": SEARCH_BRIEF_REFINEMENT_VALIDATOR_VERSION,
        "schema_version": schema_version,
        "intent": intent,
        "patch": patch,
        "confidence": confidence,
        "reason_codes": _normalize_reason_codes(llm_output.get("reason_codes")),
    }, []
