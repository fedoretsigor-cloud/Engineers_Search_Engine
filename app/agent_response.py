from app.agent_messages import (
    agent_message_language,
    agent_response_limitations_source_messages,
    agent_response_quality_notes_source_messages,
    agent_response_summary_source_message,
    agent_response_suggested_next_actions_source_messages,
    next_iteration_broaden_observed_stack_source_copy,
    next_iteration_clarify_stack_source_copy,
    next_iteration_deep_search_source_copy,
    next_iteration_narrow_visible_stack_source_copy,
    next_iteration_review_high_quality_candidates_source_copy,
)
from app.brief_patch import (
    BRIEF_PATCH_ADD_STACK,
    BRIEF_PATCH_NOOP,
    BRIEF_PATCH_RECONFIRM_FIELD,
    BRIEF_PATCH_REPLACE_STACK,
    BRIEF_PATCH_SET_SEARCH_DEPTH,
    build_brief_patch,
)
from app.candidate_quality import (
    candidate_text_sources,
    collect_term_evidence,
    terms_from_evidence,
)
from app.domain_config import (
    SEARCH_DEPTH_DEEP,
    SEARCH_DEPTH_STANDARD,
    search_domain_config_for,
)


def normalize_agent_language(value: str | None) -> str:
    return agent_message_language(value, None)


def agent_response_quality_bucket(score: object) -> str:
    try:
        score_value = int(score)
    except (TypeError, ValueError):
        score_value = 0

    if score_value >= 80:
        return "strong"
    if score_value >= 60:
        return "review"
    return "weak"


def agent_response_quality_distribution(deduped_results: list[dict]) -> dict:
    distribution = {"strong": 0, "review": 0, "weak": 0}
    for item in deduped_results:
        result = item.get("result") or {}
        distribution[agent_response_quality_bucket(result.get("quality_score"))] += 1
    return distribution


def agent_response_signal_counts(deduped_results: list[dict]) -> dict:
    counts = {
        "target_or_close_role": 0,
        "exact_technology": 0,
        "selected_stack_visible": 0,
        "selected_stack_not_visible": 0,
        "seniority_not_visible": 0,
        "role_missing": 0,
        "technology_missing": 0,
        "target_location": 0,
        "weak_location": 0,
        "unknown_location": 0,
    }

    for item in deduped_results:
        result = item.get("result") or {}
        flags = set(result.get("review_flags") or [])
        location_status = (
            result.get("location_signal_status")
            or item.get("location_signal_status")
            or ""
        )

        if result.get("role_fit") == "target_or_close_role":
            counts["target_or_close_role"] += 1
        if result.get("technology_fit") == "exact":
            counts["exact_technology"] += 1
        if result.get("stack_fit") == "selected_stack_found":
            counts["selected_stack_visible"] += 1
        if "selected_stack_missing" in flags:
            counts["selected_stack_not_visible"] += 1
        if "seniority_missing" in flags:
            counts["seniority_not_visible"] += 1
        if "role_missing" in flags:
            counts["role_missing"] += 1
        if "technology_missing" in flags:
            counts["technology_missing"] += 1
        if location_status in {"target_location", "country_domain"}:
            counts["target_location"] += 1
        if location_status == "weak_history_only":
            counts["weak_location"] += 1
        if location_status == "unknown_non_country_domain":
            counts["unknown_location"] += 1

    return counts


