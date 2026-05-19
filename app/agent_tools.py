from dataclasses import dataclass

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

AGENT_TOOL_CATEGORY_VALIDATION = "validation"
AGENT_TOOL_CATEGORY_PLANNING = "planning"
AGENT_TOOL_CATEGORY_EXECUTION = "execution"
AGENT_TOOL_CATEGORY_ANALYSIS = "analysis"
AGENT_TOOL_CATEGORY_SUGGESTION = "suggestion"

AGENT_TOOL_RISK_LEVEL_PLANNING = "planning"
AGENT_TOOL_RISK_LEVEL_ANALYSIS = "analysis"
AGENT_TOOL_RISK_LEVEL_SUGGESTION = "suggestion"
AGENT_TOOL_RISK_LEVEL_EXECUTION = "execution"

AGENT_RUNTIME_ERROR_UNSUPPORTED_TOOL = "unsupported_tool"
AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT = "invalid_tool_input"
AGENT_RUNTIME_ERROR_UNSUPPORTED_FLOW = "unsupported_flow"
AGENT_RUNTIME_ERROR_STALE_CONTEXT = "stale_context"
AGENT_RUNTIME_ERROR_APPROVAL_REQUIRED = "approval_required"
AGENT_RUNTIME_ERROR_APPROVAL_MISMATCH = "approval_mismatch"
AGENT_RUNTIME_ERROR_POLICY_BLOCKED = "policy_blocked"
AGENT_RUNTIME_ERROR_EXECUTION_FAILED = "execution_failed"
AGENT_RUNTIME_ERROR_TOOL_UNAVAILABLE = "tool_unavailable"
AGENT_RUNTIME_ERROR_INTERNAL_ERROR = "internal_error"
AGENT_RUNTIME_ERROR_BACKEND_OWNED_FIELD = "backend_owned_field_in_proposal"
AGENT_RUNTIME_ERROR_UNSUPPORTED_PROPOSAL_FIELD = "unsupported_proposal_field"
AGENT_RUNTIME_ERROR_INVALID_RUNTIME_CONTEXT = "invalid_runtime_context"

AGENT_TOOL_APPROVAL_STATUSES = [
    AGENT_TOOL_APPROVAL_NOT_REQUIRED,
    AGENT_TOOL_APPROVAL_REQUIRED,
    AGENT_TOOL_APPROVAL_APPROVED,
    AGENT_TOOL_APPROVAL_REJECTED,
]

AGENT_TOOL_RISK_LEVELS = [
    AGENT_TOOL_RISK_LEVEL_PLANNING,
    AGENT_TOOL_RISK_LEVEL_ANALYSIS,
    AGENT_TOOL_RISK_LEVEL_SUGGESTION,
    AGENT_TOOL_RISK_LEVEL_EXECUTION,
]

AGENT_RUNTIME_ERROR_CODES = [
    AGENT_RUNTIME_ERROR_UNSUPPORTED_TOOL,
    AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
    AGENT_RUNTIME_ERROR_UNSUPPORTED_FLOW,
    AGENT_RUNTIME_ERROR_STALE_CONTEXT,
    AGENT_RUNTIME_ERROR_APPROVAL_REQUIRED,
    AGENT_RUNTIME_ERROR_APPROVAL_MISMATCH,
    AGENT_RUNTIME_ERROR_POLICY_BLOCKED,
    AGENT_RUNTIME_ERROR_EXECUTION_FAILED,
    AGENT_RUNTIME_ERROR_TOOL_UNAVAILABLE,
    AGENT_RUNTIME_ERROR_INTERNAL_ERROR,
    AGENT_RUNTIME_ERROR_BACKEND_OWNED_FIELD,
    AGENT_RUNTIME_ERROR_UNSUPPORTED_PROPOSAL_FIELD,
    AGENT_RUNTIME_ERROR_INVALID_RUNTIME_CONTEXT,
]


@dataclass(frozen=True)
class AgentToolDefinition:
    tool_name: str
    requires_approval: bool
    description: str
    category: str
    risk_level: str

    def legacy_contract(self) -> dict:
        return {
            "requires_approval": self.requires_approval,
            "description": self.description,
        }

    def registry_metadata(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "requires_approval": self.requires_approval,
            "description": self.description,
            "category": self.category,
            "risk_level": self.risk_level,
        }


