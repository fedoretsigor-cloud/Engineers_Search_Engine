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


def ready_brief() -> main.SearchBrief:
    return main.SearchBrief(
        source_text="Find Backend Developer Java in Ukraine with Spring and Kafka.",
        brief_status="ready_for_planning",
        role_family="Backend Developer",
        technology="Java",
        stack=["Spring", "Kafka"],
        location="Ukraine",
        seniority=None,
        must_have=["Java"],
        nice_to_have=["Spring", "Kafka"],
        exclusions=[],
        search_depth="standard",
        profile_sources=["linkedin_public"],
        assumptions=[],
    )


def sample_agent_response() -> dict:
    query_plan = main.RuleBasedQueryPlannerV1().build(NORMALIZED_REQUEST)
    report = {
        "mode": "single_wave",
        "unique_profiles": 3,
        "raw_total": 3,
        "displayed": 3,
        "queries_succeeded": 2,
        "queries_total": 10,
    }
    deduped_results = [
        {"result": {"quality_score": 90, "role_fit": "target_or_close_role", "technology_fit": "exact", "stack_fit": "selected_stack_found", "review_flags": [], "location_signal_status": "target_location"}},
        {"result": {"quality_score": 82, "role_fit": "target_or_close_role", "technology_fit": "exact", "stack_fit": "selected_stack_found", "review_flags": ["seniority_missing"], "location_signal_status": "target_location"}},
        {"result": {"quality_score": 65, "role_fit": "target_or_close_role", "technology_fit": "exact", "stack_fit": "missing", "review_flags": ["selected_stack_missing"], "location_signal_status": "country_domain"}},
    ]
    return main.build_agent_response(query_plan, report, deduped_results, "en")


async def run_smoke() -> None:
    original_openai_key = os.environ.get("OPENAI_API_KEY")
    original_openai_model = os.environ.get("OPENAI_MODEL")
    original_wording_llm = main.run_openai_json_agent_wording
    captured_payloads: list[dict] = []

    async def fake_wording_llm(payload: dict):
        captured_payloads.append(payload)
        assert "raw candidate" not in str(payload).lower()
        assert "linkedin.com/in/" not in str(payload).lower()
        if payload["wording_use_case"] == "agent_plan":
            return {
                "message": (
                    "I understood the Java Backend Developer search in Ukraine. "
                    "If this is correct, confirm and I will start the search."
                ),
                "warnings": [],
                "limitations": [],
            }, None

        return {
            "message": (
                "Search completed: 3 unique candidates found: 2 strong, 1 review, 0 weak."
            ),
            "warnings": ["Public snippets are incomplete."],
            "limitations": [],
        }, None

    async def disallowed_number_llm(payload: dict):
        return {
            "message": "The approved backend search returned 999 candidates.",
            "warnings": [],
            "limitations": [],
        }, None

    async def disallowed_field_llm(payload: dict):
        return {
            "message": "I understood the Java Backend Developer search in Ukraine.",
            "warnings": [],
            "limitations": [],
            "suggested_next_actions": [{"label": "Run it", "executable": True}],
        }, None

    try:
        os.environ["OPENAI_API_KEY"] = "fake-openai-key"
        os.environ["OPENAI_MODEL"] = "fake-openai-model"
        main.run_openai_json_agent_wording = fake_wording_llm

        plan_response = await main.build_agent_plan_response_with_wording(
            main.AgentPlanRequest(search_brief=ready_brief(), language="en")
        )
        agent_plan = plan_response["agent_plan"]
        assert agent_plan["wording_mode"] == "llm_assisted"
        assert agent_plan["fallback_reason"] is None
        assert agent_plan["proposed_action"] == main.agent_plan_proposed_action()
        assert "confirm" in agent_plan["message"].lower()
        assert "start the search" in agent_plan["message"].lower()
        assert "Prepare search" not in agent_plan["message"]
        assert "Run search" not in agent_plan["message"]
        assert plan_response["message"] == agent_plan["message"]

        agent_response = await main.apply_llm_wording_to_agent_response(
            sample_agent_response()
        )
        assert agent_response["wording_mode"] == "llm_assisted"
        assert agent_response["fallback_reason"] is None
        assert agent_response["message"] == (
            "Search completed: 3 unique candidates found: 2 strong, 1 review, 0 weak."
        )
        assert agent_response["summary_facts"]["candidate_count"] == 3
        response_payload = captured_payloads[-1]
        assert "visible_summary_facts" in response_payload
        assert "summary_facts" not in response_payload
        assert "quality_notes" not in response_payload
        assert "limitations" not in response_payload
        assert "suggested_next_actions" not in response_payload
        assert "raw_total" not in str(response_payload)
        assert "queries_total" not in str(response_payload)
        assert all(
            action["executable"] is False
            for action in agent_response["suggested_next_actions"]
        )
        assert agent_response["next_iteration_options"]
        assert all(
            option["requires_approval_before_execution"] is True
            and option["is_executable_now"] is False
            for option in agent_response["next_iteration_options"]
        )
        assert agent_response["llm_warnings"] == ["Public snippets are incomplete."]
        assert "public snippets" in agent_response["limitations"][0]["message"]

        main.run_openai_json_agent_wording = disallowed_number_llm
        fallback_response = await main.apply_llm_wording_to_agent_response(
            sample_agent_response()
        )
        assert fallback_response["wording_mode"] == "deterministic_fallback"
        assert fallback_response["fallback_reason"] == "llm_output_disallowed_numbers"
        assert "999" not in fallback_response["message"]

        main.run_openai_json_agent_wording = disallowed_field_llm
        field_fallback_plan = await main.build_agent_plan_response_with_wording(
            main.AgentPlanRequest(search_brief=ready_brief(), language="en")
        )
        assert field_fallback_plan["agent_plan"]["wording_mode"] == (
            "deterministic_fallback"
        )
        assert (
            field_fallback_plan["agent_plan"]["fallback_reason"]
            == "llm_output_disallowed_fields"
        )
        assert field_fallback_plan["agent_plan"]["proposed_action"] == (
            main.agent_plan_proposed_action()
        )

        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("OPENAI_MODEL", None)
        no_config_plan = await main.build_agent_plan_response_with_wording(
            main.AgentPlanRequest(search_brief=ready_brief(), language="en")
        )
        assert no_config_plan["agent_plan"]["wording_mode"] == "deterministic_fallback"
        assert (
            no_config_plan["agent_plan"]["fallback_reason"]
            == "openai_not_configured"
        )

        assert {payload["wording_use_case"] for payload in captured_payloads} == {
            "agent_plan",
            "agent_response",
        }
        assert all("proposed_brief_patch" not in str(payload) for payload in captured_payloads)

    finally:
        main.run_openai_json_agent_wording = original_wording_llm
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
    print("P5 LLM Wording smoke passed")
