import json
import os
import re

import httpx

from app.domain_config import (
    PROFILE_SOURCE_LINKEDIN_PUBLIC,
    SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION,
    SEARCH_BRIEF_STATUS_READY_FOR_PLANNING,
    SEARCH_DEPTH_STANDARD,
    SEARCH_DEPTH_VALUES,
)
from app.schemas import SearchBrief
from app.search_brief import validate_and_normalize_search_brief
from app.search_validation import (
    add_validation_error,
    normalize_role_family_value,
    normalize_search_location_value,
    normalize_stack_item_value,
    normalize_stack_items,
    normalize_technology_value,
)
from app.text_utils import (
    compact_spaces,
    contains_cyrillic_text,
    normalize_text_list,
    normalize_text_value,
)


SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION = "search_brief_extractor_v2"
SEARCH_BRIEF_EXTRACTOR_VALIDATOR_VERSION = "search_brief_extractor_validator_v1"
SEARCH_BRIEF_EXTRACTOR_MAX_COMPLETION_TOKENS = 900
SEARCH_BRIEF_EXTRACTOR_TIMEOUT_SECONDS = 30
DEFAULT_OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

SEARCH_BRIEF_EXTRACTOR_CONFIDENCE_HIGH = "high"
SEARCH_BRIEF_EXTRACTOR_CONFIDENCE_MEDIUM = "medium"
SEARCH_BRIEF_EXTRACTOR_CONFIDENCE_LOW = "low"
SEARCH_BRIEF_EXTRACTOR_CONFIDENCES = {
    SEARCH_BRIEF_EXTRACTOR_CONFIDENCE_HIGH,
    SEARCH_BRIEF_EXTRACTOR_CONFIDENCE_MEDIUM,
    SEARCH_BRIEF_EXTRACTOR_CONFIDENCE_LOW,
}

SEARCH_BRIEF_EXTRACTOR_ALLOWED_TOP_LEVEL_KEYS = {
    "schema_version",
    "draft_brief",
    "confidence",
    "reason_codes",
}
SEARCH_BRIEF_EXTRACTOR_ALLOWED_DRAFT_KEYS = {
    "source_text",
    "role_family",
    "role_ambiguity",
    "technology",
    "stack",
    "location",
    "seniority",
    "must_have",
    "nice_to_have",
    "domain_experience",
    "exclusions",
    "search_depth",
    "profile_sources",
    "notes",
}
SEARCH_BRIEF_EXTRACTOR_ALLOWED_ROLE_AMBIGUITY_KEYS = {
    "is_ambiguous",
    "label",
    "options",
    "clarification_question",
}

