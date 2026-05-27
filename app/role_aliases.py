import re

from app.text_utils import compact_spaces, contains_cyrillic_text, normalize_text_value, ordered_unique


ROLE_ALIAS_PLAN_VERSION = "role_alias_plan_v1"
ROLE_ALIAS_PLAN_SOURCE_CONFIGURED_DOMAIN = "configured_domain"
ROLE_ALIAS_PLAN_SOURCE_DETERMINISTIC_FALLBACK = "deterministic_fallback"

MAX_ROLE_ALIAS_LENGTH = 80
TECHNOLOGY_ONLY_ROLE_RESIDUALS = {
    "architect",
    "consultant",
    "developer",
    "engineer",
    "programmer",
    "software developer",
    "software engineer",
    "specialist",
}
GENERIC_ROLE_WORDS = {
    "architect",
    "consultant",
    "developer",
    "engineer",
    "lead",
    "middle",
    "mid",
    "principal",
    "programmer",
    "senior",
    "software",
    "specialist",
    "staff",
    "junior",
}


def normalize_role_alias_phrase(value: object) -> str | None:
    text = normalize_text_value(value)
    if not text:
        return None

    normalized = compact_spaces(text).strip(" .,:;\"'")
    if not normalized or len(normalized) > MAX_ROLE_ALIAS_LENGTH:
        return None
    if contains_cyrillic_text(normalized):
        return None
    if re.search(
        r"https?://|www\.|@|<|>|`|{|}|\[|\]|\bsite:|\blinkedin\.com\b",
        normalized,
        flags=re.IGNORECASE,
    ):
        return None
    if re.search(r"\b(AND|OR|NOT)\b", normalized, flags=re.IGNORECASE):
        return None

    return normalized


def _token_key(value: str | None) -> str:
    return compact_spaces(value or "").lower()


def _token_words(value: str | None) -> list[str]:
    return re.findall(r"[a-z0-9+#.]+", _token_key(value))


def distinctive_role_tokens(role_family: str, technology: str | None = None) -> list[str]:
    technology_tokens = set(_token_words(technology))
    return [
        token
        for token in _token_words(role_family)
        if token not in GENERIC_ROLE_WORDS and token not in technology_tokens
    ]


def remove_technology_terms(phrase: str, technology: str | None) -> str:
    residual = phrase
    for token in _token_words(technology):
        residual = re.sub(
            r"(?<![A-Za-z0-9+#.])" + re.escape(token) + r"(?![A-Za-z0-9+#.])",
            " ",
            residual,
            flags=re.IGNORECASE,
        )
    return compact_spaces(residual)


def is_technology_only_role_phrase(
    phrase: str,
    *,
    role_family: str,
    technology: str | None,
) -> bool:
    if not technology:
        return False

    phrase_key = _token_key(phrase)
    role_key = _token_key(role_family)
    if not phrase_key or not role_key:
        return False

    residual = remove_technology_terms(phrase, technology)
    residual_key = _token_key(residual)
    if not residual_key or residual_key == phrase_key:
        return False

    if residual_key == role_key or role_key in phrase_key:
        return False

    role_specific_tokens = distinctive_role_tokens(role_family, technology)
    phrase_tokens = set(_token_words(phrase))
    if role_specific_tokens and any(token in phrase_tokens for token in role_specific_tokens):
        return False

    return residual_key in TECHNOLOGY_ONLY_ROLE_RESIDUALS


def validate_role_alias_phrase(
    phrase: object,
    *,
    role_family: str,
    technology: str | None,
    allow_configured_domain_phrase: bool = False,
) -> tuple[str | None, str | None]:
    normalized = normalize_role_alias_phrase(phrase)
    if not normalized:
        return None, "unsafe_or_invalid_alias"

    if (
        not allow_configured_domain_phrase
        and is_technology_only_role_phrase(
            normalized,
            role_family=role_family,
            technology=technology,
        )
    ):
        return None, "technology_only_role_drift"

    return normalized, None


def _configured_role_alias_candidates(
    role_family: str,
    technology: str,
    configured_role_phrases: list[str],
) -> list[str]:
    return ordered_unique(
        configured_role_phrases
        + [
            f"{technology} {role_family}",
            f"{role_family} {technology}",
            role_family,
        ]
    )


def _generic_role_alias_candidates(role_family: str, technology: str) -> list[str]:
    return ordered_unique(
        [
            f"{technology} {role_family}",
            f"{role_family} {technology}",
            role_family,
            f"{technology} Developer",
            f"{technology} Engineer",
            f"{technology} Specialist",
            f"{technology} Consultant",
            f"{technology} Software Engineer",
        ]
    )


def build_role_alias_plan(
    *,
    role_family: str,
    technology: str,
    configured_role_phrases: list[str] | None = None,
) -> dict:
    configured_phrases = configured_role_phrases or []
    source = (
        ROLE_ALIAS_PLAN_SOURCE_CONFIGURED_DOMAIN
        if configured_phrases
        else ROLE_ALIAS_PLAN_SOURCE_DETERMINISTIC_FALLBACK
    )
    candidates = (
        _configured_role_alias_candidates(role_family, technology, configured_phrases)
        if configured_phrases
        else _generic_role_alias_candidates(role_family, technology)
    )

    approved_aliases: list[str] = []
    rejected_aliases: list[dict[str, str]] = []
    for candidate in candidates:
        approved, rejection_reason = validate_role_alias_phrase(
            candidate,
            role_family=role_family,
            technology=technology,
            allow_configured_domain_phrase=bool(configured_phrases),
        )
        if approved:
            approved_aliases.append(approved)
        else:
            rejected_aliases.append(
                {
                    "alias": str(candidate),
                    "reason": rejection_reason or "rejected",
                }
            )

    if not approved_aliases:
        fallback_alias, fallback_error = validate_role_alias_phrase(
            role_family,
            role_family=role_family,
            technology=technology,
            allow_configured_domain_phrase=False,
        )
        if fallback_alias:
            approved_aliases.append(fallback_alias)
        else:
            rejected_aliases.append(
                {
                    "alias": str(role_family),
                    "reason": fallback_error or "fallback_role_rejected",
                }
            )

    return {
        "plan_version": ROLE_ALIAS_PLAN_VERSION,
        "source": source,
        "target_role": role_family,
        "technology": technology,
        "approved_aliases": ordered_unique(approved_aliases),
        "rejected_aliases": rejected_aliases,
        "validator": "backend_role_alias_validator_v1",
        "llm_alias_expansion": "not_called",
    }


def approved_role_aliases_from_plan(role_alias_plan: dict | None) -> list[str]:
    if not isinstance(role_alias_plan, dict):
        return []
    aliases = role_alias_plan.get("approved_aliases")
    if not isinstance(aliases, list):
        return []

    normalized_aliases = [
        normalized
        for alias in aliases
        if (normalized := normalize_role_alias_phrase(alias))
    ]
    return ordered_unique(normalized_aliases)
