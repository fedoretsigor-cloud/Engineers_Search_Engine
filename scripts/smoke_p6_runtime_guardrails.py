import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

RUNTIME_ENDPOINT = "/api/agent/runtime/turn"
SINGLE_TOOL = "run_single_wave_search"
MULTI_TOOL = "run_multi_wave_search"
FAKE_TAVILY_KEY = "fake-tavily-key"
UNSAFE_RUNTIME_FIELDS = [
    "query_plan",
    "endpoint",
    "path",
    "url",
    "method",
    "action",
    "query",
    "queries",
    "raw_query",
    "boolean_query",
    "search_query",
]


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


def valid_multi_wave_tool_input(overrides: dict | None = None) -> dict:
    payload = {
        **valid_runtime_tool_input(),
        "max_waves": 5,
        "min_new_unique_per_wave": 3,
        "patience": 2,
    }
    if overrides:
        payload.update(overrides)
    return payload


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

    if tool_name == MULTI_TOOL:
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
        "execution_mode": "multi_wave" if tool_name == MULTI_TOOL else "single_wave",
        "plan_fingerprint": query_plan_fingerprint(query_plan),
        "query_count": len(query_plan["queries"]),
        "search_brief_fingerprint": "brief-fingerprint-1",
        "multi_wave_enabled": tool_name == MULTI_TOOL,
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
    tool_name: str = SINGLE_TOOL,
    tool_input: dict | None = None,
    turn_mode: str = "prepare",
    runtime_approval: dict | None = None,
    context_overrides: dict | None = None,
) -> dict:
    if tool_input is None:
        tool_input = (
            valid_multi_wave_tool_input()
            if tool_name == MULTI_TOOL
            else valid_runtime_tool_input()
        )
    return {
        "turn_mode": turn_mode,
        "tool_name": tool_name,
        "tool_input": dict(tool_input),
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
    response = client.post(RUNTIME_ENDPOINT, json=payload)
    assert response.status_code == 200
    return response.json()


def assert_error_code(payload: dict, expected_code: str) -> None:
    assert payload["ok"] is False
    assert payload["errors"], payload
    assert payload["errors"][0]["code"] == expected_code, payload["errors"]


def with_fake_tavily_key() -> str | None:
    previous_value = os.environ.get("TAVILY_API_KEY")
    os.environ["TAVILY_API_KEY"] = FAKE_TAVILY_KEY
    return previous_value


def restore_tavily_key(previous_value: str | None) -> None:
    if previous_value is None:
        os.environ.pop("TAVILY_API_KEY", None)
    else:
        os.environ["TAVILY_API_KEY"] = previous_value


class ExecutionSpy:
    def __init__(self) -> None:
        self.single_calls = 0
        self.multi_calls = 0

    @property
    def total_calls(self) -> int:
        return self.single_calls + self.multi_calls

    async def single(self, request, query_plan, execution_approval):
        self.single_calls += 1
        return fake_search_response(query_plan, execution_approval)

    async def multi(self, request, query_plan, settings, execution_approval):
        self.multi_calls += 1
        response = fake_search_response(query_plan, execution_approval)
        response["experimental"] = True
        response["report"]["wave_summary"] = {
            "waves_run": settings["max_waves"],
            "stop_reason": "mocked",
        }
        response["report"]["wave_reports"] = []
        return response


def fake_search_response(query_plan: dict, execution_approval: dict) -> dict:
    return {
        "ok": True,
        "query_plan": query_plan,
        "plan_fingerprint": "mock-plan-fingerprint",
        "execution_approval": execution_approval,
        "query_results": [],
        "deduped_results": [{"normalized_url": "https://ua.linkedin.com/in/mock"}],
        "report": {
            "queries_total": len(query_plan["queries"]),
            "queries_succeeded": 1,
            "queries_failed": 0,
            "raw_total": 1,
            "unique_profiles": 1,
            "hidden_by_profile_filter": 0,
            "hidden_by_location_filter": 0,
        },
        "agent_response": {"message": "Mocked runtime execution complete."},
    }


class PatchedExecutionHelpers:
    def __init__(self, main_module) -> None:
        self.main = main_module
        self.spy = ExecutionSpy()
        self.original_single = main_module.execute_single_wave_structured_search_response
        self.original_multi = main_module.execute_multi_wave_structured_search_response

    def __enter__(self) -> ExecutionSpy:
        self.main.execute_single_wave_structured_search_response = self.spy.single
        self.main.execute_multi_wave_structured_search_response = self.spy.multi
        return self.spy

    def __exit__(self, exc_type, exc, tb) -> None:
        self.main.execute_single_wave_structured_search_response = self.original_single
        self.main.execute_multi_wave_structured_search_response = self.original_multi


def prepare_runtime_approval(
    client: TestClient,
    tool_name: str = SINGLE_TOOL,
    tool_input: dict | None = None,
) -> dict:
    prepare = post_runtime_turn(
        client,
        runtime_turn_payload(tool_name=tool_name, tool_input=tool_input),
    )
    assert prepare["ok"] is True
    assert prepare["runtime_state"] == "approval_pending"
    return approved_runtime_payload_from_prepare(prepare)


def assert_rejected_without_execution(
    client: TestClient,
    spy: ExecutionSpy,
    payload: dict,
    expected_code: str,
) -> dict:
    before_calls = spy.total_calls
    response = post_runtime_turn(client, payload)
    assert_error_code(response, expected_code)
    assert spy.total_calls == before_calls
    return response


def assert_prepare_never_executes(client: TestClient, spy: ExecutionSpy) -> None:
    previous_calls = spy.total_calls
    single_prepare = post_runtime_turn(client, runtime_turn_payload())
    multi_prepare = post_runtime_turn(
        client,
        runtime_turn_payload(tool_name=MULTI_TOOL, tool_input=valid_multi_wave_tool_input()),
    )
    assert single_prepare["ok"] is True
    assert multi_prepare["ok"] is True
    assert spy.total_calls == previous_calls


def assert_valid_execution_calls_mocked_helpers(
    client: TestClient,
    spy: ExecutionSpy,
) -> None:
    single_approval = prepare_runtime_approval(client)
    single_response = post_runtime_turn(
        client,
        runtime_turn_payload(
            turn_mode="execute_approved",
            runtime_approval=single_approval,
        ),
    )
    assert single_response["ok"] is True
    assert single_response["runtime_state"] == "observed"
    assert spy.single_calls == 1

    multi_input = valid_multi_wave_tool_input()
    multi_approval = prepare_runtime_approval(client, MULTI_TOOL, multi_input)
    multi_response = post_runtime_turn(
        client,
        runtime_turn_payload(
            tool_name=MULTI_TOOL,
            tool_input=multi_input,
            turn_mode="execute_approved",
            runtime_approval=multi_approval,
        ),
    )
    assert multi_response["ok"] is True
    assert multi_response["runtime_state"] == "observed"
    assert spy.multi_calls == 1


def assert_stale_and_mismatched_approval_guardrails(
    client: TestClient,
    spy: ExecutionSpy,
) -> None:
    approval = prepare_runtime_approval(client)

    changed_input = {**valid_runtime_tool_input(), "stack": ["Spring"]}
    assert_rejected_without_execution(
        client,
        spy,
        runtime_turn_payload(
            tool_input=changed_input,
            turn_mode="execute_approved",
            runtime_approval=approval,
        ),
        "approval_mismatch",
    )

    assert_rejected_without_execution(
        client,
        spy,
        runtime_turn_payload(
            turn_mode="execute_approved",
            runtime_approval=approval,
            context_overrides={"search_brief_fingerprint": "brief-fingerprint-2"},
        ),
        "approval_mismatch",
    )
    fresh_prepare = post_runtime_turn(
        client,
        runtime_turn_payload(
            context_overrides={"search_brief_fingerprint": "brief-fingerprint-2"},
        ),
    )
    assert fresh_prepare["ok"] is True
    assert fresh_prepare["runtime_state"] == "approval_pending"
    assert spy.total_calls == 0

    for field_name, wrong_value in [
        ("plan_fingerprint", "stale-plan"),
        ("query_count", 999),
        ("execution_mode", "multi_wave"),
        ("multi_wave_enabled", True),
        ("tool_name", MULTI_TOOL),
    ]:
        assert_rejected_without_execution(
            client,
            spy,
            runtime_turn_payload(
                turn_mode="execute_approved",
                runtime_approval=approval,
                context_overrides={field_name: wrong_value},
            ),
            "stale_context",
        )


def assert_cross_mode_and_multi_wave_settings_guardrails(
    client: TestClient,
    spy: ExecutionSpy,
) -> None:
    single_approval = prepare_runtime_approval(client)
    multi_input = valid_multi_wave_tool_input()
    assert_rejected_without_execution(
        client,
        spy,
        runtime_turn_payload(
            tool_name=MULTI_TOOL,
            tool_input=multi_input,
            turn_mode="execute_approved",
            runtime_approval=single_approval,
        ),
        "approval_mismatch",
    )

    multi_approval = prepare_runtime_approval(client, MULTI_TOOL, multi_input)
    assert_rejected_without_execution(
        client,
        spy,
        runtime_turn_payload(
            tool_name=SINGLE_TOOL,
            tool_input=valid_runtime_tool_input(),
            turn_mode="execute_approved",
            runtime_approval=multi_approval,
        ),
        "approval_mismatch",
    )

    for field_name, wrong_value in [
        ("max_waves", 6),
        ("min_new_unique_per_wave", 4),
        ("patience", 3),
    ]:
        changed_multi_input = valid_multi_wave_tool_input({field_name: wrong_value})
        assert_rejected_without_execution(
            client,
            spy,
            runtime_turn_payload(
                tool_name=MULTI_TOOL,
                tool_input=changed_multi_input,
                turn_mode="execute_approved",
                runtime_approval=multi_approval,
            ),
            "approval_mismatch",
        )


def assert_runtime_approval_mutation_guardrails(
    client: TestClient,
    spy: ExecutionSpy,
) -> None:
    approval = prepare_runtime_approval(client)
    for field_name, wrong_value in [
        ("tool_call_id", "wrong-tool-call"),
        ("tool_name", MULTI_TOOL),
        ("tool_input_fingerprint", "wrong-tool-input"),
        ("context_fingerprint", "wrong-context"),
        ("idempotency_key", "wrong-idempotency-key"),
        ("approval_status", "required"),
    ]:
        mutated_approval = {**approval, field_name: wrong_value}
        assert_rejected_without_execution(
            client,
            spy,
            runtime_turn_payload(
                turn_mode="execute_approved",
                runtime_approval=mutated_approval,
            ),
            "approval_mismatch",
        )

    extra_approval_payload = runtime_turn_payload(
        turn_mode="execute_approved",
        runtime_approval={**approval, "extra": "not allowed"},
    )
    response = client.post(RUNTIME_ENDPOINT, json=extra_approval_payload)
    assert response.status_code == 422
    assert spy.total_calls == 0


def assert_schema_and_unsafe_field_guardrails(
    client: TestClient,
    spy: ExecutionSpy,
) -> None:
    request_extra_payload = runtime_turn_payload()
    request_extra_payload["query_plan"] = {}
    response = client.post(RUNTIME_ENDPOINT, json=request_extra_payload)
    assert response.status_code == 422
    assert spy.total_calls == 0

    for field_name in UNSAFE_RUNTIME_FIELDS:
        tool_input_payload = runtime_turn_payload()
        tool_input_payload["tool_input"][field_name] = "not allowed"
        assert_rejected_without_execution(
            client,
            spy,
            tool_input_payload,
            "invalid_tool_input",
        )

        context_payload = runtime_turn_payload()
        context_payload["runtime_context"][field_name] = "not allowed"
        assert_rejected_without_execution(
            client,
            spy,
            context_payload,
            "invalid_runtime_context",
        )


def assert_missing_tavily_key_during_execution_is_blocked(
    client: TestClient,
    spy: ExecutionSpy,
) -> None:
    previous_key = with_fake_tavily_key()
    try:
        approval = prepare_runtime_approval(client)
    finally:
        restore_tavily_key(previous_key)

    os.environ.pop("TAVILY_API_KEY", None)
    response = post_runtime_turn(
        client,
        runtime_turn_payload(
            turn_mode="execute_approved",
            runtime_approval=approval,
        ),
    )
    assert_error_code(response, "tool_unavailable")
    assert spy.total_calls == 0
    restore_tavily_key(previous_key)


def extract_js_function_body(source: str, function_name: str) -> str:
    marker = f"function {function_name}("
    start = source.index(marker)
    brace_start = source.index("{", start)
    depth = 0
    for index in range(brace_start, len(source)):
        character = source[index]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return source[brace_start + 1 : index]
    raise AssertionError(f"Could not extract {function_name} body.")


def assert_frontend_runtime_only_guardrails() -> None:
    source = (PROJECT_DIR / "app" / "static" / "app.js").read_text(encoding="utf-8")
    run_body = extract_js_function_body(source, "runStructuredSearch")
    clear_plan_body = extract_js_function_body(source, "clearPlannerData")
    search_error_body = extract_js_function_body(source, "renderSearchErrors")
    update_action_body = extract_js_function_body(source, "updateActionState")
    downstream_clear_body = extract_js_function_body(
        source,
        "clearDownstreamStateAfterBriefChange",
    )

    assert "fetch(AGENT_RUNTIME_TURN_ENDPOINT" in run_body
    assert "fetch(searchEndpoint" not in run_body
    assert "/api/structured-search" not in run_body
    for obsolete_helper in [
        "searchEndpoint(",
        "buildSearchRequest(",
        "buildExecutionApproval(",
    ]:
        assert obsolete_helper not in run_body

    assert "clearRuntimeApproval();" in clear_plan_body
    assert "clearPlannerData();" in downstream_clear_body
    assert "clearRuntimeApproval();" in search_error_body
    assert "clearRuntimeApproval();" in source[
        source.index('multiWaveInput.addEventListener("change"') :
    ]
    assert "searchButton.disabled = !latestExecutablePlan || !currentRuntimePendingApproval || isBusy;" in update_action_body


def assert_runtime_guardrails() -> None:
    from app import main

    client = TestClient(main.app)
    previous_key = with_fake_tavily_key()
    try:
        with PatchedExecutionHelpers(main) as spy:
            assert_prepare_never_executes(client, spy)
            assert_valid_execution_calls_mocked_helpers(client, spy)
    finally:
        restore_tavily_key(previous_key)

    previous_key = with_fake_tavily_key()
    try:
        with PatchedExecutionHelpers(main) as spy:
            assert_stale_and_mismatched_approval_guardrails(client, spy)
            assert_cross_mode_and_multi_wave_settings_guardrails(client, spy)
    finally:
        restore_tavily_key(previous_key)

    previous_key = with_fake_tavily_key()
    try:
        with PatchedExecutionHelpers(main) as spy:
            assert_runtime_approval_mutation_guardrails(client, spy)
            assert_schema_and_unsafe_field_guardrails(client, spy)
    finally:
        restore_tavily_key(previous_key)

    with PatchedExecutionHelpers(main) as spy:
        assert_missing_tavily_key_during_execution_is_blocked(client, spy)


def run_smoke() -> None:
    assert_runtime_guardrails()
    assert_frontend_runtime_only_guardrails()


if __name__ == "__main__":
    run_smoke()
    print("P6 runtime guardrails smoke passed")
