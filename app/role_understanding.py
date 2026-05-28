import json
import os
import re

import httpx

from app.search_validation import (
    add_validation_error,
    looks_like_non_it_role,
    normalize_role_family_value,
)
from app.text_utils import (
    compact_spaces,
    contains_cyrillic_text,
    normalize_text_list,
    normalize_text_value,
)


ROLE_UNDERSTANDING_RESOLVER_VERSION = "role_understanding_resolver_v1"
ROLE_UNDERSTANDING_MAX_COMPLETION_TOKENS = 500
ROLE_UNDERSTANDING_TIMEOUT_SECONDS = 25
DEFAULT_OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

ROLE_DOMAIN_IT_SOFTWARE = "it_software"
ROLE_DOMAIN_IT_ADJACENT = "it_adjacent"
ROLE_DOMAIN_NON_IT = "non_it"
ROLE_DOMAIN_AMBIGUOUS = "ambiguous"
ROLE_DOMAIN_UNKNOWN = "unknown"
ROLE_UNDERSTANDING_DOMAINS = {
    ROLE_DOMAIN_IT_SOFTWARE,
    ROLE_DOMAIN_IT_ADJACENT,
    ROLE_DOMAIN_NON_IT,
    ROLE_DOMAIN_AMBIGUOUS,
    ROLE_DOMAIN_UNKNOWN,
}

ROLE_SUPPORT_SUPPORTED = "supported"
ROLE_SUPPORT_NEEDS_CLARIFICATION = "needs_clarification"
ROLE_SUPPORT_REJECTED = "rejected"
ROLE_UNDERSTANDING_SUPPORT_STATUSES = {
    ROLE_SUPPORT_SUPPORTED,
    ROLE_SUPPORT_NEEDS_CLARIFICATION,
    ROLE_SUPPORT_REJECTED,
}

ROLE_UNDERSTANDING_CONFIDENCE_HIGH = "high"
ROLE_UNDERSTANDING_CONFIDENCE_MEDIUM = "medium"
ROLE_UNDERSTANDING_CONFIDENCE_LOW = "low"
ROLE_UNDERSTANDING_CONFIDENCES = {
    ROLE_UNDERSTANDING_CONFIDENCE_HIGH,
    ROLE_UNDERSTANDING_CONFIDENCE_MEDIUM,
    ROLE_UNDERSTANDING_CONFIDENCE_LOW,
}

ROLE_UNDERSTANDING_ALLOWED_TOP_LEVEL_KEYS = {
    "schema_version",
    "role_label",
    "role_domain",
    "support_status",
    "confidence",
    "evidence",
    "clarification_question",
    "reason_code",
}
SAFE_REASON_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
SAFE_ROLE_TEXT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+#./&() _-]*$")

IT_ADJACENT_ROLE_PATTERNS = [
    r"\bproject manager\b",
    r"\bprogram manager\b",
    r"\bproduct manager\b",
    r"\bproduct owner\b",
    r"\bscrum master\b",
    r"\bagile coach\b",
    r"\bdelivery manager\b",
    r"\bbusiness analyst\b",
    r"\bsystems analyst\b",
    r"\bfunctional analyst\b",
]
GENERIC_ROLE_LABELS = {
    "it",
    "it role",
    "it/software role",
    "software",
    "software role",
    "technology role",
    "manager",
    "analyst",
}
IT_ADJACENT_SUPPORT_SIGNAL_PATTERNS = [
    r"\bit\b",
    r"\bsoftware\b",
    r"\btechnical\b",
    r"\btechnology\b",
    r"\bengineering\b",
    r"\bdata\b",
    r"\banalytics?\b",
    r"\bcloud\b",
    r"\bapi\b",
    r"\bsql\b",
    r"\bexcel\b",
    r"\bpower\s*bi\b",
    r"\btableau\b",
    r"\bsalesforce\b",
    r"\bjira\b",
    r"\bconfluence\b",
    r"\bagile\b",
    r"\bscrum\b",
    r"\bkanban\b",
    r"\bdevops\b",
    r"\bqa\b",
    r"\btesting\b",
    r"\bautomation\b",
    r"\bcrm\b",
    r"\berp\b",
]


def role_understanding_system_prompt() -> str:
    return (
        "You classify the recruiter-request role scope for a bounded sourcing "
        "assistant. Return strict JSON only. You may interpret role meaning, but "
        "you must not build Search Briefs, mutate fields, generate queries, browse, "
        "call providers, access LinkedIn, scrape, automate profiles, message "
        "candidates, approve searches, perform account actions, or persist data."
    )


