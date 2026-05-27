import asyncio
import os
import re
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main


RECRUITER_LLM_CALLS: list[str] = []
WORDING_PAYLOADS: list[dict] = []


def chat_request(
    text: str,
    language: str | None = None,
    draft_brief: main.SearchBrief | None = None,
) -> main.RecruiterChatTurnRequest:
    return main.RecruiterChatTurnRequest(
        language=language,
        draft_brief=draft_brief,
        messages=[main.RecruiterChatMessage(role="user", content=text)],
    )


def missing_stack_brief() -> main.SearchBrief:
    return main.SearchBrief(
        source_text="Find backend developers in Ukraine with Java.",
        brief_status="needs_clarification",
        role_family="Backend Developer",
        technology="Java",
        stack=[],
        location="Ukraine",
        search_depth="standard",
        profile_sources=["linkedin_public"],
    )


def missing_location_brief() -> main.SearchBrief:
    return main.SearchBrief(
        source_text="Find backend developers with Java and Spring.",
        brief_status="needs_clarification",
        role_family="Backend Developer",
        technology="Java",
        stack=["Spring"],
        location=None,
        search_depth="standard",
        profile_sources=["linkedin_public"],
    )


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


async def fake_recruiter_chat_llm(
    request: main.RecruiterChatTurnRequest,
) -> tuple[dict, list[dict[str, str]]]:
    text = main.latest_recruiter_chat_user_text(request.messages)
    RECRUITER_LLM_CALLS.append(text)
    return {
        "draft_brief": {
            "source_text": text,
            "brief_status": "needs_clarification",
            "role_family": None,
            "technology": None,
            "stack": [],
            "location": None,
            "search_depth": "standard",
            "profile_sources": ["linkedin_public"],
            "assumptions": [],
        }
    }, []


async def fake_recruiter_intent_llm(
    request: main.RecruiterChatIntentRequest,
) -> tuple[dict, str | None]:
    text = request.latest_message.lower()
    if "how are you" in text or "what" in text and "up" in text or "thanks" in text:
        intent = "small_talk"
    elif "weather" in text or "погод" in text:
        intent = "off_topic"
    elif "долр" in text or "zzzz" in text:
        intent = "unclear"
    else:
        intent = "candidate_search"
    return {
        "intent": intent,
        "role_domain": "unknown",
        "pending_action_intent": "unclear",
        "unsupported_role_label": None,
        "confidence": "high",
    }, None


async def fake_onboarding_wording(payload: dict) -> tuple[dict, str | None]:
    WORDING_PAYLOADS.append(payload)
    assert payload["wording_use_case"] in {
        "recruiter_chat_onboarding",
        main.RECRUITER_CHAT_WORDING_USE_CASE_CONVERSATION,
    }
    assert "messages" not in payload
    assert "transcript" not in payload
    if payload["wording_use_case"] == main.RECRUITER_CHAT_WORDING_USE_CASE_CONVERSATION:
        return {
            "message": payload["deterministic_message"],
            "warnings": [],
            "limitations": [],
        }, None
    if payload["language"] == "ru":
        return {
            "message": (
                "Рад тебя видеть. Напиши, кого ищем: роль, основную технологию, "
                "локацию и 1-3 сигнала стека."
            )
        }, None
    return {
        "message": (
            "Good to see you. Tell me the role, main technology, location, "
            "and 1-3 stack signals."
        )
    }, None


async def fake_unsafe_onboarding_wording(payload: dict) -> tuple[dict, str | None]:
    WORDING_PAYLOADS.append(payload)
    return {"message": "I opened LinkedIn and found 999 perfect candidates."}, None