AGENT_TOOL_DEFINITIONS = {
    "validate_search_brief": AgentToolDefinition(
        tool_name="validate_search_brief",
        requires_approval=False,
        description="Validate and normalize Search Brief v0.",
        category=AGENT_TOOL_CATEGORY_VALIDATION,
        risk_level=AGENT_TOOL_RISK_LEVEL_PLANNING,
    ),
    "adapt_brief_to_structured_request": AgentToolDefinition(
        tool_name="adapt_brief_to_structured_request",
        requires_approval=False,
        description="Adapt a ready Search Brief into StructuredSearchRequest.",
        category=AGENT_TOOL_CATEGORY_VALIDATION,
        risk_level=AGENT_TOOL_RISK_LEVEL_PLANNING,
    ),
    AGENT_ACTION_BUILD_QUERY_PLAN: AgentToolDefinition(
        tool_name=AGENT_ACTION_BUILD_QUERY_PLAN,
        requires_approval=False,
        description="Build a QueryPlan without executing search.",
        category=AGENT_TOOL_CATEGORY_PLANNING,
        risk_level=AGENT_TOOL_RISK_LEVEL_PLANNING,
    ),
    "validate_query_plan": AgentToolDefinition(
        tool_name="validate_query_plan",
        requires_approval=False,
        description="Validate a QueryPlan deterministically before execution.",
        category=AGENT_TOOL_CATEGORY_VALIDATION,
        risk_level=AGENT_TOOL_RISK_LEVEL_PLANNING,
    ),
    EXECUTION_ACTION_SINGLE_WAVE: AgentToolDefinition(
        tool_name=EXECUTION_ACTION_SINGLE_WAVE,
        requires_approval=True,
        description="Run single-wave Tavily search through the backend pipeline.",
        category=AGENT_TOOL_CATEGORY_EXECUTION,
        risk_level=AGENT_TOOL_RISK_LEVEL_EXECUTION,
    ),
    EXECUTION_ACTION_MULTI_WAVE: AgentToolDefinition(
        tool_name=EXECUTION_ACTION_MULTI_WAVE,
        requires_approval=True,
        description="Run explicit multi-wave search through the backend pipeline.",
        category=AGENT_TOOL_CATEGORY_EXECUTION,
        risk_level=AGENT_TOOL_RISK_LEVEL_EXECUTION,
    ),
    "analyze_candidate_quality": AgentToolDefinition(
        tool_name="analyze_candidate_quality",
        requires_approval=False,
        description="Analyze already returned candidate quality signals.",
        category=AGENT_TOOL_CATEGORY_ANALYSIS,
        risk_level=AGENT_TOOL_RISK_LEVEL_ANALYSIS,
    ),
    "summarize_search_results": AgentToolDefinition(
        tool_name="summarize_search_results",
        requires_approval=False,
        description="Summarize already available report and result data.",
        category=AGENT_TOOL_CATEGORY_ANALYSIS,
        risk_level=AGENT_TOOL_RISK_LEVEL_ANALYSIS,
    ),
    "suggest_next_iteration": AgentToolDefinition(
        tool_name="suggest_next_iteration",
        requires_approval=False,
        description="Suggest the next sourcing iteration without executing it.",
        category=AGENT_TOOL_CATEGORY_SUGGESTION,
        risk_level=AGENT_TOOL_RISK_LEVEL_SUGGESTION,
    ),
}

AGENT_TOOLS_V0 = {
    tool_name: definition.legacy_contract()
    for tool_name, definition in AGENT_TOOL_DEFINITIONS.items()
}


def agent_tool_definition(tool_name: str) -> AgentToolDefinition | None:
    return AGENT_TOOL_DEFINITIONS.get(tool_name)


def agent_tool_registry() -> dict:
    return {
        tool_name: definition.registry_metadata()
        for tool_name, definition in AGENT_TOOL_DEFINITIONS.items()
    }


def agent_tool_contract() -> dict:
    return {
        "tools": AGENT_TOOLS_V0,
        "approval_statuses": list(AGENT_TOOL_APPROVAL_STATUSES),
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
