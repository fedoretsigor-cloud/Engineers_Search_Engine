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
