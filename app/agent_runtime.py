from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any

from pydantic import ValidationError

from app.agent_tools import (
    AGENT_RUNTIME_ERROR_APPROVAL_MISMATCH,
    AGENT_RUNTIME_ERROR_BACKEND_OWNED_FIELD,
    AGENT_RUNTIME_ERROR_APPROVAL_REQUIRED,
    AGENT_RUNTIME_ERROR_INVALID_RUNTIME_CONTEXT,
    AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
    AGENT_RUNTIME_ERROR_STALE_CONTEXT,
    AGENT_RUNTIME_ERROR_UNSUPPORTED_FLOW,
    AGENT_RUNTIME_ERROR_UNSUPPORTED_PROPOSAL_FIELD,
    AGENT_RUNTIME_ERROR_UNSUPPORTED_TOOL,
    AGENT_TOOL_APPROVAL_APPROVED,
    AGENT_TOOL_APPROVAL_NOT_REQUIRED,
    AGENT_TOOL_APPROVAL_REQUIRED,
    AGENT_TOOL_RISK_LEVEL_EXECUTION,
    EXECUTION_ACTION_MULTI_WAVE,
    EXECUTION_ACTION_SINGLE_WAVE,
    agent_tool_definition,
)
from app.domain_config import PLANNER_MODE_RULE_BASED, SEARCH_DEPTH_STANDARD
from app.planning import RuleBasedQueryPlannerV1, query_plan_fingerprint
from app.schemas import (
    AgentRuntimeApproval,
    AgentRuntimeTurnRequest,
    MultiWaveStructuredSearchRequest,
    StructuredSearchRequest,
)
from app.search_validation import (
    normalize_multi_wave_search_request,
    normalize_structured_search_request,
)


AGENT_RUNTIME_STATE_BRIEF_DRAFT = "brief_draft"
AGENT_RUNTIME_STATE_BRIEF_READY = "brief_ready"
AGENT_RUNTIME_STATE_TOOL_PROPOSED = "tool_proposed"
AGENT_RUNTIME_STATE_APPROVAL_PENDING = "approval_pending"
AGENT_RUNTIME_STATE_APPROVED = "approved"
AGENT_RUNTIME_STATE_EXECUTING = "executing"
AGENT_RUNTIME_STATE_OBSERVED = "observed"
AGENT_RUNTIME_STATE_BLOCKED = "blocked"
AGENT_RUNTIME_STATE_ERROR = "error"

AGENT_RUNTIME_TURN_MODE_PREPARE = "prepare"
AGENT_RUNTIME_TURN_MODE_EXECUTE_APPROVED = "execute_approved"
AGENT_RUNTIME_EXECUTION_MODE_SINGLE_WAVE = "single_wave"
AGENT_RUNTIME_EXECUTION_MODE_MULTI_WAVE = "multi_wave"

AGENT_RUNTIME_STATES = [
    AGENT_RUNTIME_STATE_BRIEF_DRAFT,
    AGENT_RUNTIME_STATE_BRIEF_READY,
    AGENT_RUNTIME_STATE_TOOL_PROPOSED,
    AGENT_RUNTIME_STATE_APPROVAL_PENDING,
    AGENT_RUNTIME_STATE_APPROVED,
    AGENT_RUNTIME_STATE_EXECUTING,
    AGENT_RUNTIME_STATE_OBSERVED,
    AGENT_RUNTIME_STATE_BLOCKED,
    AGENT_RUNTIME_STATE_ERROR,
]

AGENT_RUNTIME_TURN_MODES = {
    AGENT_RUNTIME_TURN_MODE_PREPARE,
    AGENT_RUNTIME_TURN_MODE_EXECUTE_APPROVED,
}

AGENT_RUNTIME_EXECUTION_TOOLS = {
    EXECUTION_ACTION_SINGLE_WAVE,
    EXECUTION_ACTION_MULTI_WAVE,
}

AGENT_RUNTIME_SINGLE_WAVE_TOOL_INPUT_FIELDS = {
    "role_family",
    "technology",
    "stack",
    "location",
    "search_depth",
    "linkedin_profiles_only",
    "location_filter_enabled",
}

