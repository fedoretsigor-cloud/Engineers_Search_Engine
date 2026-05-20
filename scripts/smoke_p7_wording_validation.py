import asyncio
import copy
import os
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import agent_wording, main


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
        {
            "result": {
                "quality_score": 90,
                "role_fit": "target_or_close_role",
                "technology_fit": "exact",
                "stack_fit": "selected_stack_found",
                "review_flags": [],
                "location_signal_status": "target_location",
            }
        },
        {
            "result": {
                "quality_score": 82,
                "role_fit": "target_or_close_role",
                "technology_fit": "exact",
                "stack_fit": "selected_stack_found",
                "review_flags": ["seniority_missing"],
                "location_signal_status": "target_location",
            }
        },
        {
            "result": {
                "quality_score": 65,
                "role_fit": "target_or_close_role",
                "technology_fit": "exact",
                "stack_fit": "missing",
                "review_flags": ["selected_stack_missing"],
                "location_signal_status": "country_domain",
            }
        },
    ]
    return main.build_agent_response(query_plan, report, deduped_results, "en")


def expected_provenance_keys(
    *,
    fallback_reason: str | None = None,
    no_call_reason: str | None = None,
    model: str | None = None,
) -> set[str]:
    keys = {
        "message_type",
        "surface",
        "source_owner",
        "source_object",
        "language",
        "wording_mode",
        "taxonomy_version",
        "facts_contract_version",
        "style_policy_version",
        "routing_policy_version",
        "payload_contract_version",
        "prompt_contract_version",
        "prompt_version",
        "validator_version",
        "deterministic_builder_version",
    }
    if fallback_reason:
        keys.add("fallback_reason")
    if no_call_reason:
        keys.add("no_call_reason")
    if model:
        keys.add("model")
    return keys


def assert_provenance(
    value: dict,
    *,
    message_type: str,
    wording_mode: str,
    fallback_reason: str | None = None,
    no_call_reason: str | None = None,
    model: str | None = None,
) -> None:
    assert "no_call_reason" not in value
    provenance = value["wording_provenance"]
    assert set(provenance) == expected_provenance_keys(
        fallback_reason=fallback_reason,
        no_call_reason=no_call_reason,
        model=model,
    )
    assert provenance["message_type"] == message_type
    assert provenance["surface"] == "chat"
    assert provenance["language"] == "en"
    assert provenance["wording_mode"] == wording_mode
    assert provenance["taxonomy_version"] == (
        agent_wording.AGENT_WORDING_TAXONOMY_VERSION
    )
    assert provenance["facts_contract_version"] == (
        agent_wording.AGENT_WORDING_FACTS_CONTRACT_VERSION
    )
    assert provenance["style_policy_version"] == (
        agent_wording.AGENT_WORDING_STYLE_POLICY_VERSION
    )
    assert provenance["routing_policy_version"] == (
        agent_wording.AGENT_WORDING_ROUTING_POLICY_VERSION
    )
    assert provenance["payload_contract_version"] == (
        agent_wording.AGENT_WORDING_PAYLOAD_CONTRACT_VERSION
    )
    assert provenance["prompt_contract_version"] == (
        agent_wording.AGENT_WORDING_PROMPT_CONTRACT_VERSION
    )
    assert provenance["prompt_version"] == agent_wording.AGENT_WORDING_PROMPT_VERSION
    assert provenance["validator_version"] == (
        agent_wording.AGENT_WORDING_VALIDATOR_VERSION
    )
    assert provenance["deterministic_builder_version"] == (
        agent_wording.AGENT_WORDING_DETERMINISTIC_BUILDER_VERSION
    )

    if message_type == "agent_plan":
        assert provenance["source_owner"] == (
            "Agent Plan backend; bounded wording overlay"
        )
        assert provenance["source_object"] == "/api/agent/plan agent_plan.message"
    else:
        assert provenance["source_owner"] == (
            "deterministic Agent Response backend; bounded wording overlay"
        )
        assert provenance["source_object"] == (
            "approved search response agent_response.message"
        )

    if fallback_reason:
        assert value["fallback_reason"] == fallback_reason
        assert provenance["fallback_reason"] == fallback_reason
    else:
        assert value["fallback_reason"] is None

    if no_call_reason:
        assert provenance["no_call_reason"] == no_call_reason
    else:
        assert "no_call_reason" not in provenance

    if model:
        assert provenance["model"] == model
    else:
        assert "model" not in provenance


