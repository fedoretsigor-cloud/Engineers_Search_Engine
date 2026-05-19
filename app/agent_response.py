from app.agent_plan import agent_plan_language
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
    return agent_plan_language(value, None)


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
    quality = summary_facts["quality_distribution"]
    signals = summary_facts["strong_signal_counts"]
    candidate_count = summary_facts["candidate_count"]
    raw_total = summary_facts["raw_total"]
    queries_succeeded = summary_facts["queries_succeeded"]
    queries_total = summary_facts["queries_total"]

    return (
        f"Search completed: {candidate_count} unique candidates from {raw_total} "
        f"raw results, with {queries_succeeded}/{queries_total} queries succeeded. "
        f"Quality buckets: {quality['strong']} strong, {quality['review']} review, "
        f"{quality['weak']} weak. Strongest signals: exact Java evidence on "
        f"{signals['exact_technology']} candidates and target-role evidence on "
        f"{signals['target_or_close_role']} candidates. Main limitations: selected "
        f"stack was not visible in public snippets for "
        f"{signals['selected_stack_not_visible']} candidates, and seniority was not "
        f"visible for {signals['seniority_not_visible']} candidates. Suggested next "
        "step: review the strongest candidates first, then choose a non-executable "
        "next iteration option if the brief should change."
    )


def agent_response_message_ru(summary_facts: dict) -> str:
    quality = summary_facts["quality_distribution"]
    signals = summary_facts["strong_signal_counts"]
    candidate_count = summary_facts["candidate_count"]
    raw_total = summary_facts["raw_total"]
    queries_succeeded = summary_facts["queries_succeeded"]
    queries_total = summary_facts["queries_total"]

    return (
        f"\u041f\u043e\u0438\u0441\u043a \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d: {candidate_count} "
        f"\u0443\u043d\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u0445 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432 "
        f"\u0438\u0437 {raw_total} raw results, \u0443\u0441\u043f\u0435\u0448\u043d\u043e "
        f"{queries_succeeded}/{queries_total} \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432. "
        f"Quality buckets: {quality['strong']} strong, {quality['review']} review, "
        f"{quality['weak']} weak. \u0421\u0438\u043b\u044c\u043d\u044b\u0435 "
        f"\u0441\u0438\u0433\u043d\u0430\u043b\u044b: Java \u0432\u0438\u0434\u0435\u043d "
        f"\u0443 {signals['exact_technology']} \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432, "
        f"\u0446\u0435\u043b\u0435\u0432\u0430\u044f \u0440\u043e\u043b\u044c "
        f"\u0432\u0438\u0434\u043d\u0430 \u0443 {signals['target_or_close_role']}. "
        f"\u041e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u044f: selected stack "
        f"\u043d\u0435 \u0432\u0438\u0434\u0435\u043d \u0432 public snippets "
        f"\u0443 {signals['selected_stack_not_visible']} \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432, "
        f"seniority \u043d\u0435 \u0432\u0438\u0434\u0435\u043d \u0443 "
        f"{signals['seniority_not_visible']}. \u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 "
        "\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u044b\u0439 \u0448\u0430\u0433: "
        "\u043f\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c "
        "\u0441\u0438\u043b\u044c\u043d\u044b\u0445 "
        "\u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432 \u0438 "
        "\u0432\u044b\u0431\u0440\u0430\u0442\u044c \u043e\u0434\u043d\u0443 "
        "\u0438\u0437 non-executable next iteration options "
        "\u043d\u0438\u0436\u0435, \u0435\u0441\u043b\u0438 Search Brief "
        "\u043d\u0443\u0436\u043d\u043e \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c."
    )


def agent_response_quality_notes(
    language: str,
    summary_facts: dict,
) -> list[dict[str, object]]:
    quality = summary_facts["quality_distribution"]
    signals = summary_facts["strong_signal_counts"]

    if language == "ru":
        return [
            {
                "kind": "quality_distribution",
                "message": (
                    f"Quality buckets: {quality['strong']} strong, "
                    f"{quality['review']} review, {quality['weak']} weak."
                ),
                "facts": quality,
            },
            {
                "kind": "signals",
                "message": (
                    "Java \u0438 \u0440\u043e\u043b\u044c \u0441\u0447\u0438\u0442\u0430\u044e\u0442\u0441\u044f "
                    "\u0441\u0438\u043b\u044c\u043d\u044b\u043c\u0438 \u0442\u043e\u043b\u044c\u043a\u043e "
                    "\u043a\u043e\u0433\u0434\u0430 \u043e\u043d\u0438 \u0432\u0438\u0434\u043d\u044b "
                    "\u0432 public profile text."
                ),
                "facts": signals,
            },
        ]

    return [
        {
            "kind": "quality_distribution",
            "message": (
                f"Quality buckets: {quality['strong']} strong, "
                f"{quality['review']} review, {quality['weak']} weak."
            ),
            "facts": quality,
        },
        {
            "kind": "signals",
            "message": (
                "Java and role signals count as strong only when visible in "
                "public profile text."
            ),
            "facts": signals,
        },
    ]