AGENT_RUNTIME_MULTI_WAVE_TOOL_INPUT_FIELDS = {
    *AGENT_RUNTIME_SINGLE_WAVE_TOOL_INPUT_FIELDS,
    "max_waves",
    "min_new_unique_per_wave",
    "patience",
}

AGENT_RUNTIME_BASE_CONTEXT_FIELDS = {
    "planner_mode",
    "tool_name",
    "execution_mode",
    "plan_fingerprint",
    "query_count",
    "search_brief_fingerprint",
    "multi_wave_enabled",
}

AGENT_RUNTIME_MULTI_WAVE_CONTEXT_FIELDS = {
    *AGENT_RUNTIME_BASE_CONTEXT_FIELDS,
    "max_waves",
    "min_new_unique_per_wave",
    "patience",
}

AGENT_TOOL_PROPOSAL_FIELDS = {"tool_name", "input", "reason"}
AGENT_TOOL_BACKEND_OWNED_FIELDS = {
    "requires_approval",
    "approval_status",
    "risk_level",
    "tool_input_fingerprint",
    "context_fingerprint",
    "idempotency_key",
    "is_executable",
    "tool_call_id",
    "result",
    "errors",
    "observations",
    "next_actions",
}


@dataclass(frozen=True)
class AgentToolProposal:
    tool_name: str
    input: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentToolCall:
    tool_call_id: str
    tool_name: str
    input: dict[str, Any]
    reason: str
    requires_approval: bool
    approval_status: str
    risk_level: str
    tool_input_fingerprint: str
    context_fingerprint: str
    idempotency_key: str | None
    is_executable: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentToolResult:
    tool_call_id: str
    tool_name: str
    ok: bool
    result: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, str]] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    next_actions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentRuntimeTurnResponse:
    ok: bool
    runtime_state: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    pending_approvals: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    next_actions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeExecutionBinding:
    tool_call: AgentToolCall
    tool_name: str
    execution_mode: str
    normalized_request: dict[str, Any]
    runtime_tool_input: dict[str, Any]
    runtime_context: dict[str, Any]
    query_plan: dict[str, Any]
    settings: dict[str, Any] | None = None


def runtime_error(field_name: str, code: str, message: str) -> dict[str, str]:
    return {"field": field_name, "code": code, "message": message}


def _prefixed_runtime_errors(
    errors: list[dict[str, str]],
    prefix: str,
    code: str,
) -> list[dict[str, str]]:
    return [
        runtime_error(
            f"{prefix}.{error.get('field', 'input')}",
            code,
            error.get("message", "Invalid runtime input."),
        )
        for error in errors
    ]


def _pydantic_runtime_errors(
    exc: ValidationError,
    prefix: str,
    code: str,
) -> list[dict[str, str]]:
    converted_errors: list[dict[str, str]] = []
    for error in exc.errors():
        loc = ".".join(str(part) for part in error.get("loc", []))
        converted_errors.append(
            runtime_error(
                f"{prefix}.{loc}" if loc else prefix,
                code,
                str(error.get("msg") or "Invalid runtime input."),
            )
        )
    return converted_errors


def runtime_pending_approval(tool_call: AgentToolCall) -> dict[str, Any]:
    return {
        "approval_status": AGENT_TOOL_APPROVAL_REQUIRED,
        "tool_call_id": tool_call.tool_call_id,
        "tool_name": tool_call.tool_name,
        "tool_input_fingerprint": tool_call.tool_input_fingerprint,
        "context_fingerprint": tool_call.context_fingerprint,
        "idempotency_key": tool_call.idempotency_key,
        "approval_label": "Approve & Search",
    }


def _runtime_tool_input_fields_for(tool_name: str) -> set[str]:
    if tool_name == EXECUTION_ACTION_MULTI_WAVE:
        return AGENT_RUNTIME_MULTI_WAVE_TOOL_INPUT_FIELDS
    return AGENT_RUNTIME_SINGLE_WAVE_TOOL_INPUT_FIELDS


