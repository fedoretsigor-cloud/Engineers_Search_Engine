import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))


EXPECTED_TOOL_NAMES = {
    "validate_search_brief",
    "adapt_brief_to_structured_request",
    "build_query_plan",
    "validate_query_plan",
    "run_single_wave_search",
    "run_multi_wave_search",
    "analyze_candidate_quality",
    "summarize_search_results",
    "suggest_next_iteration",
}


def assert_registry_contract() -> None:
    from app.agent_tools import (
        AGENT_TOOLS_V0,
        agent_tool_contract,
        agent_tool_registry,
    )

    assert set(AGENT_TOOLS_V0) == EXPECTED_TOOL_NAMES
    registry = agent_tool_registry()
    assert set(registry) == EXPECTED_TOOL_NAMES

    for tool_name, legacy_metadata in AGENT_TOOLS_V0.items():
        assert set(legacy_metadata) == {"requires_approval", "description"}
        assert registry[tool_name]["requires_approval"] == legacy_metadata[
            "requires_approval"
        ]
        assert registry[tool_name]["description"] == legacy_metadata["description"]
        assert registry[tool_name]["tool_name"] == tool_name
        assert registry[tool_name]["category"]
        assert registry[tool_name]["risk_level"]

    contract = agent_tool_contract()
    assert set(contract) == {"tools", "approval_statuses", "absolute_boundaries"}
    assert contract["tools"] == AGENT_TOOLS_V0
    assert "not_required" in contract["approval_statuses"]
    assert "required" in contract["approval_statuses"]
    assert "no_direct_web_search_bypass" in contract["absolute_boundaries"]


def assert_import_direction_before_runtime_import() -> None:
    import app.agent_tools  # noqa: F401

    assert "app.agent_runtime" not in sys.modules


def assert_runtime_import_direction() -> None:
    import app.agent_runtime  # noqa: F401

    assert "app.main" not in sys.modules


def assert_agent_tools_http_contract() -> None:
    from app import main

    client = TestClient(main.app)
    response = client.get("/api/agent/tools")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    tools = payload["agent_tools"]["tools"]
    assert set(tools) == EXPECTED_TOOL_NAMES
    for metadata in tools.values():
        assert "requires_approval" in metadata
        assert "description" in metadata


def assert_error_code(call_result, expected_code: str) -> None:
    tool_call, errors = call_result
    assert tool_call is None
    assert errors
    assert errors[0]["code"] == expected_code


def assert_proposal_validation() -> None:
    from app.agent_runtime import normalize_agent_tool_proposal

    assert_error_code(
        normalize_agent_tool_proposal({"tool_name": "unknown_tool"}),
        "unsupported_tool",
    )
    assert_error_code(
        normalize_agent_tool_proposal(
            {
                "tool_name": "build_query_plan",
                "input": {},
                "approval_status": "approved",
            }
        ),
        "backend_owned_field_in_proposal",
    )
    assert_error_code(
        normalize_agent_tool_proposal(
            {
                "tool_name": "build_query_plan",
                "input": {},
                "endpoint": "/api/agent/query-plan",
            }
        ),
        "unsupported_proposal_field",
    )
    for unsupported_field in ["path", "action", "url", "method", "extra"]:
        assert_error_code(
            normalize_agent_tool_proposal(
                {
                    "tool_name": "build_query_plan",
                    "input": {},
                    unsupported_field: "not allowed",
                }
            ),
            "unsupported_proposal_field",
        )
    assert_error_code(
        normalize_agent_tool_proposal(
            {
                "tool_name": "build_query_plan",
                "input": ["not", "an", "object"],
            }
        ),
        "invalid_tool_input",
    )
    assert_error_code(
        normalize_agent_tool_proposal(
            {
                "tool_name": "build_query_plan",
                "input": {},
                "reason": 42,
            }
        ),
        "invalid_tool_input",
    )
    assert_error_code(
        normalize_agent_tool_proposal({"tool_name": "  ", "input": {}}),
        "invalid_tool_input",
    )
    assert_error_code(
        normalize_agent_tool_proposal({"input": {}}),
        "invalid_tool_input",
    )
    assert_error_code(
        normalize_agent_tool_proposal({"tool_name": 42, "input": {}}),
        "invalid_tool_input",
    )
    assert_error_code(
        normalize_agent_tool_proposal(
            {"tool_name": "build_query_plan"},
            runtime_context=["not", "an", "object"],
        ),
        "invalid_runtime_context",
    )


