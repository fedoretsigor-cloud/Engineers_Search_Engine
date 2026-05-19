import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from scripts.smoke_p6_runtime_guardrails import (  # noqa: E402
    MULTI_TOOL,
    approved_runtime_payload_from_prepare,
    post_runtime_turn,
    runtime_turn_payload,
    valid_multi_wave_tool_input,
)


FAKE_TAVILY_KEY = "fake-tavily-key"
ENV_KEYS_TO_RESTORE = ["TAVILY_API_KEY", "OPENAI_API_KEY", "OPENAI_MODEL"]


def snapshot_files(search_run_log_dir: Path) -> set[Path]:
    if not search_run_log_dir.exists():
        return set()

    return set(search_run_log_dir.glob("*.json"))


def fake_linkedin_raw_result() -> dict:
    return {
        "title": "Olena Kovalenko - Senior Java Developer - LinkedIn",
        "url": "https://ua.linkedin.com/in/olena-kovalenko",
        "content": (
            "Olena Kovalenko\n"
            "Senior Java Developer\n"
            "Kyiv, Ukraine\n"
            "500 connections\n"
            "About Java backend engineer with Spring, Kafka, REST, and "
            "microservices experience."
        ),
        "score": 0.98,
    }


def fake_query_result(query_slot: dict, wave_id: int | None = None) -> dict:
    raw_results = [fake_linkedin_raw_result()] if query_slot["id"] == "Q01" else []
    result = {
        "query_id": query_slot["id"],
        "category": query_slot["category"],
        "role_phrase": query_slot.get("role_phrase"),
        "uses_stack": query_slot.get("uses_stack", []),
        "query": query_slot["query"],
        "ok": True,
        "raw_results": raw_results,
        "raw_count": len(raw_results),
        "response_time": 0.01,
        "usage": {"mocked": True},
        "request_id": f"fake-{wave_id or 1}-{query_slot['id']}",
        "error": None,
    }
    if wave_id is not None:
        result["wave_id"] = wave_id

    return result


async def fake_run_query_plan_wave(
    query_plan: dict,
    wave_id: int | None = None,
) -> list[dict]:
    return [
        fake_query_result(query_slot, wave_id)
        for query_slot in query_plan["queries"]
    ]


def assert_successful_runtime_execution(response: dict) -> dict:
    assert response["ok"] is True
    assert response["runtime_state"] == "observed"
    assert response["tool_results"][0]["ok"] is True

    result = response["tool_results"][0]["result"]
    assert result["report"]["unique_profiles"] >= 1
    assert result["deduped_results"][0]["normalized_url"] == (
        "ua.linkedin.com/in/olena-kovalenko"
    )
    assert result["deduped_results"][0]["result"]["quality_score"] >= 1
    return result


def run_prepare_execute(client: TestClient, **payload_kwargs) -> dict:
    prepare = post_runtime_turn(client, runtime_turn_payload(**payload_kwargs))
    approval = approved_runtime_payload_from_prepare(prepare)
    return post_runtime_turn(
        client,
        runtime_turn_payload(
            **payload_kwargs,
            turn_mode="execute_approved",
            runtime_approval=approval,
        ),
    )


def run_smoke() -> None:
    from app import main

    client = TestClient(main.app)
    previous_env = {key: os.environ.get(key) for key in ENV_KEYS_TO_RESTORE}
    original_run_query_plan_wave = main.run_query_plan_wave
    original_write_structured_search_snapshot = main.write_structured_search_snapshot
    original_single_wrapper = main.execute_single_wave_structured_search_response
    original_multi_wrapper = main.execute_multi_wave_structured_search_response
    snapshots_before = snapshot_files(main.SEARCH_RUN_LOG_DIR)

    def fake_write_structured_search_snapshot(*args, **kwargs):
        return None

    try:
        os.environ["TAVILY_API_KEY"] = FAKE_TAVILY_KEY
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("OPENAI_MODEL", None)
        main.run_query_plan_wave = fake_run_query_plan_wave
        main.write_structured_search_snapshot = fake_write_structured_search_snapshot

        single_response = run_prepare_execute(client)
        single_result = assert_successful_runtime_execution(single_response)
        assert single_result.get("experimental") is not True

        multi_response = run_prepare_execute(
            client,
            tool_name=MULTI_TOOL,
            tool_input=valid_multi_wave_tool_input(),
        )
        multi_result = assert_successful_runtime_execution(multi_response)
        assert multi_result["experimental"] is True
        assert multi_result["report"]["waves_run"] >= 1
        assert multi_result["report"]["wave_reports"]
    finally:
        main.run_query_plan_wave = original_run_query_plan_wave
        main.write_structured_search_snapshot = original_write_structured_search_snapshot
        for key, value in previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert main.execute_single_wave_structured_search_response is original_single_wrapper
    assert main.execute_multi_wave_structured_search_response is original_multi_wrapper
    assert snapshot_files(main.SEARCH_RUN_LOG_DIR) == snapshots_before


if __name__ == "__main__":
    run_smoke()
    print("P6 unmocked runtime execution smoke passed")
