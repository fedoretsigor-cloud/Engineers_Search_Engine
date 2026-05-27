import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))


def assert_routes_import_without_main() -> None:
    import app.routes  # noqa: F401

    assert "app.main" not in sys.modules


def expected_route_specs() -> list[tuple[str, str, str]]:
    return [
        ("GET", "/", "index"),
        ("GET", "/api/health", "health"),
        ("POST", "/api/structured-search/validate", "validate_structured_search"),
        ("POST", "/api/search-brief/validate", "validate_search_brief_endpoint"),
        ("POST", "/api/recruiter-chat/turn", "create_recruiter_chat_turn"),
        ("POST", "/api/recruiter-chat/intent", "classify_recruiter_chat_intent"),
        ("POST", "/api/agent/plan", "create_agent_plan"),
        ("GET", "/api/agent/tools", "get_agent_tools"),
        ("POST", "/api/query-plan", "create_query_plan"),
        ("POST", "/api/agent/query-plan", "create_agent_query_plan"),
        ("POST", "/api/agent/runtime/turn", "create_agent_runtime_turn"),
        (
            "POST",
            "/api/candidate-workspace/explanation-wording",
            "create_candidate_explanation_wording",
        ),
        ("POST", "/api/ai-query-plan/validate", "validate_ai_query_plan_endpoint"),
        ("POST", "/api/structured-search", "structured_search"),
        ("POST", "/api/structured-search/multi-wave", "structured_search_multi_wave"),
        ("POST", "/api/search", "search"),
    ]


def current_route_specs(main_module) -> list[tuple[str, str, str]]:
    specs = []
    for route in main_module.app.routes:
        path = getattr(route, "path", None)
        if path != "/" and not (path and path.startswith("/api/")):
            continue

        for method in sorted(route.methods or []):
            if method in {"GET", "POST"}:
                specs.append((method, path, route.endpoint.__name__))

    return specs


def assert_main_compatibility(main_module) -> None:
    expected_names = [
        "index",
        "health",
        "validate_structured_search",
        "validate_search_brief_endpoint",
        "create_recruiter_chat_turn",
        "classify_recruiter_chat_intent",
        "create_agent_plan",
        "get_agent_tools",
        "create_query_plan",
        "create_agent_query_plan",
        "create_agent_runtime_turn",
        "create_candidate_explanation_wording",
        "validate_ai_query_plan_endpoint",
        "structured_search",
        "structured_search_multi_wave",
        "search",
        "run_query_plan_wave",
        "run_openai_json_recruiter_chat",
        "run_openai_json_recruiter_intent",
        "run_openai_json_planner",
        "run_openai_json_agent_wording",
    ]
    missing = [
        name for name in expected_names if not callable(getattr(main_module, name, None))
    ]
    assert not missing, f"Missing callable compatibility names: {missing}"


def valid_structured_payload() -> dict:
    return {
        "role_family": "Backend Developer",
        "technology": "Java",
        "stack": ["Spring", "Kafka"],
        "location": "Ukraine",
        "search_depth": "standard",
        "linkedin_profiles_only": True,
        "location_filter_enabled": True,
    }


def assert_no_network_http_routes(main_module) -> None:
    client = TestClient(main_module.app)

    root_response = client.get("/")
    assert root_response.status_code == 200
    assert "Engineers Search" in root_response.text

    health_response = client.get("/api/health")
    assert health_response.status_code == 200
    assert health_response.json() == {
        "status": "ok",
        "service": "engineers-search-engine",
        "phase": "phase-9-5-final-poc",
    }

    tools_response = client.get("/api/agent/tools")
    assert tools_response.status_code == 200
    tools_payload = tools_response.json()
    assert tools_payload["ok"] is True
    assert tools_payload["agent_tools"]

    validate_response = client.post(
        "/api/structured-search/validate",
        json=valid_structured_payload(),
    )
    assert validate_response.status_code == 200
    validate_payload = validate_response.json()
    assert validate_payload["ok"] is True
    assert validate_payload["normalized_request"]["technology"] == "Java"
    assert validate_payload["normalized_request"]["location"] == "Ukraine"

    query_plan_response = client.post(
        "/api/query-plan",
        json=valid_structured_payload(),
    )
    assert query_plan_response.status_code == 200
    query_plan_payload = query_plan_response.json()
    assert query_plan_payload["ok"] is True
    assert len(query_plan_payload["query_plan"]["queries"]) == 10
    assert query_plan_payload["plan_fingerprint"]

    intent_response = client.post(
        "/api/recruiter-chat/intent",
        json={
            "latest_message": "Confirm",
            "language": "en",
            "context_type": "pending_action",
            "pending_action_type": "start_search",
            "current_brief_status": "ready_for_planning",
        },
    )
    assert intent_response.status_code == 200
    intent_payload = intent_response.json()
    assert intent_payload["ok"] is True
    assert intent_payload["pending_action_intent"] == "confirm"

    legacy_search_response = client.post(
        "/api/search",
        json={"query": "site:linkedin.com/in Java Ukraine"},
    )
    assert legacy_search_response.status_code == 200
    legacy_search_payload = legacy_search_response.json()
    assert legacy_search_payload["ok"] is False
    assert (
        legacy_search_payload["errors"][0]["code"]
        == "legacy_raw_search_disabled"
    )


def run_smoke() -> None:
    assert_routes_import_without_main()

    from app import main

    assert current_route_specs(main) == expected_route_specs()
    assert_main_compatibility(main)
    assert_no_network_http_routes(main)


if __name__ == "__main__":
    run_smoke()
    print("P5.5 routes smoke passed")