def assert_normalization_and_fingerprints() -> None:
    from app.agent_runtime import normalize_agent_tool_proposal

    no_input_call, errors = normalize_agent_tool_proposal(
        {"tool_name": "build_query_plan"}
    )
    assert not errors
    assert no_input_call is not None
    assert no_input_call.input == {}
    assert no_input_call.reason == ""
    assert no_input_call.approval_status == "not_required"
    assert no_input_call.is_executable is True
    assert no_input_call.idempotency_key is None

    no_approval_call, errors = normalize_agent_tool_proposal(
        {
            "tool_name": "build_query_plan",
            "input": {"stack": ["Spring", "Kafka"], "location": "Ukraine"},
            "reason": "  Build a plan  ",
        },
        runtime_context={"brief_fingerprint": "brief-1"},
    )
    assert not errors
    assert no_approval_call is not None
    assert no_approval_call.reason == "Build a plan"
    assert no_approval_call.risk_level == "planning"

    same_no_approval_call, errors = normalize_agent_tool_proposal(
        {
            "tool_name": "build_query_plan",
            "input": {"location": "Ukraine", "stack": ["Spring", "Kafka"]},
            "reason": "Build a plan",
        },
        runtime_context={"brief_fingerprint": "brief-1"},
    )
    assert not errors
    assert same_no_approval_call is not None
    assert (
        same_no_approval_call.tool_input_fingerprint
        == no_approval_call.tool_input_fingerprint
    )
    assert same_no_approval_call.context_fingerprint == no_approval_call.context_fingerprint

    changed_context_call, errors = normalize_agent_tool_proposal(
        {
            "tool_name": "build_query_plan",
            "input": {"stack": ["Spring", "Kafka"], "location": "Ukraine"},
        },
        runtime_context={"brief_fingerprint": "brief-2"},
    )
    assert not errors
    assert changed_context_call is not None
    assert changed_context_call.context_fingerprint != no_approval_call.context_fingerprint

    changed_input_call, errors = normalize_agent_tool_proposal(
        {
            "tool_name": "build_query_plan",
            "input": {"stack": ["Spring"], "location": "Ukraine"},
        },
        runtime_context={"brief_fingerprint": "brief-1"},
    )
    assert not errors
    assert changed_input_call is not None
    assert changed_input_call.tool_input_fingerprint != no_approval_call.tool_input_fingerprint

    execution_call, errors = normalize_agent_tool_proposal(
        {
            "tool_name": "run_single_wave_search",
            "input": {"plan_fingerprint": "plan-1"},
        },
        runtime_context={"brief_fingerprint": "brief-1"},
    )
    assert not errors
    assert execution_call is not None
    assert execution_call.approval_status == "required"
    assert execution_call.risk_level == "execution"
    assert execution_call.is_executable is False
    assert execution_call.idempotency_key

    same_execution_call, errors = normalize_agent_tool_proposal(
        {
            "tool_name": "run_single_wave_search",
            "input": {"plan_fingerprint": "plan-1"},
        },
        runtime_context={"brief_fingerprint": "brief-1"},
    )
    assert not errors
    assert same_execution_call is not None
    assert same_execution_call.idempotency_key == execution_call.idempotency_key


def valid_runtime_tool_input() -> dict:
    return {
        "role_family": "Backend Developer",
        "technology": "Java",
        "stack": ["Spring", "Kafka"],
        "location": "Ukraine",
        "search_depth": "standard",
        "linkedin_profiles_only": True,
        "location_filter_enabled": True,
    }


