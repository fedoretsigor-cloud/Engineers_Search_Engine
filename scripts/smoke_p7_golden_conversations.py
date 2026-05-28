import asyncio
import copy
import os
import re
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import agent_wording, main, search_brief_extractor as extractor, search_execution


NORMALIZED_REQUEST = {
    "role_family": "Backend Developer",
    "technology": "Java",
    "stack": ["Spring", "Kafka"],
    "location": "Ukraine",
    "search_depth": "standard",
    "linkedin_profiles_only": True,
    "location_filter_enabled": True,
}

SINGLE_WAVE_TOOL = "run_single_wave_search"
FAKE_OPENAI_KEY = "fake-openai-key"
FAKE_OPENAI_MODEL = "fake-openai-model"
FAKE_TAVILY_KEY = "fake-tavily-key"


class SmokeRecorder:
    def __init__(self) -> None:
        self.recruiter_llm_calls: list[str] = []
        self.wording_llm_calls: list[dict] = []
        self.search_execution_calls = 0
        self.query_wave_calls = 0
        self.tavily_calls = 0


RECORDER = SmokeRecorder()


def ready_brief(stack: list[str] | None = None) -> main.SearchBrief:
    selected_stack = stack or ["Spring", "Kafka"]
    return main.SearchBrief(
        source_text="Find Backend Developer Java in Ukraine with Spring and Kafka.",
        brief_status="ready_for_planning",
        role_family="Backend Developer",
        technology="Java",
        stack=selected_stack,
        location="Ukraine",
        seniority=None,
        must_have=["Java"],
        nice_to_have=selected_stack,
        exclusions=[],
        search_depth="standard",
        profile_sources=["linkedin_public"],
        assumptions=[],
    )


def chat_request(
    text: str,
    *,
    language: str = "en",
    draft_brief: main.SearchBrief | None = None,
) -> main.RecruiterChatTurnRequest:
    return main.RecruiterChatTurnRequest(
        messages=[main.RecruiterChatMessage(role="user", content=text)],
        draft_brief=draft_brief,
        language=language,
    )


async def fake_recruiter_chat_llm(
    request: main.RecruiterChatTurnRequest,
) -> tuple[dict | None, list[dict[str, str]]]:
    latest_text = request.messages[-1].content
    RECORDER.recruiter_llm_calls.append(latest_text)
    text = " ".join(message.content.lower() for message in request.messages)

    if "backend" in text and "java" in text and "ukraine" in text:
        return {
            "draft_brief": {
                "source_text": latest_text,
                "brief_status": "ready_for_planning",
                "role_family": "Backend Developer",
                "technology": "Java",
                "stack": ["Spring", "Kafka"],
                "location": "Ukraine",
                "seniority": None,
                "must_have": ["Java"],
                "nice_to_have": ["Spring", "Kafka"],
                "exclusions": [],
                "search_depth": "standard",
                "profile_sources": ["linkedin_public"],
                "assumptions": [],
            }
        }, []

    return {
        "draft_brief": {
            "source_text": latest_text,
            "brief_status": "needs_clarification",
            "role_family": "Backend Developer",
            "technology": "Java",
            "stack": [],
            "location": None,
            "search_depth": "standard",
            "profile_sources": ["linkedin_public"],
            "assumptions": [],
        }
    }, []


async def fake_search_brief_extractor(
    *,
    latest_message: str,
    language: str,
    previous_brief: dict | None = None,
) -> tuple[dict | None, str | None]:
    request = main.RecruiterChatTurnRequest(
        language=language,
        messages=[main.RecruiterChatMessage(role="user", content=latest_message)],
    )
    output, errors = await fake_recruiter_chat_llm(request)
    if errors or not output:
        return None, "fake_search_brief_extractor_error"
    draft = output["draft_brief"]
    return {
        "schema_version": extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
        "draft_brief": {
            "source_text": draft.get("source_text") or latest_message,
            "role_family": draft.get("role_family"),
            "role_ambiguity": {
                "is_ambiguous": False,
                "label": None,
                "options": [],
                "clarification_question": None,
            },
            "technology": draft.get("technology"),
            "stack": draft.get("stack") or [],
            "location": draft.get("location"),
            "seniority": draft.get("seniority"),
            "must_have": draft.get("must_have") or [],
            "nice_to_have": draft.get("nice_to_have") or [],
            "domain_experience": [],
            "exclusions": draft.get("exclusions") or [],
            "search_depth": draft.get("search_depth") or "standard",
            "profile_sources": draft.get("profile_sources") or ["linkedin_public"],
            "notes": None,
        },
        "confidence": "high",
        "reason_codes": ["smoke_fixture"],
    }, None


