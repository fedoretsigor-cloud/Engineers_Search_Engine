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


async def fake_onboarding_wording(payload: dict) -> tuple[dict, str | None]:
    WORDING_PAYLOADS.append(payload)
    assert payload["wording_use_case"] == "recruiter_chat_onboarding"
    assert "messages" not in payload
    assert "transcript" not in payload
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


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


async def assert_onboarding_overlay_and_fallback() -> None:
    os.environ["OPENAI_API_KEY"] = "fake-openai-key"
    os.environ["OPENAI_MODEL"] = "fake-model"
    main.run_openai_json_agent_wording = fake_onboarding_wording

    response = await main.recruiter_chat_turn_response(
        chat_request("привет", language="ru")
    )
    assert response["state"] == "needs_clarification"
    assert "Рад тебя видеть" in response["assistant_message"]
    assert response["wording_provenance"]["wording_mode"] == "llm_assisted"
    assert response["normalized_brief"] is None
    assert response["can_build_plan"] is False
    assert WORDING_PAYLOADS[-1]["greeting_count"] == 1

    main.run_openai_json_agent_wording = fake_unsafe_onboarding_wording
    unsafe = await main.recruiter_chat_turn_response(
        chat_request("hello", language="en")
    )
    assert unsafe["assistant_message"].startswith("Hi.")
    assert unsafe["wording_provenance"]["wording_mode"] == "deterministic_fallback"
    assert "999" not in unsafe["assistant_message"]


async def assert_off_topic_and_unclear_guardrails() -> None:
    before = len(RECRUITER_LLM_CALLS)
    noise = await main.recruiter_chat_turn_response(
        chat_request("долрлрлрлрл", language="ru")
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert noise["normalized_brief"] is None
    assert noise["can_build_plan"] is False
    assert "Не понял запрос" in noise["assistant_message"]

    weather = await main.recruiter_chat_turn_response(
        chat_request("какая погода?", language="ru")
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert weather["normalized_brief"] is None
    assert "не про поиск кандидатов" in weather["assistant_message"]

    recruiter_context = await main.recruiter_chat_turn_response(
        chat_request(
            "какой курс доллара учитывать для зарплаты кандидата?",
            language="ru",
        )
    )
    assert len(RECRUITER_LLM_CALLS) == before + 1
    assert recruiter_context["state"] == "needs_clarification"


async def assert_pending_russian_stack_answers() -> None:
    before = len(RECRUITER_LLM_CALLS)
    spring = await main.recruiter_chat_turn_response(
        chat_request("Спринг", language="ru", draft_brief=missing_stack_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert spring["state"] == "ready_for_planning"
    assert spring["normalized_brief"]["stack"] == ["Spring"]
    assert spring["can_build_plan"] is True

    kafka = await main.recruiter_chat_turn_response(
        chat_request("кафка", language="ru", draft_brief=missing_stack_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert kafka["normalized_brief"]["stack"] == ["Kafka"]

    clean_state = await main.recruiter_chat_turn_response(
        chat_request("кафка", language="ru")
    )
    assert clean_state["state"] == "needs_clarification"
    assert clean_state["can_build_plan"] is False


async def assert_pending_location_answers_and_noise() -> None:
    before = len(RECRUITER_LLM_CALLS)
    kyiv = await main.recruiter_chat_turn_response(
        chat_request("Киев", language="ru", draft_brief=missing_location_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert kyiv["state"] == "ready_for_planning"
    assert kyiv["normalized_brief"]["location"] == "Ukraine"
    assert kyiv["can_build_plan"] is True

    noise = await main.recruiter_chat_turn_response(
        chat_request("сантехника", language="ru", draft_brief=missing_location_brief())
    )
    assert len(RECRUITER_LLM_CALLS) == before
    assert noise["state"] == "needs_clarification"
    assert noise["normalized_brief"]["location"] is None
    assert "Не распознал локацию" in noise["assistant_message"]
    assert noise["can_build_plan"] is False


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
    assert "let pendingChatAction = null;" in source
    assert "function pendingBuildPlanActionIsCurrent()" in source
    assert "await handlePendingBuildPlanChatAction(userText)" in source
    assert "chat confirmation never calls runtime/Tavily" not in source
    assert "event.isComposing" in source
    assert "chatForm.requestSubmit()" in source
    assert "Shift+Enter" not in source or "event.shiftKey" in source
    assert 'const ASSISTANT_SPEAKER_LABEL = "AI Assistant";' in source
    assert "${escapeHtml(meta.speaker)} - ${escapeHtml(meta.label)}" not in source
    assert "data-message-type-label" in source
    assert "renderNextIterationOptions(" in source
    assert "Варианты следующей итерации" in source
    assert "Not executable. Write a follow-up in chat" in source


async def run_smoke() -> None:
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }
    original_chat_llm = main.run_openai_json_recruiter_chat
    original_wording_llm = main.run_openai_json_agent_wording
    main.run_openai_json_recruiter_chat = fake_recruiter_chat_llm

    try:
        await assert_onboarding_overlay_and_fallback()
        await assert_off_topic_and_unclear_guardrails()
        await assert_pending_russian_stack_answers()
        await assert_pending_location_answers_and_noise()
        assert_next_iteration_options_localized()
        assert_frontend_static_contract()
    finally:
        main.run_openai_json_recruiter_chat = original_chat_llm
        main.run_openai_json_agent_wording = original_wording_llm
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    asyncio.run(run_smoke())
    print("P8 chat quality smoke passed")
