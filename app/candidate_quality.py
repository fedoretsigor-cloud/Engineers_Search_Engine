import re

from app.domain_config import (
    CANDIDATE_QUALITY_SCORE_VERSION,
    CANDIDATE_SENIORITY_CONFIG,
    REVIEW_FLAG_TAXONOMY,
    search_domain_config_for,
)
from app.role_aliases import approved_role_aliases_from_plan
from app.text_utils import (
    clean_headline_value,
    clean_profile_text,
    compact_spaces,
    find_term_match,
    ordered_unique,
    term_match_pattern,
)


def candidate_text_sources(result: dict) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    seen_values: set[str] = set()
    source_fields = [
        ("headline", result.get("headline")),
        ("title", result.get("title")),
        ("snippet", result.get("snippet")),
        ("raw_content", result.get("raw_content")),
    ]

    for source, raw_value in source_fields:
        value = clean_profile_text(raw_value)
        if not value or value.lower() in {"unknown", "n/a"}:
            continue

        value_key = value.lower()
        if value_key in seen_values:
            continue

        seen_values.add(value_key)
        sources.append({"source": source, "value": value})

    return sources


def collect_term_evidence(
    sources: list[dict[str, str]],
    terms: list[str],
) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    seen_terms: set[str] = set()

    for source in sources:
        value = source["value"]
        for term in terms:
            if term in seen_terms:
                continue
            if find_term_match(value, term):
                seen_terms.add(term)
                evidence.append(
                    {
                        "term": term,
                        "source": source["source"],
                        "value": value,
                    }
                )

    return evidence


def terms_from_evidence(
    evidence: list[dict],
    term_order: list[str],
) -> list[str]:
    found_terms = {item.get("term") for item in evidence if item.get("term")}
    return [term for term in term_order if term in found_terms]


def query_plan_by_id(query_plan: dict) -> dict[str, dict]:
    return {query["id"]: query for query in query_plan.get("queries", [])}


def role_context_phrases(query_sources: list[dict], query_plan: dict) -> list[str]:
    queries_by_id = query_plan_by_id(query_plan)
    approved_aliases = approved_role_aliases_from_plan(query_plan.get("role_alias_plan"))
    role_phrases: list[str] = []
    approved_alias_keys = {alias.lower() for alias in approved_aliases}

    for source in query_sources:
        role_phrase = source.get("role_phrase")
        if not role_phrase:
            query = queries_by_id.get(source.get("id"))
            role_phrase = query.get("role_phrase") if query else None
        if role_phrase and (
            not approved_alias_keys or role_phrase.lower() in approved_alias_keys
        ):
            role_phrases.append(role_phrase)

    input_snapshot = query_plan.get("input_snapshot") or {}
    if input_snapshot.get("role_family"):
        role_phrases.append(input_snapshot["role_family"])

    if approved_aliases:
        role_phrases.extend(approved_aliases)
    else:
        for query in query_plan.get("queries", []):
            if query.get("role_phrase"):
                role_phrases.append(query["role_phrase"])

    return ordered_unique(role_phrases)


def derived_role_phrases(
    role_phrases: list[str],
    technology_terms: list[str],
) -> list[dict[str, str]]:
    derived_phrases: list[dict[str, str]] = []
    seen_phrases: set[str] = set()

    for role_phrase in role_phrases:
        derived_phrase = role_phrase
        for technology_term in technology_terms:
            derived_phrase = re.sub(
                term_match_pattern(technology_term),
                " ",
                derived_phrase,
                flags=re.IGNORECASE,
            )

        derived_phrase = compact_spaces(derived_phrase)
        if (
            derived_phrase
            and derived_phrase.lower() != role_phrase.lower()
            and derived_phrase.lower() not in seen_phrases
        ):
            seen_phrases.add(derived_phrase.lower())
            derived_phrases.append(
                {
                    "phrase": derived_phrase,
                    "source_role_phrase": role_phrase,
                }
            )

    return derived_phrases


def role_prefix_terms(
    role_phrases: list[str],
    technology_terms: list[str],
) -> list[str]:
    terms = ["Junior", "Middle", "Mid", "Senior", "Lead", "Principal", "Staff"]
    for phrase in role_phrases + technology_terms:
        terms.extend(re.findall(r"[A-Za-z][A-Za-z+#.]*", phrase))

    return sorted(ordered_unique(terms), key=len, reverse=True)