DOMAIN_CONTEXT_PATTERNS = [
    r"\bdomain\b",
    r"\bindustry\b",
    r"\bsector\b",
    r"\bbusiness context\b",
    r"\bbusiness experience\b",
    r"\bfunctional experience\b",
    r"\bbanking\b",
    r"\bfintech\b",
    r"\bfinance\b",
    r"\bfinancial services\b",
    r"\bhealthcare\b",
    r"\be-?commerce\b",
    r"\btelecom\b",
    r"\binsurance\b",
    r"\bretail\b",
    r"\blogistics\b",
    r"\btravel\b",
    r"\bmedia\b",
    r"\bautomotive\b",
    r"\beducation\b",
    r"\blegal\b",
    r"\breal estate\b",
]
SAFE_REASON_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
SEARCH_BRIEF_EXTRACTOR_MISSING_FIELD_PRIORITY = {
    "role_family": 0,
    "technology": 1,
    "stack": 2,
    "location": 3,
    "search_depth": 4,
    "profile_sources": 5,
}
REQUIREMENT_SEARCH_SIGNAL_RESOLVER_VERSION = "requirement_search_signal_resolver_v1"
NON_DEVELOPER_REQUIREMENT_ROLE_PATTERNS = [
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
DEVELOPER_REQUIREMENT_ROLE_BLOCK_PATTERNS = [
    r"\bdeveloper\b",
    r"\bengineer\b",
    r"\bprogrammer\b",
    r"\barchitect\b",
    r"\bdevops\b",
    r"\bsre\b",
    r"\bqa\b",
    r"\btester\b",
    r"\bautomation\b",
    r"\bsecurity\b",
    r"\bdba\b",
    r"\bsysadmin\b",
]
REQUIREMENT_SIGNAL_ADJECTIVE_PATTERN = re.compile(
    r"^(?:strong|advanced|excellent|fluent|good|solid|deep|proven|hands[- ]on)\s+",
    flags=re.IGNORECASE,
)
REQUIREMENT_SIGNAL_TRAILING_CONTEXT_PATTERN = re.compile(
    r"\s+(?:skills?|experience|background|knowledge|expertise)$",
    flags=re.IGNORECASE,
)
REQUIREMENT_SIGNAL_GENERIC_TOKENS = {
    "and",
    "domain",
    "experience",
    "background",
    "knowledge",
    "expertise",
    "skill",
    "skills",
    "strong",
}
REQUIREMENT_SIGNAL_UPPERCASE_TOKENS = {
    "ai",
    "api",
    "aws",
    "bi",
    "crm",
    "erp",
    "gcp",
    "hr",
    "ml",
    "qa",
    "sql",
    "ui",
    "uk",
    "ux",
}


def search_brief_extractor_system_prompt() -> str:
    return (
        "You extract a recruiter's initial candidate-search request into a bounded "
        "Search Brief draft. Return strict JSON only. You may extract meaning, but "
        "you must not validate, generate search queries, browse, call providers, "
        "access LinkedIn, scrape, automate profiles, message candidates, approve "
        "searches, perform account actions, or persist data."
    )


def search_brief_extractor_user_prompt(
    *,
    latest_message: str,
    language: str,
    previous_brief: dict | None = None,
) -> str:
    return json.dumps(
        {
            "task": (
                "Extract a raw SearchBriefExtractor v2 draft from the latest "
                "clean-state recruiter message."
            ),
            "required_output": {
                "schema_version": SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
                "draft_brief": {
                    "source_text": "original recruiter request text",
                    "role_family": "explicit IT/software/data/product/security/design/operations role or null",
                    "role_ambiguity": {
                        "is_ambiguous": "boolean",
                        "label": "ambiguous role label or null",
                        "options": ["safe role options when obvious"],
                        "clarification_question": "one targeted role question or null",
                    },
                    "technology": "main technical skill/platform/language/tool, or primary domain/search anchor for non-developer IT roles when no technical skill is explicit, or null",
                    "stack": ["1-3 explicitly requested technical, tool, language, or work-skill search signals"],
                    "location": "target country/city/region/remote value or null",
                    "seniority": "optional seniority or null",
                    "must_have": ["required non-stack requirements"],
                    "nice_to_have": ["optional requirements"],
                    "domain_experience": ["business/domain context such as banking or fintech"],
                    "exclusions": [],
                    "search_depth": "standard or deep",
                    "profile_sources": ["linkedin_public"],
                    "notes": "safe non-instructional note or null",
                },
                "confidence": "high | medium | low",
                "reason_codes": ["short_snake_case"],
            },
            "latest_message": latest_message,
            "language": language,
            "previous_brief": previous_brief or {},
            "semantic_rules": [
                "Keep the requested candidate role in role_family.",
                "Do not convert a technology into the target role.",
                "Separate domain/business context from technical skills.",
                "For non-developer IT roles such as Project Manager or Product Manager, a primary business domain can be the search anchor when no technical skill is explicit.",
                "For non-developer IT roles, explicit work-skill requirements such as English or Excel can be stack/search signals.",
                "Examples of domain/business context: banking, fintech, healthcare, ecommerce, telecom.",
                "Examples of technical skills: SQL, Java, Selenium, AWS, Terraform, Power BI.",
                "If a role label such as Analyst is ambiguous, set role_ambiguity.is_ambiguous to true.",
                "Do not invent missing role, technology, stack, or location values.",
                "Use English field values only.",
            ],
            "hard_boundaries": [
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
            "prompt_version": SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
        },
        ensure_ascii=False,
        indent=2,
    )


def search_brief_extractor_openai_payload(
    *,
    model: str,
    latest_message: str,
    language: str = "en",
    previous_brief: dict | None = None,
) -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": search_brief_extractor_system_prompt()},
            {
                "role": "user",
                "content": search_brief_extractor_user_prompt(
                    latest_message=latest_message,
                    language=language,
                    previous_brief=previous_brief,
                ),
            },
        ],
        "temperature": 0,
        "max_completion_tokens": SEARCH_BRIEF_EXTRACTOR_MAX_COMPLETION_TOKENS,
        "response_format": {"type": "json_object"},
    }