def build_runtime_context(
    tool_name: str,
    tool_input: dict,
    overrides: dict | None = None,
) -> dict:
    from app.planning import RuleBasedQueryPlannerV1, query_plan_fingerprint
    from app.schemas import MultiWaveStructuredSearchRequest, StructuredSearchRequest
    from app.search_validation import (
        normalize_multi_wave_search_request,
        normalize_structured_search_request,
    )

    if tool_name == "run_multi_wave_search":
        normalized_request, settings, errors = normalize_multi_wave_search_request(
            MultiWaveStructuredSearchRequest(**tool_input)
        )
    else:
        normalized_request, errors = normalize_structured_search_request(
            StructuredSearchRequest(**tool_input)
        )
        settings = None
    assert not errors
    query_plan = RuleBasedQueryPlannerV1().build(normalized_request)
    context = {
        "planner_mode": "rule_based",
        "tool_name": tool_name,
        "execution_mode": (
            "multi_wave" if tool_name == "run_multi_wave_search" else "single_wave"
        ),
        "plan_fingerprint": query_plan_fingerprint(query_plan),
        "query_count": len(query_plan["queries"]),
        "search_brief_fingerprint": "brief-fingerprint-1",
        "multi_wave_enabled": tool_name == "run_multi_wave_search",
    }
    if settings:
        context.update(
            {
                "max_waves": settings["max_waves"],
                "min_new_unique_per_wave": settings["min_new_unique_per_wave"],
                "patience": settings["patience"],
            }
        )
    if overrides:
        context.update(overrides)
    return context


def runtime_turn_payload(
    tool_name: str = "run_single_wave_search",
    tool_input: dict | None = None,
    turn_mode: str = "prepare",
    runtime_approval: dict | None = None,
    context_overrides: dict | None = None,
) -> dict:
    tool_input = dict(tool_input or valid_runtime_tool_input())
    return {
        "turn_mode": turn_mode,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "runtime_context": build_runtime_context(
            tool_name,
            tool_input,
            context_overrides,
        ),
        "runtime_approval": runtime_approval,
        "agent_language": "en",
    }


def approved_runtime_payload_from_prepare(prepare_payload: dict) -> dict:
    approval = prepare_payload["pending_approvals"][0]
    return {
        "approval_status": "approved",
        "tool_call_id": approval["tool_call_id"],
        "tool_name": approval["tool_name"],
        "tool_input_fingerprint": approval["tool_input_fingerprint"],
        "context_fingerprint": approval["context_fingerprint"],
        "idempotency_key": approval["idempotency_key"],
    }


def post_runtime_turn(client: TestClient, payload: dict) -> dict:
    response = client.post("/api/agent/runtime/turn", json=payload)
    assert response.status_code == 200
    return response.json()


def with_fake_tavily_key() -> str | None:
    previous_value = os.environ.get("TAVILY_API_KEY")
    os.environ["TAVILY_API_KEY"] = "fake-tavily-key"
    return previous_value


def restore_tavily_key(previous_value: str | None) -> None:
    if previous_value is None:
        os.environ.pop("TAVILY_API_KEY", None)
    else:
        os.environ["TAVILY_API_KEY"] = previous_value