def role_understanding_user_prompt(
    *,
    latest_message: str,
    language: str,
    extracted_role_family: str | None = None,
    extracted_technology: str | None = None,
    extracted_stack: list[str] | None = None,
    extracted_domain_experience: list[str] | None = None,
) -> str:
    return json.dumps(
        {
            "task": (
                "Classify whether the role in the latest clean-state recruiter "
                "message is an IT/software role, an IT-adjacent recruiter role, "
                "non-IT, or needs role-scope clarification."
            ),
            "required_output": {
                "schema_version": ROLE_UNDERSTANDING_RESOLVER_VERSION,
                "role_label": "concrete role label from the message, or null",
                "role_domain": (
                    "it_software | it_adjacent | non_it | ambiguous | unknown"
                ),
                "support_status": "supported | needs_clarification | rejected",
                "confidence": "high | medium | low",
                "evidence": ["short evidence copied or paraphrased from latest_message only"],
                "clarification_question": "one short question or null",
                "reason_code": "short_snake_case",
            },
            "latest_message": latest_message,
            "language": language,
            "extractor_hints": {
                "role_family": extracted_role_family,
                "technology": extracted_technology,
                "stack": extracted_stack or [],
                "domain_experience": extracted_domain_experience or [],
            },
            "classification_rules": [
                "Developer, engineer, QA, DevOps, data, security, cloud, design, product, and analyst roles with explicit software/data/technical context are supported IT/software roles.",
                "Project Manager, Program Manager, Product Manager, Product Owner, Scrum Master, Delivery Manager, and Business Analyst can be supported as IT-adjacent only when the latest message contains IT/software/data/technical/tool/work-skill evidence.",
                "A generic Project Manager request without IT/software/data/technical/tool/work-skill evidence should need clarification.",
                "Clearly non-IT professions should be rejected even if the message mentions a tool such as Excel.",
                "Use evidence from latest_message only. Extractor hints are context, not proof.",
                "Do not invent missing role or technical context.",
            ],
            "hard_boundaries": [
                "No Search Brief mutation.",
                "No query generation.",
                "No Tavily, Serper, SerpApi, or provider calls.",
                "No direct web-search bypass.",
                "No LinkedIn login.",
                "No LinkedIn scraping, profile automation, or restriction bypass.",
                "No candidate messaging or outreach.",
                "No user or third-party account actions.",
                "No search approval.",
                "No persistence.",
            ],
            "resolver_version": ROLE_UNDERSTANDING_RESOLVER_VERSION,
        },
        ensure_ascii=False,
        indent=2,
    )


def role_understanding_openai_payload(
    *,
    model: str,
    latest_message: str,
    language: str = "en",
    extracted_role_family: str | None = None,
    extracted_technology: str | None = None,
    extracted_stack: list[str] | None = None,
    extracted_domain_experience: list[str] | None = None,
) -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": role_understanding_system_prompt()},
            {
                "role": "user",
                "content": role_understanding_user_prompt(
                    latest_message=latest_message,
                    language=language,
                    extracted_role_family=extracted_role_family,
                    extracted_technology=extracted_technology,
                    extracted_stack=extracted_stack,
                    extracted_domain_experience=extracted_domain_experience,
                ),
            },
        ],
        "temperature": 0,
        "max_completion_tokens": ROLE_UNDERSTANDING_MAX_COMPLETION_TOKENS,
        "response_format": {"type": "json_object"},
    }