async def forbidden_recruiter_chat_llm(*args, **kwargs):
    raise AssertionError("Recruiter-chat OpenAI runner must not be called here.")


async def forbidden_planner_llm(*args, **kwargs):
    raise AssertionError("AI Query Planner OpenAI runner must not be called.")


async def forbidden_wording_llm(*args, **kwargs):
    raise AssertionError("Agent wording OpenAI runner must not be called here.")


async def forbidden_query_plan_wave(*args, **kwargs):
    RECORDER.query_wave_calls += 1
    raise AssertionError("Tavily query wave must not be called by this smoke.")


async def forbidden_tavily_query(*args, **kwargs):
    RECORDER.tavily_calls += 1
    raise AssertionError("Tavily HTTP query must not be called by this smoke.")


async def forbidden_single_wave_execution(*args, **kwargs):
    RECORDER.search_execution_calls += 1
    raise AssertionError("Single-wave search execution must not run in P7 golden smoke.")


async def forbidden_multi_wave_execution(*args, **kwargs):
    RECORDER.search_execution_calls += 1
    raise AssertionError("Multi-wave search execution must not run in P7 golden smoke.")


class ForbiddenAsyncClient:
    def __init__(self, *args, **kwargs) -> None:
        raise AssertionError("Network calls are not allowed in P7 golden smoke.")


def set_openai_env() -> None:
    os.environ["OPENAI_API_KEY"] = FAKE_OPENAI_KEY
    os.environ["OPENAI_MODEL"] = FAKE_OPENAI_MODEL


def clear_openai_env() -> None:
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)


