import asyncio
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main
from app.pending_answer_interpreter import (
    validate_pending_answer_interpreter_output,
)


def missing_stack_brief() -> main.SearchBrief:
    return main.SearchBrief(
        source_text="I need QA Automation in Spain with Java skills.",
        brief_status="needs_clarification",
        role_family="QA Automation",
        technology="Java",
        stack=[],
        location="Spain",
        must_have=["Java"],
        nice_to_have=[],
        search_depth="standard",
        profile_sources=["linkedin_public"],
        missing_fields=["stack"],
        clarifying_questions=["Which 1-3 stack signals are important for this search?"],
    )


def missing_location_brief() -> main.SearchBrief:
    return main.SearchBrief(
        source_text="I need QA Automation with Java skills.",
        brief_status="needs_clarification",
        role_family="QA Automation",
        technology="Java",
        stack=["Java"],
        location=None,
        must_have=["Java"],
        nice_to_have=["Java"],
        search_depth="standard",
        profile_sources=["linkedin_public"],
        missing_fields=["location"],
        clarifying_questions=["What target location should the search use?"],
    )


def ready_brief() -> main.SearchBrief:
    return main.SearchBrief(
        source_text="Find QA Automation in Spain with Java, Spring, and Kafka.",
        brief_status="ready_for_planning",
        role_family="QA Automation",
        technology="Java",
        stack=["Spring", "Kafka"],
        location="Spain",
        must_have=["Java"],
        nice_to_have=["Spring", "Kafka"],
        search_depth="standard",
        profile_sources=["linkedin_public"],
    )


def chat_request(
    text: str,
    draft_brief: main.SearchBrief | None = None,
    pending_update_field: str | None = None,
) -> main.RecruiterChatTurnRequest:
    return main.RecruiterChatTurnRequest(
        language="en",
        draft_brief=draft_brief,
        pending_update_field=pending_update_field,
        messages=[main.RecruiterChatMessage(role="user", content=text)],
    )


async def neutral_intent_classifier(
    request: main.RecruiterChatIntentRequest,
) -> dict:
    return {
        "intent": "unclear",
        "role_domain": "unknown",
        "role_support_status": "unknown",
        "pending_action_intent": "unclear",
        "field_intent": "unclear",
        "unsupported_role_label": None,
        "confidence": "medium",
        "response_language": "en",
    }


async def fake_pending_answer_interpreter(
    *,
    latest_message: str,
    language: str,
    expected_field: str | None = None,
    pending_update_field: str | None = None,
    current_brief: main.SearchBrief | dict | None = None,
) -> tuple[dict | None, str | None]:
    text = latest_message.lower()
    field = expected_field or pending_update_field
    if field == "stack" and "java only" in text:
        return {
            "intent": "answer_pending_field",
            "field": "stack",
            "values": ["Java"],
            "confidence": "high",
            "reason_code": "natural_stack_answer",
        }, None
    if field == "stack" and "selenium" in text:
        return {
            "intent": "provide_update_value",
            "field": "stack",
            "values": ["Selenium"],
            "confidence": "high",
            "reason_code": "stack_update_value",
        }, None
    if field == "location" and "madrid" in text:
        return {
            "intent": "answer_pending_field",
            "field": "location",
            "values": ["Madrid"],
            "confidence": "high",
            "reason_code": "natural_location_answer",
        }, None
    if field == "location" and "spain" in text:
        return {
            "intent": "answer_pending_field",
            "field": "location",
            "values": ["Spain"],
            "confidence": "high",
            "reason_code": "natural_location_answer",
        }, None
    return {
        "intent": "unclear",
        "field": None,
        "values": [],
        "confidence": "high",
        "reason_code": "unclear",
    }, None


async def fake_stack_signal_classifier(
    terms: list[str],
    current_brief: Any = None,
) -> tuple[dict | None, str | None]:
    return {
        "accepted_terms": [
            {
                "input": term,
                "normalized": term,
                "reason_code": "qa_tool",
            }
            for term in terms
        ],
        "rejected_terms": [],
        "confidence": "high",
    }, None


