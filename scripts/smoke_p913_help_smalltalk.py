import asyncio
import os
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import help_smalltalk, main
from app import search_brief_extractor as extractor
from app.schemas import RecruiterChatMessage, RecruiterChatTurnRequest, SearchBrief


HELP_TEXT = "Can you help me"


class HelpSmallTalkSmokeError(AssertionError):
    pass


def chat_request(
    message: str,
    *,
    draft_brief: SearchBrief | None = None,
) -> RecruiterChatTurnRequest:
    return RecruiterChatTurnRequest(
        messages=[RecruiterChatMessage(role="user", content=message)],
        draft_brief=draft_brief,
        language="en",
    )


def ready_brief() -> SearchBrief:
    return SearchBrief(
        source_text="Find Backend Developer Java in Ukraine with Spring.",
        brief_status="ready_for_planning",
        role_family="Backend Developer",
        technology="Java",
        stack=["Spring"],
        location="Ukraine",
        search_depth="standard",
        profile_sources=["linkedin_public"],
    )


def raw_ready_extractor_output(text: str) -> dict[str, Any]:
    return {
        "schema_version": extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
        "draft_brief": {
            "source_text": text,
            "role_family": "Backend Developer",
            "role_ambiguity": {
                "is_ambiguous": False,
                "label": None,
                "options": [],
                "clarification_question": None,
            },
            "technology": "Java",
            "stack": ["Spring"],
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
        "reason_codes": ["help_smalltalk_fixture"],
    }


def help_or_onboarding_output() -> dict[str, Any]:
    return {
        "schema_version": help_smalltalk.HELP_SMALLTALK_RESOLVER_VERSION,
        "intent": "help_or_onboarding",
        "confidence": "high",
        "response_style": "friendly",
        "evidence": ["Can you help me"],
        "should_preserve_brief": True,
        "can_mutate_search_brief": False,
        "can_execute": False,
        "reason_code": "help_request",
    }


def assert_prompt_contract() -> None:
    prompt = help_smalltalk.help_smalltalk_user_prompt(
        latest_message=HELP_TEXT,
        language="en",
    )
    payload = help_smalltalk.help_smalltalk_openai_payload(
        model="test-model",
        latest_message=HELP_TEXT,
        language="en",
    )
    for expected in (
        help_smalltalk.HELP_SMALLTALK_RESOLVER_VERSION,
        "help_or_onboarding",
        "No Search Brief mutation.",
        "No query generation.",
        "No LinkedIn scraping",
        "No search approval.",
    ):
        if expected not in prompt:
            raise HelpSmallTalkSmokeError(f"Prompt is missing {expected!r}.")
    if payload.get("response_format") != {"type": "json_object"}:
        raise HelpSmallTalkSmokeError(f"Unexpected OpenAI payload: {payload!r}")


def assert_trigger_scope() -> None:
    expected_true = [
        "Can you help me",
        "I need help",
        "What can you do?",
        "help me find candidates",
    ]
    for text in expected_true:
        if not help_smalltalk.should_run_help_smalltalk_resolver(text):
            raise HelpSmallTalkSmokeError(f"Expected help trigger for {text!r}.")

    expected_false = [
        "Find Backend Developer in Ukraine with Java and Spring",
        "Can you help me find Backend Developer in Ukraine with Java",
        "Project Manager with SQL in Poland",
    ]
    for text in expected_false:
        if help_smalltalk.should_run_help_smalltalk_resolver(text):
            raise HelpSmallTalkSmokeError(f"Unexpected help trigger for {text!r}.")


def assert_validator_guardrails() -> None:
    validated, errors = help_smalltalk.validate_help_smalltalk_intent_output(
        help_or_onboarding_output(),
        latest_message=HELP_TEXT,
    )
    if errors or validated is None:
        raise HelpSmallTalkSmokeError(f"Expected valid help output: {errors!r}")
    if validated["intent"] != "help_or_onboarding":
        raise HelpSmallTalkSmokeError(f"Unexpected validated output: {validated!r}")

    unsafe = help_or_onboarding_output()
    unsafe["can_execute"] = True
    validated, errors = help_smalltalk.validate_help_smalltalk_intent_output(
        unsafe,
        latest_message=HELP_TEXT,
    )
    if validated is not None or not any(error["field"] == "can_execute" for error in errors):
        raise HelpSmallTalkSmokeError(f"Expected execution guardrail error: {errors!r}")

    spoofed = help_or_onboarding_output()
    validated, errors = help_smalltalk.validate_help_smalltalk_intent_output(
        spoofed,
        latest_message="Find Backend Developer in Ukraine with Java",
    )
    if validated is not None or not any(error["field"] == "intent" for error in errors):
        raise HelpSmallTalkSmokeError(f"Expected source-support error: {errors!r}")


async def fail_legacy_chat(*args: Any, **kwargs: Any):
    raise HelpSmallTalkSmokeError("Legacy recruiter-chat parser should not run.")


async def fail_intent(*args: Any, **kwargs: Any):
    raise HelpSmallTalkSmokeError("Broad recruiter intent classifier should not run.")


async def fail_extractor(*args: Any, **kwargs: Any):
    raise HelpSmallTalkSmokeError("Search Brief extractor should not run for help text.")


async def assert_help_resolver_runs_before_unclear_and_extractor() -> None:
    calls = {"help": 0}

    async def fake_help_smalltalk(**kwargs: Any):
        calls["help"] += 1
        if kwargs.get("latest_message") != HELP_TEXT:
            raise HelpSmallTalkSmokeError(f"Unexpected help text: {kwargs!r}")
        return help_or_onboarding_output(), None

    original_help = main.run_openai_json_help_smalltalk_intent
    original_intent = main.run_openai_json_recruiter_intent
    original_extractor = main.run_openai_json_search_brief_extractor
    original_legacy_chat = main.run_openai_json_recruiter_chat
    main.run_openai_json_help_smalltalk_intent = fake_help_smalltalk
    main.run_openai_json_recruiter_intent = fail_intent
    main.run_openai_json_search_brief_extractor = fail_extractor
    main.run_openai_json_recruiter_chat = fail_legacy_chat
    try:
        response = await main.recruiter_chat_turn_response(chat_request(HELP_TEXT))
    finally:
        main.run_openai_json_help_smalltalk_intent = original_help
        main.run_openai_json_recruiter_intent = original_intent
        main.run_openai_json_search_brief_extractor = original_extractor
        main.run_openai_json_recruiter_chat = original_legacy_chat

    if calls["help"] != 1:
        raise HelpSmallTalkSmokeError("Expected one help resolver call.")
    if response["state"] != "needs_clarification":
        raise HelpSmallTalkSmokeError(f"Expected onboarding state: {response!r}")
    if response["normalized_brief"] is not None:
        raise HelpSmallTalkSmokeError(f"Help text must not create brief: {response!r}")
    if response.get("can_build_plan"):
        raise HelpSmallTalkSmokeError(f"Help text must not build plan: {response!r}")
    if response.get("brief_changed") or response.get("stale_state_should_clear"):
        raise HelpSmallTalkSmokeError(f"Help text must not mutate state: {response!r}")
    message = response.get("assistant_message") or ""
    if "Yes, I can help." not in message:
        raise HelpSmallTalkSmokeError(f"Expected friendly help response: {response!r}")
    if "does not look like" in message:
        raise HelpSmallTalkSmokeError(f"Help text hit unclear fallback: {response!r}")
    if "tool_results" in response or "results" in response:
        raise HelpSmallTalkSmokeError("Help text must not execute search.")


async def assert_no_openai_fallback_still_handles_help() -> None:
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }
    original_extractor = main.run_openai_json_search_brief_extractor
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)
    main.run_openai_json_search_brief_extractor = fail_extractor
    try:
        response = await main.recruiter_chat_turn_response(chat_request(HELP_TEXT))
    finally:
        main.run_openai_json_search_brief_extractor = original_extractor
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    if "Yes, I can help." not in (response.get("assistant_message") or ""):
        raise HelpSmallTalkSmokeError(f"Expected deterministic help fallback: {response!r}")