def role_display_from_match(
    value: str,
    match: re.Match,
    technology_terms: list[str],
    role_phrases: list[str],
) -> str:
    start = match.start()
    end = match.end()
    prefix_terms = role_prefix_terms(role_phrases, technology_terms)
    prefix_options = "|".join(re.escape(term) for term in prefix_terms) or r"$^"
    prefix_pattern = r"(?:(?:" + prefix_options + r")\s+){0,5}$"
    prefix_match = re.search(prefix_pattern, value[:start], flags=re.IGNORECASE)
    if prefix_match and prefix_match.group(0).strip():
        start = prefix_match.start()

    return clean_headline_value(value[start:end])


def find_role_match(
    sources: list[dict[str, str]],
    role_phrases: list[str],
    technology_terms: list[str],
) -> dict | None:
    ordered_role_phrases = sorted(role_phrases, key=len, reverse=True)
    derived_phrases = sorted(
        derived_role_phrases(role_phrases, technology_terms),
        key=lambda item: len(item["phrase"]),
        reverse=True,
    )

    for source in sources:
        value = source["value"]
        for role_phrase in ordered_role_phrases:
            match = find_term_match(value, role_phrase)
            if match:
                return {
                    "role_display": role_display_from_match(
                        value,
                        match,
                        technology_terms,
                        role_phrases,
                    ),
                    "role_fit": "target_or_close_role",
                    "evidence": {
                        "source": source["source"],
                        "value": value,
                        "matched_phrase": role_phrase,
                        "match_type": "role_phrase",
                    },
                }

    for source in sources:
        value = source["value"]
        for derived_phrase in derived_phrases:
            match = find_term_match(value, derived_phrase["phrase"])
            if match:
                return {
                    "role_display": role_display_from_match(
                        value,
                        match,
                        technology_terms,
                        role_phrases,
                    ),
                    "role_fit": "similar_role",
                    "evidence": {
                        "source": source["source"],
                        "value": value,
                        "matched_phrase": derived_phrase["phrase"],
                        "source_role_phrase": derived_phrase["source_role_phrase"],
                        "match_type": "derived_role_phrase",
                    },
                }

    return None


def build_role_quality(
    result: dict,
    query_sources: list[dict],
    query_plan: dict,
    domain_config: dict,
) -> dict:
    quality_config = domain_config.get("quality", {})
    technology_terms = quality_config.get("technology", {}).get("exact_terms", [])
    role_phrases = role_context_phrases(query_sources, query_plan)
    sources = candidate_text_sources(result)
    role_match = find_role_match(sources, role_phrases, technology_terms)

    if not role_match:
        return {
            "role_display": "n/a",
            "role_fit": "missing_role",
            "role_evidence": [],
            "review_flags": ["role_missing"],
        }

    review_flags: list[str] = []
    evidence_source = role_match["evidence"]["source"]
    if evidence_source not in {"headline", "title"}:
        review_flags.append("role_from_snippet_only")
    if role_match["role_fit"] == "similar_role":
        review_flags.append("role_similar_only")

    return {
        "role_display": role_match["role_display"] or "n/a",
        "role_fit": role_match["role_fit"],
        "role_evidence": [role_match["evidence"]],
        "review_flags": review_flags,
    }


def build_technology_quality(
    result: dict,
    domain_config: dict,
) -> dict:
    quality_config = domain_config.get("quality", {})
    technology_config = quality_config.get("technology", {})
    exact_terms = technology_config.get("exact_terms", [])
    exclude_terms = technology_config.get("exclude_terms", [])
    related_terms = technology_config.get("related_terms", [])
    sources = candidate_text_sources(result)
    exact_evidence = collect_term_evidence(sources, exact_terms)
    exclude_evidence = collect_term_evidence(sources, exclude_terms)
    related_evidence = collect_term_evidence(sources, related_terms)
    exact_matches = terms_from_evidence(exact_evidence, exact_terms)
    related_matches = terms_from_evidence(related_evidence, related_terms)
    review_flags: list[str] = []

    if exact_matches:
        return {
            "technology_display": ", ".join(exact_matches),
            "technology_fit": "exact",
            "technology_evidence": exact_evidence + exclude_evidence,
            "review_flags": review_flags,
        }

    if related_matches:
        review_flags.append("technology_related_only")
        if exclude_evidence:
            review_flags.append("possible_technology_false_positive")
        return {
            "technology_display": ", ".join(related_matches),
            "technology_fit": "related_only",
            "technology_evidence": related_evidence + exclude_evidence,
            "review_flags": review_flags,
        }

    if exclude_evidence:
        return {
            "technology_display": "n/a",
            "technology_fit": "ambiguous",
            "technology_evidence": exclude_evidence,
            "review_flags": [
                "technology_ambiguous",
                "possible_technology_false_positive",
            ],
        }

    return {
        "technology_display": "n/a",
        "technology_fit": "missing",
        "technology_evidence": [],
        "review_flags": ["technology_missing"],
    }