async def run_openai_json_search_brief_extractor(
    *,
    latest_message: str,
    language: str = "en",
    previous_brief: dict | None = None,
    chat_completions_url: str | None = None,
) -> tuple[dict | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return None, "openai_not_configured"

    payload = search_brief_extractor_openai_payload(
        model=model,
        latest_message=latest_message,
        language=language,
        previous_brief=previous_brief,
    )

    try:
        async with httpx.AsyncClient(timeout=SEARCH_BRIEF_EXTRACTOR_TIMEOUT_SECONDS) as client:
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
        return None, "openai_search_brief_extractor_timeout"
    except httpx.HTTPStatusError as exc:
        return None, f"openai_search_brief_extractor_http_{exc.response.status_code}"
    except httpx.HTTPError:
        return None, "openai_search_brief_extractor_request_failed"

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        return None, "openai_search_brief_extractor_empty_content"

    try:
        parsed_content = json.loads(content)
    except json.JSONDecodeError:
        return None, "openai_search_brief_extractor_invalid_json"
    if not isinstance(parsed_content, dict):
        return None, "openai_search_brief_extractor_wrong_shape"

    return parsed_content, None


def safe_extractor_text_value(value: object, max_length: int = 120) -> str | None:
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


def safe_extractor_text_list(
    value: object,
    *,
    max_items: int = 5,
    item_max_length: int = 120,
) -> tuple[list[str], str | None]:
    if value is None:
        return [], None
    if not isinstance(value, list):
        return [], "search_brief_extractor_list_wrong_shape"

    values: list[str] = []
    for raw_item in value:
        safe_item = safe_extractor_text_value(raw_item, max_length=item_max_length)
        if not safe_item:
            return [], "search_brief_extractor_unsafe_value"
        if safe_item not in values:
            values.append(safe_item)
    if len(values) > max_items:
        return [], "search_brief_extractor_too_many_values"
    return values, None


def looks_like_domain_context(value: object) -> bool:
    if value is not None and not isinstance(value, str):
        return False
    text = normalize_text_value(value)
    if not text:
        return False
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in DOMAIN_CONTEXT_PATTERNS)


def role_allows_requirement_search_signal_resolution(role_family: object) -> bool:
    role = normalize_text_value(role_family)
    if not role:
        return False

    if any(
        re.search(pattern, role, flags=re.IGNORECASE)
        for pattern in DEVELOPER_REQUIREMENT_ROLE_BLOCK_PATTERNS
    ):
        return False

    return any(
        re.search(pattern, role, flags=re.IGNORECASE)
        for pattern in NON_DEVELOPER_REQUIREMENT_ROLE_PATTERNS
    )