def assert_validator_contract() -> None:
    valid, error = validate_pending_answer_interpreter_output(
        {
            "intent": "answer_pending_field",
            "field": "stack",
            "values": ["Java"],
            "confidence": "high",
            "reason_code": "natural_stack_answer",
        },
        expected_field="stack",
    )
    assert error is None, error
    assert valid is not None, valid
    assert valid["values"] == ["Java"], valid
    assert valid["validator_version"] == "pending_answer_interpreter_validator_v1", valid

    invalid, error = validate_pending_answer_interpreter_output(
        {
            "intent": "answer_pending_field",
            "field": "stack",
            "values": ["Java"],
            "confidence": "high",
            "reason_code": "natural_stack_answer",
            "extra": "not allowed",
        },
        expected_field="stack",
    )
    assert invalid is None, invalid
    assert error == "pending_answer_unknown_fields", error

    invalid, error = validate_pending_answer_interpreter_output(
        {
            "intent": "answer_pending_field",
            "field": "location",
            "values": ["Spain"],
            "confidence": "low",
            "reason_code": "low_confidence",
        },
        expected_field="location",
    )
    assert invalid is None, invalid
    assert error == "pending_answer_low_confidence", error

    invalid, error = validate_pending_answer_interpreter_output(
        {
            "intent": "answer_pending_field",
            "field": "location",
            "values": ["https://example.com"],
            "confidence": "high",
            "reason_code": "unsafe",
        },
        expected_field="location",
    )
    assert invalid is None, invalid
    assert error == "pending_answer_unsafe_value", error


async def assert_pending_stack_natural_answer() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("Java only", draft_brief=missing_stack_brief())
    )
    assert response["ok"] is True, response
    assert response["state"] == "ready_for_planning", response
    assert response["normalized_brief"]["stack"] == ["Java"], response


async def assert_pending_location_natural_answer() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("Madrid would work", draft_brief=missing_location_brief())
    )
    assert response["ok"] is True, response
    assert response["state"] == "ready_for_planning", response
    assert response["normalized_brief"]["location"] == "Madrid", response


async def assert_pending_update_stack_value() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request(
            "replace Kafka with Selenium",
            draft_brief=ready_brief(),
            pending_update_field="stack",
        )
    )
    assert response["ok"] is True, response
    assert response["state"] == "ready_for_planning", response
    assert response["normalized_brief"]["stack"] == ["Selenium"], response


async def assert_low_confidence_does_not_patch() -> None:
    original_pending_interpreter = main.run_openai_json_pending_answer_interpreter

    async def low_confidence_interpreter(**kwargs: Any) -> tuple[dict | None, str | None]:
        return {
            "intent": "answer_pending_field",
            "field": "stack",
            "values": ["Java"],
            "confidence": "low",
            "reason_code": "low_confidence",
        }, None

    main.run_openai_json_pending_answer_interpreter = low_confidence_interpreter
    try:
        response = await main.recruiter_chat_turn_response(
            chat_request("Java only", draft_brief=missing_stack_brief())
        )
    finally:
        main.run_openai_json_pending_answer_interpreter = original_pending_interpreter

    assert response["state"] == "needs_clarification", response
    assert response["normalized_brief"]["stack"] == [], response


async def main_smoke() -> None:
    assert_validator_contract()

    original_intent_classifier = main.classify_recruiter_chat_intent_response
    original_pending_interpreter = main.run_openai_json_pending_answer_interpreter
    original_stack_classifier = main.run_openai_json_stack_signal_classifier
    main.classify_recruiter_chat_intent_response = neutral_intent_classifier
    main.run_openai_json_pending_answer_interpreter = fake_pending_answer_interpreter
    main.run_openai_json_stack_signal_classifier = fake_stack_signal_classifier
    try:
        await assert_pending_stack_natural_answer()
        await assert_pending_location_natural_answer()
        await assert_pending_update_stack_value()
        await assert_low_confidence_does_not_patch()
    finally:
        main.classify_recruiter_chat_intent_response = original_intent_classifier
        main.run_openai_json_pending_answer_interpreter = original_pending_interpreter
        main.run_openai_json_stack_signal_classifier = original_stack_classifier


if __name__ == "__main__":
    asyncio.run(main_smoke())
