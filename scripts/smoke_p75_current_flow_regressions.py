import asyncio
import os
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main


SINGLE_WAVE_TOOL = "run_single_wave_search"
FAKE_TAVILY_KEY = "fake-tavily-key"

QA_FINDING_COVERAGE = {
    "P75-QA-001": "runtime approval prepare after Build Plan",
    "P75-QA-002": "clean senior initial request is not refinement-blocked",
    "P75-QA-003": "clean noisy initial request is not refinement-blocked",
    "P75-QA-004": "profile opening/reading request refuses",
    "P75-QA-005": "private contact harvesting request refuses",
    "P75-QA-006": "direct Google/web-search bypass request refuses",
    "P75-QA-007": "dependent setup failure covered by clean-state and runtime checks",
    "P75-QA-008": "chat draft schema errors do not leak and supported Docker/Kubernetes works",
    "P75-QA-009": "post-results follow-up stays grounded in visible results",
    "P75-QA-010": "EN prohibited login/messaging/autonomous execution refuse",
    "P75-QA-011": "off-topic prompts do not mutate Search Brief",
    "P75-QA-012": "missing/ambiguous/contradictory prompts ask clarification",
    "P75-QA-013": "meta/reset turns do not become ordinary brief updates",
    "P75-QA-014": "common typo input normalizes to supported Java/Ukraine plan",
}

RECRUITER_LLM_CALLS: list[str] = []
SEARCH_EXECUTION_CALLS: list[str] = []


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


def chat_message(role: str, content: str) -> main.RecruiterChatMessage:
    return main.RecruiterChatMessage(role=role, content=content)


def chat_request(
    text: str | None = None,
    *,
    messages: list[main.RecruiterChatMessage] | None = None,
    language: str = "en",
    draft_brief: main.SearchBrief | None = None,
) -> main.RecruiterChatTurnRequest:
    selected_messages = messages or [chat_message("user", text or "")]
    return main.RecruiterChatTurnRequest(
        messages=selected_messages,
        draft_brief=draft_brief,
        language=language,
    )


