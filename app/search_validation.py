import re

from app.domain_config import (
    CANONICAL_ROLE_FAMILIES,
    JAVA_STACK_VALUES,
    KNOWN_BACKEND_TECHNOLOGIES,
    MULTI_WAVE_DEFAULT_MAX_WAVES,
    MULTI_WAVE_DEFAULT_MIN_NEW_UNIQUE_PER_WAVE,
    MULTI_WAVE_DEFAULT_PATIENCE,
    MULTI_WAVE_MAX_ALLOWED_WAVES,
    SEARCH_DEPTH_STANDARD,
    SEARCH_DEPTH_VALUES,
    location_filter_config_for,
)
from app.schemas import MultiWaveStructuredSearchRequest, StructuredSearchRequest
from app.text_utils import compact_spaces, contains_cyrillic_text, normalize_text_value


SAFE_RECRUITER_FIELD_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+#./&() _-]*$")
UNSAFE_SEARCH_FIELD_PATTERNS = [
    r"\bhttps?://",
    r"\bwww\.",
    r"\bsite:",
    r"\blinkedin\.com/login\b",
    r"\b(scrape|scraping|crawler|bypass|password|inmail|message candidate)\b",
]
NON_IT_ROLE_PATTERNS = [
    r"\bplumber\b",
    r"\bdentist\b",
    r"\belectrician\b",
    r"\bmechanical engineer\b",
    r"\baccountant\b",
    r"\blawyer\b",
    r"\bdoctor\b",
    r"\bnurse\b",
    r"\bteacher\b",
    r"\bdriver\b",
    r"\bcook\b",
    r"\bchef\b",
]
IT_ROLE_PATTERNS = [
    r"\bdeveloper\b",
    r"\bdev\b",
    r"\bengineer\b",
    r"\bprogrammer\b",
    r"\barchitect\b",
    r"\bdevops\b",
    r"\bsre\b",
    r"\bqa\b",
    r"\btester\b",
    r"\bautomation\b",
    r"\banalyst\b",
    r"\bdata\b",
    r"\bscientist\b",
    r"\bproduct manager\b",
    r"\bproject manager\b",
    r"\bscrum\b",
    r"\bdesigner\b",
    r"\bux\b",
    r"\bui\b",
    r"\bsecurity\b",
    r"\bcloud\b",
    r"\bplatform\b",
    r"\bdatabase\b",
    r"\bdba\b",
    r"\bsysadmin\b",
    r"\badministrator\b",
    r"\bml\b",
    r"\bai\b",
    r"\bsoftware\b",
    r"\bfrontend\b",
    r"\bfront-end\b",
    r"\bbackend\b",
    r"\bback-end\b",
    r"\bfullstack\b",
    r"\bfull-stack\b",
    r"\bmobile\b",
    r"\bios\b",
    r"\bandroid\b",
    r"\bembedded\b",
    r"\bfirmware\b",
    r"\bblockchain\b",
    r"\bsap\b",
    r"\bsalesforce\b",
]


def canonical_value(value: str | None, allowed_values: dict[str, str]) -> str | None:
    if value is None:
        return None

    normalized_key = value.strip().lower()
    if not normalized_key:
        return None

    return allowed_values.get(normalized_key)


def search_field_validation_error(
    value: str | None,
    *,
    field: str,
    max_length: int,
) -> str | None:
    normalized_value = normalize_text_value(value)
    if not normalized_value:
        return f"{field} is required."
    if contains_cyrillic_text(normalized_value):
        return "This POC accepts English input only."
    if len(normalized_value) > max_length:
        return f"{field} is too long."
    if not SAFE_RECRUITER_FIELD_PATTERN.match(normalized_value):
        return f"{field} contains unsupported characters."
    for pattern in UNSAFE_SEARCH_FIELD_PATTERNS:
        if re.search(pattern, normalized_value, flags=re.IGNORECASE):
            return f"{field} contains unsupported search instructions."
    return None


def looks_like_non_it_role(value: str) -> bool:
    return any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in NON_IT_ROLE_PATTERNS)


def looks_like_it_role(value: str) -> bool:
    if looks_like_non_it_role(value):
        return False
    return any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in IT_ROLE_PATTERNS)


def normalize_freeform_label(value: str) -> str:
    return compact_spaces(value).strip(" .,_-/")