def _runtime_context_fields_for(tool_name: str) -> set[str]:
    if tool_name == EXECUTION_ACTION_MULTI_WAVE:
        return AGENT_RUNTIME_MULTI_WAVE_CONTEXT_FIELDS
    return AGENT_RUNTIME_BASE_CONTEXT_FIELDS


def _normalize_runtime_tool_input(
    tool_name: str,
    tool_input: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[dict[str, str]]]:
    allowed_fields = _runtime_tool_input_fields_for(tool_name)
    extra_fields = sorted(set(tool_input) - allowed_fields)
    if extra_fields:
        return (
            None,
            None,
            [
                runtime_error(
                    "tool_input",
                    AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
                    f"Runtime tool input includes unsupported fields: {', '.join(extra_fields)}.",
                )
            ],
        )

    if tool_name == EXECUTION_ACTION_MULTI_WAVE:
        try:
            search_request = MultiWaveStructuredSearchRequest(**tool_input)
        except ValidationError as exc:
            return (
                None,
                None,
                _pydantic_runtime_errors(
                    exc,
                    "tool_input",
                    AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
                ),
            )
        normalized_request, settings, errors = normalize_multi_wave_search_request(
            search_request
        )
        if errors:
            return (
                None,
                None,
                _prefixed_runtime_errors(
                    errors,
                    "tool_input",
                    AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
                ),
            )
        return normalized_request, settings, []

    try:
        search_request = StructuredSearchRequest(**tool_input)
    except ValidationError as exc:
        return (
            None,
            None,
            _pydantic_runtime_errors(
                exc,
                "tool_input",
                AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
            ),
        )
    normalized_request, errors = normalize_structured_search_request(search_request)
    if errors:
        return (
            None,
            None,
            _prefixed_runtime_errors(
                errors,
                "tool_input",
                AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
            ),
        )
    return normalized_request, None, []


