import asyncio
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main, search_brief_extractor as extractor


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


def brief_missing_technology_with_stack() -> main.SearchBrief:
    return main.SearchBrief(
        source_text="Find Backend Developer in Ukraine with AWS.",
        brief_status="needs_clarification",
        role_family="Backend Developer",
        technology=None,
        stack=["AWS"],
        location="Ukraine",
        must_have=[],
        nice_to_have=["AWS"],
        search_depth="standard",
        profile_sources=["linkedin_public"],
        missing_fields=["technology"],
        clarifying_questions=["What is the main programming technology?"],
    )


async def fake_recruiter_intent(
    request: main.RecruiterChatIntentRequest,
) -> tuple[dict, str | None]:
    INTENT_CALLS.append(request.latest_message)
    text = request.latest_message.lower()
    if "role family" in text:
        return {
            "intent": "unclear",
            "role_domain": "unknown",
            "role_support_status": "unknown",
            "pending_action_intent": "unclear",
            "field_intent": "field_explanation",
            "field": "role_family",
            "unsupported_role_label": None,
            "confidence": "high",
            "response_language": "en",
        }, None
    if "stack" in text and "mean" in text:
        return {
            "intent": "unclear",
            "role_domain": "unknown",
            "role_support_status": "unknown",
            "pending_action_intent": "unclear",
            "field_intent": "field_explanation",
            "field": "stack",
            "unsupported_role_label": None,
            "confidence": "high",
            "response_language": "en",
        }, None
    if request.pending_field == "technology" and text.strip() == "aws":
        return {
            "intent": "candidate_search",
            "role_domain": "unknown",
            "role_support_status": "unknown",
            "pending_action_intent": "unclear",
            "field_intent": "repeats_existing_value",
            "field": "stack",
            "answered_field": "stack",
            "field_value": "AWS",
            "field_reason_code": "repeated_stack_value",
            "unsupported_role_label": None,
            "confidence": "high",
            "response_language": "en",
        }, None
    if "start again" in text or "start over" in text or "restart" in text:
        return {
            "intent": "restart",
            "role_domain": "unknown",
            "role_support_status": "unknown",
            "pending_action_intent": "unclear",
            "field_intent": "unclear",
            "unsupported_role_label": None,
            "confidence": "high",
            "response_language": "en",
        }, None
    if request.pending_action_type == "start_search" and "update" in text:
        return {
            "intent": "unclear",
            "role_domain": "unknown",
            "role_support_status": "unknown",
            "pending_action_intent": "refine",
            "pending_action_reason_code": "wants_to_update_before_search",
            "field_intent": "unclear",
            "unsupported_role_label": None,
            "confidence": "high",
            "response_language": "en",
        }, None
    if request.pending_action_type == "start_search" and text.strip() == "great":
        return {
            "intent": "small_talk",
            "role_domain": "unknown",
            "role_support_status": "unknown",
            "pending_action_intent": "unclear",
            "pending_action_reason_code": "positive_acknowledgement_not_confirmation",
            "field_intent": "unclear",
            "unsupported_role_label": None,
            "confidence": "medium",
            "response_language": "en",
        }, None
    if "what" in text and "up" in text:
        return {
            "intent": "small_talk",
            "role_domain": "unknown",
            "role_support_status": "unknown",
            "pending_action_intent": "unclear",
            "field_intent": "unclear",
            "unsupported_role_label": None,
            "confidence": "high",
        }, None
    if "qa automation" in text:
        return {
            "intent": "candidate_search",
            "role_domain": "it_software",
            "role_support_status": "unsupported",
            "role_label": "QA Automation",
            "role_reason_code": "unsupported_it_role",
            "is_profession_like": True,
            "java_programmer_role": False,
            "pending_action_intent": "unclear",
            "field_intent": "unclear",
            "unsupported_role_label": None,
            "confidence": "high",
            "response_language": "en",
        }, None
    if text.strip() == "analyst":
        return {
            "intent": "candidate_search",
            "role_domain": "ambiguous",
            "role_support_status": "ambiguous",
            "role_label": "Analyst",
            "role_reason_code": "ambiguous_role_like_phrase",
            "is_profession_like": True,
            "java_programmer_role": None,
            "pending_action_intent": "unclear",
            "field_intent": "unclear",
            "unsupported_role_label": None,
            "confidence": "high",
            "response_language": "en",
        }, None
    if text.strip() == "banana":
        return {
            "intent": "unclear",
            "role_domain": "unknown",
            "role_support_status": "noise",
            "role_label": None,
            "role_reason_code": "not_a_role_request",
            "is_profession_like": False,
            "java_programmer_role": False,
            "pending_action_intent": "unclear",
            "field_intent": "noise",
            "unsupported_role_label": None,
            "confidence": "high",
            "response_language": "en",
        }, None
    if "data engineer" in text:
        return {
            "intent": "candidate_search",
            "role_domain": "it_software",
            "role_support_status": "unknown",
            "pending_action_intent": "unclear",
            "field_intent": "unclear",
            "unsupported_role_label": None,
            "confidence": "high",
        }, None
    return {
        "intent": "unclear",
        "role_domain": "unknown",
        "role_support_status": "unknown",
        "pending_action_intent": "unclear",
        "field_intent": "unclear",
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


def raw_extractor_output_from_draft(draft: dict, reason_code: str = "smoke_fixture") -> dict:
    return {
        "schema_version": extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
        "draft_brief": {
            "source_text": draft.get("source_text"),
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
        "reason_codes": [reason_code],
    }


async def fake_search_brief_extractor_hallucinated_ready(
    *,
    latest_message: str,
    language: str,
    previous_brief: dict | None = None,
) -> tuple[dict | None, str | None]:
    request = main.RecruiterChatTurnRequest(
        language=language,
        messages=[main.RecruiterChatMessage(role="user", content=latest_message)],
    )
    output, errors = await fake_recruiter_chat_hallucinated_ready(request)
    if errors or not output:
        return None, "fake_search_brief_extractor_error"
    return raw_extractor_output_from_draft(output["draft_brief"], "hallucinated_ready"), None


async def fake_search_brief_extractor_valid(
    *,
    latest_message: str,
    language: str,
    previous_brief: dict | None = None,
) -> tuple[dict | None, str | None]:
    request = main.RecruiterChatTurnRequest(
        language=language,
        messages=[main.RecruiterChatMessage(role="user", content=latest_message)],
    )
    output, errors = await fake_recruiter_chat_valid(request)
    if errors or not output:
        return None, "fake_search_brief_extractor_error"
    return raw_extractor_output_from_draft(output["draft_brief"], "valid_ready"), None


async def fake_search_brief_extractor_default(
    *,
    latest_message: str,
    language: str,
    previous_brief: dict | None = None,
) -> tuple[dict | None, str | None]:
    normalized_message = latest_message.lower().strip()
    if normalized_message in {"qa automation", "analyst"}:
        role_family = "QA Automation" if normalized_message == "qa automation" else "Analyst"
        return {
            "schema_version": extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
            "draft_brief": {
                "source_text": latest_message,
                "role_family": role_family,
                "role_ambiguity": {
                    "is_ambiguous": False,
                    "label": None,
                    "options": [],
                    "clarification_question": None,
                },
                "technology": None,
                "stack": [],
                "location": None,
                "seniority": None,
                "must_have": [],
                "nice_to_have": [],
                "domain_experience": [],
                "exclusions": [],
                "search_depth": "standard",
                "profile_sources": ["linkedin_public"],
                "notes": None,
            },
            "confidence": "high",
            "reason_codes": ["role_only_partial"],
        }, None
    if "data engineer" in normalized_message:
        return {
            "schema_version": extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
            "draft_brief": {
                "source_text": latest_message,
                "role_family": "Data Engineer",
                "role_ambiguity": {
                    "is_ambiguous": False,
                    "label": None,
                    "options": [],
                    "clarification_question": None,
                },
                "technology": None,
                "stack": [],
                "location": "Ukraine",
                "seniority": None,
                "must_have": [],
                "nice_to_have": [],
                "domain_experience": [],
                "exclusions": [],
                "search_depth": "standard",
                "profile_sources": ["linkedin_public"],
                "notes": None,
            },
            "confidence": "high",
            "reason_codes": ["data_engineer_partial"],
        }, None
    return await fake_search_brief_extractor_valid(
        latest_message=latest_message,
        language=language,
        previous_brief=previous_brief,
    )


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
    main.run_openai_json_search_brief_extractor = fake_search_brief_extractor_hallucinated_ready
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
    main.run_openai_json_search_brief_extractor = fake_search_brief_extractor_valid
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


async def assert_llm_role_classifier_handles_java_scope_edges() -> None:
    main.run_openai_json_search_brief_extractor = fake_search_brief_extractor_default
    qa = await main.recruiter_chat_turn_response(chat_request("QA Automation", "en"))
    assert qa["state"] == "needs_clarification"
    assert qa["normalized_brief"]["role_family"] == "QA Automation"
    assert qa["normalized_brief"]["technology"] is None
    assert qa["normalized_brief"]["stack"] == []
    assert qa["can_build_plan"] is False
    assert "main technology" in qa["assistant_message"].lower()
    assert "did not understand" not in qa["assistant_message"].lower()

    analyst = await main.recruiter_chat_turn_response(chat_request("Analyst", "en"))
    assert analyst["state"] == "needs_clarification"
    assert analyst["normalized_brief"]["role_family"] == "Analyst"
    assert analyst["can_build_plan"] is False
    assert "main technology" in analyst["assistant_message"].lower()

    noise = await main.recruiter_chat_turn_response(chat_request("banana", "en"))
    assert noise["state"] == "needs_clarification"
    assert noise["normalized_brief"] is None
    assert noise["can_build_plan"] is False
    assert "does not look like" in noise["assistant_message"].lower()


async def assert_field_explanations_preserve_brief_state() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("What role family means?", "en", draft_brief=ready_brief())
    )
    assert response["state"] == "ready_for_planning"
    assert response["can_build_plan"] is True
    assert response["brief_changed"] is False
    assert response["stale_state_should_clear"] is False
    assert "broad type of role" in response["assistant_message"].lower()

    stack = await main.recruiter_chat_turn_response(
        chat_request("What does stack mean?", "en", draft_brief=ready_brief())
    )
    assert stack["state"] == "ready_for_planning"
    assert stack["brief_changed"] is False
    assert "1-3 signals" in stack["assistant_message"].lower()


async def assert_pending_field_answer_classifier_blocks_wrong_field() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("AWS", "en", draft_brief=brief_missing_technology_with_stack())
    )
    assert response["state"] == "needs_clarification"
    assert response["can_build_plan"] is False
    assert response["brief_changed"] is False
    assert response["stale_state_should_clear"] is False
    assert "main programming technology" in response["assistant_message"].lower()
    assert "java" in response["assistant_message"].lower()
    assert response["normalized_brief"]["stack"] == ["AWS"]
    assert response["normalized_brief"]["technology"] is None


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

    general_update = await main.classify_recruiter_chat_intent(
        main.RecruiterChatIntentRequest(
            latest_message="I want to update",
            language="en",
            context_type="pending_action",
            pending_action_type="start_search",
            current_brief_status="ready_for_planning",
        )
    )
    assert general_update["pending_action_intent"] == "refine"
    assert general_update["pending_action_reason_code"] == "wants_to_update_before_search"

    vague_ack = await main.classify_recruiter_chat_intent(
        main.RecruiterChatIntentRequest(
            latest_message="great",
            language="en",
            context_type="pending_action",
            pending_action_type="start_search",
            current_brief_status="ready_for_planning",
        )
    )
    assert vague_ack["pending_action_intent"] == "unclear"
    assert vague_ack["pending_action_reason_code"] == "positive_acknowledgement_not_confirmation"

    restart = await main.classify_recruiter_chat_intent(
        main.RecruiterChatIntentRequest(
            latest_message="ok, can we start again?",
            language="en",
            context_type="pending_action",
            pending_action_type="start_search",
            current_brief_status="ready_for_planning",
        )
    )
    assert restart["intent"] == "restart"
    assert restart["confidence"] == "high"


