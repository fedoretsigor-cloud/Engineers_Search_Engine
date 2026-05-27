import html
import re


def compact_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def term_match_pattern(term: str) -> str:
    escaped_term = re.escape(term.strip()).replace(r"\ ", r"\s+")
    return r"(?<![a-z0-9])" + escaped_term + r"(?![a-z0-9])"


def find_term_match(text: str, term: str) -> re.Match | None:
    if not text or not term:
        return None

    return re.search(term_match_pattern(term), text, flags=re.IGNORECASE)


def normalize_text_value(value: str | None) -> str | None:
    normalized_value = compact_spaces(value or "")
    return normalized_value or None


def contains_cyrillic_text(value: object) -> bool:
    return bool(re.search(r"[\u0400-\u04FF]", str(value or "")))


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


def clean_headline_value(value: str) -> str:
    headline = strip_linkedin_suffix(value)
    headline = re.sub(r"(?i)\b(?:\d+(?:[.,]\d+)?\s*)?(?:followers|connections)\b.*$", "", headline)
    return headline.strip(" -|.")


def ordered_unique(values: list[str]) -> list[str]:
    seen_values: set[str] = set()
    unique_values: list[str] = []

    for value in values:
        if value and value not in seen_values:
            seen_values.add(value)
            unique_values.append(value)

    return unique_values
