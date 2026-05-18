from app.domain_config import PLANNER_MODE_RULE_BASED
from app.planning import add_plan_validation_error, query_plan_fingerprint
from app.schemas import ExecutionApproval


EXECUTION_ACTION_SINGLE_WAVE = "run_single_wave_search"
EXECUTION_ACTION_MULTI_WAVE = "run_multi_wave_search"

AGENT_TOOL_APPROVAL_NOT_REQUIRED = "not_required"
AGENT_TOOL_APPROVAL_REQUIRED = "required"
AGENT_TOOL_APPROVAL_APPROVED = "approved"
AGENT_TOOL_APPROVAL_REJECTED = "rejected"

AGENT_ACTION_BUILD_QUERY_PLAN = "build_query_plan"
AGENT_QUERY_PLAN_ENDPOINT = "/api/agent/query-plan"

AGENT_TOOLS_V0 = {
    "validate_search_brief": {
        "requires_approval": False,
        "description": "Validate and normalize Search Brief v0.",
    },
    "adapt_brief_to_structured_request": {
        "requires_approval": False,
        "description": "Adapt a ready Search Brief into StructuredSearchRequest.",
    },
    AGENT_ACTION_BUILD_QUERY_PLAN: {
        "requires_approval": False,
        "description": "Build a QueryPlan without executing search.",
    },
    "validate_query_plan": {
        "requires_approval": False,
        "description": "Validate a QueryPlan deterministically before execution.",
    },
    EXECUTION_ACTION_SINGLE_WAVE: {
        "requires_approval": True,
        "description": "Run single-wave Tavily search through the backend pipeline.",
    },
    EXECUTION_ACTION_MULTI_WAVE: {
        "requires_approval": True,
        "description": "Run explicit multi-wave search through the backend pipeline.",
    },
    "analyze_candidate_quality": {
        "requires_approval": False,
        "description": "Analyze already returned candidate quality signals.",
    },
    "summarize_search_results": {
        "requires_approval": False,
        "description": "Summarize already available report and result data.",
    },
    "suggest_next_iteration": {
        "requires_approval": False,
        "description": "Suggest the next sourcing iteration without executing it.",
    },
}


def agent_tool_contract() -> dict:
    return {
        "tools": AGENT_TOOLS_V0,
        "approval_statuses": [
            AGENT_TOOL_APPROVAL_NOT_REQUIRED,
            AGENT_TOOL_APPROVAL_REQUIRED,
            AGENT_TOOL_APPROVAL_APPROVED,
            AGENT_TOOL_APPROVAL_REJECTED,
        ],
        "absolute_boundaries": [
            "no_direct_web_search_bypass",
            "no_linkedin_login",
            "no_linkedin_scraping_or_bypass",
            "no_automatic_candidate_messaging",
            "no_account_actions",
        ],
    }


def execution_approval_metadata(
    approval: ExecutionApproval,
    expected_action: str,
    query_plan: dict,
) -> dict:
    return {
        "approval_status": approval.approval_status,
        "approved_action": approval.approved_action,
        "approved_planner_mode": approval.approved_planner_mode,
        "approved_query_count": approval.approved_query_count,
        "approved_plan_fingerprint": approval.approved_plan_fingerprint,
        "expected_action": expected_action,
        "current_plan_fingerprint": query_plan_fingerprint(query_plan),
        "current_query_count": len(query_plan.get("queries", [])),
        "execution_allowed": True,
    }


def validate_execution_approval(
    approval: ExecutionApproval | None,
    expected_action: str,
    query_plan: dict,
) -> tuple[dict | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    current_fingerprint = query_plan_fingerprint(query_plan)
    current_query_count = len(query_plan.get("queries", []))

    if approval is None:
        add_plan_validation_error(
            errors,
            "execution_approval",
            "missing_execution_approval",
            "Tavily execution requires explicit approval for the visible QueryPlan.",
        )
        return None, errors

    if approval.approval_status != AGENT_TOOL_APPROVAL_APPROVED:
        add_plan_validation_error(
            errors,
            "execution_approval.approval_status",
            "approval_not_approved",
            "Execution approval status must be approved.",
        )

    if approval.approved_action != expected_action:
        add_plan_validation_error(
            errors,
            "execution_approval.approved_action",
            "wrong_execution_action",
            f"Approval must be for {expected_action}.",
        )

    if approval.approved_planner_mode != PLANNER_MODE_RULE_BASED:
        add_plan_validation_error(
            errors,
            "execution_approval.approved_planner_mode",
            "unsupported_execution_planner_mode",
            "Only rule_based QueryPlan execution is supported in this phase.",
        )

    if approval.approved_query_count != current_query_count:
        add_plan_validation_error(
            errors,
            "execution_approval.approved_query_count",
            "stale_or_mismatched_query_count",
            "Approved query count does not match the current QueryPlan.",
        )

    if approval.approved_plan_fingerprint != current_fingerprint:
        add_plan_validation_error(
            errors,
            "execution_approval.approved_plan_fingerprint",
            "stale_or_mismatched_plan_fingerprint",
            "Approved plan fingerprint does not match the current QueryPlan.",
        )

    if errors:
        return None, errors

    return execution_approval_metadata(approval, expected_action, query_plan), []