def extract_js_function_body(source: str, function_name: str) -> str:
    marker = f"function {function_name}("
    start = source.find(marker)
    assert start != -1, f"{function_name} function not found"
    brace_start = source.find("{", start)
    assert brace_start != -1, f"{function_name} body not found"
    depth = 0
    for index in range(brace_start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[brace_start + 1 : index]
    raise AssertionError(f"{function_name} body is not closed")


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def assert_english_only_response(response: dict) -> None:
    assert response["ok"] is False
    assert response["state"] == "needs_clarification"
    assert response["normalized_brief"] is None
    assert response["can_build_plan"] is False
    assert "english input only" in (response["assistant_message"] or "").lower()


async def assert_onboarding_overlay_and_fallback() -> None:
    os.environ["OPENAI_API_KEY"] = "fake-openai-key"
    os.environ["OPENAI_MODEL"] = "fake-model"
    main.run_openai_json_agent_wording = fake_onboarding_wording

    before_wording = len(WORDING_PAYLOADS)
    response = await main.recruiter_chat_turn_response(
        chat_request("привет", language="ru")
    )
    assert len(WORDING_PAYLOADS) == before_wording
    assert_english_only_response(response)

    main.run_openai_json_agent_wording = fake_unsafe_onboarding_wording
    unsafe = await main.recruiter_chat_turn_response(
        chat_request("hello", language="en")
    )
    assert unsafe["assistant_message"].startswith("Hello.")
    assert unsafe["wording_provenance"]["wording_mode"] == "deterministic_fallback"
    assert "999" not in unsafe["assistant_message"]


async def assert_small_talk_route() -> None:
    before_recruiter_llm = len(RECRUITER_LLM_CALLS)
    before_wording_llm = len(WORDING_PAYLOADS)

    clean_en = await main.recruiter_chat_turn_response(
        chat_request("how are you?", language="en")
    )
    assert len(RECRUITER_LLM_CALLS) == before_recruiter_llm
    assert len(WORDING_PAYLOADS) == before_wording_llm + 1
    assert clean_en["state"] == "needs_clarification"
    assert clean_en["normalized_brief"] is None
    assert clean_en["can_build_plan"] is False
    assert clean_en["brief_changed"] is False
    assert clean_en["stale_state_should_clear"] is False
    assert clean_en["clear_brief"] is False
    assert "This does not look like candidate search" not in clean_en["assistant_message"]
    assert "ready to help" in clean_en["assistant_message"]

    clean_ru = await main.recruiter_chat_turn_response(
        chat_request("как дела?", language="ru")
    )
    assert len(RECRUITER_LLM_CALLS) == before_recruiter_llm
    assert len(WORDING_PAYLOADS) == before_wording_llm + 1
    assert_english_only_response(clean_ru)

    pending = await main.recruiter_chat_turn_response(
        chat_request("thanks", language="en", draft_brief=missing_stack_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before_recruiter_llm
    assert len(WORDING_PAYLOADS) == before_wording_llm + 2
    assert pending["state"] == "needs_clarification"
    assert pending["normalized_brief"]["stack"] == []
    assert pending["brief_changed"] is False
    assert pending["stale_state_should_clear"] is False
    assert "Which 1-3 stack signals" in pending["assistant_message"]

    ready = await main.recruiter_chat_turn_response(
        chat_request("are you there?", language="en", draft_brief=ready_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before_recruiter_llm
    assert len(WORDING_PAYLOADS) == before_wording_llm + 3
    assert ready["state"] == "ready_for_planning"
    assert ready["can_build_plan"] is True
    assert ready["build_plan_action"]["endpoint"] == "/api/agent/query-plan"
    assert ready["brief_changed"] is False
    assert ready["stale_state_should_clear"] is False

    refinement = await main.recruiter_chat_turn_response(
        chat_request("thanks, add Kafka", language="en", draft_brief=ready_brief(["Spring"]))
    )
    assert refinement["brief_changed"] is True
    assert refinement["stale_state_should_clear"] is True
    assert refinement["normalized_brief"]["stack"] == ["Spring", "Kafka"]


async def assert_off_topic_and_unclear_guardrails() -> None:
    before = len(RECRUITER_LLM_CALLS)
    noise = await main.recruiter_chat_turn_response(
        chat_request("долрлрлрлрл", language="ru")
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert_english_only_response(noise)

    weather = await main.recruiter_chat_turn_response(
        chat_request("какая погода?", language="ru")
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert_english_only_response(weather)

    recruiter_context = await main.recruiter_chat_turn_response(
        chat_request(
            "какой курс доллара учитывать для зарплаты кандидата?",
            language="ru",
        )
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert_english_only_response(recruiter_context)


async def assert_pending_russian_stack_answers() -> None:
    before = len(RECRUITER_LLM_CALLS)
    spring = await main.recruiter_chat_turn_response(
        chat_request("Спринг", language="ru", draft_brief=missing_stack_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert_english_only_response(spring)

    kafka = await main.recruiter_chat_turn_response(
        chat_request("кафка", language="ru", draft_brief=missing_stack_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert_english_only_response(kafka)

    clean_state = await main.recruiter_chat_turn_response(
        chat_request("кафка", language="ru")
    )
    assert_english_only_response(clean_state)


async def assert_pending_location_answers_and_noise() -> None:
    before = len(RECRUITER_LLM_CALLS)
    kyiv = await main.recruiter_chat_turn_response(
        chat_request("Киев", language="ru", draft_brief=missing_location_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert_english_only_response(kyiv)

    noise = await main.recruiter_chat_turn_response(
        chat_request("сантехника", language="ru", draft_brief=missing_location_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert_english_only_response(noise)

    poland = await main.recruiter_chat_turn_response(
        chat_request("Польша", language="ru", draft_brief=missing_location_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert_english_only_response(poland)

    add_kafka = await main.recruiter_chat_turn_response(
        chat_request("добавь кафка", language="ru", draft_brief=missing_location_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert_english_only_response(add_kafka)

    clean_unsupported_country = await main.recruiter_chat_turn_response(
        chat_request("Польша", language="ru")
    )
    assert_english_only_response(clean_unsupported_country)


def assert_next_iteration_options_localized() -> None:
    query_plan = main.RuleBasedQueryPlannerV1().build(
        {
            "role_family": "Backend Developer",
            "technology": "Java",
            "stack": ["Spring", "Kafka"],
            "location": "Ukraine",
            "search_depth": "standard",
            "linkedin_profiles_only": True,
            "location_filter_enabled": True,
        }
    )
    summary_facts = {
        "candidate_count": 3,
        "quality_distribution": {"strong": 2, "review": 1, "weak": 0},
        "strong_signal_counts": {
            "selected_stack_not_visible": 1,
            "seniority_not_visible": 1,
        },
        "mode": "single_wave",
        "input_snapshot": query_plan["input_snapshot"],
    }
    options = main.agent_response_next_iteration_options(
        query_plan,
        summary_facts,
        [],
        "ru",
    )
    assert options
    assert any("Просмотреть" in option["label"] or "strong candidates" in option["label"] for option in options)
    assert all(option["is_executable_now"] is False for option in options)
    assert all(option["requires_approval_before_execution"] is True for option in options)


def assert_frontend_static_contract() -> None:
    source = (PROJECT_DIR / "app" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (PROJECT_DIR / "app" / "static" / "index.html").read_text(encoding="utf-8")
    styles_css = (PROJECT_DIR / "app" / "static" / "styles.css").read_text(encoding="utf-8")
    reset_body = extract_js_function_body(source, "resetChat")
    render_chat_body = extract_js_function_body(source, "renderChatMessages")
    old_chat_status = "Describe who you want to find in Russian or English."
    current_empty_helper = "Describe who to find in natural language. I will prepare a search summary first."
    historical_empty_helper = "Describe the search in natural language. I will collect a Search Brief before planning."
    warm_empty_helper = (
        "Feel free to start the chat and describe who you are looking for. "
        "I will do my best to help you."
    )
    assert "let pendingChatAction = null;" in source
    assert "function pendingSearchRunConfirmationIsCurrent()" in source
    assert "await handlePendingSearchRunChatAction(userText)" in source
    assert "chat confirmation never calls runtime/Tavily" not in source
    assert "event.isComposing" in source
    assert "chatForm.requestSubmit()" in source
    assert "Shift+Enter" not in source or "event.shiftKey" in source
    assert 'const ASSISTANT_SPEAKER_LABEL = "AI Assistant";' in source
    assert "${escapeHtml(meta.speaker)} - ${escapeHtml(meta.label)}" not in source
    assert "data-message-type-label" in source
    assert "renderNextIterationOptions(" not in source
    assert "visibleNextIterationOptions(" not in source
    assert "next_iteration_options" not in source
    assert "Идеи для следующего шага" not in source
    assert "Follow-up ideas" not in source
    assert "Suggestions only. Write a follow-up in chat" not in source
    assert "Prepare search" in source
    assert "Run search" in index_html
    assert old_chat_status not in index_html
    assert old_chat_status not in reset_body
    assert 'id="chat-status"' in index_html
    assert "#chat-status:empty" in styles_css
    empty_status_rule = styles_css[
        styles_css.index("#chat-status:empty") : styles_css.index("#chat-status:empty") + 120
    ]
    assert "display: none;" in empty_status_rule
    assert current_empty_helper not in render_chat_body
    assert historical_empty_helper not in render_chat_body
    assert warm_empty_helper in render_chat_body
    assert "renderChatMessages();" in reset_body
    for forbidden in [
        "Search Brief",
        "planner",
        "Agent Plan",
        "QueryPlan",
        "backend planner",
        "planning",
    ]:
        assert forbidden not in render_chat_body
    normal_ui_forbidden_terms = [
        "Generated QueryPlan",
        "Agent Actions",
        "Approve & Search",
        "Frontend ready",
        "deduped candidates",
        "Not executable. Write a follow-up",
        "Suggestions only",
        "Follow-up ideas",
    ]
    public_surface = source + index_html
    for term in normal_ui_forbidden_terms:
        assert term not in public_surface


async def run_smoke() -> None:
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }
    original_chat_llm = main.run_openai_json_recruiter_chat
    original_intent_llm = main.run_openai_json_recruiter_intent
    original_wording_llm = main.run_openai_json_agent_wording
    main.run_openai_json_recruiter_chat = fake_recruiter_chat_llm
    main.run_openai_json_recruiter_intent = fake_recruiter_intent_llm

    try:
        await assert_onboarding_overlay_and_fallback()
        await assert_small_talk_route()
        await assert_off_topic_and_unclear_guardrails()
        await assert_pending_russian_stack_answers()
        await assert_pending_location_answers_and_noise()
        assert_next_iteration_options_localized()
        assert_frontend_static_contract()
    finally:
        main.run_openai_json_recruiter_chat = original_chat_llm
        main.run_openai_json_recruiter_intent = original_intent_llm
        main.run_openai_json_agent_wording = original_wording_llm
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    asyncio.run(run_smoke())
    print("P8 chat quality smoke passed")