async def assert_pending_hypothesis_confirmation_completes_brief() -> None:
    initial = await main.recruiter_chat_turn_response(
        chat_request("Java dev in Ukraine with Spring", "en")
    )
    assert initial["state"] == "ready_for_planning"
    assert initial["can_build_plan"] is True
    assert initial["normalized_brief"]["role_family"] == "Backend Developer"
    assert initial["normalized_brief"]["technology"] == "Java"
    assert initial["normalized_brief"]["location"] == "Ukraine"
    assert initial["normalized_brief"]["stack"] == ["Spring"]

    unsupported_yes = await main.recruiter_chat_turn_response(chat_request("yes", "en"))
    assert unsupported_yes["state"] == "needs_clarification"
    assert unsupported_yes["can_build_plan"] is False
    assert unsupported_yes["normalized_brief"] is None


async def assert_pending_update_intent_and_field_value_flow() -> None:
    field = await main.classify_recruiter_chat_intent(
        main.RecruiterChatIntentRequest(
            latest_message="location",
            language="en",
            context_type="pending_update",
            current_brief_status="ready_for_planning",
            current_brief=ready_brief(),
        )
    )
    assert field["pending_update_intent"] == "select_field"
    assert field["field"] == "location"

    value = await main.classify_recruiter_chat_intent(
        main.RecruiterChatIntentRequest(
            latest_message="Kyiv",
            language="en",
            context_type="pending_update_value",
            pending_update_field="location",
            current_brief_status="ready_for_planning",
            current_brief=ready_brief(),
        )
    )
    assert value["pending_update_intent"] == "provide_value"
    assert value["field"] == "location"

    updated_stack = await main.recruiter_chat_turn_response(
        main.RecruiterChatTurnRequest(
            language="en",
            draft_brief=ready_brief(),
            pending_update_field="stack",
            messages=[main.RecruiterChatMessage(role="user", content="Kafka")],
        )
    )
    assert updated_stack["state"] == "ready_for_planning"
    assert updated_stack["normalized_brief"]["stack"] == ["Kafka"]
    assert updated_stack["brief_changed"] is True

    updated_location = await main.recruiter_chat_turn_response(
        main.RecruiterChatTurnRequest(
            language="en",
            draft_brief=ready_brief(),
            pending_update_field="location",
            messages=[main.RecruiterChatMessage(role="user", content="Germany")],
        )
    )
    assert updated_location["state"] == "ready_for_planning"
    assert updated_location["normalized_brief"]["location"] == "Germany"
    assert updated_location["brief_changed"] is True
    assert updated_location["stale_state_should_clear"] is True

    restarted = await main.recruiter_chat_turn_response(
        main.RecruiterChatTurnRequest(
            language="en",
            draft_brief=ready_brief(),
            messages=[main.RecruiterChatMessage(role="user", content="ok, can we start again?")],
        )
    )
    assert restarted["state"] == "needs_clarification"
    assert restarted["clear_brief"] is True
    assert restarted["stale_state_should_clear"] is False
    assert restarted["normalized_brief"] is None


