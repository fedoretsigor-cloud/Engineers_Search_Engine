import asyncio
import os
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main


NORMALIZED_REQUEST = {
    "role_family": "Backend Developer",
    "technology": "Java",
    "stack": ["Spring", "Kafka"],
    "location": "Ukraine",
    "search_depth": "standard",
    "linkedin_profiles_only": True,
    "location_filter_enabled": True,
}


def execution_approval(action: str) -> main.ExecutionApproval:
    query_plan = main.RuleBasedQueryPlannerV1().build(NORMALIZED_REQUEST)
    return main.ExecutionApproval(
        approval_status="approved",
        approved_action=action,
        approved_planner_mode="rule_based",
        approved_query_count=len(query_plan["queries"]),
        approved_plan_fingerprint=main.query_plan_fingerprint(query_plan),
    )


def structured_request(language: str = "en") -> main.StructuredSearchRequest:
    return main.StructuredSearchRequest(
        **NORMALIZED_REQUEST,
        execution_approval=execution_approval("run_single_wave_search"),
        agent_language=language,
    )


def multi_wave_request(language: str = "ru") -> main.MultiWaveStructuredSearchRequest:
    return main.MultiWaveStructuredSearchRequest(
        **NORMALIZED_REQUEST,
        execution_approval=execution_approval("run_multi_wave_search"),
        agent_language=language,
        max_waves=1,
        min_new_unique_per_wave=0,
        patience=1,
    )


def fake_raw_result(
    slug: str,
    name: str,
    headline: str,
    content: str,
) -> dict:
    return {
        "title": f"{name} - {headline} | LinkedIn",
        "url": f"https://www.linkedin.com/in/{slug}",
        "content": content,
    }


async def fake_run_query_plan_wave(
    query_plan: dict,
    wave_id: int | None = None,
) -> list[dict]:
    query_results = []
    for query in query_plan["queries"]:
        raw_results = []
        if query["id"] == "Q01":
            raw_results = [
                fake_raw_result(
                    "anna-java-backend",
                    "Anna Kovalenko",
                    "Senior Java Backend Developer",
                    (
                        "Anna Kovalenko - Senior Java Backend Developer\n"
                        "Kyiv, Ukraine\n"
                        "Java Spring Kafka microservices."
                    ),
                ),
                fake_raw_result(
                    "oleg-software-engineer",
                    "Oleg Bondar",
                    "Software Engineer",
                    (
                        "Oleg Bondar - Software Engineer\n"
                        "Ukraine\n"
                        "Java backend services."
                    ),
                ),
            ]
        elif query["id"] == "Q07":
            raw_results = [
                fake_raw_result(
                    "iryna-java-engineer",
                    "Iryna Melnyk",
                    "Java Engineer",
                    (
                        "Iryna Melnyk - Java Engineer\n"
                        "Lviv, Ukraine\n"
                        "Kafka distributed systems."
                    ),
                )
            ]

        query_result = {
            "query_id": query["id"],
            "category": query["category"],
            "role_phrase": query.get("role_phrase"),
            "uses_stack": query.get("uses_stack", []),
            "query": query["query"],
            "ok": True,
            "raw_results": raw_results,
            "raw_count": len(raw_results),
            "response_time": 0.01,
            "usage": None,
            "request_id": f"fake-{query['id']}",
            "error": None,
        }
        if wave_id is not None:
            query_result["wave_id"] = wave_id
        query_results.append(query_result)

    return query_results


async def forbidden_openai_call(*args, **kwargs):
    raise AssertionError("P5-006 Agent Response must not call OpenAI/LLM.")


async def run_smoke() -> None:
    original_tavily_key = os.environ.get("TAVILY_API_KEY")
    original_openai_key = os.environ.get("OPENAI_API_KEY")
    original_openai_model = os.environ.get("OPENAI_MODEL")
    original_run_query_plan_wave = main.run_query_plan_wave
    original_chat_llm = main.run_openai_json_recruiter_chat
    original_planner_llm = main.run_openai_json_planner
    original_wording_llm = main.run_openai_json_agent_wording

    os.environ["TAVILY_API_KEY"] = "fake-no-network-key"
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)
    main.run_query_plan_wave = fake_run_query_plan_wave
    main.run_openai_json_recruiter_chat = forbidden_openai_call
    main.run_openai_json_planner = forbidden_openai_call
    main.run_openai_json_agent_wording = forbidden_openai_call

    try:
        assert main.StructuredSearchRequest(agent_language="ru").agent_language == "ru"

        single_wave = await main.structured_search(structured_request("en"))
        assert single_wave["ok"] is True
        assert single_wave["agent_response"]["language"] == "en"
        assert single_wave["agent_response"]["summary_facts"]["candidate_count"] == 3
        assert single_wave["agent_response"]["summary_facts"][
            "quality_distribution"
        ] == {
            "strong": 2,
            "review": 1,
            "weak": 0,
        }
        assert all(
            action["executable"] is False
            for action in single_wave["agent_response"]["suggested_next_actions"]
        )
        assert all(
            "multi-wave" not in action["label"].lower()
            for action in single_wave["agent_response"]["suggested_next_actions"]
        )
        next_options = single_wave["agent_response"]["next_iteration_options"]
        assert [option["id"] for option in next_options] == [
            "review_high_quality_candidates",
            "try_deep_search_depth",
        ]
        assert all(
            option["requires_approval_before_execution"] is True
            and option["is_executable_now"] is False
            and option["proposed_brief_patch"]["operations"]
            for option in next_options
        )
        assert next_options[1]["proposed_brief_patch"]["operations"][0] == {
            "operation": main.BRIEF_PATCH_SET_SEARCH_DEPTH,
            "field": "search_depth",
            "value": main.SEARCH_DEPTH_DEEP,
        }
        assert "public snippets" in single_wave["agent_response"]["limitations"][0][
            "message"
        ]

        multi_wave = await main.structured_search_multi_wave(multi_wave_request("ru"))
        assert multi_wave["ok"] is True
        assert multi_wave["agent_response"]["language"] == "ru"
        assert (
            multi_wave["agent_response"]["summary_facts"]["mode"] == "multi_wave"
        )
        assert "agent_response" in multi_wave
        assert all(
            option["id"] != "try_deep_search_depth"
            for option in multi_wave["agent_response"]["next_iteration_options"]
        )

    finally:
        main.run_query_plan_wave = original_run_query_plan_wave
        main.run_openai_json_recruiter_chat = original_chat_llm
        main.run_openai_json_planner = original_planner_llm
        main.run_openai_json_agent_wording = original_wording_llm
        if original_tavily_key is None:
            os.environ.pop("TAVILY_API_KEY", None)
        else:
            os.environ["TAVILY_API_KEY"] = original_tavily_key
        if original_openai_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = original_openai_key
        if original_openai_model is None:
            os.environ.pop("OPENAI_MODEL", None)
        else:
            os.environ["OPENAI_MODEL"] = original_openai_model


if __name__ == "__main__":
    asyncio.run(run_smoke())
    print("P5 Agent Response smoke passed")
