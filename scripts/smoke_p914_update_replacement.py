import asyncio
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main
from app.pending_answer_interpreter import validate_pending_answer_interpreter_output


class UpdateReplacementSmokeError(AssertionError):
    pass


PENDING_INTERPRETER_CALLS: list[str] = []
FORBIDDEN_CALLS: list[str] = []


def ready_brief(
    *,
    technology: str = "Java",
    stack: list[str] | None = None,
    must_have: list[str] | None = None,
) -> main.SearchBrief:
    selected_stack = stack or ["Spring", "Kafka"]
    return main.SearchBrief(
        source_text="Find candidates.",
        brief_status="ready_for_planning",
        role_family="Backend Developer",
        technology=technology,
        stack=selected_stack,
        location="Ukraine",
        seniority=None,
        must_have=must_have or [technology],
        nice_to_have=selected_stack,
        exclusions=[],
        search_depth="standard",
        profile_sources=["linkedin_public"],
        assumptions=[],
    )


def chat_request(text: str, draft_brief: main.SearchBrief) -> main.RecruiterChatTurnRequest:
    return main.RecruiterChatTurnRequest(
        language="en",
        draft_brief=draft_brief,
        messages=[main.RecruiterChatMessage(role="user", content=text)],
    )


def replacement_output(
    *,
    field: str | None,
    old_value: str,
    new_value: str,
) -> dict[str, Any]:
    return {
        "intent": "replace_value",
        "field": field,
        "old_value": old_value,
        "values": [new_value],
        "confidence": "high",
        "reason_code": "value_replacement",
    }


async def fake_pending_answer_interpreter(**kwargs: Any) -> tuple[dict[str, Any] | None, str | None]:
    text = kwargs["latest_message"]
    PENDING_INTERPRETER_CALLS.append(text)
    fixtures = {
        "Change Angular skill to PHP": replacement_output(
            field="stack",
            old_value="Angular",
            new_value="PHP",
        ),
        "update Selenium to Cucumber": replacement_output(
            field=None,
            old_value="Selenium",
            new_value="Cucumber",
        ),
        "replace Java with PHP": replacement_output(
            field=None,
            old_value="Java",
            new_value="PHP",
        ),
        "Change React skill to PHP": replacement_output(
            field="stack",
            old_value="React",
            new_value="PHP",
        ),
    }
    if text not in fixtures:
        raise UpdateReplacementSmokeError(f"Unexpected pending interpreter text: {text!r}")
    return fixtures[text], None


async def fake_stack_signal_classifier(
    terms: list[str],
    current_brief: Any = None,
) -> tuple[dict[str, Any] | None, str | None]:
    return {
        "accepted_terms": [
            {
                "input": term,
                "normalized": term,
                "reason_code": "accepted_test_stack_signal",
            }
            for term in terms
        ],
        "rejected_terms": [],
        "confidence": "high",
    }, None


async def forbidden_call(*args: Any, **kwargs: Any) -> Any:
    FORBIDDEN_CALLS.append(str(args or kwargs))
    raise UpdateReplacementSmokeError("Unexpected fallback call for value replacement.")


def assert_validator_contract() -> None:
    valid, error = validate_pending_answer_interpreter_output(
        {
            "intent": "replace_value",
            "field": "stack",
            "old_value": "Angular",
            "values": ["PHP"],
            "confidence": "high",
            "reason_code": "stack_value_replacement",
        },
    )
    if error or not valid:
        raise UpdateReplacementSmokeError(f"Expected valid replace_value output, got {error!r}")
    if valid["old_value"] != "Angular":
        raise UpdateReplacementSmokeError(f"Expected old value Angular, got {valid!r}")
    if valid["values"] != ["PHP"]:
        raise UpdateReplacementSmokeError(f"Expected normalized PHP value, got {valid!r}")
    if valid["validator_version"] != "pending_answer_interpreter_validator_v2":
        raise UpdateReplacementSmokeError(f"Unexpected validator version: {valid!r}")

    invalid, error = validate_pending_answer_interpreter_output(
        {
            "intent": "replace_value",
            "field": "stack",
            "values": ["PHP"],
            "confidence": "high",
            "reason_code": "missing_old_value",
        },
    )
    if invalid is not None or error != "pending_answer_missing_old_value":
        raise UpdateReplacementSmokeError(f"Expected missing old value rejection, got {invalid!r} {error!r}")

    invalid, error = validate_pending_answer_interpreter_output(
        {
            "intent": "replace_value",
            "field": "technology",
            "old_value": "Angular",
            "values": ["PHP"],
            "confidence": "high",
            "reason_code": "field_mismatch",
        },
        pending_update_field="stack",
    )
    if invalid is not None or error != "pending_answer_update_field_mismatch":
        raise UpdateReplacementSmokeError(f"Expected field mismatch rejection, got {invalid!r} {error!r}")


async def assert_direct_stack_replacement() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request(
            "Change Angular skill to PHP",
            ready_brief(technology="TypeScript", stack=["Angular", "Playwright"]),
        )
    )
    if response["ok"] is not True:
        raise UpdateReplacementSmokeError(f"Expected ok response: {response}")
    if response["normalized_brief"]["stack"] != ["PHP", "Playwright"]:
        raise UpdateReplacementSmokeError(f"Expected preserved stack replacement: {response}")
    if response.get("brief_changed") is not True:
        raise UpdateReplacementSmokeError(f"Expected changed brief: {response}")