def query_source_stack_evidence(
    query_sources: list[dict],
    query_plan: dict,
) -> list[dict]:
    queries_by_id = query_plan_by_id(query_plan)
    evidence: list[dict] = []
    seen_query_ids: set[str] = set()

    for source in query_sources:
        query_id = source.get("id")
        if not query_id or query_id in seen_query_ids:
            continue

        uses_stack = source.get("uses_stack")
        if uses_stack is None:
            query = queries_by_id.get(query_id)
            uses_stack = query.get("uses_stack") if query else []

        if not uses_stack:
            continue

        seen_query_ids.add(query_id)
        evidence.append(
            {
                "terms": uses_stack,
                "source": "query_source",
                "query_id": query_id,
                "category": source.get("category"),
                "evidence_type": "stack_query_group",
            }
        )

    return evidence


def build_stack_quality(
    result: dict,
    query_sources: list[dict],
    query_plan: dict,
    domain_config: dict,
) -> dict:
    input_snapshot = query_plan.get("input_snapshot") or {}
    selected_stack = input_snapshot.get("stack") or []
    quality_config = domain_config.get("quality", {})
    stack_config = quality_config.get("stack", {})
    allowed_terms = stack_config.get("allowed_terms", [])
    related_terms = stack_config.get("related_terms", [])
    selected_terms = [term for term in selected_stack if term in allowed_terms]
    sources = candidate_text_sources(result)
    selected_evidence = collect_term_evidence(sources, selected_terms)
    related_evidence = collect_term_evidence(sources, related_terms)
    query_group_evidence = query_source_stack_evidence(query_sources, query_plan)
    selected_matches = terms_from_evidence(selected_evidence, selected_terms)
    related_matches = terms_from_evidence(related_evidence, related_terms)

    if selected_matches:
        return {
            "stack_display": ", ".join(selected_matches),
            "stack_fit": "selected_stack_found",
            "stack_evidence": selected_evidence + query_group_evidence,
            "review_flags": [],
        }

    if query_group_evidence:
        return {
            "stack_display": "n/a",
            "stack_fit": "stack_query_source_only",
            "stack_evidence": query_group_evidence,
            "review_flags": [
                "selected_stack_missing",
                "stack_from_query_source_only",
            ],
        }

    if related_matches:
        return {
            "stack_display": ", ".join(related_matches),
            "stack_fit": "related_stack_only",
            "stack_evidence": related_evidence,
            "review_flags": ["stack_related_only"],
        }

    return {
        "stack_display": "n/a",
        "stack_fit": "missing_selected_stack" if selected_stack else "missing",
        "stack_evidence": [],
        "review_flags": ["selected_stack_missing"] if selected_stack else [],
    }


def collect_seniority_evidence(
    sources: list[dict[str, str]],
    seniority_config: dict,
) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    seen_levels: set[str] = set()

    for source in sources:
        value = source["value"]
        for level, config in seniority_config.items():
            if level in seen_levels:
                continue

            terms = sorted(config.get("terms", []), key=len, reverse=True)
            for term in terms:
                if find_term_match(value, term):
                    seen_levels.add(level)
                    evidence.append(
                        {
                            "term": term,
                            "level": level,
                            "display": config["display"],
                            "source": source["source"],
                            "value": value,
                        }
                    )
                    break

    return evidence


def seniority_display_from_evidence(evidence: list[dict]) -> str:
    found_levels = {item["level"] for item in evidence}
    experience_order = ["junior", "middle", "senior"]
    experience_levels = [
        level for level in experience_order if level in found_levels
    ]
    has_leadership = "leadership" in found_levels

    display_parts: list[str] = []
    if experience_levels:
        highest_experience_level = experience_levels[-1]
        display_parts.append(
            CANDIDATE_SENIORITY_CONFIG[highest_experience_level]["display"]
        )
    if has_leadership:
        display_parts.append(CANDIDATE_SENIORITY_CONFIG["leadership"]["display"])

    return " ".join(display_parts) if display_parts else "n/a"


