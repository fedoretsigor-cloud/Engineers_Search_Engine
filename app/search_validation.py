import re

from app.domain_config import (
    CANONICAL_ROLE_FAMILIES,
    IMPLEMENTED_BACKEND_TECHNOLOGIES,
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
from app.text_utils import normalize_text_value


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
    if re.search("^\u0443\u043a\u0440\u0430(\u0438|\u0457)\u043d", normalized_key) or normalized_key == "ukraine":
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

    search_depth = normalize_text_value(request.search_depth) or SEARCH_DEPTH_STANDARD
    if search_depth not in SEARCH_DEPTH_VALUES:
        add_validation_error(errors, "search_depth", "Unsupported search depth.")
        search_depth = SEARCH_DEPTH_STANDARD

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