def humanize_requirement_signal_label(value: str) -> str | None:
    label = compact_spaces(value).strip(" .,:;\"'()[]")
    label = REQUIREMENT_SIGNAL_ADJECTIVE_PATTERN.sub("", label)
    label = REQUIREMENT_SIGNAL_TRAILING_CONTEXT_PATTERN.sub("", label)
    label = compact_spaces(label).strip(" .,:;\"'()[]")
    if not label:
        return None

    tokens = re.findall(r"[A-Za-z0-9+#./&-]+", label)
    if not tokens:
        return None
    if all(token.lower() in REQUIREMENT_SIGNAL_GENERIC_TOKENS for token in tokens):
        return None

    normalized_tokens: list[str] = []
    for token in tokens:
        lowered = token.lower()
        if lowered in REQUIREMENT_SIGNAL_UPPERCASE_TOKENS:
            normalized_tokens.append(lowered.upper())
        elif token.isupper():
            normalized_tokens.append(token)
        else:
            normalized_tokens.append(token[:1].upper() + token[1:].lower())

    return " ".join(normalized_tokens)


def requirement_domain_search_anchor(requirement: str) -> str | None:
    text = normalize_text_value(requirement)
    if not text:
        return None

    patterns = [
        r"\b(?P<value>[A-Za-z0-9+#./&() _-]{2,80}?)\s+(?:domain|industry|sector)\s*(?:experience|background|knowledge|expertise)?\b",
        r"\b(?P<value>[A-Za-z0-9+#./&() _-]{2,80}?)\s+(?:business|functional)\s+(?:experience|background|knowledge|expertise)\b",
        r"\b(?P<value>[A-Za-z0-9+#./&() _-]{2,80}?)\s+experience\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        raw_value = match.group("value")
        if looks_like_domain_context(raw_value) or looks_like_domain_context(text):
            return humanize_requirement_signal_label(raw_value)

    return None


def split_requirement_signal_terms(value: str) -> list[str]:
    return [
        compact_spaces(term).strip(" .,:;\"'()[]")
        for term in re.split(r"\s+(?:and|or)\s+|[,/;]+", value, flags=re.IGNORECASE)
        if compact_spaces(term).strip(" .,:;\"'()[]")
    ]


def requirement_stack_signals(requirement: str) -> list[str]:
    text = normalize_text_value(requirement)
    if not text:
        return []
    if looks_like_domain_context(text):
        return []

    raw_candidates: list[str] = []
    patterns = [
        r"\b(?:strong|advanced|excellent|fluent|good|solid|deep|proven|hands[- ]on)?\s*(?P<value>[A-Za-z0-9+#./&() _-]{2,80}?)\s+skills?\b",
        r"\b(?:experience|knowledge|expertise)\s+(?:in|with|of)\s+(?P<value>[A-Za-z0-9+#./&() _-]{2,80})\b",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            raw_candidates.extend(split_requirement_signal_terms(match.group("value")))

    signals: list[str] = []
    seen: set[str] = set()
    for raw_candidate in raw_candidates:
        signal = humanize_requirement_signal_label(raw_candidate)
        if not signal:
            continue
        signal_key = signal.lower()
        if signal_key in seen:
            continue
        normalized_signal, signal_error = normalize_stack_item_value(signal)
        if signal_error or not normalized_signal:
            continue
        seen.add(signal_key)
        signals.append(normalized_signal)

    return signals


def requirement_search_signal_sources(draft: dict) -> list[str]:
    sources = []
    for field_name in ("must_have", "nice_to_have", "domain_experience"):
        sources.extend(normalize_text_list(draft.get(field_name)))

    deduped_sources: list[str] = []
    seen_sources: set[str] = set()
    for source in sources:
        source_key = source.lower()
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            deduped_sources.append(source)
    return deduped_sources


def apply_requirement_search_signal_resolution_to_draft(
    draft: dict,
) -> tuple[dict, bool]:
    resolved = dict(draft)
    if not role_allows_requirement_search_signal_resolution(resolved.get("role_family")):
        return resolved, False

    requirement_sources = requirement_search_signal_sources(resolved)
    if not requirement_sources:
        return resolved, False

    changed = False
    if not normalize_text_value(resolved.get("technology")):
        for requirement in requirement_sources:
            anchor = requirement_domain_search_anchor(requirement)
            if not anchor:
                continue
            technology, technology_errors = normalize_technology_value(anchor)
            if not technology_errors and technology:
                resolved["technology"] = technology
                changed = True
                break

    if not normalize_text_list(resolved.get("stack")):
        stack_candidates: list[str] = []
        seen_stack: set[str] = set()
        for requirement in requirement_sources:
            for signal in requirement_stack_signals(requirement):
                signal_key = signal.lower()
                if signal_key in seen_stack:
                    continue
                seen_stack.add(signal_key)
                stack_candidates.append(signal)
                if len(stack_candidates) == 3:
                    break
            if len(stack_candidates) == 3:
                break

        if stack_candidates:
            normalized_stack, stack_errors = normalize_stack_items(stack_candidates)
            if not stack_errors and normalized_stack:
                resolved["stack"] = normalized_stack
                if not normalize_text_list(resolved.get("nice_to_have")):
                    resolved["nice_to_have"] = normalized_stack
                changed = True

    if changed:
        assumptions = normalize_text_list(resolved.get("assumptions"))
        assumption = (
            "Derived executable search signals from explicit recruiter requirements."
        )
        if assumption not in assumptions:
            assumptions.append(assumption)
            resolved["assumptions"] = assumptions

    return resolved, changed


def normalize_reason_codes(value: object) -> list[str]:
    raw_codes = normalize_text_list(value)
    reason_codes: list[str] = []
    for raw_code in raw_codes[:5]:
        code = raw_code.lower().replace("-", "_").replace(" ", "_")
        if SAFE_REASON_CODE_PATTERN.match(code) and code not in reason_codes:
            reason_codes.append(code)
    return reason_codes or ["validated"]


def prioritize_extractor_missing_fields(normalized_brief: dict) -> None:
    missing_fields = normalized_brief.get("missing_fields") or []
    normalized_brief["missing_fields"] = sorted(
        missing_fields,
        key=lambda field: (
            SEARCH_BRIEF_EXTRACTOR_MISSING_FIELD_PRIORITY.get(field, 99),
            field,
        ),
    )


def normalize_role_ambiguity_value(
    value: object,
    errors: list[dict[str, str]],
) -> tuple[dict, list[str]]:
    if value is None:
        return {
            "is_ambiguous": False,
            "label": None,
            "options": [],
            "clarification_question": None,
        }, []
    if not isinstance(value, dict):
        add_validation_error(errors, "role_ambiguity", "Role ambiguity must be an object.")
        return {
            "is_ambiguous": False,
            "label": None,
            "options": [],
            "clarification_question": None,
        }, []

    unknown_keys = set(value) - SEARCH_BRIEF_EXTRACTOR_ALLOWED_ROLE_AMBIGUITY_KEYS
    if unknown_keys:
        add_validation_error(errors, "role_ambiguity", "Role ambiguity contains unsupported fields.")

    is_ambiguous = bool(value.get("is_ambiguous"))
    label = safe_extractor_text_value(value.get("label"), max_length=80)
    options, options_error = safe_extractor_text_list(
        value.get("options"),
        max_items=4,
        item_max_length=80,
    )
    if options_error:
        add_validation_error(errors, "role_ambiguity.options", "Role ambiguity options are invalid.")
        options = []
    clarification_question = safe_extractor_text_value(
        value.get("clarification_question"),
        max_length=160,
    )

    clarification_targets = ["role_family"] if is_ambiguous else []
    return {
        "is_ambiguous": is_ambiguous,
        "label": label,
        "options": options,
        "clarification_question": clarification_question,
    }, clarification_targets


def validate_search_brief_extractor_output(
    llm_output: dict | None,
) -> tuple[dict | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    if not isinstance(llm_output, dict):
        add_validation_error(errors, "extractor_output", "Extractor output must be an object.")
        return None, errors

    unknown_top_level_keys = set(llm_output) - SEARCH_BRIEF_EXTRACTOR_ALLOWED_TOP_LEVEL_KEYS
    if unknown_top_level_keys:
        add_validation_error(errors, "extractor_output", "Extractor output contains unsupported fields.")

    schema_version = safe_extractor_text_value(
        llm_output.get("schema_version"),
        max_length=80,
    )
    if schema_version != SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION:
        add_validation_error(errors, "schema_version", "Unsupported extractor schema version.")

    confidence = safe_extractor_text_value(llm_output.get("confidence"), max_length=24)
    if confidence not in SEARCH_BRIEF_EXTRACTOR_CONFIDENCES:
        add_validation_error(errors, "confidence", "Unsupported extractor confidence.")
    elif confidence == SEARCH_BRIEF_EXTRACTOR_CONFIDENCE_LOW:
        add_validation_error(errors, "confidence", "Extractor confidence is too low.")

    draft_brief = llm_output.get("draft_brief")
    if not isinstance(draft_brief, dict):
        add_validation_error(errors, "draft_brief", "Draft brief must be an object.")
        return None, errors

    unknown_draft_keys = set(draft_brief) - SEARCH_BRIEF_EXTRACTOR_ALLOWED_DRAFT_KEYS
    if unknown_draft_keys:
        add_validation_error(errors, "draft_brief", "Draft brief contains unsupported fields.")

    role_ambiguity, clarification_targets = normalize_role_ambiguity_value(
        draft_brief.get("role_ambiguity"),
        errors,
    )

    source_text = safe_extractor_text_value(draft_brief.get("source_text"), max_length=500)
    role_family = None
    raw_role_family = safe_extractor_text_value(draft_brief.get("role_family"), max_length=80)
    if draft_brief.get("role_family") is not None and not raw_role_family:
        add_validation_error(errors, "role_family", "Role value is unsafe.")
    elif raw_role_family:
        role_family, role_errors = normalize_role_family_value(raw_role_family)
        errors.extend(role_errors)

    technology = None
    raw_technology = safe_extractor_text_value(draft_brief.get("technology"), max_length=40)
    if draft_brief.get("technology") is not None and not raw_technology:
        add_validation_error(errors, "technology", "Technology value is unsafe.")
    elif raw_technology:
        if looks_like_domain_context(raw_technology) and not (
            role_allows_requirement_search_signal_resolution(role_family)
        ):
            add_validation_error(errors, "technology", "Technology looks like domain context.")
        else:
            if looks_like_domain_context(raw_technology):
                technology_source = (
                    requirement_domain_search_anchor(raw_technology)
                    or humanize_requirement_signal_label(raw_technology)
                )
            else:
                technology_source = raw_technology
            technology, technology_errors = normalize_technology_value(technology_source)
            errors.extend(technology_errors)

    raw_stack = draft_brief.get("stack")
    stack: list[str] = []
    if raw_stack:
        if not isinstance(raw_stack, list):
            add_validation_error(errors, "stack", "Stack must be a list.")
        elif any(looks_like_domain_context(item) for item in raw_stack):
            add_validation_error(errors, "stack", "Stack contains domain context.")
        else:
            stack, stack_errors = normalize_stack_items(raw_stack)
            errors.extend(stack_errors)

    location = None
    raw_location = safe_extractor_text_value(draft_brief.get("location"), max_length=80)
    if draft_brief.get("location") is not None and not raw_location:
        add_validation_error(errors, "location", "Location value is unsafe.")
    elif raw_location:
        location, location_errors = normalize_search_location_value(raw_location)
        errors.extend(location_errors)

    seniority = safe_extractor_text_value(draft_brief.get("seniority"), max_length=40)
    notes = safe_extractor_text_value(draft_brief.get("notes"), max_length=200)

    must_have, must_have_error = safe_extractor_text_list(
        draft_brief.get("must_have"),
        max_items=6,
        item_max_length=120,
    )
    if must_have_error:
        add_validation_error(errors, "must_have", "Must-have values are invalid.")
    nice_to_have, nice_to_have_error = safe_extractor_text_list(
        draft_brief.get("nice_to_have"),
        max_items=6,
        item_max_length=120,
    )
    if nice_to_have_error:
        add_validation_error(errors, "nice_to_have", "Nice-to-have values are invalid.")
    domain_experience, domain_error = safe_extractor_text_list(
        draft_brief.get("domain_experience"),
        max_items=5,
        item_max_length=120,
    )
    if domain_error:
        add_validation_error(errors, "domain_experience", "Domain experience values are invalid.")
    exclusions, exclusions_error = safe_extractor_text_list(
        draft_brief.get("exclusions"),
        max_items=5,
        item_max_length=120,
    )
    if exclusions_error:
        add_validation_error(errors, "exclusions", "Exclusion values are invalid.")

    search_depth = (
        safe_extractor_text_value(draft_brief.get("search_depth"), max_length=24)
        or SEARCH_DEPTH_STANDARD
    )
    if search_depth not in SEARCH_DEPTH_VALUES:
        add_validation_error(errors, "search_depth", "Unsupported search depth.")
        search_depth = SEARCH_DEPTH_STANDARD

    profile_sources, profile_sources_error = safe_extractor_text_list(
        draft_brief.get("profile_sources") or [PROFILE_SOURCE_LINKEDIN_PUBLIC],
        max_items=1,
        item_max_length=40,
    )
    if profile_sources_error or profile_sources != [PROFILE_SOURCE_LINKEDIN_PUBLIC]:
        add_validation_error(errors, "profile_sources", "Unsupported profile source.")
        profile_sources = [PROFILE_SOURCE_LINKEDIN_PUBLIC]

    if domain_experience:
        for domain_item in domain_experience:
            if domain_item not in must_have:
                must_have.append(domain_item)

    resolved_draft, _ = apply_requirement_search_signal_resolution_to_draft(
        {
            "role_family": role_family,
            "technology": technology,
            "stack": stack,
            "must_have": must_have,
            "nice_to_have": nice_to_have,
            "domain_experience": domain_experience,
            "assumptions": [],
        }
    )
    technology = resolved_draft.get("technology")
    stack = resolved_draft.get("stack") or []
    if not nice_to_have:
        nice_to_have = resolved_draft.get("nice_to_have") or []
    assumptions = resolved_draft.get("assumptions") or []

    if errors:
        return None, errors

    brief_status = (
        SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION
        if role_ambiguity.get("is_ambiguous")
        else SEARCH_BRIEF_STATUS_READY_FOR_PLANNING
    )
    candidate_brief = SearchBrief(
        source_text=source_text,
        brief_status=brief_status,
        role_family=role_family,
        technology=technology,
        stack=stack,
        location=location,
        seniority=seniority,
        must_have=must_have,
        nice_to_have=nice_to_have,
        exclusions=exclusions,
        search_depth=search_depth,
        profile_sources=profile_sources,
        notes=notes,
        assumptions=assumptions,
    )
    normalized_brief, brief_errors = validate_and_normalize_search_brief(candidate_brief)
    if brief_errors:
        return None, brief_errors

    for missing_field in normalized_brief.get("missing_fields") or []:
        if missing_field not in clarification_targets:
            clarification_targets.append(missing_field)
    if role_ambiguity.get("is_ambiguous"):
        normalized_brief["brief_status"] = SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION
        if "role_family" not in normalized_brief["missing_fields"]:
            normalized_brief["missing_fields"].append("role_family")
        if role_ambiguity.get("clarification_question"):
            normalized_brief["clarifying_questions"].insert(
                0,
                role_ambiguity["clarification_question"],
            )

    prioritize_extractor_missing_fields(normalized_brief)

    return {
        "validator_version": SEARCH_BRIEF_EXTRACTOR_VALIDATOR_VERSION,
        "schema_version": schema_version,
        "confidence": confidence,
        "normalized_brief": normalized_brief,
        "domain_experience": domain_experience,
        "role_ambiguity": role_ambiguity,
        "clarification_targets": clarification_targets,
        "reason_codes": normalize_reason_codes(llm_output.get("reason_codes")),
    }, []