def build_seniority_quality(result: dict) -> dict:
    sources = candidate_text_sources(result)
    seniority_evidence = collect_seniority_evidence(
        sources,
        CANDIDATE_SENIORITY_CONFIG,
    )

    if not seniority_evidence:
        return {
            "seniority_display": "n/a",
            "seniority_fit": "missing",
            "seniority_evidence": [],
            "review_flags": ["seniority_missing"],
        }

    found_levels = {item["level"] for item in seniority_evidence}
    experience_levels = found_levels.intersection({"junior", "middle", "senior"})
    review_flags: list[str] = []
    if len(experience_levels) > 1:
        review_flags.append("seniority_ambiguous")
    if all(item["source"] not in {"headline", "title"} for item in seniority_evidence):
        review_flags.append("seniority_from_snippet_only")

    return {
        "seniority_display": seniority_display_from_evidence(seniority_evidence),
        "seniority_fit": "ambiguous" if "seniority_ambiguous" in review_flags else "found",
        "seniority_evidence": seniority_evidence,
        "review_flags": review_flags,
    }


def merge_review_flags(existing_flags: list[str], new_flags: list[str]) -> list[str]:
    return ordered_unique(existing_flags + new_flags)


def review_flag_detail(flag_code: str) -> dict:
    flag_config = REVIEW_FLAG_TAXONOMY.get(flag_code)
    if not flag_config:
        return {
            "code": flag_code,
            "category": "unknown",
            "severity": "info",
            "label": flag_code.replace("_", " ").title(),
            "description": "Unknown review flag preserved for compatibility.",
            "affects_quality_score": False,
            "score_penalty_group": None,
        }

    return {"code": flag_code, **flag_config}


def normalize_review_flags(review_flags: list[str]) -> tuple[list[str], list[dict]]:
    unique_flags = ordered_unique(review_flags)
    known_flags = [
        flag_code for flag_code in REVIEW_FLAG_TAXONOMY if flag_code in unique_flags
    ]
    unknown_flags = [
        flag_code for flag_code in unique_flags if flag_code not in REVIEW_FLAG_TAXONOMY
    ]
    normalized_flags = known_flags + unknown_flags
    return normalized_flags, [review_flag_detail(flag) for flag in normalized_flags]


def score_component(
    component: str,
    points: int,
    max_points: int,
    status: str,
    reason: str,
    optional: bool = False,
) -> dict:
    return {
        "component": component,
        "points": points,
        "max_points": max_points,
        "status": status,
        "reason": reason,
        "optional": optional,
    }


def build_location_score_component(result: dict) -> dict:
    status = result.get("location_signal_status") or "not_applied"
    if status == "not_applied":
        return score_component(
            "location",
            0,
            0,
            "not_evaluated",
            "Location filter was not evaluated.",
        )

    score_by_status = {
        "target_location": (
            25,
            "Current-location text contains the target location.",
        ),
        "rescued_header_location": (
            20,
            "Header/location text supports the target location.",
        ),
        "country_domain": (
            16,
            "Country-specific LinkedIn domain supports the target location.",
        ),
    }
    points, reason = score_by_status.get(
        status,
        (0, "Location confidence is weak or not displayed by the filter."),
    )
    return score_component("location", points, 25, status, reason)


def build_role_score_component(result: dict) -> dict:
    role_fit = result.get("role_fit") or "missing_role"
    score_by_fit = {
        "target_or_close_role": (
            25,
            "Target or close role matched candidate text.",
        ),
        "similar_role": (
            16,
            "Similar role matched candidate text.",
        ),
    }
    points, reason = score_by_fit.get(
        role_fit,
        (0, "Target or similar role was not confirmed."),
    )
    return score_component("role", points, 25, role_fit, reason)


def build_technology_score_component(result: dict) -> dict:
    technology_fit = result.get("technology_fit") or "missing"
    score_by_fit = {
        "exact": (
            20,
            "Selected technology was directly found.",
        ),
        "related_only": (
            10,
            "Only a configured related technology was found.",
        ),
    }
    points, reason = score_by_fit.get(
        technology_fit,
        (0, "Selected technology was not confidently confirmed."),
    )
    return score_component("technology", points, 20, technology_fit, reason)


