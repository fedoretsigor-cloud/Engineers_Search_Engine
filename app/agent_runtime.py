from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any

from app.agent_tools import (
    AGENT_RUNTIME_ERROR_BACKEND_OWNED_FIELD,
    AGENT_RUNTIME_ERROR_INVALID_RUNTIME_CONTEXT,
    AGENT_RUNTIME_ERROR_INVALID_TOOL_INPUT,
    AGENT_RUNTIME_ERROR_UNSUPPORTED_PROPOSAL_FIELD,
    AGENT_RUNTIME_ERROR_UNSUPPORTED_TOOL,
    AGENT_TOOL_APPROVAL_NOT_REQUIRED,
    AGENT_TOOL_APPROVAL_REQUIRED,
    AGENT_TOOL_RISK_LEVEL_EXECUTION,
    agent_tool_definition,
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


def runtime_error(field_name: str, code: str, message: str) -> dict[str, str]:
    return {"field": field_name, "code": code, "message": message}


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
