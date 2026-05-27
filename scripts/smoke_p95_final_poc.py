import asyncio
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import main
from app.agent_plan import build_agent_plan_response
from app.agent_runtime import (
    AGENT_RUNTIME_TURN_MODE_PREPARE,
    normalize_runtime_execution_binding,
)
from app.agent_tools import EXECUTION_ACTION_MULTI_WAVE
from app.domain_config import (
    MULTI_WAVE_DEFAULT_MAX_WAVES,
    MULTI_WAVE_DEFAULT_MIN_NEW_UNIQUE_PER_WAVE,
    MULTI_WAVE_DEFAULT_PATIENCE,
    PLANNER_MODE_RULE_BASED,
    PROFILE_SOURCE_LINKEDIN_PUBLIC,
    SEARCH_BRIEF_STATUS_READY_FOR_PLANNING,
    SEARCH_DEPTH_STANDARD,
)
from app.planning import RuleBasedQueryPlannerV1, query_plan_fingerprint
from app.schemas import AgentPlanRequest, AgentRuntimeTurnRequest, RecruiterChatMessage, RecruiterChatTurnRequest, SearchBrief, StructuredSearchRequest


def final_poc_brief(**overrides) -> SearchBrief:
    payload = {
        "source_text": "Find frontend developers in Poland, main technology TypeScript, stack React and Next.js.",
        "brief_status": SEARCH_BRIEF_STATUS_READY_FOR_PLANNING,
        "role_family": "Frontend Developer",
        "technology": "TypeScript",
        "stack": ["React", "Next.js"],
        "location": "Poland",
        "search_depth": SEARCH_DEPTH_STANDARD,
        "profile_sources": [PROFILE_SOURCE_LINKEDIN_PUBLIC],
    }
    payload.update(overrides)
    return SearchBrief(**payload)


def assert_generic_structured_search_is_supported() -> dict:
    response = main.validate_structured_search(
        StructuredSearchRequest(
            role_family="Frontend Developer",
            technology="TypeScript",
            stack=["React", "Next.js"],
            location="Poland",
            search_depth=SEARCH_DEPTH_STANDARD,
            linkedin_profiles_only=True,
            location_filter_enabled=True,
        )
    )
    assert response["ok"] is True, response
    normalized = response["normalized_request"]
    assert normalized["role_family"] == "Frontend Developer"
    assert normalized["technology"] == "TypeScript"
    assert normalized["stack"] == ["React", "Next.js"]
    assert normalized["location"] == "Poland"
    assert normalized["location_filter_enabled"] is False
    return normalized


def assert_generic_planner_returns_bounded_queries(normalized_request: dict) -> dict:
    query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
    queries = query_plan["queries"]
    assert len(queries) == 10
    assert all(query["max_results"] == 20 for query in queries)
    assert all("site:linkedin.com/in" in query["query"] for query in queries)
    assert all('"Poland"' in query["query"] for query in queries)
    assert all("TypeScript" in query["query"] for query in queries)
    assert sum(1 for query in queries if query["uses_stack"]) == 4
    return query_plan


def assert_non_it_and_cyrillic_are_rejected() -> None:
    non_it_response = main.validate_structured_search(
        StructuredSearchRequest(
            role_family="Dentist",
            technology="Java",
            stack=["Spring"],
            location="Ukraine",
        )
    )
    assert non_it_response["ok"] is False
    assert any(error["field"] == "role_family" for error in non_it_response["errors"])

    cyrillic_structured = main.validate_structured_search(
        StructuredSearchRequest(
            role_family="Backend Developer",
            technology="Java",
            stack=["Spring"],
            location="Украина",
        )
    )
    assert cyrillic_structured["ok"] is False
    assert any("English input only" in error["message"] for error in cyrillic_structured["errors"])

    cyrillic_brief = main.validate_search_brief_endpoint(
        final_poc_brief(source_text="Найди Java developer", location="Ukraine")
    )
    assert cyrillic_brief["ok"] is False
    assert any(error["field"] == "source_text" for error in cyrillic_brief["errors"])