def agent_response_limitations(language: str, summary_facts: dict) -> list[dict[str, object]]:
    signals = summary_facts["strong_signal_counts"]
    if language == "ru":
        return [
            {
                "kind": "public_snippets",
                "message": (
                    "\u041e\u0442\u0432\u0435\u0442 \u043e\u0441\u043d\u043e\u0432\u0430\u043d "
                    "\u0442\u043e\u043b\u044c\u043a\u043e \u043d\u0430 public snippets "
                    "\u0438 \u0434\u0430\u043d\u043d\u044b\u0445, \u0443\u0436\u0435 "
                    "\u0432\u0435\u0440\u043d\u0443\u0442\u044b\u0445 backend."
                ),
            },
            {
                "kind": "stack_visibility",
                "message": (
                    "Selected stack \u043d\u0435 \u0432\u0438\u0434\u0435\u043d "
                    f"\u0432 public snippets \u0443 {signals['selected_stack_not_visible']} "
                    "\u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432; "
                    "\u044d\u0442\u043e \u043d\u0435 \u0434\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0435\u0442, "
                    "\u0447\u0442\u043e \u0443 \u043d\u0438\u0445 \u043d\u0435\u0442 "
                    "\u044d\u0442\u043e\u0433\u043e stack."
                ),
            },
            {
                "kind": "seniority_visibility",
                "message": (
                    "Seniority \u043d\u0435 \u0432\u0438\u0434\u0435\u043d "
                    f"\u0443 {signals['seniority_not_visible']} "
                    "\u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432."
                ),
            },
        ]

    return [
        {
            "kind": "public_snippets",
            "message": (
                "This response is based only on public snippets and data already "
                "returned by the backend."
            ),
        },
        {
            "kind": "stack_visibility",
            "message": (
                "Selected stack is not visible in public snippets for "
                f"{signals['selected_stack_not_visible']} candidates; this does "
                "not prove they lack that stack."
            ),
        },
        {
            "kind": "seniority_visibility",
            "message": (
                f"Seniority is not visible for {signals['seniority_not_visible']} "
                "candidates."
            ),
        },
    ]


def agent_response_suggested_next_actions(
    language: str,
    summary_facts: dict,
) -> list[dict[str, object]]:
    if language == "ru":
        actions = [
            {
                "label": "\u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c top candidates",
                "description": (
                    "\u041d\u0430\u0447\u0430\u0442\u044c \u0441 strong bucket "
                    "\u0438 \u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c "
                    "\u043f\u0440\u043e\u0444\u0438\u043b\u0438 \u0432\u0440\u0443\u0447\u043d\u0443\u044e."
                ),
                "executable": False,
            },
            {
                "label": "\u0423\u0442\u043e\u0447\u043d\u0438\u0442\u044c stack",
                "description": (
                    "\u0415\u0441\u043b\u0438 stack \u0432 snippets "
                    "\u0432\u0438\u0434\u0435\u043d \u0441\u043b\u0430\u0431\u043e, "
                    "\u043c\u043e\u0436\u043d\u043e \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c "
                    "\u0438\u043b\u0438 \u0441\u0443\u0437\u0438\u0442\u044c stack."
                ),
                "executable": False,
            },
        ]
        return actions

    actions = [
        {
            "label": "Review top candidates",
            "description": "Start with the strong bucket and manually inspect profiles.",
            "executable": False,
        },
        {
            "label": "Adjust stack",
            "description": (
                "If stack visibility is weak in snippets, consider narrowing or "
                "changing selected stack terms."
            ),
            "executable": False,
        },
    ]
    return actions


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
        options.append(
            next_iteration_option(
                "review_high_quality_candidates",
                "Review high-quality candidates first",
                (
                    f"{strong_count} candidates are in the strong quality bucket. "
                    "This is a review-focus suggestion only and does not change the Search Brief."
                ),
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
        options.append(
            next_iteration_option(
                "narrow_to_visible_selected_stack",
                "Narrow stack to visible selected terms",
                (
                    "Current results directly show "
                    f"{', '.join(visible_selected_stack)}, while "
                    f"{', '.join(missing_selected_stack)} is not visible in returned snippets."
                ),
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
        options.append(
            next_iteration_option(
                "broaden_with_observed_stack",
                f"Broaden stack with {term}",
                (
                    f"{term} is visible in {count} returned candidates but is not "
                    "part of the selected stack."
                ),
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
        options.append(
            next_iteration_option(
                "clarify_stack_preference",
                "Clarify stack preference",
                (
                    "Selected stack is not directly visible in the returned public snippets. "
                    "The safest next step is to ask whether to keep or replace it."
                ),
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
        options.append(
            next_iteration_option(
                "try_deep_search_depth",
                "Try deep search depth",
                (
                    "The current Search Brief uses standard depth. Deep depth is "
                    "a brief-level change that still requires Build Plan and approval."
                ),
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
        ),
        "language": normalized_language,
        "source": "backend_returned_search_data",
        "requires_approval_for_execution": True,
    }