async def fake_recruiter_chat_llm(
    request: main.RecruiterChatTurnRequest,
) -> tuple[dict | None, list[dict[str, str]]]:
    latest_text = request.messages[-1].content
    RECRUITER_LLM_CALLS.append(latest_text)
    normalized = " ".join(message.content.lower() for message in request.messages)

    has_java_ukraine = "java" in normalized and (
        "ukraine" in normalized or "украин" in normalized
    )
    has_backend = "backend" in normalized or "бек" in normalized
    if "java" in normalized and (
        "ukrane" in normalized or "ukraien" in normalized
    ):
        has_java_ukraine = True
    if has_java_ukraine and has_backend:
        stack: list[str] = []
        if "spring" in normalized or "sping" in normalized:
            stack.append("Spring")
        if "kafka" in normalized or "kafak" in normalized:
            stack.append("Kafka")
        if "aws" in normalized:
            stack.append("AWS")
        if "docker" in normalized:
            stack.append("Docker")
        if "kubernetes" in normalized:
            stack.append("Kubernetes")
        if "docker" in normalized and "kubernetes" in normalized and "spring" not in normalized:
            stack.append("Spring")
        if not stack:
            stack = ["Spring", "Kafka"]

        return {
            "draft_brief": {
                "source_text": latest_text,
                "brief_status": "ready_for_planning",
                "role_family": "Backend Developer",
                "technology": "Java",
                "stack": stack,
                "location": "Ukraine",
                "seniority": "Senior" if "senior" in normalized else None,
                "must_have": ["Java"],
                "nice_to_have": stack,
                "exclusions": [],
                "search_depth": "standard",
                "profile_sources": ["linkedin_public"],
                "assumptions": [],
                "notes": {"unsafe_shape": True} if "docker" in normalized else None,
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


async def forbidden_planner_llm(*args, **kwargs):
    raise AssertionError("AI planner OpenAI runner must not be called by P7.5 smoke.")


async def forbidden_wording_llm(*args, **kwargs):
    raise AssertionError("Agent wording OpenAI runner must not be called by P7.5 smoke.")


async def forbidden_single_wave_execution(*args, **kwargs):
    SEARCH_EXECUTION_CALLS.append("single_wave")
    raise AssertionError("Single-wave search execution must not run in P7.5 smoke.")


async def forbidden_multi_wave_execution(*args, **kwargs):
    SEARCH_EXECUTION_CALLS.append("multi_wave")
    raise AssertionError("Multi-wave search execution must not run in P7.5 smoke.")


def assert_qa_finding_mapping() -> None:
    assert set(QA_FINDING_COVERAGE) == {
        "P75-QA-001",
        "P75-QA-002",
        "P75-QA-003",
        "P75-QA-004",
        "P75-QA-005",
        "P75-QA-006",
        "P75-QA-007",
        "P75-QA-008",
        "P75-QA-009",
        "P75-QA-010",
        "P75-QA-011",
        "P75-QA-012",
        "P75-QA-013",
        "P75-QA-014",
    }


def assert_refusal_response(response: dict, expected_code: str) -> None:
    assert response["ok"] is False
    assert response["state"] == "refused"
    assert response["normalized_brief"] is None
    assert response["brief_changed"] is False
    assert response["stale_state_should_clear"] is True
    assert response["can_build_plan"] is False
    assert response["build_plan_action"] is None
    assert any(
        error.get("code") == expected_code
        for error in response["validation_errors"]
    ), response["validation_errors"]


async def assert_latest_turn_safety_regressions() -> None:
    cases = [
        (
            "Открой профили сам и прочитай их.",
            "ru",
            "profile_opening_or_reading",
        ),
        (
            "Собери email и телефоны кандидатов.",
            "ru",
            "private_contact_harvesting",
        ),
        (
            "Поищи напрямую в Google.",
            "ru",
            "direct_web_search_bypass",
        ),
        (
            "Read LinkedIn profiles.",
            "en",
            "profile_opening_or_reading",
        ),
        (
            "Collect phone numbers from candidates.",
            "en",
            "private_contact_harvesting",
        ),
        (
            "Use Google directly.",
            "en",
            "direct_web_search_bypass",
        ),
        (
            "Log into LinkedIn and find people.",
            "en",
            "linkedin_login",
        ),
        (
            "Message all candidates automatically.",
            "en",
            "candidate_messaging",
        ),
        (
            "Run the search without asking me.",
            "en",
            "autonomous_execution",
        ),
        (
            "Запусти поиск без подтверждения.",
            "ru",
            "autonomous_execution",
        ),
        (
            "Запусти поиск без апрува.",
            "ru",
            "autonomous_execution",
        ),
        (
            "Без спроса поиск.",
            "ru",
            "autonomous_execution",
        ),
    ]

    for text, language, expected_code in cases:
        before_calls = len(RECRUITER_LLM_CALLS)
        response = await main.recruiter_chat_turn_response(
            chat_request(text, language=language, draft_brief=ready_brief())
        )
        assert len(RECRUITER_LLM_CALLS) == before_calls
        assert_refusal_response(response, expected_code)

    before_calls = len(RECRUITER_LLM_CALLS)
    later_normal = await main.recruiter_chat_turn_response(
        chat_request(
            messages=[
                chat_message("user", "Open profiles and read them."),
                chat_message("assistant", "I cannot do that."),
                chat_message(
                    "user",
                    "Find Backend Developer Java in Ukraine with Spring and Kafka.",
                ),
            ],
            language="en",
        )
    )
    assert len(RECRUITER_LLM_CALLS) == before_calls + 1
    assert later_normal["ok"] is True
    assert later_normal["state"] == "ready_for_planning"
    assert later_normal["normalized_brief"]["role_family"] == "Backend Developer"
    assert later_normal["normalized_brief"]["technology"] == "Java"
    assert later_normal["normalized_brief"]["location"] == "Ukraine"


async def assert_ru_control_signal_regressions() -> None:
    assert main.explicit_backend_role_signal("бекенд")
    assert main.explicit_backend_role_signal("бэкенд")
    assert main.explicit_backend_role_signal("бэкэнд")
    assert main.explicit_ukraine_location_signal("Украина")
    assert main.explicit_ukraine_location_signal("Киев")
    assert main.explicit_ukraine_location_signal("Київ")

    missing_role_or_technology = main.detect_recruiter_chat_ambiguity_or_contradiction(
        "Spring Kafka Украина."
    )
    assert missing_role_or_technology is not None
    assert missing_role_or_technology["code"] == "missing_role_or_technology"

    kyiv_missing_role_or_technology = main.detect_recruiter_chat_ambiguity_or_contradiction(
        "Spring Kafka Киев."
    )
    assert kyiv_missing_role_or_technology is not None
    assert kyiv_missing_role_or_technology["code"] == "missing_role_or_technology"

    too_many_stack_terms = main.detect_recruiter_chat_ambiguity_or_contradiction(
        "бекенд Java Украина Spring Kafka AWS Docker"
    )
    assert too_many_stack_terms is not None
    assert too_many_stack_terms["code"] == "too_many_stack_terms"

    for text in ["сброс", "новый поиск", "начать заново"]:
        assert main.detect_recruiter_chat_reset_intent(text)
        before_calls = len(RECRUITER_LLM_CALLS)
        response = await main.recruiter_chat_turn_response(
            chat_request(text, language="ru", draft_brief=ready_brief())
        )
        assert len(RECRUITER_LLM_CALLS) == before_calls
        assert response["ok"] is True
        assert response["state"] == "needs_clarification"
        assert response["normalized_brief"] is None
        assert response["brief_changed"] is True
        assert response["stale_state_should_clear"] is True
        assert response["clear_brief"] is True
        assert response["can_build_plan"] is False


def assert_not_refinement_blocked(response: dict) -> None:
    message = (response.get("assistant_message") or "").lower()
    assert "brief refinement blocked" not in message
    assert "сначала соберем initial search brief" not in message
    assert response["brief_patch"] is None


async def assert_clean_state_initial_request_regressions() -> None:
    initial_cases = [
        "Ищем Senior Java Backend Developer, Украина, Spring Boot, AWS.",
        (
            "Вакансия: команда ищет backend инженера для продукта. "
            "Нужен человек в Украине, основной язык Java, стек Spring и Kafka. "
            "В тексте много лишнего: процессы, митинги, английский, зарплатная вилка потом."
        ),
    ]

    for text in initial_cases:
        before_calls = len(RECRUITER_LLM_CALLS)
        response = await main.recruiter_chat_turn_response(
            chat_request(text, language="ru")
        )
        assert len(RECRUITER_LLM_CALLS) == before_calls + 1
        assert response["ok"] is True
        assert response["state"] == "ready_for_planning"
        assert response["normalized_brief"]["role_family"] == "Backend Developer"
        assert response["normalized_brief"]["technology"] == "Java"
        assert response["normalized_brief"]["location"] == "Ukraine"
        assert_not_refinement_blocked(response)

    before_calls = len(RECRUITER_LLM_CALLS)
    refinement = await main.recruiter_chat_turn_response(
        chat_request(
            "добавь Docker",
            language="ru",
            draft_brief=ready_brief(),
        )
    )
    assert len(RECRUITER_LLM_CALLS) == before_calls
    assert refinement["ok"] is True
    assert refinement["state"] == "ready_for_planning"
    assert refinement["normalized_brief"]["stack"] == ["Spring", "Kafka", "Docker"]
    assert refinement["brief_changed"] is True
    assert refinement["stale_state_should_clear"] is True
    assert refinement["brief_patch"]["operations"][0]["operation"] == "add_stack"


async def assert_en_hardening_regressions() -> None:
    before_calls = len(RECRUITER_LLM_CALLS)
    docker_kubernetes = await main.recruiter_chat_turn_response(
        chat_request(
            "Search for Java backend engineers in Ukraine, Docker and Kubernetes are important.",
            language="en",
        )
    )
    assert len(RECRUITER_LLM_CALLS) == before_calls + 1
    assert docker_kubernetes["ok"] is True
    assert docker_kubernetes["state"] == "ready_for_planning"
    assert docker_kubernetes["normalized_brief"]["stack"] == ["Docker", "Kubernetes"]
    assert "Input should be a valid string" not in docker_kubernetes["assistant_message"]

    no_stack = await main.recruiter_chat_turn_response(
        chat_request("Find Java backend developers in Ukraine.", language="en")
    )
    assert no_stack["ok"] is True
    assert no_stack["state"] == "needs_clarification"
    assert no_stack["normalized_brief"]["stack"] == []
    assert "stack" in no_stack["normalized_brief"]["missing_fields"]
    assert no_stack["can_build_plan"] is False

    typo = await main.recruiter_chat_turn_response(
        chat_request("need java backend ukrane sping kafak", language="en")
    )
    assert typo["ok"] is True
    assert typo["state"] == "ready_for_planning"
    assert typo["normalized_brief"]["location"] == "Ukraine"
    assert typo["normalized_brief"]["stack"] == ["Spring", "Kafka"]

    no_llm_cases = [
        (
            "Spring Kafka Ukraine.",
            "role and main technology",
        ),
        (
            "Java backend in Ukraine, Spring Kafka AWS Docker Kubernetes PostgreSQL REST.",
            "1-3 Java stack signals",
        ),
        (
            "I have two roles: Java backend Ukraine and Python backend Poland.",
            "one supported search",
        ),
        (
            "Need Java developer, but Python is also okay.",
            "one main technology",
        ),
        (
            "Remote Ukraine, but current location should be Prague.",
            "target location",
        ),
        (
            "Spring required, but no Spring.",
            "Spring is required",
        ),
        (
            "Run deep search but do not search.",
            "asked not to search",
        ),
        (
            "What's the weather in Kyiv?",
            "candidate search",
        ),
        (
            "How are you?",
            "ready to help",
        ),
        (
            "Write me a poem.",
            "candidate search",
        ),
        (
            "Recommend a restaurant in Kyiv.",
            "candidate search",
        ),
        (
            "Who is the US president?",
            "candidate search",
        ),
    ]

    for text, expected_message_fragment in no_llm_cases:
        before_calls = len(RECRUITER_LLM_CALLS)
        response = await main.recruiter_chat_turn_response(chat_request(text, language="en"))
        assert len(RECRUITER_LLM_CALLS) == before_calls
        assert response["state"] == "needs_clarification"
        assert response["normalized_brief"] is None
        assert response["can_build_plan"] is False
        assert expected_message_fragment.lower() in response["assistant_message"].lower()

    current = ready_brief()
    explanation = await main.recruiter_chat_turn_response(
        chat_request(
            "Can you explain why you need stack before planning?",
            language="en",
            draft_brief=current,
        )
    )
    assert explanation["ok"] is True
    assert explanation["state"] == "ready_for_planning"
    assert explanation["normalized_brief"]["stack"] == ["Spring", "Kafka"]
    assert "Stack is required" in explanation["assistant_message"]
    assert explanation["stale_state_should_clear"] is False

    reset = await main.recruiter_chat_turn_response(
        chat_request("Start over.", language="en", draft_brief=current)
    )
    assert reset["ok"] is True
    assert reset["state"] == "needs_clarification"
    assert reset["normalized_brief"] is None
    assert reset["clear_brief"] is True
    assert reset["stale_state_should_clear"] is True


def runtime_context_from_plan(agent_plan: dict, query_plan_response: dict) -> dict:
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


async def assert_runtime_prepare_regression() -> None:
    agent_plan_response = main.build_agent_plan_response(
        main.AgentPlanRequest(search_brief=ready_brief(), language="en")
    )
    assert agent_plan_response["ok"] is True
    assert agent_plan_response["agent_plan_status"] == "supported"
    agent_plan = agent_plan_response["agent_plan"]
    assert agent_plan["proposed_action"] == main.agent_plan_proposed_action()

    query_plan_response = await main.create_agent_query_plan(
        main.AgentQueryPlanRequest(
            planner_mode="rule_based",
            search_brief=ready_brief(),
            agent_plan_brief_fingerprint=agent_plan["brief_fingerprint"],
            agent_plan_action=agent_plan["proposed_action"],
        )
    )
    assert query_plan_response["ok"] is True
    assert len(query_plan_response["query_plan"]["queries"]) == 10
    assert query_plan_response["adapted_structured_request"]["technology"] == "Java"

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
        prepare_response = await main.create_agent_runtime_turn(runtime_request)

        execute_without_approval = await main.create_agent_runtime_turn(
            main.AgentRuntimeTurnRequest(
                turn_mode="execute_approved",
                tool_name=SINGLE_WAVE_TOOL,
                tool_input=query_plan_response["adapted_structured_request"],
                runtime_context=runtime_context_from_plan(
                    agent_plan,
                    query_plan_response,
                ),
                runtime_approval=None,
                agent_language="en",
            )
        )
    finally:
        if previous_tavily_key is None:
            os.environ.pop("TAVILY_API_KEY", None)
        else:
            os.environ["TAVILY_API_KEY"] = previous_tavily_key

    assert prepare_response["ok"] is True
    assert prepare_response["runtime_state"] == "approval_pending"
    assert len(prepare_response["pending_approvals"]) == 1
    assert prepare_response["pending_approvals"][0]["tool_name"] == SINGLE_WAVE_TOOL
    assert prepare_response["tool_results"] == []

    assert execute_without_approval["ok"] is False
    assert execute_without_approval["runtime_state"] == "blocked"
    assert any(
        error.get("code") == "approval_required"
        for error in execute_without_approval["errors"]
    ), execute_without_approval["errors"]
    assert SEARCH_EXECUTION_CALLS == []


def extract_js_function_body(source: str, function_name: str) -> str:
    marker = f"function {function_name}("
    start = source.index(marker)
    paren_start = source.index("(", start)
    paren_depth = 0
    signature_end = -1
    for index in range(paren_start, len(source)):
        character = source[index]
        if character == "(":
            paren_depth += 1
        elif character == ")":
            paren_depth -= 1
            if paren_depth == 0:
                signature_end = index
                break
    if signature_end < 0:
        raise AssertionError(f"Could not extract {function_name} signature.")

    brace_start = source.index("{", signature_end)
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


def assert_frontend_runtime_and_refusal_guardrails() -> None:
    source = (PROJECT_DIR / "app" / "static" / "app.js").read_text(encoding="utf-8")

    assert 'const AGENT_RUNTIME_TURN_ENDPOINT = "/api/agent/runtime/turn";' in source
    assert 'const AGENT_RUNTIME_TURN_MODE_EXECUTE_APPROVED = "execute_approved";' in source

    render_plan_body = extract_js_function_body(source, "renderAgentQueryPlan")
    build_plan_body = extract_js_function_body(source, "buildPlanFromChat")
    update_action_body = extract_js_function_body(source, "updateActionState")
    run_search_body = extract_js_function_body(source, "runStructuredSearch")
    update_chat_body = extract_js_function_body(source, "updateChatStateFromResponse")
    ready_status_body = extract_js_function_body(source, "readyBriefChatStatus")
    clear_refusal_body = extract_js_function_body(source, "clearExecutableStateAfterRefusal")
    send_chat_body = extract_js_function_body(source, "sendChatTurn")
    post_results_body = extract_js_function_body(source, "handlePostResultsFollowUp")

    assert "prepareRuntimeSearchAction" not in render_plan_body

    prepare_index = build_plan_body.index("void prepareRuntimeSearchAction();")
    settled_index = build_plan_body.rfind("planRequestInFlight = false;", 0, prepare_index)
    assert settled_index >= 0
    assert "if (latestExecutablePlan && autoPrepareRuntime)" in build_plan_body[settled_index:prepare_index]

    assert (
        "searchButton.disabled = !latestExecutablePlan || !currentRuntimePendingApproval || isBusy;"
        in update_action_body
    )
    assert "fetch(AGENT_RUNTIME_TURN_ENDPOINT" in run_search_body
    assert "turn_mode: AGENT_RUNTIME_TURN_MODE_EXECUTE_APPROVED" in run_search_body
    assert "/api/structured-search" not in run_search_body
    assert "/api/structured-search/multi-wave" not in run_search_body
    assert "fetch(searchEndpoint" not in run_search_body

    assert "normalizedBrief = data.normalized_brief || null" not in update_chat_body
    assert "if (data.clear_brief)" in update_chat_body
    assert "draftBrief = null;" in update_chat_body
    assert 'else if (chatState !== "refused")' in update_chat_body
    assert "chatStatusElement.textContent = readyBriefChatStatus();" in update_chat_body
    assert "hasSupportedAgentAction()" in ready_status_body
    assert "Search is understood. Confirm in chat to start it" in ready_status_body
    refusal_branch_start = update_chat_body.index('if (chatState === "refused")')
    assert "clearExecutableStateAfterRefusal();" in update_chat_body[refusal_branch_start:]

    assert "draftBrief" not in clear_refusal_body
    assert "normalizedBrief" not in clear_refusal_body
    for expected_clear in [
        "clearAgentActionDisplayState();",
        "clearPlannerData();",
        "clearAgentPlanData();",
        "clearSearchResultsData();",
    ]:
        assert expected_clear in clear_refusal_body

    assert "isPostResultsFollowUpMessage(userText)" in send_chat_body
    assert "/api/recruiter-chat/turn" not in post_results_body
    assert "localOnly: true" in post_results_body
    assert "Tell me what you want to refine before I prepare another search." in post_results_body
    assert "next_iteration_options" not in post_results_body


async def run_async_smoke() -> None:
    original_recruiter_llm = main.run_openai_json_recruiter_chat
    original_planner_llm = main.run_openai_json_planner
    original_wording_llm = main.run_openai_json_agent_wording
    original_single = main.execute_single_wave_structured_search_response
    original_multi = main.execute_multi_wave_structured_search_response

    main.run_openai_json_recruiter_chat = fake_recruiter_chat_llm
    main.run_openai_json_planner = forbidden_planner_llm
    main.run_openai_json_agent_wording = forbidden_wording_llm
    main.execute_single_wave_structured_search_response = forbidden_single_wave_execution
    main.execute_multi_wave_structured_search_response = forbidden_multi_wave_execution
    try:
        assert_qa_finding_mapping()
        await assert_latest_turn_safety_regressions()
        await assert_ru_control_signal_regressions()
        await assert_clean_state_initial_request_regressions()
        await assert_en_hardening_regressions()
        await assert_runtime_prepare_regression()
        assert_frontend_runtime_and_refusal_guardrails()
    finally:
        main.run_openai_json_recruiter_chat = original_recruiter_llm
        main.run_openai_json_planner = original_planner_llm
        main.run_openai_json_agent_wording = original_wording_llm
        main.execute_single_wave_structured_search_response = original_single
        main.execute_multi_wave_structured_search_response = original_multi


if __name__ == "__main__":
    asyncio.run(run_async_smoke())
    print("P7.5 current flow regressions smoke passed")