def top_review_flag_counts(
    deduped_results: list[dict],
    limit: int = 5,
) -> list[dict[str, int | str]]:
    flag_counts: dict[str, int] = {}
    for item in deduped_results:
        result = item.get("result") or {}
        for flag in result.get("review_flags") or []:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

    return [
        {"flag": flag, "count": count}
        for flag, count in sorted(
            flag_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[:limit]
    ]


def agent_response_summary_facts(
    query_plan: dict,
    report: dict,
    deduped_results: list[dict],
) -> dict:
    input_snapshot = query_plan.get("input_snapshot") or {}
    return {
        "mode": report.get("mode", "single_wave"),
        "candidate_count": report.get("unique_profiles", len(deduped_results)),
        "raw_total": report.get("raw_total", 0),
        "displayed": report.get("displayed", 0),
        "queries_succeeded": report.get("queries_succeeded", 0),
        "queries_total": report.get("queries_total", len(query_plan.get("queries", []))),
        "quality_distribution": agent_response_quality_distribution(deduped_results),
        "strong_signal_counts": agent_response_signal_counts(deduped_results),
        "top_review_flags": top_review_flag_counts(deduped_results),
        "input_snapshot": input_snapshot,
    }


def agent_response_message_en(summary_facts: dict) -> str:
    return agent_response_summary_source_message("en", summary_facts)


def agent_response_message_ru(summary_facts: dict) -> str:
    return agent_response_summary_source_message("ru", summary_facts)


def agent_response_quality_notes(
    language: str,
    summary_facts: dict,
) -> list[dict[str, object]]:
    return agent_response_quality_notes_source_messages(language, summary_facts)


def agent_response_limitations(language: str, summary_facts: dict) -> list[dict[str, object]]:
    return agent_response_limitations_source_messages(language, summary_facts)


def agent_response_suggested_next_actions(
    language: str,
    summary_facts: dict,
) -> list[dict[str, object]]:
    return agent_response_suggested_next_actions_source_messages(language, summary_facts)


def next_iteration_option(
    option_id: str,
    label: str,
    reason: str,
    operations: list[dict],
    *,
    requires_clarification: bool = False,
) -> dict[str, object]:
    return {
        "id": option_id,
        "label": label,
        "reason": reason,
        "proposed_brief_patch": build_brief_patch(
            source_message=f"next_iteration_option:{option_id}",
            operations=operations,
            requires_clarification=requires_clarification,
        ),
        "requires_approval_before_execution": True,
        "is_executable_now": False,
    }


def stack_term_visibility_counts(
    deduped_results: list[dict],
    stack_terms: list[str],
) -> dict[str, int]:
    counts = {term: 0 for term in stack_terms}
    if not stack_terms:
        return counts

    for item in deduped_results:
        result = item.get("result") or {}
        sources = candidate_text_sources(result)
        evidence = collect_term_evidence(sources, stack_terms)
        for term in terms_from_evidence(evidence, stack_terms):
            counts[term] += 1

    return counts


def next_iteration_stack_observation_threshold(candidate_count: int) -> int:
    if candidate_count <= 0:
        return 2
    return max(2, min(5, (candidate_count + 11) // 12))


def agent_response_next_iteration_options(
    query_plan: dict,
    summary_facts: dict,
    deduped_results: list[dict],
    language: str = "en",
) -> list[dict[str, object]]:
    input_snapshot = (
        query_plan.get("input_snapshot")
        or summary_facts.get("input_snapshot")
        or {}
    )
    candidate_count = int(summary_facts.get("candidate_count") or 0)
    quality = summary_facts.get("quality_distribution") or {}
    signals = summary_facts.get("strong_signal_counts") or {}
    selected_stack = input_snapshot.get("stack") or []
    search_depth = input_snapshot.get("search_depth") or SEARCH_DEPTH_STANDARD
    mode = summary_facts.get("mode")
    domain_config = search_domain_config_for(
        input_snapshot.get("role_family") or "",
        input_snapshot.get("technology") or "",
    )
    allowed_stack = (
        domain_config.get("quality", {})
        .get("stack", {})
        .get("allowed_terms", [])
    )
    selected_stack = [term for term in selected_stack if term in allowed_stack]
    selected_counts = stack_term_visibility_counts(deduped_results, selected_stack)
    unselected_stack = [term for term in allowed_stack if term not in selected_stack]
    unselected_counts = stack_term_visibility_counts(deduped_results, unselected_stack)
    options: list[dict[str, object]] = []

    strong_count = int(quality.get("strong") or 0)
    if strong_count:
        label, reason = next_iteration_review_high_quality_candidates_source_copy(
            strong_count,
            language,
        )
        options.append(
            next_iteration_option(
                "review_high_quality_candidates",
                label,
                reason,
                [
                    {
                        "operation": BRIEF_PATCH_NOOP,
                        "field": "review_focus",
                        "value": "high_quality_candidates",
                    }
                ],
            )
        )

    visible_selected_stack = [
        term for term in selected_stack if selected_counts.get(term, 0) > 0
    ]
    missing_selected_stack = [
        term for term in selected_stack if selected_counts.get(term, 0) == 0
    ]
    if (
        len(selected_stack) > 1
        and visible_selected_stack
        and missing_selected_stack
        and visible_selected_stack != selected_stack
    ):
        label, reason = next_iteration_narrow_visible_stack_source_copy(
            visible_selected_stack,
            missing_selected_stack,
            language,
        )
        options.append(
            next_iteration_option(
                "narrow_to_visible_selected_stack",
                label,
                reason,
                [
                    {
                        "operation": BRIEF_PATCH_REPLACE_STACK,
                        "field": "stack",
                        "values": visible_selected_stack[:3],
                    }
                ],
            )
        )

    observation_threshold = next_iteration_stack_observation_threshold(candidate_count)
    observed_unselected_stack = [
        (term, count)
        for term, count in unselected_counts.items()
        if count >= observation_threshold
    ]
    observed_unselected_stack.sort(key=lambda item: (-item[1], item[0]))
    if selected_stack and len(selected_stack) < 3 and observed_unselected_stack:
        term, count = observed_unselected_stack[0]
        label, reason = next_iteration_broaden_observed_stack_source_copy(
            term,
            count,
            language,
        )
        options.append(
            next_iteration_option(
                "broaden_with_observed_stack",
                label,
                reason,
                [
                    {
                        "operation": BRIEF_PATCH_ADD_STACK,
                        "field": "stack",
                        "value": term,
                    }
                ],
            )
        )

    if (
        selected_stack
        and not visible_selected_stack
        and int(signals.get("selected_stack_not_visible") or 0) > 0
    ):
        label, reason = next_iteration_clarify_stack_source_copy(language)
        options.append(
            next_iteration_option(
                "clarify_stack_preference",
                label,
                reason,
                [
                    {
                        "operation": BRIEF_PATCH_RECONFIRM_FIELD,
                        "field": "stack",
                        "value": "current",
                    }
                ],
                requires_clarification=True,
            )
        )

    if search_depth != SEARCH_DEPTH_DEEP and mode != "multi_wave":
        label, reason = next_iteration_deep_search_source_copy(language)
        options.append(
            next_iteration_option(
                "try_deep_search_depth",
                label,
                reason,
                [
                    {
                        "operation": BRIEF_PATCH_SET_SEARCH_DEPTH,
                        "field": "search_depth",
                        "value": SEARCH_DEPTH_DEEP,
                    }
                ],
            )
        )

    return options[:4]


def build_agent_response(
    query_plan: dict,
    report: dict,
    deduped_results: list[dict],
    language: str | None = None,
) -> dict:
    normalized_language = normalize_agent_language(language)
    summary_facts = agent_response_summary_facts(
        query_plan,
        report,
        deduped_results,
    )
    message = (
        agent_response_message_ru(summary_facts)
        if normalized_language == "ru"
        else agent_response_message_en(summary_facts)
    )

    return {
        "message": message,
        "summary_facts": summary_facts,
        "quality_notes": agent_response_quality_notes(
            normalized_language,
            summary_facts,
        ),
        "limitations": agent_response_limitations(
            normalized_language,
            summary_facts,
        ),
        "suggested_next_actions": agent_response_suggested_next_actions(
            normalized_language,
            summary_facts,
        ),
        "next_iteration_options": agent_response_next_iteration_options(
            query_plan,
            summary_facts,
            deduped_results,
            normalized_language,
        ),
        "language": normalized_language,
        "source": "backend_returned_search_data",
        "requires_approval_for_execution": True,
    }


