import asyncio
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main
from app.pending_answer_interpreter import validate_pending_answer_interpreter_output


def ready_brief(
    *,
    technology: str = "Java",
    stack: list[str] | None = None,
    location: str = "Poland",
    role_family: str = "QA Automation",
) -> main.SearchBrief:
    selected_stack = stack if stack is not None else ["Selenium"]
    return main.SearchBrief(
        source_text=(
            f"Find {role_family} profiles in {location} with {technology} "
            f"and {', '.join(selected_stack)}."
        ),
        brief_status="ready_for_planning",
        role_family=role_family,
        technology=technology,
        stack=selected_stack,
        location=location,
        must_have=[technology],
        nice_to_have=selected_stack,
        search_depth="standard",
        profile_sources=["linkedin_public"],
    )


def chat_request(text: str, draft_brief: main.SearchBrief) -> main.RecruiterChatTurnRequest:
    return main.RecruiterChatTurnRequest(
        language="en",
        draft_brief=draft_brief,
        messages=[main.RecruiterChatMessage(role="user", content=text)],
    )


async def fake_replacement_interpreter(
    *,
    latest_message: str,
    language: str,
    expected_field: str | None = None,
    pending_update_field: str | None = None,
    current_brief: main.SearchBrief | dict | None = None,
) -> tuple[dict | None, str | None]:
    text = latest_message.lower()
    replacements = [
        ("selenium", "cucumber"),
        ("java", "python"),
        ("poland", "germany"),
        ("cypress", "cucumber"),
    ]
    if "https://bad" in text:
        return {
            "intent": "replace_value",
            "field": None,
            "old_value": "Selenium",
            "new_value": "https://bad",
            "confidence": "high",
            "reason_code": "replace_value",
        }, None
    for old_value, new_value in replacements:
        if old_value in text and new_value in text:
            return {
                "intent": "replace_value",
                "field": None,
                "old_value": old_value.title(),
                "new_value": new_value.title(),
                "confidence": "high",
                "reason_code": "replace_value",
            }, None
    return {
        "intent": "unclear",
        "field": None,
        "values": [],
        "confidence": "high",
        "reason_code": "unclear",
    }, None


async def unavailable_replacement_interpreter(**kwargs: Any) -> tuple[dict | None, str | None]:
    return None, "openai_not_configured"


def assert_replace_value_validator_contract() -> None:
    valid, error = validate_pending_answer_interpreter_output(
        {
            "intent": "replace_value",
            "field": None,
            "old_value": "Selenium",
            "new_value": "Cucumber",
            "confidence": "high",
            "reason_code": "replace_value",
        },
    )
    assert error is None, error
    assert valid is not None, valid
    assert valid["intent"] == "replace_value", valid
    assert valid["old_value"] == "Selenium", valid
    assert valid["new_value"] == "Cucumber", valid
    assert valid["validator_version"] == "pending_answer_interpreter_validator_v2", valid

    invalid, error = validate_pending_answer_interpreter_output(
        {
            "intent": "replace_value",
            "field": None,
            "old_value": "Selenium",
            "new_value": "https://bad",
            "confidence": "high",
            "reason_code": "replace_value",
        },
    )
    assert invalid is None, invalid
    assert error == "pending_answer_missing_replacement_value", error


async def assert_stack_value_replacement() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("update Selenium to Cucumber", ready_brief(stack=["Selenium"]))
    )
    assert response["ok"] is True, response
    assert response["state"] == "ready_for_planning", response
    assert response["normalized_brief"]["stack"] == ["Cucumber"], response
    assert response["brief_changed"] is True, response
    assert response["stale_state_should_clear"] is True, response
    assert "Which field" not in response["assistant_message"], response
    assert "query_plan" not in response, response


async def assert_technology_value_replacement() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("change Java to Python", ready_brief(stack=["Selenium"]))
    )
    assert response["ok"] is True, response
    assert response["normalized_brief"]["technology"] == "Python", response
    assert response["normalized_brief"]["must_have"] == ["Python"], response
    assert response["brief_changed"] is True, response


async def assert_location_value_replacement() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("update Poland to Germany", ready_brief(location="Poland"))
    )
    assert response["ok"] is True, response
    assert response["normalized_brief"]["location"] == "Germany", response
    assert response["brief_changed"] is True, response


async def assert_ambiguous_value_requires_clarification() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("update Java to Python", ready_brief(technology="Java", stack=["Java"]))
    )
    assert response["ok"] is True, response
    assert response["normalized_brief"]["technology"] == "Java", response
    assert response["normalized_brief"]["stack"] == ["Java"], response
    assert response["brief_changed"] is False, response
    assert response["brief_patch"]["requires_clarification"] is True, response
    assert "more than one search summary field" in response["assistant_message"], response


async def assert_missing_old_value_requires_clarification() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("update Cypress to Cucumber", ready_brief(stack=["Selenium"]))
    )
    assert response["ok"] is True, response
    assert response["normalized_brief"]["stack"] == ["Selenium"], response
    assert response["brief_changed"] is False, response
    assert response["brief_patch"]["requires_clarification"] is True, response
    assert "could not find" in response["assistant_message"], response


async def assert_invalid_new_value_is_rejected() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("update Selenium to https://bad", ready_brief(stack=["Selenium"]))
    )
    assert response["ok"] is True, response
    assert response["normalized_brief"]["stack"] == ["Selenium"], response
    assert response["brief_changed"] is False, response
    assert response["brief_patch"]["requires_clarification"] is True, response
    assert "could not use" in response["assistant_message"], response


async def assert_unavailable_llm_uses_safe_deterministic_fallback() -> None:
    original_pending_interpreter = main.run_openai_json_pending_answer_interpreter
    main.run_openai_json_pending_answer_interpreter = unavailable_replacement_interpreter
    try:
        response = await main.recruiter_chat_turn_response(
            chat_request("replace Selenium with Cucumber", ready_brief(stack=["Selenium"]))
        )
    finally:
        main.run_openai_json_pending_answer_interpreter = original_pending_interpreter

    assert response["ok"] is True, response
    assert response["normalized_brief"]["stack"] == ["Cucumber"], response
    assert response["brief_changed"] is True, response


async def main_smoke() -> None:
    assert_replace_value_validator_contract()

    original_pending_interpreter = main.run_openai_json_pending_answer_interpreter
    main.run_openai_json_pending_answer_interpreter = fake_replacement_interpreter
    try:
        await assert_stack_value_replacement()
        await assert_technology_value_replacement()
        await assert_location_value_replacement()
        await assert_ambiguous_value_requires_clarification()
        await assert_missing_old_value_requires_clarification()
        await assert_invalid_new_value_is_rejected()
        await assert_unavailable_llm_uses_safe_deterministic_fallback()
    finally:
        main.run_openai_json_pending_answer_interpreter = original_pending_interpreter


if __name__ == "__main__":
    asyncio.run(main_smoke())