async def assert_accepted_wording() -> None:
    captured_payloads: list[dict] = []

    async def fake_wording_llm(payload: dict):
        captured_payloads.append(payload)
        assert "linkedin.com/in/" not in str(payload).lower()
        if payload["wording_use_case"] == "agent_plan":
            return {
                "message": (
                    "I understood the Java Backend Developer search in Ukraine. "
                    "Build Plan can prepare the approved backend plan, and search "
                    "execution still needs approval."
                ),
                "warnings": [],
                "limitations": [],
            }, None

        limitation_kind = payload["limitations"][0]["kind"]
        return {
            "message": (
                "The approved backend search returned 3 candidates from 3 raw "
                "results. Review the strongest matches before changing the brief."
            ),
            "warnings": ["Public snippets are incomplete."],
            "limitations": [
                {
                    "kind": limitation_kind,
                    "message": (
                        "This summary uses only public snippets already returned "
                        "by the backend."
                    ),
                }
            ],
        }, None

    main.run_openai_json_agent_wording = fake_wording_llm

    plan_response = await main.build_agent_plan_response_with_wording(
        main.AgentPlanRequest(search_brief=ready_brief(), language="en")
    )
    agent_plan = plan_response["agent_plan"]
    assert agent_plan["wording_mode"] == "llm_assisted"
    assert agent_plan["proposed_action"] == main.agent_plan_proposed_action()
    assert agent_plan["brief_fingerprint"]
    assert agent_plan["input_snapshot"]["technology"] == "Java"
    assert plan_response["message"] == agent_plan["message"]
    assert_provenance(
        agent_plan,
        message_type="agent_plan",
        wording_mode="llm_assisted",
        model="fake-openai-model",
    )

    original_response = sample_agent_response()
    response_snapshot = copy.deepcopy(original_response)
    agent_response = await main.apply_llm_wording_to_agent_response(
        original_response
    )
    assert agent_response["wording_mode"] == "llm_assisted"
    assert agent_response["summary_facts"] == response_snapshot["summary_facts"]
    assert agent_response["quality_notes"] == response_snapshot["quality_notes"]
    assert (
        agent_response["suggested_next_actions"]
        == response_snapshot["suggested_next_actions"]
    )
    assert (
        agent_response["next_iteration_options"]
        == response_snapshot["next_iteration_options"]
    )
    assert [item["kind"] for item in agent_response["limitations"]] == [
        item["kind"] for item in response_snapshot["limitations"]
    ]
    assert agent_response["llm_warnings"] == ["Public snippets are incomplete."]
    assert_provenance(
        agent_response,
        message_type="agent_response",
        wording_mode="llm_assisted",
        model="fake-openai-model",
    )

    assert {payload["wording_use_case"] for payload in captured_payloads} == {
        "agent_plan",
        "agent_response",
    }


async def assert_no_config_fallback() -> None:
    async def forbidden_wording_llm(payload: dict):
        raise AssertionError("OpenAI wording runner should not be called")

    main.run_openai_json_agent_wording = forbidden_wording_llm
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)

    plan_response = await main.build_agent_plan_response_with_wording(
        main.AgentPlanRequest(search_brief=ready_brief(), language="en")
    )
    agent_plan = plan_response["agent_plan"]
    assert agent_plan["wording_mode"] == "deterministic_fallback"
    assert plan_response["message"] == agent_plan["message"]
    assert_provenance(
        agent_plan,
        message_type="agent_plan",
        wording_mode="deterministic_fallback",
        fallback_reason="openai_not_configured",
        no_call_reason="openai_not_configured",
    )


