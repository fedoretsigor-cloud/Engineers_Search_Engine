import json
import re

from app.domain_config import (
    AI_PLANNER_COVERAGE_NOT_CONFIGURED_WARNING,
    AI_PLANNER_COVERAGE_POLICIES,
    FORBIDDEN_AI_QUERY_TERMS,
    PLANNER_MODE_AI,
    PLANNER_MODE_RULE_BASED,
    PROFILE_SOURCE_LINKEDIN_PUBLIC,
    QUERY_PLAN_MAX_RESULTS,
    QUERY_PLAN_REPORTING_FIELDS,
    SEARCH_DEPTH_STANDARD,
)
from app.planning import RuleBasedQueryPlannerV1, add_plan_validation_error
from app.text_utils import compact_spaces, find_term_match


def ai_planner_coverage_policy_for(
    normalized_brief: dict,
    normalized_request: dict,
) -> dict | None:
    search_depth = normalized_brief.get("search_depth") or SEARCH_DEPTH_STANDARD

    for policy in AI_PLANNER_COVERAGE_POLICIES:
        if (
            normalized_request.get("role_family") == policy["role_family"]
            and normalized_request.get("technology") == policy["technology"]
            and (normalized_request.get("location") or "").strip().lower()
            == policy["location"].lower()
            and search_depth == policy["search_depth"]
        ):
            policy_copy = dict(policy)
            policy_copy["selected_stack"] = normalized_request.get("stack", [])
            return policy_copy

    return None


def ai_planner_coverage_policy_prompt(
    coverage_policy: dict | None,
    normalized_request: dict,
) -> dict:
    if not coverage_policy:
        return {
            "configured": False,
            "warning": AI_PLANNER_COVERAGE_NOT_CONFIGURED_WARNING,
        }

    expected_plan = RuleBasedQueryPlannerV1().build(normalized_request)
    return {
        "configured": True,
        "policy_id": coverage_policy["policy_id"],
        "policy_version": coverage_policy["policy_version"],
        "expected_query_count": coverage_policy["expected_query_count"],
        "required_shape": {
            "role_based_min": coverage_policy["role_based_min"],
            "stack_focused_min": coverage_policy["stack_focused_min"],
            "min_role_phrase_diversity": coverage_policy[
                "min_role_phrase_diversity"
            ],
        },
        "selected_stack": coverage_policy.get("selected_stack", []),
        "max_ai_plan_revision_attempts": coverage_policy[
            "max_ai_plan_revision_attempts"
        ],
        "query_slot_blueprint": [
            {
                "id": query["id"],
                "category": query["category"],
                "purpose": query["purpose"],
                "role_phrase": query["role_phrase"],
                "uses_stack": query.get("uses_stack", []),
                "query": query["query"],
                "max_results": query["max_results"],
            }
            for query in expected_plan.get("queries", [])
        ],
    }


def normalize_ai_text_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []

    return [str(value) for value in values if str(value or "").strip()]


def ai_plan_output_warnings(ai_output: dict | None) -> list[str]:
    if not isinstance(ai_output, dict):
        return []

    return normalize_ai_text_list(ai_output.get("warnings", []))


def ai_plan_output_assumptions(ai_output: dict | None) -> list[str]:
    if not isinstance(ai_output, dict):
        return []

    return normalize_ai_text_list(ai_output.get("assumptions", []))


def ai_query_planner_system_prompt() -> str:
    return (
        "You are an AI Query Planner for a recruiter sourcing search engine. "
        "Return only valid JSON. You may propose a draft QueryPlan, but you must not "
        "execute searches, browse the web, scrape LinkedIn, log in to LinkedIn, send "
        "messages, or act on accounts. Build LinkedIn public profile X-ray queries only "
        "inside the approved QueryPlan contract."
    )