async def assert_inferred_stack_replacement() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request(
            "update Selenium to Cucumber",
            ready_brief(stack=["Selenium", "JUnit"]),
        )
    )
    if response["normalized_brief"]["stack"] != ["Cucumber", "JUnit"]:
        raise UpdateReplacementSmokeError(f"Expected inferred stack replacement: {response}")


async def assert_inferred_technology_replacement() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request(
            "replace Java with PHP",
            ready_brief(technology="Java", stack=["Spring"]),
        )
    )
    if response["normalized_brief"]["technology"] != "PHP":
        raise UpdateReplacementSmokeError(f"Expected technology replacement: {response}")
    if response["normalized_brief"]["stack"] != ["Spring"]:
        raise UpdateReplacementSmokeError(f"Expected unchanged stack: {response}")


async def assert_missing_old_value_does_not_mutate() -> None:
    original_brief = ready_brief(technology="TypeScript", stack=["Angular", "Playwright"])
    response = await main.recruiter_chat_turn_response(
        chat_request("Change React skill to PHP", original_brief)
    )
    if response["normalized_brief"]["stack"] != ["Angular", "Playwright"]:
        raise UpdateReplacementSmokeError(f"Expected unchanged stack: {response}")
    if response.get("brief_changed") is True:
        raise UpdateReplacementSmokeError(f"Expected no brief change: {response}")
    if "could not find" not in (response.get("assistant_message") or "").lower():
        raise UpdateReplacementSmokeError(f"Expected narrow old-value clarification: {response}")


async def assert_ambiguous_old_value_does_not_mutate() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request(
            "replace Java with PHP",
            ready_brief(technology="Java", stack=["Java", "Spring"]),
        )
    )
    if response["normalized_brief"]["technology"] != "Java":
        raise UpdateReplacementSmokeError(f"Expected unchanged technology: {response}")
    if response["normalized_brief"]["stack"] != ["Java", "Spring"]:
        raise UpdateReplacementSmokeError(f"Expected unchanged stack: {response}")
    if "more than one" not in (response.get("assistant_message") or "").lower():
        raise UpdateReplacementSmokeError(f"Expected ambiguity clarification: {response}")


async def assert_selected_field_replacement_patch() -> None:
    patch, message = await main.pending_update_field_patch_from_message(
        "stack",
        "Change Angular skill to PHP",
        "en",
        ready_brief(technology="TypeScript", stack=["Angular", "Playwright"]),
    )
    if message:
        raise UpdateReplacementSmokeError(f"Expected patch without message: {message}")
    if not patch:
        raise UpdateReplacementSmokeError("Expected replacement patch.")
    operations = patch.get("operations") or []
    if operations != [
        {
            "operation": "replace_stack",
            "field": "stack",
            "values": ["PHP", "Playwright"],
        }
    ]:
        raise UpdateReplacementSmokeError(f"Unexpected selected-field patch: {patch}")


async def run_smoke() -> None:
    assert_validator_contract()

    original_pending_interpreter = main.run_openai_json_pending_answer_interpreter
    original_stack_classifier = main.run_openai_json_stack_signal_classifier
    original_intent_classifier = main.classify_recruiter_chat_intent_response
    original_refinement = main.run_openai_json_search_brief_refinement_interpreter
    original_legacy = main.run_openai_json_recruiter_chat

    main.run_openai_json_pending_answer_interpreter = fake_pending_answer_interpreter
    main.run_openai_json_stack_signal_classifier = fake_stack_signal_classifier
    main.classify_recruiter_chat_intent_response = forbidden_call
    main.run_openai_json_search_brief_refinement_interpreter = forbidden_call
    main.run_openai_json_recruiter_chat = forbidden_call
    try:
        await assert_direct_stack_replacement()
        await assert_inferred_stack_replacement()
        await assert_inferred_technology_replacement()
        await assert_missing_old_value_does_not_mutate()
        await assert_ambiguous_old_value_does_not_mutate()
        await assert_selected_field_replacement_patch()
    finally:
        main.run_openai_json_pending_answer_interpreter = original_pending_interpreter
        main.run_openai_json_stack_signal_classifier = original_stack_classifier
        main.classify_recruiter_chat_intent_response = original_intent_classifier
        main.run_openai_json_search_brief_refinement_interpreter = original_refinement
        main.run_openai_json_recruiter_chat = original_legacy

    if FORBIDDEN_CALLS:
        raise UpdateReplacementSmokeError(f"Unexpected fallback calls: {FORBIDDEN_CALLS!r}")
    if len(PENDING_INTERPRETER_CALLS) != 6:
        raise UpdateReplacementSmokeError(
            f"Expected 6 pending interpreter calls, got {len(PENDING_INTERPRETER_CALLS)}."
        )
    print("P9.14 Search Brief value replacement smoke passed")


if __name__ == "__main__":
    asyncio.run(run_smoke())
