import asyncio
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main


RECRUITER_LLM_CALLS: list[str] = []
INTENT_CALLS: list[str] = []
WORDING_PAYLOADS: list[dict[str, Any]] = []


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


def ready_brief() -> main.SearchBrief:
    return main.SearchBrief(
        source_text="Find Backend Developer Java in Ukraine with Spring.",
        brief_status="ready_for_planning",
        role_family="Backend Developer",
        technology="Java",
        stack=["Spring"],
        location="Ukraine",
        must_have=["Java"],
        nice_to_have=["Spring"],
        search_depth="standard",
        profile_sources=["linkedin_public"],
    )


async def fake_recruiter_intent(
    request: main.RecruiterChatIntentRequest,
) -> tuple[dict, str | None]:
    INTENT_CALLS.append(request.latest_message)
    text = request.latest_message.lower()
    if "what" in text and "up" in text:
        return {
            "intent": "small_talk",
            "role_domain": "unknown",
            "pending_action_intent": "unclear",
            "unsupported_role_label": None,
            "confidence": "high",
        }, None
    if "data engineer" in text:
        return {
            "intent": "candidate_search",
            "role_domain": "it_software",
            "pending_action_intent": "unclear",
            "unsupported_role_label": None,
            "confidence": "high",
        }, None
    return {
        "intent": "unclear",
        "role_domain": "unknown",
        "pending_action_intent": "unclear",
        "unsupported_role_label": None,
        "confidence": "high",
    }, None


async def fake_recruiter_chat_hallucinated_ready(
    request: main.RecruiterChatTurnRequest,
) -> tuple[dict, list[dict[str, str]]]:
    text = main.latest_recruiter_chat_user_text(request.messages)
    RECRUITER_LLM_CALLS.append(text)
    return {
        "draft_brief": {
            "source_text": text,
            "brief_status": "ready_for_planning",
            "role_family": "Backend Developer",
            "technology": "Java",
            "stack": ["Spring"],
            "location": "Ukraine",
            "must_have": ["Java"],
            "nice_to_have": ["Spring"],
            "search_depth": "standard",
            "profile_sources": ["linkedin_public"],
            "assumptions": [],
        }
    }, []


async def fake_recruiter_chat_valid(
    request: main.RecruiterChatTurnRequest,
) -> tuple[dict, list[dict[str, str]]]:
    text = main.latest_recruiter_chat_user_text(request.messages)
    RECRUITER_LLM_CALLS.append(text)
    return {
        "draft_brief": {
            "source_text": text,
            "brief_status": "ready_for_planning",
            "role_family": "Backend Developer",
            "technology": "Java",
            "stack": ["Spring"],
            "location": "Ukraine",
            "must_have": ["Java"],
            "nice_to_have": ["Spring"],
            "search_depth": "standard",
            "profile_sources": ["linkedin_public"],
            "assumptions": [],
        }
    }, []


async def fake_conversation_wording(payload: dict[str, Any]) -> tuple[dict, str | None]:
    WORDING_PAYLOADS.append(payload)
    assert payload["wording_use_case"] == main.RECRUITER_CHAT_WORDING_USE_CASE_CONVERSATION
    assert "candidate" not in payload
    assert "raw_results" not in payload
    message_type = payload["message_type"]
    if payload["language"] == "ru":
        return {
            "message": "Могу помочь с IT-поиском кандидатов. Напиши роль, технологию, локацию и 1-3 сигнала стека.",
            "warnings": [],
            "limitations": [],
        }, None
    if message_type == "small_talk":
        return {
            "message": "I'm here to help with candidate search. Tell me the role, technology, location, and 1-3 stack signals.",
            "warnings": [],
            "limitations": [],
        }, None
    return {
        "message": payload["deterministic_message"],
        "warnings": [],
        "limitations": [],
    }, None


async def assert_non_it_roles_do_not_advance_brief() -> None:
    plumber = await main.recruiter_chat_turn_response(chat_request("The plumber", "en"))
    assert plumber["state"] == "needs_clarification"
    assert plumber["can_build_plan"] is False
    assert plumber["normalized_brief"] is None
    assert "target location" not in plumber["assistant_message"].lower()
    assert "outside the supported search scope" in plumber["assistant_message"]

    dentist = await main.recruiter_chat_turn_response(
        chat_request("I told you the role - dentist", "en")
    )
    assert dentist["state"] == "needs_clarification"
    assert dentist["can_build_plan"] is False
    assert "target location" not in dentist["assistant_message"].lower()
    assert "outside the supported search scope" in dentist["assistant_message"]

    data_engineer = await main.recruiter_chat_turn_response(
        chat_request("Find data engineer candidates in Ukraine", "en")
    )
    assert data_engineer["state"] == "needs_clarification"
    assert "outside the supported search scope" not in data_engineer["assistant_message"]


