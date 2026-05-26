from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain_config import PLANNER_MODE_RULE_BASED


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    max_results: int = Field(default=20, ge=1, le=20)
    linkedin_profiles_only: bool = False
    ukraine_linkedin_domain_only: bool = False


class ExecutionApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_status: str | None = None
    approved_action: str | None = None
    approved_planner_mode: str | None = None
    approved_query_count: int | None = None
    approved_plan_fingerprint: str | None = None


class StructuredSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_family: str | None = None
    technology: str | None = None
    stack: list[str] | None = None
    location: str | None = None
    search_depth: str | None = None
    linkedin_profiles_only: bool | None = None
    location_filter_enabled: bool | None = None
    execution_approval: ExecutionApproval | None = None
    agent_language: str | None = None


class MultiWaveStructuredSearchRequest(StructuredSearchRequest):
    max_waves: int | None = None
    min_new_unique_per_wave: int | None = None
    patience: int | None = None


class SearchBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_text: str | None = None
    brief_status: str | None = None
    role_family: str | None = None
    technology: str | None = None
    stack: list[str] | None = None
    location: str | None = None
    seniority: str | None = None
    must_have: list[str] | None = None
    nice_to_have: list[str] | None = None
    exclusions: list[str] | None = None
    search_depth: str | None = None
    profile_sources: list[str] | None = None
    notes: str | None = None
    missing_fields: list[str] | None = None
    clarifying_questions: list[str] | None = None
    assumptions: list[str] | None = None


class AgentQueryPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    planner_mode: str = PLANNER_MODE_RULE_BASED
    search_brief: SearchBrief
    agent_plan_brief_fingerprint: str | None = None
    agent_plan_action: dict | None = None


class AgentPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search_brief: SearchBrief
    language: str | None = None


class AIQueryPlanValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search_brief: SearchBrief
    draft_query_plan: dict | None = None


class RecruiterChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    content: str = Field(..., min_length=1)


class RecruiterChatTurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[RecruiterChatMessage] = Field(default_factory=list)
    draft_brief: SearchBrief | None = None
    language: str | None = None
    planner_mode: str | None = None
    pending_update_field: str | None = None


class RecruiterChatIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latest_message: str = Field(..., min_length=1)
    language: str | None = None
    context_type: str | None = None
    pending_action_type: str | None = None
    pending_field: str | None = None
    pending_update_field: str | None = None
    pending_hypothesis: dict[str, Any] | None = None
    current_brief_status: str | None = None
    current_brief: SearchBrief | None = None


class AgentRuntimeApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_status: str
    tool_call_id: str
    tool_name: str
    tool_input_fingerprint: str
    context_fingerprint: str
    idempotency_key: str | None


class AgentRuntimeTurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_mode: str
    tool_name: str
    tool_input: dict[str, Any]
    runtime_context: dict[str, Any]
    runtime_approval: AgentRuntimeApproval | None
    agent_language: str | None


class CandidateExplanationWordingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wording_use_case: str
    request_payload_contract_version: str
    target_language: str
    workspace_run_id: str
    wording_target_key: str
    request_explanation_fingerprint: str
    explanation_version: str
    source: str
    summary: str
    positive_signals: list[dict[str, Any]] = Field(default_factory=list)
    cautions: list[dict[str, Any]] = Field(default_factory=list)
    evidence_items: list[dict[str, Any]] = Field(default_factory=list)