def build_stack_score_component(result: dict) -> dict:
    stack_fit = result.get("stack_fit") or "missing"
    score_by_fit = {
        "selected_stack_found": (
            20,
            "Selected stack was directly found in candidate text.",
        ),
        "related_stack_only": (
            8,
            "Only configured related stack evidence was found.",
        ),
        "stack_query_source_only": (
            6,
            "Candidate came from a stack-focused query, but no specific OR term was directly observed.",
        ),
    }
    points, reason = score_by_fit.get(
        stack_fit,
        (0, "Selected stack was not directly confirmed."),
    )
    return score_component("stack", points, 20, stack_fit, reason)


def build_identity_score_component(result: dict) -> dict:
    name_found = bool(result.get("name") and result.get("name") != "unknown")
    headline_found = bool(result.get("headline") and result.get("headline") != "n/a")
    points = (3 if name_found else 0) + (2 if headline_found else 0)
    return score_component(
        "identity",
        points,
        5,
        "complete" if points == 5 else "partial",
        "Candidate name/headline extraction completeness.",
    )


def build_seniority_score_component(result: dict) -> dict:
    seniority_fit = result.get("seniority_fit") or "missing"
    score_by_fit = {
        "found": (
            5,
            "Seniority signal was found as a bonus signal.",
        ),
        "ambiguous": (
            2,
            "Seniority signal was found but needs review.",
        ),
    }
    points, reason = score_by_fit.get(
        seniority_fit,
        (0, "Seniority was not found and is not penalized without a requirement."),
    )
    return score_component("seniority", points, 5, seniority_fit, reason, optional=True)


def build_quality_score_penalties(result: dict) -> list[dict]:
    review_flag_details = result.get("review_flag_details") or []
    penalty_by_group = {
        "technology_false_positive": {
            "points": -10,
            "reason": "Technology evidence may be a false positive.",
        },
        "low_confidence_source": {
            "points": -3,
            "reason": "Important evidence came only from lower-confidence snippet text.",
        },
        "low_confidence_seniority": {
            "points": -2,
            "reason": "Seniority evidence is ambiguous.",
        },
    }
    applied_groups: set[str] = set()
    penalties: list[dict] = []

    for flag_detail in review_flag_details:
        group = flag_detail.get("score_penalty_group")
        if group not in penalty_by_group or group in applied_groups:
            continue

        applied_groups.add(group)
        penalty_config = penalty_by_group[group]
        penalties.append(
            {
                "flag": flag_detail["code"],
                "group": group,
                "points": penalty_config["points"],
                "reason": penalty_config["reason"],
            }
        )

    return penalties


def build_quality_score(result: dict) -> dict:
    breakdown = [
        build_location_score_component(result),
        build_role_score_component(result),
        build_technology_score_component(result),
        build_stack_score_component(result),
        build_identity_score_component(result),
        build_seniority_score_component(result),
    ]
    required_components = [item for item in breakdown if not item.get("optional")]
    optional_components = [item for item in breakdown if item.get("optional")]
    available_points = sum(item["max_points"] for item in required_components)
    earned_points = sum(item["points"] for item in required_components)
    optional_points = sum(item["points"] for item in optional_components)
    base_score = round((earned_points / available_points) * 95) if available_points else 0
    penalties = build_quality_score_penalties(result)
    penalty_points = sum(item["points"] for item in penalties)
    quality_score = min(100, max(0, base_score + optional_points + penalty_points))

    return {
        "quality_score": quality_score,
        "quality_score_version": CANDIDATE_QUALITY_SCORE_VERSION,
        "quality_score_breakdown": breakdown,
        "quality_score_penalties": penalties,
    }


def build_candidate_quality(
    result: dict,
    query_sources: list[dict],
    query_plan: dict,
) -> dict:
    input_snapshot = query_plan.get("input_snapshot") or {}
    domain_config = search_domain_config_for(
        input_snapshot.get("role_family") or "",
        input_snapshot.get("technology") or "",
        input_snapshot.get("stack") or [],
    )
    quality: dict = {}
    review_flags = list(result.get("review_flags", []))

    for quality_part in (
        build_role_quality(result, query_sources, query_plan, domain_config),
        build_technology_quality(result, domain_config),
        build_stack_quality(result, query_sources, query_plan, domain_config),
        build_seniority_quality(result),
    ):
        review_flags = merge_review_flags(
            review_flags,
            quality_part.pop("review_flags", []),
        )
        quality.update(quality_part)

    normalized_flags, flag_details = normalize_review_flags(review_flags)
    quality["review_flags"] = normalized_flags
    quality["review_flag_details"] = flag_details
    quality.update(build_quality_score({**result, **quality}))
    return quality