async def assert_evidence_gate_blocks_hallucinated_ready() -> None:
    main.run_openai_json_recruiter_chat = fake_recruiter_chat_hallucinated_ready
    weak = await main.recruiter_chat_turn_response(
        chat_request("candidate candidate candidate", "en")
    )
    assert weak["state"] == "needs_clarification"
    assert weak["can_build_plan"] is False
    assert weak["normalized_brief"]["brief_status"] == "needs_clarification"
    assert "I understood the search" not in weak["assistant_message"]

    noise = await main.recruiter_chat_turn_response(chat_request("zzzzzzzzzzzz", "en"))
    assert noise["state"] == "needs_clarification"
    assert noise["can_build_plan"] is False
    assert noise["normalized_brief"] is None


async def assert_valid_request_still_reaches_ready() -> None:
    main.run_openai_json_recruiter_chat = fake_recruiter_chat_valid
    valid = await main.recruiter_chat_turn_response(
        chat_request("Find Backend Developer in Ukraine, Java, Spring.", "en")
    )
    assert valid["state"] == "ready_for_planning"
    assert valid["can_build_plan"] is True
    assert valid["normalized_brief"]["stack"] == ["Spring"]


async def assert_small_talk_uses_safe_wording() -> None:
    before_recruiter_llm = len(RECRUITER_LLM_CALLS)
    response = await main.recruiter_chat_turn_response(chat_request("What's up?", "en"))
    assert len(RECRUITER_LLM_CALLS) == before_recruiter_llm
    assert response["state"] == "needs_clarification"
    assert response["normalized_brief"] is None
    assert response["can_build_plan"] is False
    assert response["wording_provenance"]["wording_mode"] == "llm_assisted"
    assert "candidate search" in response["assistant_message"]

    preserved = await main.recruiter_chat_turn_response(
        chat_request("What's up?", "en", draft_brief=ready_brief())
    )
    assert preserved["state"] == "ready_for_planning"
    assert preserved["can_build_plan"] is True
    assert preserved["brief_changed"] is False
    assert preserved["stale_state_should_clear"] is False


async def assert_pending_action_intent_endpoint() -> None:
    confirm = await main.classify_recruiter_chat_intent(
        main.RecruiterChatIntentRequest(
            latest_message="Confirm",
            language="en",
            context_type="pending_action",
            pending_action_type="start_search",
            current_brief_status="ready_for_planning",
        )
    )
    assert confirm["pending_action_intent"] == "confirm"
    assert confirm["source"] == "deterministic_fallback"

    refine = await main.classify_recruiter_chat_intent(
        main.RecruiterChatIntentRequest(
            latest_message="wait, change Spring to Kafka",
            language="en",
            context_type="pending_action",
            pending_action_type="start_search",
            current_brief_status="ready_for_planning",
        )
    )
    assert refine["pending_action_intent"] == "refine"


def assert_frontend_phase_88_contract() -> None:
    source = (PROJECT_DIR / "app" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (PROJECT_DIR / "app" / "static" / "index.html").read_text(encoding="utf-8")
    styles = (PROJECT_DIR / "app" / "static" / "styles.css").read_text(encoding="utf-8")
    assert 'const RECRUITER_CHAT_INTENT_ENDPOINT = "/api/recruiter-chat/intent";' in source
    assert "async function classifyPendingSearchRunIntent" in source
    assert "pending_action_type: \"start_search\"" in source
    assert "pendingIntent === \"confirm\"" in source
    assert "pendingIntent === \"refine\"" in source
    assert "recruiter-hidden-technical" in index_html
    assert ".recruiter-hidden-technical" in styles
    assert "display: none !important;" in styles
    for technical_label in [
        "Search details",
        "LinkedIn profiles only",
        "Location filter",
        "Multi-wave",
        "Prepare search",
        "Run search",
    ]:
        marker = f'{technical_label}</'
        if marker in index_html:
            assert "recruiter-hidden-technical" in index_html


async def run_smoke() -> None:
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }
    original_chat_llm = main.run_openai_json_recruiter_chat
    original_intent_llm = main.run_openai_json_recruiter_intent
    original_wording_llm = main.run_openai_json_agent_wording

    os.environ["OPENAI_API_KEY"] = "fake-openai-key"
    os.environ["OPENAI_MODEL"] = "fake-model"
    main.run_openai_json_recruiter_intent = fake_recruiter_intent
    main.run_openai_json_agent_wording = fake_conversation_wording

    try:
        await assert_non_it_roles_do_not_advance_brief()
        await assert_evidence_gate_blocks_hallucinated_ready()
        await assert_valid_request_still_reaches_ready()
        await assert_small_talk_uses_safe_wording()
        await assert_pending_action_intent_endpoint()
        assert_frontend_phase_88_contract()
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
    print("P8.8 conversation hardening smoke passed")