def assert_agent_runtime_turn_http_contract() -> None:
    from app import main

    client = TestClient(main.app)
    previous_tavily_key = with_fake_tavily_key()
    try:
        prepare = post_runtime_turn(client, runtime_turn_payload())
        assert prepare["ok"] is True
        assert prepare["runtime_state"] == "approval_pending"
        assert prepare["tool_calls"][0]["tool_name"] == "run_single_wave_search"
        assert prepare["pending_approvals"][0]["approval_status"] == "required"

        multi_tool_input = {
            **valid_runtime_tool_input(),
            "max_waves": 5,
            "min_new_unique_per_wave": 3,
            "patience": 2,
        }
        multi_prepare = post_runtime_turn(
            client,
            runtime_turn_payload(
                tool_name="run_multi_wave_search",
                tool_input=multi_tool_input,
            ),
        )
        assert multi_prepare["ok"] is True
        assert multi_prepare["runtime_state"] == "approval_pending"
        assert multi_prepare["pending_approvals"][0]["tool_name"] == (
            "run_multi_wave_search"
        )

        for tool_name in ["build_query_plan", "summarize_search_results"]:
            payload = runtime_turn_payload()
            payload["tool_name"] = tool_name
            payload["runtime_context"]["tool_name"] = tool_name
            rejected = post_runtime_turn(client, payload)
            assert rejected["ok"] is False
            assert rejected["errors"][0]["code"] == "unsupported_tool"

        unsafe_payload = runtime_turn_payload()
        unsafe_payload["tool_input"]["query_plan"] = {}
        unsafe = post_runtime_turn(client, unsafe_payload)
        assert unsafe["ok"] is False
        assert unsafe["errors"][0]["code"] == "invalid_tool_input"

        top_level_extra_payload = runtime_turn_payload()
        top_level_extra_payload["query_plan"] = {}
        top_level_extra_response = client.post(
            "/api/agent/runtime/turn",
            json=top_level_extra_payload,
        )
        assert top_level_extra_response.status_code == 422

        unsupported_flow_input = {
            **valid_runtime_tool_input(),
            "location": "Poland",
            "location_filter_enabled": False,
        }
        unsupported_flow = post_runtime_turn(
            client,
            runtime_turn_payload(tool_input=unsupported_flow_input),
        )
        assert unsupported_flow["ok"] is False
        assert unsupported_flow["errors"][0]["code"] == "unsupported_flow"

        missing_brief_context = runtime_turn_payload()
        missing_brief_context["runtime_context"].pop("search_brief_fingerprint")
        missing_brief = post_runtime_turn(client, missing_brief_context)
        assert missing_brief["ok"] is False
        assert missing_brief["errors"][0]["code"] == "invalid_runtime_context"

        prepare_with_approval = runtime_turn_payload(
            runtime_approval={
                "approval_status": "approved",
                "tool_call_id": "tool-call",
                "tool_name": "run_single_wave_search",
                "tool_input_fingerprint": "tool-input",
                "context_fingerprint": "context",
                "idempotency_key": "idem",
            }
        )
        rejected_prepare = post_runtime_turn(client, prepare_with_approval)
        assert rejected_prepare["ok"] is False
        assert rejected_prepare["errors"][0]["code"] == "approval_mismatch"

        execute_without_approval = post_runtime_turn(
            client,
            runtime_turn_payload(turn_mode="execute_approved"),
        )
        assert execute_without_approval["ok"] is False
        assert execute_without_approval["errors"][0]["code"] == "approval_required"

        stale_context = runtime_turn_payload(
            context_overrides={"plan_fingerprint": "stale-plan"}
        )
        stale = post_runtime_turn(client, stale_context)
        assert stale["ok"] is False
        assert stale["errors"][0]["code"] == "stale_context"

        wrong_mode = runtime_turn_payload(
            context_overrides={"execution_mode": "multi_wave"}
        )
        wrong_mode_response = post_runtime_turn(client, wrong_mode)
        assert wrong_mode_response["ok"] is False
        assert wrong_mode_response["errors"][0]["code"] == "stale_context"

        approval = approved_runtime_payload_from_prepare(prepare)
        wrong_idempotency_payload = runtime_turn_payload(
            turn_mode="execute_approved",
            runtime_approval={**approval, "idempotency_key": "wrong"},
        )
        wrong_idempotency = post_runtime_turn(client, wrong_idempotency_payload)
        assert wrong_idempotency["ok"] is False
        assert wrong_idempotency["errors"][0]["code"] == "approval_mismatch"
    finally:
        restore_tavily_key(previous_tavily_key)

    os.environ.pop("TAVILY_API_KEY", None)
    missing_key = post_runtime_turn(client, runtime_turn_payload())
    assert missing_key["ok"] is False
    assert missing_key["errors"][0]["code"] == "tool_unavailable"
    restore_tavily_key(previous_tavily_key)