async def assert_help_preserves_existing_ready_brief() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request(HELP_TEXT, draft_brief=ready_brief())
    )
    if response["state"] != "ready_for_planning":
        raise HelpSmallTalkSmokeError(f"Expected ready state preserved: {response!r}")
    if not response.get("can_build_plan"):
        raise HelpSmallTalkSmokeError(f"Expected build-plan gate preserved: {response!r}")
    if response.get("brief_changed") or response.get("stale_state_should_clear"):
        raise HelpSmallTalkSmokeError(f"Help must not clear ready brief: {response!r}")
    message = response.get("assistant_message") or ""
    if "current search summary is still ready" not in message:
        raise HelpSmallTalkSmokeError(f"Expected ready-context help response: {response!r}")


async def assert_concrete_search_still_uses_extractor() -> None:
    calls = {"help": 0, "extractor": 0}
    text = "Find Backend Developer in Ukraine with Java and Spring"

    async def unexpected_help(**kwargs: Any):
        calls["help"] += 1
        raise HelpSmallTalkSmokeError("Concrete search should not call help resolver.")

    async def fake_extractor(**kwargs: Any):
        calls["extractor"] += 1
        return raw_ready_extractor_output(text), None

    original_help = main.run_openai_json_help_smalltalk_intent
    original_extractor = main.run_openai_json_search_brief_extractor
    main.run_openai_json_help_smalltalk_intent = unexpected_help
    main.run_openai_json_search_brief_extractor = fake_extractor
    try:
        response = await main.recruiter_chat_turn_response(chat_request(text))
    finally:
        main.run_openai_json_help_smalltalk_intent = original_help
        main.run_openai_json_search_brief_extractor = original_extractor

    if calls["help"] != 0:
        raise HelpSmallTalkSmokeError("Unexpected help resolver call.")
    if calls["extractor"] != 1:
        raise HelpSmallTalkSmokeError("Expected Search Brief extractor call.")
    if response["state"] != "ready_for_planning":
        raise HelpSmallTalkSmokeError(f"Expected ready search brief: {response!r}")