def _runtime_tool_input_from_normalized(
    normalized_request: dict[str, Any],
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runtime_tool_input = dict(normalized_request)
    if settings:
        runtime_tool_input.update(
            {
                "max_waves": settings["max_waves"],
                "min_new_unique_per_wave": settings[
                    "min_new_unique_per_wave"
                ],
                "patience": settings["patience"],
            }
        )
    return runtime_tool_input


def _validate_supported_runtime_flow(
    normalized_request: dict[str, Any],
) -> list[dict[str, str]]:
    if (
        normalized_request.get("role_family") == "Backend Developer"
        and normalized_request.get("technology") == "Java"
        and normalized_request.get("location") == "Ukraine"
        and normalized_request.get("search_depth") == SEARCH_DEPTH_STANDARD
        and normalized_request.get("stack")
    ):
        return []

    return [
        runtime_error(
            "tool_input",
            AGENT_RUNTIME_ERROR_UNSUPPORTED_FLOW,
            "Agent Runtime v0 supports only Backend Developer + Java + Ukraine + standard depth with at least one stack item.",
        )
    ]


def _validate_runtime_context(
    runtime_context: dict[str, Any],
    tool_name: str,
    query_plan: dict[str, Any],
    settings: dict[str, Any] | None,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    allowed_fields = _runtime_context_fields_for(tool_name)
    extra_fields = sorted(set(runtime_context) - allowed_fields)
    missing_fields = sorted(allowed_fields - set(runtime_context))
    if extra_fields:
        errors.append(
            runtime_error(
                "runtime_context",
                AGENT_RUNTIME_ERROR_INVALID_RUNTIME_CONTEXT,
                f"Runtime context includes unsupported fields: {', '.join(extra_fields)}.",
            )
        )
    if missing_fields:
        errors.append(
            runtime_error(
                "runtime_context",
                AGENT_RUNTIME_ERROR_INVALID_RUNTIME_CONTEXT,
                f"Runtime context is missing required fields: {', '.join(missing_fields)}.",
            )
        )
        return errors
    if extra_fields:
        return errors

    expected_execution_mode = (
        AGENT_RUNTIME_EXECUTION_MODE_MULTI_WAVE
        if tool_name == EXECUTION_ACTION_MULTI_WAVE
        else AGENT_RUNTIME_EXECUTION_MODE_SINGLE_WAVE
    )
    expected_multi_wave_enabled = tool_name == EXECUTION_ACTION_MULTI_WAVE
    current_plan_fingerprint = query_plan_fingerprint(query_plan)
    current_query_count = len(query_plan.get("queries", []))

    if runtime_context.get("planner_mode") != PLANNER_MODE_RULE_BASED:
        errors.append(
            runtime_error(
                "runtime_context.planner_mode",
                AGENT_RUNTIME_ERROR_STALE_CONTEXT,
                "Runtime execution supports only rule_based planner context.",
            )
        )
    if runtime_context.get("tool_name") != tool_name:
        errors.append(
            runtime_error(
                "runtime_context.tool_name",
                AGENT_RUNTIME_ERROR_STALE_CONTEXT,
                "Runtime context tool_name does not match the requested tool.",
            )
        )
    if runtime_context.get("execution_mode") != expected_execution_mode:
        errors.append(
            runtime_error(
                "runtime_context.execution_mode",
                AGENT_RUNTIME_ERROR_STALE_CONTEXT,
                "Runtime context execution mode does not match the requested tool.",
            )
        )
    if not isinstance(runtime_context.get("multi_wave_enabled"), bool):
        errors.append(
            runtime_error(
                "runtime_context.multi_wave_enabled",
                AGENT_RUNTIME_ERROR_INVALID_RUNTIME_CONTEXT,
                "Runtime context multi_wave_enabled must be a boolean.",
            )
        )
    elif runtime_context.get("multi_wave_enabled") != expected_multi_wave_enabled:
        errors.append(
            runtime_error(
                "runtime_context.multi_wave_enabled",
                AGENT_RUNTIME_ERROR_STALE_CONTEXT,
                "Runtime context multi_wave_enabled does not match the requested tool.",
            )
        )
    if runtime_context.get("plan_fingerprint") != current_plan_fingerprint:
        errors.append(
            runtime_error(
                "runtime_context.plan_fingerprint",
                AGENT_RUNTIME_ERROR_STALE_CONTEXT,
                "Runtime context plan fingerprint does not match the current QueryPlan.",
            )
        )
    query_count = runtime_context.get("query_count")
    if not isinstance(query_count, int) or isinstance(query_count, bool):
        errors.append(
            runtime_error(
                "runtime_context.query_count",
                AGENT_RUNTIME_ERROR_INVALID_RUNTIME_CONTEXT,
                "Runtime context query_count must be an integer.",
            )
        )
    elif query_count != current_query_count:
        errors.append(
            runtime_error(
                "runtime_context.query_count",
                AGENT_RUNTIME_ERROR_STALE_CONTEXT,
                "Runtime context query_count does not match the current QueryPlan.",
            )
        )
    search_brief_fingerprint = runtime_context.get("search_brief_fingerprint")
    if (
        not isinstance(search_brief_fingerprint, str)
        or not search_brief_fingerprint.strip()
    ):
        errors.append(
            runtime_error(
                "runtime_context.search_brief_fingerprint",
                AGENT_RUNTIME_ERROR_INVALID_RUNTIME_CONTEXT,
                "Runtime context requires a current Search Brief fingerprint.",
            )
        )

    if tool_name == EXECUTION_ACTION_MULTI_WAVE and settings:
        for field_name in ("max_waves", "min_new_unique_per_wave", "patience"):
            value = runtime_context.get(field_name)
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(
                    runtime_error(
                        f"runtime_context.{field_name}",
                        AGENT_RUNTIME_ERROR_INVALID_RUNTIME_CONTEXT,
                        f"Runtime context {field_name} must be an integer.",
                    )
                )
            elif value != settings[field_name]:
                errors.append(
                    runtime_error(
                        f"runtime_context.{field_name}",
                        AGENT_RUNTIME_ERROR_STALE_CONTEXT,
                        f"Runtime context {field_name} does not match normalized multi-wave settings.",
                    )
                )

    return errors


def normalize_runtime_execution_binding(
    request: AgentRuntimeTurnRequest,
) -> tuple[RuntimeExecutionBinding | None, list[dict[str, str]]]:
    if request.turn_mode not in AGENT_RUNTIME_TURN_MODES:
        return None, [
            runtime_error(
                "turn_mode",
                AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
                "Unsupported runtime turn mode.",
            )
        ]

    if (
        request.turn_mode == AGENT_RUNTIME_TURN_MODE_PREPARE
        and request.runtime_approval is not None
    ):
        return None, [
            runtime_error(
                "runtime_approval",
                AGENT_RUNTIME_ERROR_APPROVAL_MISMATCH,
                "Prepare mode must not include runtime_approval.",
            )
        ]

    tool_definition = agent_tool_definition(request.tool_name)
    if not tool_definition or request.tool_name not in AGENT_RUNTIME_EXECUTION_TOOLS:
        return None, [
            runtime_error(
                "tool_name",
                AGENT_RUNTIME_ERROR_UNSUPPORTED_TOOL,
                "Agent runtime turn supports execution tools only.",
            )
        ]

    normalized_request, settings, errors = _normalize_runtime_tool_input(
        request.tool_name,
        request.tool_input,
    )
    if errors:
        return None, errors

    assert normalized_request is not None
    flow_errors = _validate_supported_runtime_flow(normalized_request)
    if flow_errors:
        return None, flow_errors

    query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
    context_errors = _validate_runtime_context(
        request.runtime_context,
        request.tool_name,
        query_plan,
        settings,
    )
    if context_errors:
        return None, context_errors

    runtime_tool_input = _runtime_tool_input_from_normalized(
        normalized_request,
        settings,
    )
    tool_call, tool_call_errors = normalize_agent_tool_proposal(
        {
            "tool_name": request.tool_name,
            "input": runtime_tool_input,
            "reason": "Run the human-approved visible QueryPlan.",
        },
        runtime_context=request.runtime_context,
    )
    if tool_call_errors:
        return None, tool_call_errors
    assert tool_call is not None

    return (
        RuntimeExecutionBinding(
            tool_call=tool_call,
            tool_name=request.tool_name,
            execution_mode=request.runtime_context["execution_mode"],
            normalized_request=normalized_request,
            runtime_tool_input=runtime_tool_input,
            runtime_context=request.runtime_context,
            query_plan=query_plan,
            settings=settings,
        ),
        [],
    )


def validate_runtime_execution_approval(
    approval: AgentRuntimeApproval | None,
    binding: RuntimeExecutionBinding,
) -> list[dict[str, str]]:
    if approval is None:
        return [
            runtime_error(
                "runtime_approval",
                AGENT_RUNTIME_ERROR_APPROVAL_REQUIRED,
                "Runtime execution requires explicit approval for the pending tool call.",
            )
        ]

    expected_values = {
        "approval_status": AGENT_TOOL_APPROVAL_APPROVED,
        "tool_call_id": binding.tool_call.tool_call_id,
        "tool_name": binding.tool_call.tool_name,
        "tool_input_fingerprint": binding.tool_call.tool_input_fingerprint,
        "context_fingerprint": binding.tool_call.context_fingerprint,
        "idempotency_key": binding.tool_call.idempotency_key,
    }
    approval_values = approval.model_dump()

    errors: list[dict[str, str]] = []
    for field_name, expected_value in expected_values.items():
        if approval_values.get(field_name) != expected_value:
            errors.append(
                runtime_error(
                    f"runtime_approval.{field_name}",
                    AGENT_RUNTIME_ERROR_APPROVAL_MISMATCH,
                    "Runtime approval does not match the current pending tool call.",
                )
            )

    return errors


def canonical_fingerprint_payload(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def runtime_fingerprint(value: dict[str, Any]) -> str:
    payload = canonical_fingerprint_payload(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def tool_input_fingerprint(tool_input: dict[str, Any]) -> str:
    return runtime_fingerprint(tool_input)


def context_fingerprint(runtime_context: dict[str, Any]) -> str:
    return runtime_fingerprint(runtime_context)


def tool_call_fingerprint_payload(
    tool_name: str,
    tool_input_hash: str,
    context_hash: str,
) -> dict[str, str]:
    return {
        "tool_name": tool_name,
        "tool_input_fingerprint": tool_input_hash,
        "context_fingerprint": context_hash,
    }


def tool_call_id_for(
    tool_name: str,
    tool_input_hash: str,
    context_hash: str,
) -> str:
    return runtime_fingerprint(
        tool_call_fingerprint_payload(tool_name, tool_input_hash, context_hash)
    )


def idempotency_key_for(
    tool_name: str,
    tool_input_hash: str,
    context_hash: str,
) -> str:
    return runtime_fingerprint(
        {
            "idempotency_scope": "agent_runtime_tool_call_v0",
            **tool_call_fingerprint_payload(tool_name, tool_input_hash, context_hash),
        }
    )


def normalize_agent_tool_proposal(
    proposal: dict[str, Any],
    runtime_context: dict[str, Any] | None = None,
) -> tuple[AgentToolCall | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    if not isinstance(proposal, dict):
        return None, [
            runtime_error(
                "proposal",
                AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
                "Agent tool proposal must be an object.",
            )
        ]

    extra_fields = set(proposal) - AGENT_TOOL_PROPOSAL_FIELDS
    backend_owned_fields = extra_fields & AGENT_TOOL_BACKEND_OWNED_FIELDS
    if backend_owned_fields:
        return None, [
            runtime_error(
                "proposal",
                AGENT_RUNTIME_ERROR_BACKEND_OWNED_FIELD,
                "Agent tool proposal includes backend-owned fields.",
            )
        ]

    if extra_fields:
        return None, [
            runtime_error(
                "proposal",
                AGENT_RUNTIME_ERROR_UNSUPPORTED_PROPOSAL_FIELD,
                "Agent tool proposal includes unsupported fields.",
            )
        ]

    raw_tool_name = proposal.get("tool_name")
    if not isinstance(raw_tool_name, str) or not raw_tool_name.strip():
        return None, [
            runtime_error(
                "tool_name",
                AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
                "Agent tool proposal requires a non-empty string tool_name.",
            )
        ]
    tool_name = raw_tool_name.strip()

    raw_input = proposal.get("input", {})
    if not isinstance(raw_input, dict):
        return None, [
            runtime_error(
                "input",
                AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
                "Agent tool proposal input must be an object.",
            )
        ]

    raw_reason = proposal.get("reason", "")
    if not isinstance(raw_reason, str):
        return None, [
            runtime_error(
                "reason",
                AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
                "Agent tool proposal reason must be a string.",
            )
        ]
    reason = raw_reason.strip()

    normalized_context = runtime_context if runtime_context is not None else {}
    if not isinstance(normalized_context, dict):
        return None, [
            runtime_error(
                "runtime_context",
                AGENT_RUNTIME_ERROR_INVALID_RUNTIME_CONTEXT,
                "Agent runtime context must be an object.",
            )
        ]

    definition = agent_tool_definition(tool_name)
    if definition is None:
        return None, [
            runtime_error(
                "tool_name",
                AGENT_RUNTIME_ERROR_UNSUPPORTED_TOOL,
                "Agent tool is not allowlisted.",
            )
        ]

    input_hash = tool_input_fingerprint(raw_input)
    context_hash = context_fingerprint(normalized_context)
    requires_approval = definition.requires_approval
    approval_status = (
        AGENT_TOOL_APPROVAL_REQUIRED
        if requires_approval
        else AGENT_TOOL_APPROVAL_NOT_REQUIRED
    )
    idempotency_key = (
        idempotency_key_for(tool_name, input_hash, context_hash)
        if requires_approval
        else None
    )
    is_executable = not requires_approval

    return (
        AgentToolCall(
            tool_call_id=tool_call_id_for(tool_name, input_hash, context_hash),
            tool_name=tool_name,
            input=raw_input,
            reason=reason,
            requires_approval=requires_approval,
            approval_status=approval_status,
            risk_level=(
                AGENT_TOOL_RISK_LEVEL_EXECUTION
                if requires_approval
                else definition.risk_level
            ),
            tool_input_fingerprint=input_hash,
            context_fingerprint=context_hash,
            idempotency_key=idempotency_key,
            is_executable=is_executable,
        ),
        errors,
    )
