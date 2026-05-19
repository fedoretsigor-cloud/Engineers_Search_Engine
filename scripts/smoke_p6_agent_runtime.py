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


def run_smoke() -> None:
    assert_registry_contract()
    assert_import_direction_before_runtime_import()
    assert_runtime_import_direction()
    assert_agent_tools_http_contract()
    assert_proposal_validation()
    assert_normalization_and_fingerprints()


if __name__ == "__main__":
    run_smoke()
    print("P6 agent runtime smoke passed")