async def assert_prohibited_request_still_refuses_before_help() -> None:
    calls = {"help": 0}

    async def unexpected_help(**kwargs: Any):
        calls["help"] += 1
        raise HelpSmallTalkSmokeError("Prohibited request must not call help resolver.")

    original_help = main.run_openai_json_help_smalltalk_intent
    main.run_openai_json_help_smalltalk_intent = unexpected_help
    try:
        response = await main.recruiter_chat_turn_response(
            chat_request("Can you help me scrape LinkedIn?")
        )
    finally:
        main.run_openai_json_help_smalltalk_intent = original_help

    if calls["help"] != 0:
        raise HelpSmallTalkSmokeError("Unexpected help call for prohibited request.")
    if response["state"] != "refused":
        raise HelpSmallTalkSmokeError(f"Expected refusal: {response!r}")


async def main_smoke() -> None:
    assert_prompt_contract()
    assert_trigger_scope()
    assert_validator_guardrails()
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)
    try:
        await assert_help_resolver_runs_before_unclear_and_extractor()
        await assert_no_openai_fallback_still_handles_help()
        await assert_help_preserves_existing_ready_brief()
        await assert_concrete_search_still_uses_extractor()
        await assert_prohibited_request_still_refuses_before_help()
    finally:
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    print("P9.13 help/small-talk resolver smoke passed.")


if __name__ == "__main__":
    asyncio.run(main_smoke())