def assert_forbidden_phrases_absent(text: str) -> None:
    lowered = text.lower()
    forbidden_phrases = [
        "log in to linkedin",
        "scrape linkedin",
        "message candidates",
        "without approval",
        "direct linkedin search",
        "direct web search",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lowered, phrase


async def assert_onboarding_is_no_call() -> None:
    before_calls = len(RECORDER.recruiter_llm_calls)

    greeting = await main.recruiter_chat_turn_response(
        chat_request("hello", language="en")
    )
    assert len(RECORDER.recruiter_llm_calls) == before_calls
    assert greeting["ok"] is True
    assert greeting["state"] == "needs_clarification"
    assert greeting["normalized_brief"] is None
    assert greeting["can_build_plan"] is False
    assert not greeting.get("build_plan_action")

    near_empty = await main.recruiter_chat_turn_response(
        chat_request("...", language="en")
    )
    assert len(RECORDER.recruiter_llm_calls) == before_calls
    assert near_empty["ok"] is True
    assert near_empty["state"] == "needs_clarification"
    assert near_empty["normalized_brief"] is None
    assert near_empty["can_build_plan"] is False
    assert not near_empty.get("build_plan_action")


async def assert_complete_brief_flow() -> dict:
    before_calls = len(RECORDER.recruiter_llm_calls)
    response = await main.recruiter_chat_turn_response(
        chat_request(
            "Find backend developers in Ukraine with Java as main skill, "
            "ideally Spring and Kafka.",
            language="en",
        )
    )

    assert len(RECORDER.recruiter_llm_calls) == before_calls + 1
    assert response["ok"] is True
    assert response["state"] == "ready_for_planning"
    assert response["can_build_plan"] is True
    assert response["recommended_planner_mode"] == "rule_based"
    assert response["build_plan_action"]["endpoint"] == "/api/agent/query-plan"
    assert response["build_plan_action"]["planner_mode"] == "rule_based"

    brief = response["normalized_brief"]
    assert brief["role_family"] == "Backend Developer"
    assert brief["technology"] == "Java"
    assert brief["location"] == "Ukraine"
    assert brief["stack"] == ["Spring", "Kafka"]
    return response


async def assert_safety_refusal_is_no_call() -> None:
    before_calls = len(RECORDER.recruiter_llm_calls)
    response = await main.recruiter_chat_turn_response(
        chat_request(
            "Log in to LinkedIn, scrape profiles, and message candidates.",
            language="en",
        )
    )
    assert len(RECORDER.recruiter_llm_calls) == before_calls
    assert response["ok"] is False
    assert response["state"] == "refused"
    assert response["can_build_plan"] is False
    assert not response.get("build_plan_action")
    assert response["validation_errors"]
    assert_forbidden_phrases_absent(response["assistant_message"])


async def assert_brief_refinement_boundaries() -> None:
    before_calls = len(RECORDER.recruiter_llm_calls)

    add_stack = await main.recruiter_chat_turn_response(
        chat_request(
            "add Docker",
            language="en",
            draft_brief=ready_brief(),
        )
    )
    assert len(RECORDER.recruiter_llm_calls) == before_calls
    assert add_stack["state"] == "ready_for_planning"
    assert add_stack["normalized_brief"]["stack"] == ["Spring", "Kafka", "Docker"]
    assert add_stack["brief_changed"] is True
    assert add_stack["stale_state_should_clear"] is True
    assert add_stack["brief_patch"]["operations"][0]["operation"] == "add_stack"

    duplicate_add = await main.recruiter_chat_turn_response(
        chat_request(
            "add Spring",
            language="en",
            draft_brief=ready_brief(["Spring"]),
        )
    )
    assert len(RECORDER.recruiter_llm_calls) == before_calls
    assert duplicate_add["normalized_brief"]["stack"] == ["Spring"]
    assert duplicate_add["brief_changed"] is False
    assert duplicate_add["stale_state_should_clear"] is False

    generic_stack_patch = await main.recruiter_chat_turn_response(
        chat_request(
            "remove Kafka and add React",
            language="en",
            draft_brief=ready_brief(),
        )
    )
    assert len(RECORDER.recruiter_llm_calls) == before_calls
    assert generic_stack_patch["normalized_brief"]["stack"] == ["Spring", "React"]
    assert generic_stack_patch["brief_changed"] is True
    assert generic_stack_patch["stale_state_should_clear"] is True
    assert [
        operation["operation"]
        for operation in generic_stack_patch["brief_patch"]["operations"]
    ] == ["remove_stack", "add_stack"]

    last_stack_remove = await main.recruiter_chat_turn_response(
        chat_request(
            "remove Spring",
            language="en",
            draft_brief=ready_brief(["Spring"]),
        )
    )
    assert len(RECORDER.recruiter_llm_calls) == before_calls
    assert last_stack_remove["normalized_brief"]["stack"] == ["Spring"]
    assert last_stack_remove["brief_changed"] is False
    assert last_stack_remove["stale_state_should_clear"] is False
    assert last_stack_remove["brief_patch"]["requires_clarification"] is True


async def assert_agent_plan_and_query_plan_boundaries() -> tuple[dict, dict]:
    clear_openai_env()
    main.run_openai_json_agent_wording = forbidden_wording_llm

    plan_response = await main.build_agent_plan_response_with_wording(
        main.AgentPlanRequest(search_brief=ready_brief(), language="en")
    )
    assert plan_response["agent_plan_status"] == "supported"
    agent_plan = plan_response["agent_plan"]
    assert agent_plan["brief_fingerprint"]
    assert agent_plan["input_snapshot"]["technology"] == "Java"
    assert agent_plan["proposed_action"] == main.agent_plan_proposed_action()
    assert agent_plan["wording_mode"] == "deterministic_fallback"
    assert agent_plan["wording_provenance"]["no_call_reason"] == "openai_not_configured"

    query_plan_response = await main.create_agent_query_plan(
        main.AgentQueryPlanRequest(
            planner_mode="rule_based",
            search_brief=ready_brief(),
            agent_plan_brief_fingerprint=agent_plan["brief_fingerprint"],
            agent_plan_action=agent_plan["proposed_action"],
        )
    )
    assert query_plan_response["ok"] is True
    assert query_plan_response["planner_mode"] == "rule_based"
    assert query_plan_response["execution_allowed"] is False
    assert query_plan_response["execution_approval_required"] is True
    assert query_plan_response["approval_notice"]
    assert len(query_plan_response["query_plan"]["queries"]) == 10
    assert RECORDER.search_execution_calls == 0
    assert RECORDER.query_wave_calls == 0
    assert RECORDER.tavily_calls == 0

    return agent_plan, query_plan_response


def runtime_context_from_plan(
    agent_plan: dict,
    query_plan_response: dict,
) -> dict:
    query_plan = query_plan_response["query_plan"]
    return {
        "planner_mode": "rule_based",
        "tool_name": SINGLE_WAVE_TOOL,
        "execution_mode": "single_wave",
        "plan_fingerprint": query_plan_response["plan_fingerprint"],
        "query_count": len(query_plan["queries"]),
        "search_brief_fingerprint": agent_plan["brief_fingerprint"],
        "multi_wave_enabled": False,
    }


async def assert_runtime_prepare_boundary(
    agent_plan: dict,
    query_plan_response: dict,
) -> None:
    previous_tavily_key = os.environ.get("TAVILY_API_KEY")
    os.environ["TAVILY_API_KEY"] = FAKE_TAVILY_KEY
    try:
        runtime_request = main.AgentRuntimeTurnRequest(
            turn_mode="prepare",
            tool_name=SINGLE_WAVE_TOOL,
            tool_input=query_plan_response["adapted_structured_request"],
            runtime_context=runtime_context_from_plan(
                agent_plan,
                query_plan_response,
            ),
            runtime_approval=None,
            agent_language="en",
        )
        response = await main.create_agent_runtime_turn(runtime_request)
    finally:
        if previous_tavily_key is None:
            os.environ.pop("TAVILY_API_KEY", None)
        else:
            os.environ["TAVILY_API_KEY"] = previous_tavily_key

    assert response["ok"] is True
    assert response["runtime_state"] == "approval_pending"
    assert len(response["pending_approvals"]) == 1
    approval = response["pending_approvals"][0]
    assert approval["approval_status"] == "required"
    assert approval["tool_name"] == SINGLE_WAVE_TOOL
    assert approval["tool_call_id"]
    assert approval["tool_input_fingerprint"]
    assert approval["context_fingerprint"]
    assert "tool_results" in response
    assert response["tool_results"] == []
    assert RECORDER.search_execution_calls == 0
    assert RECORDER.query_wave_calls == 0
    assert RECORDER.tavily_calls == 0


def sample_agent_response(query_plan_response: dict) -> dict:
    report = {
        "mode": "single_wave",
        "unique_profiles": 3,
        "raw_total": 5,
        "displayed": 3,
        "queries_succeeded": 10,
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
    return main.build_agent_response(
        query_plan_response["query_plan"],
        report,
        deduped_results,
        "en",
    )


def assert_agent_response_contract(agent_response: dict) -> None:
    assert agent_response["summary_facts"]["candidate_count"] == 3
    assert agent_response["summary_facts"]["queries_total"] == 10
    assert agent_response["requires_approval_for_execution"] is True
    assert agent_response["quality_notes"]
    assert agent_response["limitations"]
    assert all(
        action["executable"] is False
        for action in agent_response["suggested_next_actions"]
    )

    options = agent_response["next_iteration_options"]
    assert options
    assert all(option["is_executable_now"] is False for option in options)
    assert all(option["requires_approval_before_execution"] is True for option in options)
    assert all(option["proposed_brief_patch"]["operations"] for option in options)


async def fake_valid_wording_llm(payload: dict):
    RECORDER.wording_llm_calls.append(copy.deepcopy(payload))
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


async def fake_disallowed_wording_llm(payload: dict):
    RECORDER.wording_llm_calls.append(copy.deepcopy(payload))
    return {
        "message": "The approved backend search returned 999 candidates.",
        "warnings": [],
        "limitations": [],
        "suggested_next_actions": [{"label": "Run now", "executable": True}],
    }, None


async def assert_wording_contracts(query_plan_response: dict) -> None:
    set_openai_env()
    main.run_openai_json_agent_wording = fake_valid_wording_llm
    before_wording_calls = len(RECORDER.wording_llm_calls)

    plan_response = await main.build_agent_plan_response_with_wording(
        main.AgentPlanRequest(search_brief=ready_brief(), language="en")
    )
    agent_plan = plan_response["agent_plan"]
    assert len(RECORDER.wording_llm_calls) == before_wording_calls + 1
    assert agent_plan["wording_mode"] == "llm_assisted"
    assert agent_plan["proposed_action"] == main.agent_plan_proposed_action()
    assert agent_plan["wording_provenance"]["model"] == FAKE_OPENAI_MODEL
    assert agent_plan["wording_provenance"]["taxonomy_version"] == (
        agent_wording.AGENT_WORDING_TAXONOMY_VERSION
    )

    original_response = sample_agent_response(query_plan_response)
    response_snapshot = copy.deepcopy(original_response)
    worded_response = await main.apply_llm_wording_to_agent_response(
        original_response
    )
    assert worded_response["wording_mode"] == "llm_assisted"
    assert worded_response["message"] == (
        "Search completed: 3 unique candidates found: 2 strong, 1 review, 0 weak."
    )
    assert worded_response["summary_facts"] == response_snapshot["summary_facts"]
    assert worded_response["quality_notes"] == response_snapshot["quality_notes"]
    assert (
        worded_response["suggested_next_actions"]
        == response_snapshot["suggested_next_actions"]
    )
    assert (
        worded_response["next_iteration_options"]
        == response_snapshot["next_iteration_options"]
    )
    response_payload = RECORDER.wording_llm_calls[-1]
    assert "visible_summary_facts" in response_payload
    assert "summary_facts" not in response_payload
    assert "quality_notes" not in response_payload
    assert "limitations" not in response_payload
    assert "suggested_next_actions" not in response_payload
    assert "raw_total" not in str(response_payload)
    assert "queries_total" not in str(response_payload)
    assert worded_response["wording_provenance"]["model"] == FAKE_OPENAI_MODEL

    clear_openai_env()
    main.run_openai_json_agent_wording = forbidden_wording_llm
    no_call_response = await main.build_agent_plan_response_with_wording(
        main.AgentPlanRequest(search_brief=ready_brief(), language="en")
    )
    no_call_plan = no_call_response["agent_plan"]
    assert no_call_plan["wording_mode"] == "deterministic_fallback"
    assert no_call_plan["fallback_reason"] == "openai_not_configured"
    assert (
        no_call_plan["wording_provenance"]["no_call_reason"]
        == "openai_not_configured"
    )
    assert "model" not in no_call_plan["wording_provenance"]

    set_openai_env()
    main.run_openai_json_agent_wording = fake_disallowed_wording_llm
    fallback_response = await main.apply_llm_wording_to_agent_response(
        sample_agent_response(query_plan_response)
    )
    assert fallback_response["wording_mode"] == "deterministic_fallback"
    assert fallback_response["fallback_reason"] in {
        "llm_output_disallowed_fields",
        "llm_output_disallowed_numbers",
    }
    assert "999" not in fallback_response["message"]
    assert "no_call_reason" not in fallback_response["wording_provenance"]
    assert fallback_response["wording_provenance"]["model"] == FAKE_OPENAI_MODEL


def extract_function(source: str, function_name: str) -> str:
    start_marker = f"function {function_name}"
    start = source.index(start_marker)
    next_function = re.search(r"\nfunction\s+\w+", source[start + 1 :])
    if next_function:
        end = start + 1 + next_function.start()
    else:
        end = len(source)
    return source[start:end]


def assert_frontend_typed_message_contract() -> None:
    source = (PROJECT_DIR / "app" / "static" / "app.js").read_text(encoding="utf-8")

    chat_payload = extract_function(source, "chatMessagesForBackend")
    assert ".filter((message) => !message.localOnly)" in chat_payload
    assert "role: message.role" in chat_payload
    assert "content: message.content" in chat_payload
    assert "messageType" not in chat_payload
    assert "surface" not in chat_payload
    assert "payload" not in chat_payload

    assert "function visibleNextIterationOptions" not in source
    assert "function renderNextIterationOptions" not in source
    assert "Follow-up ideas" not in source
    assert "Suggestions only" not in source

    agent_plan_message = extract_function(source, "appendAgentPlanMessage")
    assert 'kind: "agent_plan"' in agent_plan_message
    assert "localOnly: true" in agent_plan_message
    assert "agentPlanMessageType(data.agent_plan_status)" in agent_plan_message

    agent_response_message = extract_function(source, "appendAgentResponseMessage")
    assert 'kind: "agent_response"' in agent_response_message
    assert "localOnly: true" in agent_response_message
    assert "next_iteration_options" not in agent_response_message


async def run_smoke() -> None:
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY"),
        "OPENAI_CHAT_COMPLETIONS_URL": os.environ.get("OPENAI_CHAT_COMPLETIONS_URL"),
    }
    original_recruiter_llm = main.run_openai_json_recruiter_chat
    original_extractor = main.run_openai_json_search_brief_extractor
    original_planner_llm = main.run_openai_json_planner
    original_wording_llm = main.run_openai_json_agent_wording
    original_query_plan_wave = main.run_query_plan_wave
    original_main_tavily_query = main.run_tavily_query
    original_search_tavily_query = search_execution.run_tavily_query
    original_single_execution = main.execute_single_wave_structured_search_response
    original_multi_execution = main.execute_multi_wave_structured_search_response
    original_main_async_client = main.httpx.AsyncClient
    original_agent_wording_async_client = agent_wording.httpx.AsyncClient
    original_search_execution_async_client = search_execution.httpx.AsyncClient

    clear_openai_env()
    os.environ.pop("TAVILY_API_KEY", None)
    os.environ.pop("OPENAI_CHAT_COMPLETIONS_URL", None)
    main.run_openai_json_recruiter_chat = fake_recruiter_chat_llm
    main.run_openai_json_search_brief_extractor = fake_search_brief_extractor
    main.run_openai_json_planner = forbidden_planner_llm
    main.run_openai_json_agent_wording = forbidden_wording_llm
    main.run_query_plan_wave = forbidden_query_plan_wave
    main.run_tavily_query = forbidden_tavily_query
    search_execution.run_tavily_query = forbidden_tavily_query
    main.execute_single_wave_structured_search_response = forbidden_single_wave_execution
    main.execute_multi_wave_structured_search_response = forbidden_multi_wave_execution
    main.httpx.AsyncClient = ForbiddenAsyncClient
    agent_wording.httpx.AsyncClient = ForbiddenAsyncClient
    search_execution.httpx.AsyncClient = ForbiddenAsyncClient

    try:
        await assert_onboarding_is_no_call()
        await assert_complete_brief_flow()
        await assert_safety_refusal_is_no_call()
        await assert_brief_refinement_boundaries()
        agent_plan, query_plan_response = await assert_agent_plan_and_query_plan_boundaries()
        await assert_runtime_prepare_boundary(agent_plan, query_plan_response)
        agent_response = sample_agent_response(query_plan_response)
        assert_agent_response_contract(agent_response)
        await assert_wording_contracts(query_plan_response)
        assert_frontend_typed_message_contract()
        assert RECORDER.query_wave_calls == 0
        assert RECORDER.tavily_calls == 0
        assert RECORDER.search_execution_calls == 0
    finally:
        main.run_openai_json_recruiter_chat = original_recruiter_llm
        main.run_openai_json_search_brief_extractor = original_extractor
        main.run_openai_json_planner = original_planner_llm
        main.run_openai_json_agent_wording = original_wording_llm
        main.run_query_plan_wave = original_query_plan_wave
        main.run_tavily_query = original_main_tavily_query
        search_execution.run_tavily_query = original_search_tavily_query
        main.execute_single_wave_structured_search_response = original_single_execution
        main.execute_multi_wave_structured_search_response = original_multi_execution
        main.httpx.AsyncClient = original_main_async_client
        agent_wording.httpx.AsyncClient = original_agent_wording_async_client
        search_execution.httpx.AsyncClient = original_search_execution_async_client
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    asyncio.run(run_smoke())
    print("P7 Golden Conversations smoke passed")