async def assert_recruiter_chat_cyrillic_rejected() -> None:
    response = await main.create_recruiter_chat_turn(
        RecruiterChatTurnRequest(
            messages=[
                RecruiterChatMessage(
                    role="user",
                    content="Найди backend developers in Ukraine with Java",
                )
            ],
            language="en",
        )
    )
    assert response["ok"] is False
    assert response["language"] == "en"
    assert any("English input only" in error["message"] for error in response["validation_errors"])


def assert_agent_plan_and_runtime_support_generic_flow(normalized_request: dict, query_plan: dict) -> None:
    plan_response = build_agent_plan_response(
        AgentPlanRequest(search_brief=final_poc_brief(), language="en"),
        validation_error_formatter=main.validation_error_message,
    )
    assert plan_response["ok"] is True
    assert plan_response["agent_plan_status"] == "supported"
    assert "Frontend Developer" in plan_response["message"]
    assert "TypeScript" in plan_response["message"]
    assert "Poland" in plan_response["message"]

    runtime_context = {
        "planner_mode": PLANNER_MODE_RULE_BASED,
        "tool_name": EXECUTION_ACTION_MULTI_WAVE,
        "execution_mode": "multi_wave",
        "plan_fingerprint": query_plan_fingerprint(query_plan),
        "query_count": len(query_plan["queries"]),
        "search_brief_fingerprint": plan_response["agent_plan"]["brief_fingerprint"],
        "multi_wave_enabled": True,
        "max_waves": MULTI_WAVE_DEFAULT_MAX_WAVES,
        "min_new_unique_per_wave": MULTI_WAVE_DEFAULT_MIN_NEW_UNIQUE_PER_WAVE,
        "patience": MULTI_WAVE_DEFAULT_PATIENCE,
    }
    runtime_request = AgentRuntimeTurnRequest(
        turn_mode=AGENT_RUNTIME_TURN_MODE_PREPARE,
        tool_name=EXECUTION_ACTION_MULTI_WAVE,
        tool_input={
            **normalized_request,
            "max_waves": MULTI_WAVE_DEFAULT_MAX_WAVES,
            "min_new_unique_per_wave": MULTI_WAVE_DEFAULT_MIN_NEW_UNIQUE_PER_WAVE,
            "patience": MULTI_WAVE_DEFAULT_PATIENCE,
        },
        runtime_context=runtime_context,
        runtime_approval=None,
        agent_language="en",
    )
    binding, errors = normalize_runtime_execution_binding(runtime_request)
    assert not errors, errors
    assert binding is not None


def assert_frontend_final_poc_static_contract() -> None:
    index_html = (REPO_ROOT / "app/static/index.html").read_text(encoding="utf-8")
    app_js = (REPO_ROOT / "app/static/app.js").read_text(encoding="utf-8")
    styles_css = (REPO_ROOT / "app/static/styles.css").read_text(encoding="utf-8")

    assert "Workspace ready" not in index_html
    assert "Workspace ready" not in app_js
    assert "I understood the search. Review the summary" not in app_js
    assert "This POC accepts English input only" in app_js
    assert "candidate-results-empty-state" in app_js
    assert "candidate-results-loading-state" in app_js
    assert "candidate-results-spinner" in styles_css


async def main_smoke() -> None:
    normalized_request = assert_generic_structured_search_is_supported()
    query_plan = assert_generic_planner_returns_bounded_queries(normalized_request)
    assert_non_it_and_cyrillic_are_rejected()
    await assert_recruiter_chat_cyrillic_rejected()
    assert_agent_plan_and_runtime_support_generic_flow(normalized_request, query_plan)
    assert_frontend_final_poc_static_contract()


if __name__ == "__main__":
    asyncio.run(main_smoke())
