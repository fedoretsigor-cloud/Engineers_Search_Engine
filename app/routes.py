from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.schemas import (
    AIQueryPlanValidationRequest,
    AgentPlanRequest,
    AgentQueryPlanRequest,
    AgentRuntimeTurnRequest,
    CandidateExplanationWordingRequest,
    MultiWaveStructuredSearchRequest,
    RecruiterChatTurnRequest,
    SearchBrief,
    SearchRequest,
    StructuredSearchRequest,
)


@dataclass(frozen=True)
class RouteDependencies:
    index: Callable[[], FileResponse]
    health: Callable[[], dict[str, str]]
    validate_structured_search: Callable[[StructuredSearchRequest], dict]
    validate_search_brief_endpoint: Callable[[SearchBrief], dict]
    create_recruiter_chat_turn: Callable[[RecruiterChatTurnRequest], Awaitable[dict]]
    create_agent_plan: Callable[[AgentPlanRequest], Awaitable[dict]]
    get_agent_tools: Callable[[], dict]
    create_query_plan: Callable[[StructuredSearchRequest], dict]
    create_agent_query_plan: Callable[[AgentQueryPlanRequest], Awaitable[dict]]
    create_agent_runtime_turn: Callable[[AgentRuntimeTurnRequest], Awaitable[dict]]
    create_candidate_explanation_wording: Callable[
        [CandidateExplanationWordingRequest],
        Awaitable[dict],
    ]
    validate_ai_query_plan_endpoint: Callable[[AIQueryPlanValidationRequest], dict]
    structured_search: Callable[[StructuredSearchRequest], Awaitable[dict]]
    structured_search_multi_wave: Callable[
        [MultiWaveStructuredSearchRequest],
        Awaitable[dict],
    ]
    search: Callable[[SearchRequest], Awaitable[dict]]


def create_router(deps: RouteDependencies, static_dir: Path) -> APIRouter:
    router = APIRouter()
    _ = static_dir

    @router.get("/")
    def index() -> FileResponse:
        return deps.index()

    @router.get("/api/health")
    def health() -> dict[str, str]:
        return deps.health()

    @router.post("/api/structured-search/validate")
    def validate_structured_search(request: StructuredSearchRequest) -> dict:
        return deps.validate_structured_search(request)

    @router.post("/api/search-brief/validate")
    def validate_search_brief_endpoint(request: SearchBrief) -> dict:
        return deps.validate_search_brief_endpoint(request)

    @router.post("/api/recruiter-chat/turn")
    async def create_recruiter_chat_turn(
        request: RecruiterChatTurnRequest,
    ) -> dict:
        return await deps.create_recruiter_chat_turn(request)

    @router.post("/api/agent/plan")
    async def create_agent_plan(request: AgentPlanRequest) -> dict:
        return await deps.create_agent_plan(request)

    @router.get("/api/agent/tools")
    def get_agent_tools() -> dict:
        return deps.get_agent_tools()

    @router.post("/api/query-plan")
    def create_query_plan(request: StructuredSearchRequest) -> dict:
        return deps.create_query_plan(request)

    @router.post("/api/agent/query-plan")
    async def create_agent_query_plan(request: AgentQueryPlanRequest) -> dict:
        return await deps.create_agent_query_plan(request)

    @router.post("/api/agent/runtime/turn")
    async def create_agent_runtime_turn(request: AgentRuntimeTurnRequest) -> dict:
        return await deps.create_agent_runtime_turn(request)

    @router.post("/api/candidate-workspace/explanation-wording")
    async def create_candidate_explanation_wording(
        request: CandidateExplanationWordingRequest,
    ) -> dict:
        return await deps.create_candidate_explanation_wording(request)

    @router.post("/api/ai-query-plan/validate")
    def validate_ai_query_plan_endpoint(
        request: AIQueryPlanValidationRequest,
    ) -> dict:
        return deps.validate_ai_query_plan_endpoint(request)

    @router.post("/api/structured-search")
    async def structured_search(request: StructuredSearchRequest) -> dict:
        return await deps.structured_search(request)

    @router.post("/api/structured-search/multi-wave")
    async def structured_search_multi_wave(
        request: MultiWaveStructuredSearchRequest,
    ) -> dict:
        return await deps.structured_search_multi_wave(request)

    @router.post("/api/search")
    async def search(request: SearchRequest) -> dict:
        return await deps.search(request)

    return router