def assert_agent_runtime_turn_execution_with_mocked_tools() -> None:
    from app import main

    client = TestClient(main.app)
    previous_tavily_key = with_fake_tavily_key()
    original_single = main.execute_single_wave_structured_search_response
    original_multi = main.execute_multi_wave_structured_search_response

    async def fake_single_search_response(request, query_plan, execution_approval):
        return {
            "ok": True,
            "query_plan": query_plan,
            "plan_fingerprint": "plan-fingerprint",
            "execution_approval": execution_approval,
            "query_results": [],
            "deduped_results": [{"normalized_url": "https://ua.linkedin.com/in/a"}],
            "report": {
                "queries_total": len(query_plan["queries"]),
                "queries_succeeded": 1,
                "raw_total": 1,
                "unique_profiles": 1,
                "hidden_by_profile_filter": 0,
                "hidden_by_location_filter": 0,
            },
            "agent_response": {"message": "Done."},
        }

    async def fake_multi_search_response(
        request,
        query_plan,
        settings,
        execution_approval,
    ):
        response = await fake_single_search_response(
            request,
            query_plan,
            execution_approval,
        )
        response["experimental"] = True
        response["report"]["wave_reports"] = []
        response["report"]["wave_summary"] = {
            "waves_run": settings["max_waves"],
            "stop_reason": "mocked",
        }
        return response

    try:
        main.execute_single_wave_structured_search_response = fake_single_search_response
        main.execute_multi_wave_structured_search_response = fake_multi_search_response

        prepare_payload = runtime_turn_payload()
        prepare = post_runtime_turn(client, prepare_payload)
        approval = approved_runtime_payload_from_prepare(prepare)
        executed = post_runtime_turn(
            client,
            runtime_turn_payload(
                turn_mode="execute_approved",
                runtime_approval=approval,
            ),
        )
        assert executed["ok"] is True
        assert executed["runtime_state"] == "observed"
        assert executed["tool_results"][0]["ok"] is True
        assert executed["tool_results"][0]["result"]["report"]["unique_profiles"] == 1

        multi_tool_input = {
            **valid_runtime_tool_input(),
            "max_waves": 5,
            "min_new_unique_per_wave": 3,
            "patience": 2,
        }
        multi_prepare_payload = runtime_turn_payload(
            tool_name="run_multi_wave_search",
            tool_input=multi_tool_input,
        )
        multi_prepare = post_runtime_turn(client, multi_prepare_payload)
        multi_approval = approved_runtime_payload_from_prepare(multi_prepare)
        multi_executed = post_runtime_turn(
            client,
            runtime_turn_payload(
                tool_name="run_multi_wave_search",
                tool_input=multi_tool_input,
                turn_mode="execute_approved",
                runtime_approval=multi_approval,
            ),
        )
        assert multi_executed["ok"] is True
        assert multi_executed["runtime_state"] == "observed"
        assert multi_executed["tool_results"][0]["result"]["experimental"] is True
    finally:
        main.execute_single_wave_structured_search_response = original_single
        main.execute_multi_wave_structured_search_response = original_multi
        restore_tavily_key(previous_tavily_key)


def run_smoke() -> None:
    assert_registry_contract()
    assert_import_direction_before_runtime_import()
    assert_runtime_import_direction()
    assert_agent_tools_http_contract()
    assert_proposal_validation()
    assert_normalization_and_fingerprints()
    assert_agent_runtime_turn_http_contract()
    assert_agent_runtime_turn_execution_with_mocked_tools()


if __name__ == "__main__":
    run_smoke()
    print("P6 agent runtime smoke passed")