async def run_openai_json_role_understanding(
    *,
    latest_message: str,
    language: str = "en",
    extracted_role_family: str | None = None,
    extracted_technology: str | None = None,
    extracted_stack: list[str] | None = None,
    extracted_domain_experience: list[str] | None = None,
    chat_completions_url: str | None = None,
) -> tuple[dict | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return None, "openai_not_configured"

    payload = role_understanding_openai_payload(
        model=model,
        latest_message=latest_message,
        language=language,
        extracted_role_family=extracted_role_family,
        extracted_technology=extracted_technology,
        extracted_stack=extracted_stack,
        extracted_domain_experience=extracted_domain_experience,
    )

    try:
        async with httpx.AsyncClient(timeout=ROLE_UNDERSTANDING_TIMEOUT_SECONDS) as client:
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
        return None, "openai_role_understanding_timeout"
    except httpx.HTTPStatusError as exc:
        return None, f"openai_role_understanding_http_{exc.response.status_code}"
    except httpx.HTTPError:
        return None, "openai_role_understanding_request_failed"

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        return None, "openai_role_understanding_empty_content"

    try:
        parsed_content = json.loads(content)
    except json.JSONDecodeError:
        return None, "openai_role_understanding_invalid_json"
    if not isinstance(parsed_content, dict):
        return None, "openai_role_understanding_wrong_shape"

    return parsed_content, None


def safe_role_understanding_text_value(value: object, max_length: int = 120) -> str | None:
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


def safe_role_understanding_text_list(
    value: object,
    *,
    max_items: int = 4,
    item_max_length: int = 120,
) -> tuple[list[str], str | None]:
    if value is None:
        return [], None
    if not isinstance(value, list):
        return [], "role_understanding_list_wrong_shape"

    values: list[str] = []
    for raw_item in value:
        safe_item = safe_role_understanding_text_value(
            raw_item,
            max_length=item_max_length,
        )
        if not safe_item:
            return [], "role_understanding_unsafe_value"
        if safe_item not in values:
            values.append(safe_item)
    if len(values) > max_items:
        return [], "role_understanding_too_many_values"
    return values, None


def normalize_role_understanding_reason_code(value: object) -> str:
    raw_code = safe_role_understanding_text_value(value, max_length=64)
    if not raw_code:
        return "validated"
    code = raw_code.lower().replace("-", "_").replace(" ", "_")
    return code if SAFE_REASON_CODE_PATTERN.match(code) else "validated"


def source_contains_role_phrase(source_text: object, role_label: object) -> bool:
    source = normalize_text_value(source_text).lower()
    role = normalize_text_value(role_label).lower()
    if not source or not role:
        return False
    role_tokens = re.findall(r"[a-z0-9]+", role)
    if not role_tokens:
        return False
    return all(re.search(rf"\b{re.escape(token)}\b", source) for token in role_tokens)


def source_has_it_adjacent_role(source_text: object) -> bool:
    source = normalize_text_value(source_text)
    if not source:
        return False
    return any(
        re.search(pattern, source, flags=re.IGNORECASE)
        for pattern in IT_ADJACENT_ROLE_PATTERNS
    )


def role_label_is_it_adjacent(role_label: object) -> bool:
    role = normalize_text_value(role_label)
    if not role:
        return False
    return any(
        re.search(pattern, role, flags=re.IGNORECASE)
        for pattern in IT_ADJACENT_ROLE_PATTERNS
    )


def source_has_it_adjacent_support_signal(source_text: object) -> bool:
    source = normalize_text_value(source_text)
    if not source:
        return False
    return any(
        re.search(pattern, source, flags=re.IGNORECASE)
        for pattern in IT_ADJACENT_SUPPORT_SIGNAL_PATTERNS
    )


def extracted_role_family_from_output(extractor_output: dict | None) -> str | None:
    if not isinstance(extractor_output, dict):
        return None
    draft = extractor_output.get("draft_brief")
    if not isinstance(draft, dict):
        return None
    return normalize_text_value(draft.get("role_family")) or None


def should_run_role_understanding_resolver(
    extractor_output: dict | None,
    *,
    latest_message: str | None = None,
) -> bool:
    if not isinstance(extractor_output, dict):
        return False
    draft = extractor_output.get("draft_brief")
    if not isinstance(draft, dict):
        return False

    source_text = normalize_text_value(latest_message) or normalize_text_value(
        draft.get("source_text")
    )
    raw_role = normalize_text_value(draft.get("role_family")) or ""
    raw_role_key = raw_role.lower()

    if source_text and looks_like_non_it_role(source_text):
        return True
    if raw_role and looks_like_non_it_role(raw_role):
        return True
    if raw_role_key in GENERIC_ROLE_LABELS and source_has_it_adjacent_role(source_text):
        return True
    if source_has_it_adjacent_role(source_text) or role_label_is_it_adjacent(raw_role):
        return True

    if raw_role:
        _, role_errors = normalize_role_family_value(raw_role)
        return bool(role_errors)
    return False


def validate_role_understanding_output(
    llm_output: dict | None,
    *,
    latest_message: str,
) -> tuple[dict | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    if not isinstance(llm_output, dict):
        add_validation_error(errors, "role_understanding", "Role understanding output must be an object.")
        return None, errors

    unknown_keys = set(llm_output) - ROLE_UNDERSTANDING_ALLOWED_TOP_LEVEL_KEYS
    if unknown_keys:
        add_validation_error(errors, "role_understanding", "Role understanding contains unsupported fields.")

    schema_version = safe_role_understanding_text_value(
        llm_output.get("schema_version"),
        max_length=80,
    )
    if schema_version != ROLE_UNDERSTANDING_RESOLVER_VERSION:
        add_validation_error(errors, "schema_version", "Unsupported role understanding schema version.")

    role_domain = safe_role_understanding_text_value(
        llm_output.get("role_domain"),
        max_length=32,
    )
    if role_domain not in ROLE_UNDERSTANDING_DOMAINS:
        add_validation_error(errors, "role_domain", "Unsupported role domain.")

    support_status = safe_role_understanding_text_value(
        llm_output.get("support_status"),
        max_length=32,
    )
    if support_status not in ROLE_UNDERSTANDING_SUPPORT_STATUSES:
        add_validation_error(errors, "support_status", "Unsupported role support status.")

    confidence = safe_role_understanding_text_value(
        llm_output.get("confidence"),
        max_length=24,
    )
    if confidence not in ROLE_UNDERSTANDING_CONFIDENCES:
        add_validation_error(errors, "confidence", "Unsupported role understanding confidence.")
    elif confidence == ROLE_UNDERSTANDING_CONFIDENCE_LOW:
        add_validation_error(errors, "confidence", "Role understanding confidence is too low.")

    role_label = safe_role_understanding_text_value(
        llm_output.get("role_label"),
        max_length=80,
    )
    if llm_output.get("role_label") is not None and not role_label:
        add_validation_error(errors, "role_label", "Role label is unsafe.")

    evidence, evidence_error = safe_role_understanding_text_list(
        llm_output.get("evidence"),
        max_items=4,
        item_max_length=120,
    )
    if evidence_error:
        add_validation_error(errors, "evidence", "Role evidence is invalid.")

    clarification_question = safe_role_understanding_text_value(
        llm_output.get("clarification_question"),
        max_length=160,
    )
    reason_code = normalize_role_understanding_reason_code(llm_output.get("reason_code"))

    if role_label and not SAFE_ROLE_TEXT_PATTERN.match(role_label):
        add_validation_error(errors, "role_label", "Role label contains unsupported characters.")

    if support_status == ROLE_SUPPORT_SUPPORTED:
        if role_domain not in {ROLE_DOMAIN_IT_SOFTWARE, ROLE_DOMAIN_IT_ADJACENT}:
            add_validation_error(errors, "role_domain", "Supported role must be IT/software or IT-adjacent.")
        if not role_label:
            add_validation_error(errors, "role_label", "Supported role requires a concrete role label.")
        elif not source_contains_role_phrase(latest_message, role_label):
            add_validation_error(errors, "role_label", "Role label lacks source-message evidence.")
        else:
            _, role_errors = normalize_role_family_value(role_label)
            errors.extend(role_errors)
        if (
            role_domain == ROLE_DOMAIN_IT_ADJACENT
            and role_label_is_it_adjacent(role_label)
            and not source_has_it_adjacent_support_signal(latest_message)
        ):
            add_validation_error(
                errors,
                "role_domain",
                "IT-adjacent role lacks IT/software/tool/work-skill evidence.",
            )

    if support_status == ROLE_SUPPORT_NEEDS_CLARIFICATION:
        if role_domain not in {ROLE_DOMAIN_AMBIGUOUS, ROLE_DOMAIN_UNKNOWN, ROLE_DOMAIN_IT_ADJACENT}:
            add_validation_error(errors, "role_domain", "Clarification status requires ambiguous role domain.")
        if not clarification_question:
            add_validation_error(errors, "clarification_question", "Clarification status requires a question.")

    if support_status == ROLE_SUPPORT_REJECTED:
        if role_domain != ROLE_DOMAIN_NON_IT:
            add_validation_error(errors, "role_domain", "Rejected role must be non-IT.")
        if role_label and not (
            looks_like_non_it_role(role_label) or source_contains_role_phrase(latest_message, role_label)
        ):
            add_validation_error(errors, "role_label", "Rejected role label lacks source-message evidence.")

    if errors:
        return None, errors

    return {
        "resolver_version": ROLE_UNDERSTANDING_RESOLVER_VERSION,
        "schema_version": schema_version,
        "role_label": role_label,
        "role_domain": role_domain,
        "support_status": support_status,
        "confidence": confidence,
        "evidence": evidence,
        "clarification_question": clarification_question,
        "reason_code": reason_code,
    }, []