def assert_frontend_phase_88_contract() -> None:
    source = (PROJECT_DIR / "app" / "static" / "app.js").read_text(encoding="utf-8")
    index_html = (PROJECT_DIR / "app" / "static" / "index.html").read_text(encoding="utf-8")
    styles = (PROJECT_DIR / "app" / "static" / "styles.css").read_text(encoding="utf-8")
    assert 'const RECRUITER_CHAT_INTENT_ENDPOINT = "/api/recruiter-chat/intent";' in source
    assert "async function classifyPendingSearchRunIntent" in source
    assert "async function classifyPendingSearchSummaryUpdateIntent" in source
    assert "function setPendingSearchSummaryUpdateAction" in source
    assert "pending_update_field: pendingUpdateFieldForRequest" in source
    assert "context_type: isFieldValue ? \"pending_update_value\" : \"pending_update\"" in source
    assert "pending_action_type: \"start_search\"" in source
    assert "pendingIntent === \"confirm\"" in source
    assert "pendingIntent === \"refine\"" in source
    assert "pendingIntent === \"restart\"" in source
    assert "updateIntent === \"restart\"" in source
    assert "appendOutgoingUserMessage" in source
    assert "appendAssistantThinkingMessage" in source
    assert "clearAssistantThinkingMessage" in source
    assert "Updating search summary..." not in source
    assert "data-workspace-page-action" in source
    assert "workspacePaginationState" in source
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
    original_extractor = main.run_openai_json_search_brief_extractor
    original_intent_llm = main.run_openai_json_recruiter_intent
    original_wording_llm = main.run_openai_json_agent_wording

    os.environ["OPENAI_API_KEY"] = "fake-openai-key"
    os.environ["OPENAI_MODEL"] = "fake-model"
    main.run_openai_json_search_brief_extractor = fake_search_brief_extractor_default
    main.run_openai_json_recruiter_intent = fake_recruiter_intent
    main.run_openai_json_agent_wording = fake_conversation_wording

    try:
        await assert_non_it_roles_do_not_advance_brief()
        await assert_evidence_gate_blocks_hallucinated_ready()
        await assert_valid_request_still_reaches_ready()
        await assert_small_talk_uses_safe_wording()
        await assert_llm_role_classifier_handles_java_scope_edges()
        await assert_field_explanations_preserve_brief_state()
        await assert_pending_field_answer_classifier_blocks_wrong_field()
        await assert_pending_action_intent_endpoint()
        await assert_pending_hypothesis_confirmation_completes_brief()
        await assert_pending_update_intent_and_field_value_flow()
        assert_frontend_phase_88_contract()
    finally:
        main.run_openai_json_recruiter_chat = original_chat_llm
        main.run_openai_json_search_brief_extractor = original_extractor
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