def ai_query_planner_user_prompt(
    normalized_brief: dict,
    normalized_request: dict,
    repair_feedback: list[dict[str, str]] | None = None,
    previous_draft_plan: dict | None = None,
) -> str:
    coverage_policy = ai_planner_coverage_policy_for(
        normalized_brief,
        normalized_request,
    )
    coverage_policy_prompt = ai_planner_coverage_policy_prompt(
        coverage_policy,
        normalized_request,
    )
    is_repair = bool(repair_feedback)
    task = (
        "Repair the previous draft QueryPlan using the coverage feedback."
        if is_repair
        else "Create a draft QueryPlan for recruiter sourcing."
    )

    return json.dumps(
        {
            "task": task,
            "required_output": {
                "planner_version": "ai_query_planner_v0",
                "planner_mode": "ai",
                "explanation": "Short explanation of the planning logic.",
                "draft_query_plan": {
                    "planner_version": "ai_query_planner_v0",
                    "planner_mode": "ai",
                    "input_snapshot": normalized_request,
                    "queries": coverage_policy_prompt.get("query_slot_blueprint")
                    or [
                        {
                            "id": "Q01",
                            "category": "role_based",
                            "purpose": "Why this query exists.",
                            "role_phrase": "Role phrase used in query.",
                            "query": "site:linkedin.com/in AND \"Role\" AND \"Location\"",
                            "uses_stack": [],
                            "max_results": QUERY_PLAN_MAX_RESULTS,
                        }
                    ],
                    "filters": {
                        "linkedin_profiles_only": normalized_request[
                            "linkedin_profiles_only"
                        ],
                        "location_filter_enabled": normalized_request[
                            "location_filter_enabled"
                        ],
                    },
                    "execution": {
                        "mode": "sequential",
                        "max_results_per_query": QUERY_PLAN_MAX_RESULTS,
                    },
                    "reporting": QUERY_PLAN_REPORTING_FIELDS,
                },
                "warnings": [],
                "assumptions": [],
            },
            "search_brief": normalized_brief,
            "normalized_structured_request": normalized_request,
            "coverage_policy": coverage_policy_prompt,
            "repair_feedback": repair_feedback or [],
            "previous_draft_query_plan": previous_draft_plan if is_repair else None,
            "hard_limits": {
                "max_queries": 10,
                "expected_queries_when_coverage_policy_configured": coverage_policy_prompt.get(
                    "expected_query_count"
                ),
                "max_results_per_query": QUERY_PLAN_MAX_RESULTS,
                "allowed_source_scope": "site:linkedin.com/in",
                "allowed_profile_sources": [PROFILE_SOURCE_LINKEDIN_PUBLIC],
                "default_planner_remains": PLANNER_MODE_RULE_BASED,
            },
            "coverage_rules": [
                "If coverage_policy.configured is true, return exactly the expected query count.",
                "For the Java Backend Ukraine standard policy, return exactly 10 query slots.",
                "Use role-based coverage plus stack-focused coverage; do not collapse the plan to one broad query.",
                "For the Java Backend Ukraine standard policy, target at least 6 role-based slots and 4 stack-focused slots.",
                "Use diverse role phrases instead of repeating the same phrase across all slots.",
                "If selected stack terms are present, stack-focused slots must include those terms in the query text and uses_stack.",
            ],
            "safety_rules": [
                "Every query must include site:linkedin.com/in.",
                "Every query must include the target location.",
                "Every query must include the main technology signal from the brief.",
                "Every query must include a role signal from the brief or policy blueprint.",
                "Do not include arbitrary domains.",
                "Do not include LinkedIn login, scraping, bypass, messaging, or account-action behavior.",
                "Do not change filters, scoring, dedupe, location filtering, or execution behavior.",
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


def query_site_scopes(query: str) -> list[str]:
    return re.findall(r"(?i)\bsite:([^\s)]+)", query or "")


def query_has_forbidden_terms(query: str) -> bool:
    lowered_query = (query or "").lower()
    return any(term in lowered_query for term in FORBIDDEN_AI_QUERY_TERMS)


def query_has_allowed_scope_only(query: str) -> bool:
    scopes = [scope.lower().strip('"') for scope in query_site_scopes(query)]
    return bool(scopes) and all(scope == "linkedin.com/in" for scope in scopes)


def query_has_brief_signal(query: str, normalized_request: dict) -> bool:
    technology = normalized_request.get("technology")
    role_family = normalized_request.get("role_family")
    if technology and find_term_match(query, technology):
        return True
    if role_family and all(
        find_term_match(query, term)
        for term in re.findall(r"[A-Za-z][A-Za-z+#.]*", role_family)
    ):
        return True
    return False


def validate_ai_query_plan(
    draft_plan: dict | None,
    normalized_brief: dict,
    normalized_request: dict,
) -> tuple[dict | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    if not isinstance(draft_plan, dict):
        add_plan_validation_error(
            errors,
            "draft_query_plan",
            "invalid_plan_shape",
            "AI draft plan must be an object.",
        )
        return None, errors

    for field in [
        "planner_version",
        "planner_mode",
        "input_snapshot",
        "queries",
        "filters",
        "execution",
        "reporting",
    ]:
        if field not in draft_plan:
            add_plan_validation_error(
                errors,
                field,
                "missing_required_field",
                f"QueryPlan is missing {field}.",
            )

    queries = draft_plan.get("queries")
    if not isinstance(queries, list) or not queries:
        add_plan_validation_error(
            errors,
            "queries",
            "invalid_queries",
            "QueryPlan must contain at least one query.",
        )
        queries = []

    if len(queries) > 10:
        add_plan_validation_error(
            errors,
            "queries",
            "too_many_queries",
            "Standard AI QueryPlan must not exceed 10 queries.",
        )

    planner_mode = draft_plan.get("planner_mode")
    if planner_mode != PLANNER_MODE_AI:
        add_plan_validation_error(
            errors,
            "planner_mode",
            "invalid_planner_mode",
            "AI QueryPlan must declare planner_mode as ai.",
        )

    seen_query_ids: set[str] = set()
    for index, query_slot in enumerate(queries):
        field_prefix = f"queries[{index}]"
        if not isinstance(query_slot, dict):
            add_plan_validation_error(
                errors,
                field_prefix,
                "invalid_query_slot",
                "Query slot must be an object.",
            )
            continue

        for field in [
            "id",
            "category",
            "purpose",
            "role_phrase",
            "query",
            "uses_stack",
            "max_results",
        ]:
            if field not in query_slot:
                add_plan_validation_error(
                    errors,
                    f"{field_prefix}.{field}",
                    "missing_required_field",
                    f"Query slot is missing {field}.",
                )

        query_id = query_slot.get("id")
        if query_id in seen_query_ids:
            add_plan_validation_error(
                errors,
                f"{field_prefix}.id",
                "duplicate_query_id",
                "Query IDs must be unique.",
            )
        elif query_id:
            seen_query_ids.add(query_id)

        query = query_slot.get("query") or ""
        if not query:
            add_plan_validation_error(
                errors,
                f"{field_prefix}.query",
                "empty_query",
                "Query string must not be empty.",
            )
        else:
            if not query_has_allowed_scope_only(query):
                add_plan_validation_error(
                    errors,
                    f"{field_prefix}.query",
                    "invalid_source_scope",
                    "Query must use only site:linkedin.com/in.",
                )
            if query_has_forbidden_terms(query):
                add_plan_validation_error(
                    errors,
                    f"{field_prefix}.query",
                    "forbidden_query_behavior",
                    "Query contains forbidden behavior terms.",
                )
            location = normalized_request.get("location")
            if location and not find_term_match(query, location):
                add_plan_validation_error(
                    errors,
                    f"{field_prefix}.query",
                    "missing_target_location",
                    f"Query does not include target location {location}.",
                )
            if not query_has_brief_signal(query, normalized_request):
                add_plan_validation_error(
                    errors,
                    f"{field_prefix}.query",
                    "missing_role_or_technology_signal",
                    "Query must include a role or technology signal from the brief.",
                )

        max_results = query_slot.get("max_results")
        if not isinstance(max_results, int) or max_results > QUERY_PLAN_MAX_RESULTS:
            add_plan_validation_error(
                errors,
                f"{field_prefix}.max_results",
                "invalid_max_results",
                f"max_results must be an integer no greater than {QUERY_PLAN_MAX_RESULTS}.",
            )

        uses_stack = query_slot.get("uses_stack")
        if uses_stack is not None and not isinstance(uses_stack, list):
            add_plan_validation_error(
                errors,
                f"{field_prefix}.uses_stack",
                "invalid_uses_stack",
                "uses_stack must be a list.",
            )

    filters = draft_plan.get("filters") or {}
    if filters:
        if filters.get("linkedin_profiles_only") is False:
            add_plan_validation_error(
                errors,
                "filters.linkedin_profiles_only",
                "filter_override_not_allowed",
                "AI plan must not disable LinkedIn profiles only filter.",
            )
        if filters.get("location_filter_enabled") is False:
            add_plan_validation_error(
                errors,
                "filters.location_filter_enabled",
                "filter_override_not_allowed",
                "AI plan must not disable location filter.",
            )

    execution = draft_plan.get("execution") or {}
    if execution and execution.get("mode") not in {None, "sequential"}:
        add_plan_validation_error(
            errors,
            "execution.mode",
            "unsupported_execution_mode",
            "AI plan execution mode must remain sequential.",
        )

    if errors:
        return None, errors

    validated_plan = {
        **draft_plan,
        "planner_version": draft_plan.get("planner_version") or "ai_query_planner_v0",
        "planner_mode": PLANNER_MODE_AI,
        "input_snapshot": normalized_request,
        "filters": {
            "linkedin_profiles_only": normalized_request["linkedin_profiles_only"],
            "location_filter_enabled": normalized_request["location_filter_enabled"],
        },
        "execution": {
            "mode": "sequential",
            "max_results_per_query": QUERY_PLAN_MAX_RESULTS,
        },
        "reporting": QUERY_PLAN_REPORTING_FIELDS,
    }

    return validated_plan, []


def role_phrase_key(value: object) -> str:
    return compact_spaces(str(value or "")).lower()


def query_slot_stack_terms(query_slot: dict, selected_stack: list[str]) -> list[str]:
    query = query_slot.get("query") or ""
    uses_stack = query_slot.get("uses_stack")
    if not isinstance(uses_stack, list):
        uses_stack = []

    matched_terms = []
    for stack_term in selected_stack:
        if stack_term in uses_stack and find_term_match(query, stack_term):
            matched_terms.append(stack_term)

    return matched_terms


def query_slot_is_stack_focused(query_slot: dict, selected_stack: list[str]) -> bool:
    return bool(query_slot_stack_terms(query_slot, selected_stack))


def validate_ai_query_plan_coverage(
    query_plan: dict,
    normalized_brief: dict,
    normalized_request: dict,
) -> tuple[list[dict[str, str]], list[str], dict | None]:
    coverage_policy = ai_planner_coverage_policy_for(
        normalized_brief,
        normalized_request,
    )
    if not coverage_policy:
        return [], [AI_PLANNER_COVERAGE_NOT_CONFIGURED_WARNING], None

    errors: list[dict[str, str]] = []
    queries = [
        query
        for query in query_plan.get("queries", [])
        if isinstance(query, dict)
    ]
    selected_stack = coverage_policy.get("selected_stack", [])
    expected_query_count = coverage_policy["expected_query_count"]

    if len(queries) != expected_query_count:
        add_plan_validation_error(
            errors,
            "coverage.query_count",
            "undercovered_query_count",
            (
                f"AI plan returned {len(queries)} queries, but coverage policy "
                f"requires exactly {expected_query_count} queries."
            ),
        )

    stack_focused_queries = [
        query for query in queries if query_slot_is_stack_focused(query, selected_stack)
    ]
    stack_focused_query_ids = {id(query) for query in stack_focused_queries}
    role_based_queries = [
        query for query in queries if id(query) not in stack_focused_query_ids
    ]

    if len(role_based_queries) < coverage_policy["role_based_min"]:
        add_plan_validation_error(
            errors,
            "coverage.role_based",
            "missing_role_based_coverage",
            (
                f"AI plan has {len(role_based_queries)} role-based queries, but "
                f"coverage policy requires at least {coverage_policy['role_based_min']}."
            ),
        )

    if selected_stack and len(stack_focused_queries) < coverage_policy["stack_focused_min"]:
        add_plan_validation_error(
            errors,
            "coverage.stack_focused",
            "missing_stack_focused_coverage",
            (
                f"AI plan has {len(stack_focused_queries)} stack-focused queries, but "
                f"coverage policy requires at least {coverage_policy['stack_focused_min']}."
            ),
        )

    role_phrase_count = len(
        {
            role_phrase_key(query.get("role_phrase"))
            for query in queries
            if role_phrase_key(query.get("role_phrase"))
        }
    )
    if role_phrase_count < coverage_policy["min_role_phrase_diversity"]:
        add_plan_validation_error(
            errors,
            "coverage.role_phrase_diversity",
            "insufficient_role_phrase_diversity",
            (
                f"AI plan has {role_phrase_count} distinct role phrases, but "
                "coverage policy requires at least "
                f"{coverage_policy['min_role_phrase_diversity']}."
            ),
        )

    technology = normalized_request.get("technology")
    if technology:
        missing_technology_indexes = [
            str(index + 1)
            for index, query in enumerate(queries)
            if not find_term_match(query.get("query") or "", technology)
        ]
        if missing_technology_indexes:
            add_plan_validation_error(
                errors,
                "coverage.technology",
                "missing_technology_signal",
                (
                    "AI plan has queries without the required technology signal: "
                    + ", ".join(missing_technology_indexes)
                    + "."
                ),
            )

    location = normalized_request.get("location")
    if location:
        missing_location_indexes = [
            str(index + 1)
            for index, query in enumerate(queries)
            if not find_term_match(query.get("query") or "", location)
        ]
        if missing_location_indexes:
            add_plan_validation_error(
                errors,
                "coverage.location",
                "missing_target_location",
                (
                    "AI plan has queries without the required target location: "
                    + ", ".join(missing_location_indexes)
                    + "."
                ),
            )

    if selected_stack:
        stack_terms_seen = {
            term
            for query in stack_focused_queries
            for term in query_slot_stack_terms(query, selected_stack)
        }
        missing_stack_terms = [
            term for term in selected_stack if term not in stack_terms_seen
        ]
        if missing_stack_terms:
            add_plan_validation_error(
                errors,
                "coverage.stack_terms",
                "missing_selected_stack_terms",
                (
                    "AI plan stack-focused queries did not cover selected stack terms: "
                    + ", ".join(missing_stack_terms)
                    + "."
                ),
            )

    return errors, [], coverage_policy