async def assert_attempted_call_fallbacks() -> None:
    async def disallowed_number_llm(payload: dict):
        return {
            "message": "The approved backend search returned 999 candidates.",
            "warnings": [],
            "limitations": [],
        }, None

    main.run_openai_json_agent_wording = disallowed_number_llm
    response = await main.apply_llm_wording_to_agent_response(sample_agent_response())
    assert response["wording_mode"] == "deterministic_fallback"
    assert "999" not in response["message"]
    assert_provenance(
        response,
        message_type="agent_response",
        wording_mode="deterministic_fallback",
        fallback_reason="llm_output_disallowed_numbers",
        model="fake-openai-model",
    )

    async def disallowed_field_llm(payload: dict):
        return {
            "message": "I understood the Java Backend Developer search in Ukraine.",
            "warnings": [],
            "limitations": [],
            "suggested_next_actions": [{"label": "Run it", "executable": True}],
        }, None

    main.run_openai_json_agent_wording = disallowed_field_llm
    plan_response = await main.build_agent_plan_response_with_wording(
        main.AgentPlanRequest(search_brief=ready_brief(), language="en")
    )
    agent_plan = plan_response["agent_plan"]
    assert agent_plan["proposed_action"] == main.agent_plan_proposed_action()
    assert plan_response["message"] == agent_plan["message"]
    assert_provenance(
        agent_plan,
        message_type="agent_plan",
        wording_mode="deterministic_fallback",
        fallback_reason="llm_output_disallowed_fields",
        model="fake-openai-model",
    )

    async def plan_limitation_llm(payload: dict):
        return {
            "message": "I understood the Java Backend Developer search in Ukraine.",
            "warnings": [],
            "limitations": [
                {
                    "kind": "extra_limitation",
                    "message": "This should not become an Agent Plan channel.",
                }
            ],
        }, None

    main.run_openai_json_agent_wording = plan_limitation_llm
    plan_response = await main.build_agent_plan_response_with_wording(
        main.AgentPlanRequest(search_brief=ready_brief(), language="en")
    )
    assert_provenance(
        plan_response["agent_plan"],
        message_type="agent_plan",
        wording_mode="deterministic_fallback",
        fallback_reason="llm_output_agent_plan_limitations_not_allowed",
        model="fake-openai-model",
    )

    async def new_limitation_kind_llm(payload: dict):
        return {
            "message": "The approved backend search returned 3 candidates.",
            "warnings": [],
            "limitations": [
                {
                    "kind": "new_kind",
                    "message": "This new limitation kind is not allowed.",
                }
            ],
        }, None

    main.run_openai_json_agent_wording = new_limitation_kind_llm
    response = await main.apply_llm_wording_to_agent_response(sample_agent_response())
    assert_provenance(
        response,
        message_type="agent_response",
        wording_mode="deterministic_fallback",
        fallback_reason="llm_output_new_limitation_kind",
        model="fake-openai-model",
    )


async def assert_unsafe_content_fallbacks() -> None:
    unsafe_messages = [
        "I found this profile at https://example.com.",
        "I inspected linkedin.com/in/example directly.",
        "I checked LinkedIn directly for this search.",
        "I will run the search without approval.",
        "I will message candidates now.",
    ]
    for unsafe_message in unsafe_messages:
        async def unsafe_llm(payload: dict, message=unsafe_message):
            return {
                "message": message,
                "warnings": [],
                "limitations": [],
            }, None

        main.run_openai_json_agent_wording = unsafe_llm
        response = await main.apply_llm_wording_to_agent_response(
            sample_agent_response()
        )
        assert_provenance(
            response,
            message_type="agent_response",
            wording_mode="deterministic_fallback",
            fallback_reason="llm_output_unsafe_content",
            model="fake-openai-model",
        )


async def run_smoke() -> None:
    original_openai_key = os.environ.get("OPENAI_API_KEY")
    original_openai_model = os.environ.get("OPENAI_MODEL")
    original_wording_llm = main.run_openai_json_agent_wording

    try:
        os.environ["OPENAI_API_KEY"] = "fake-openai-key"
        os.environ["OPENAI_MODEL"] = "fake-openai-model"
        await assert_accepted_wording()
        await assert_attempted_call_fallbacks()
        await assert_unsafe_content_fallbacks()
        await assert_no_config_fallback()
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
    print("P7 Wording Validation smoke passed")