def normalize_role_family_value(value: str | None) -> tuple[str | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    validation_error = search_field_validation_error(value, field="Role", max_length=80)
    if validation_error:
        add_validation_error(errors, "role_family", validation_error)
        return None, errors

    assert value is not None
    canonical_role = canonical_value(value, CANONICAL_ROLE_FAMILIES)
    normalized_role = canonical_role or normalize_freeform_label(value)
    if not looks_like_it_role(normalized_role):
        add_validation_error(
            errors,
            "role_family",
            "Role must be an English IT/software role.",
        )
        return None, errors

    return normalized_role, errors


def normalize_technology_value(value: str | None) -> tuple[str | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    validation_error = search_field_validation_error(
        value,
        field="Technology",
        max_length=40,
    )
    if validation_error:
        add_validation_error(errors, "technology", validation_error)
        return None, errors

    assert value is not None
    canonical_technology = canonical_value(value, KNOWN_BACKEND_TECHNOLOGIES)
    return canonical_technology or normalize_freeform_label(value), errors


def normalize_stack_item_value(value: str | None) -> tuple[str | None, str | None]:
    validation_error = search_field_validation_error(value, field="Stack item", max_length=40)
    if validation_error:
        return None, validation_error

    assert value is not None
    canonical_stack_item = canonical_value(value, JAVA_STACK_VALUES)
    return canonical_stack_item or normalize_freeform_label(value), None


def normalize_location_value(value: str | None) -> str | None:
    normalized_value = normalize_text_value(value)
    if not normalized_value:
        return None

    normalized_key = normalized_value.lower()
    if re.search("^\u0443\u043a\u0440\u0430(\u0438|\u0457)\u043d", normalized_key) or normalized_key == "ukraine":
        return "Ukraine"

    return normalized_value


def normalize_search_location_value(value: str | None) -> tuple[str | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    validation_error = search_field_validation_error(value, field="Location", max_length=80)
    if validation_error:
        add_validation_error(errors, "location", validation_error)
        return None, errors

    return normalize_location_value(value), errors


def add_validation_error(errors: list[dict[str, str]], field: str, message: str) -> None:
    errors.append({"field": field, "message": message})


def normalize_stack_items(stack: list[str] | None) -> tuple[list[str], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    normalized_stack: list[str] = []
    seen_stack_values: set[str] = set()

    if not stack:
        add_validation_error(errors, "stack", "At least one stack item is required.")
        return normalized_stack, errors

    for item in stack:
        normalized_item, item_error = normalize_stack_item_value(item)
        if item_error or not normalized_item:
            add_validation_error(errors, "stack", item_error or "Unsupported stack item.")
            continue

        stack_key = normalized_item.lower()
        if stack_key not in seen_stack_values:
            seen_stack_values.add(stack_key)
            normalized_stack.append(normalized_item)

    if len(normalized_stack) > 3:
        add_validation_error(errors, "stack", "Stack supports up to 3 selected items.")

    return normalized_stack, errors


def normalize_structured_search_request(
    request: StructuredSearchRequest,
) -> tuple[dict | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []

    role_family, role_errors = normalize_role_family_value(request.role_family)
    errors.extend(role_errors)

    technology, technology_errors = normalize_technology_value(request.technology)
    errors.extend(technology_errors)

    location, location_errors = normalize_search_location_value(request.location)
    errors.extend(location_errors)
    location = location or ""

    search_depth = normalize_text_value(request.search_depth) or SEARCH_DEPTH_STANDARD
    if search_depth not in SEARCH_DEPTH_VALUES:
        add_validation_error(errors, "search_depth", "Unsupported search depth.")
        search_depth = SEARCH_DEPTH_STANDARD

    normalized_stack, stack_errors = normalize_stack_items(request.stack)
    errors.extend(stack_errors)

    linkedin_profiles_only = (
        True
        if request.linkedin_profiles_only is None
        else request.linkedin_profiles_only
    )
    location_filter_config = location_filter_config_for(location)
    location_filter_enabled = bool(
        location_filter_config
        and (
            True
            if request.location_filter_enabled is None
            else request.location_filter_enabled
        )
    )

    if errors:
        return None, errors

    return (
        {
            "role_family": role_family,
            "technology": technology,
            "stack": normalized_stack,
            "location": location,
            "search_depth": search_depth,
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
