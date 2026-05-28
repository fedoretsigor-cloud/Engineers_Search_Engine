import asyncio
import os
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main, role_understanding
from app import search_brief_extractor as extractor
from app.schemas import RecruiterChatMessage, RecruiterChatTurnRequest


PROJECT_MANAGER_TEXT = (
    "I need Project Manager with banking domain experience and strong SQL "
    "and Excel skills in Ukraine"
)


class RoleUnderstandingSmokeError(AssertionError):
    pass


def chat_request(message: str) -> RecruiterChatTurnRequest:
    return RecruiterChatTurnRequest(
        messages=[RecruiterChatMessage(role="user", content=message)],
        language="en",
    )


def raw_extractor_output(
    *,
    text: str,
    role_family: str | None,
    technology: str | None,
    stack: list[str] | None,
    location: str | None,
    must_have: list[str] | None = None,
    domain_experience: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
        "draft_brief": {
            "source_text": text,
            "role_family": role_family,
            "role_ambiguity": {
                "is_ambiguous": False,
                "label": None,
                "options": [],
                "clarification_question": None,
            },
            "technology": technology,
            "stack": stack or [],
            "location": location,
            "seniority": None,
            "must_have": must_have or [],
            "nice_to_have": [],
            "domain_experience": domain_experience or [],
            "exclusions": [],
            "search_depth": "standard",
            "profile_sources": ["linkedin_public"],
            "notes": None,
        },
        "confidence": "high",
        "reason_codes": ["role_understanding_fixture"],
    }


def supported_project_manager_understanding() -> dict[str, Any]:
    return {
        "schema_version": role_understanding.ROLE_UNDERSTANDING_RESOLVER_VERSION,
        "role_label": "Project Manager",
        "role_domain": "it_adjacent",
        "support_status": "supported",
        "confidence": "high",
        "evidence": ["Project Manager", "SQL", "Excel"],
        "clarification_question": None,
        "reason_code": "it_adjacent_with_tool_signals",
    }


def ambiguous_project_manager_understanding() -> dict[str, Any]:
    return {
        "schema_version": role_understanding.ROLE_UNDERSTANDING_RESOLVER_VERSION,
        "role_label": "Project Manager",
        "role_domain": "ambiguous",
        "support_status": "needs_clarification",
        "confidence": "high",
        "evidence": ["Project Manager"],
        "clarification_question": "Should this be an IT/software Project Manager role?",
        "reason_code": "it_scope_unclear",
    }


def rejected_plumber_understanding() -> dict[str, Any]:
    return {
        "schema_version": role_understanding.ROLE_UNDERSTANDING_RESOLVER_VERSION,
        "role_label": "Plumber",
        "role_domain": "non_it",
        "support_status": "rejected",
        "confidence": "high",
        "evidence": ["Plumber"],
        "clarification_question": None,
        "reason_code": "non_it_role",
    }


def assert_prompt_contract() -> None:
    prompt = role_understanding.role_understanding_user_prompt(
        latest_message=PROJECT_MANAGER_TEXT,
        language="en",
        extracted_role_family="IT",
        extracted_stack=["SQL", "Excel"],
        extracted_domain_experience=["banking domain experience"],
    )
    payload = role_understanding.role_understanding_openai_payload(
        model="test-model",
        latest_message=PROJECT_MANAGER_TEXT,
        language="en",
    )
    for expected in (
        role_understanding.ROLE_UNDERSTANDING_RESOLVER_VERSION,
        "IT-adjacent",
        "latest_message only",
        "No Search Brief mutation.",
        "No query generation.",
        "No LinkedIn scraping",
    ):
        if expected not in prompt:
            raise RoleUnderstandingSmokeError(f"Role prompt is missing {expected!r}.")
    if payload.get("response_format") != {"type": "json_object"}:
        raise RoleUnderstandingSmokeError(f"Unexpected OpenAI payload: {payload!r}")


def assert_role_understanding_trigger_scope() -> None:
    project_manager = raw_extractor_output(
        text="Find Project Manager in Ukraine",
        role_family="Project Manager",
        technology=None,
        stack=[],
        location="Ukraine",
    )
    backend_developer = raw_extractor_output(
        text="Find Backend Developer in Ukraine with Java and Spring",
        role_family="Backend Developer",
        technology="Java",
        stack=["Spring"],
        location="Ukraine",
    )
    plumber = raw_extractor_output(
        text="Find Plumber in Ukraine with Excel",
        role_family="Plumber",
        technology=None,
        stack=["Excel"],
        location="Ukraine",
    )
    if not role_understanding.should_run_role_understanding_resolver(project_manager):
        raise RoleUnderstandingSmokeError("Project Manager should trigger resolver.")
    if role_understanding.should_run_role_understanding_resolver(backend_developer):
        raise RoleUnderstandingSmokeError("Backend Developer should not trigger resolver.")
    if not role_understanding.should_run_role_understanding_resolver(plumber):
        raise RoleUnderstandingSmokeError("Non-IT role should trigger resolver rejection path.")


def assert_supported_it_adjacent_role_can_recover_generic_extractor_role() -> None:
    role_result, role_errors = role_understanding.validate_role_understanding_output(
        supported_project_manager_understanding(),
        latest_message=PROJECT_MANAGER_TEXT,
    )
    if role_errors or role_result is None:
        raise RoleUnderstandingSmokeError(
            f"Expected valid role understanding: {role_errors!r}"
        )

    raw = raw_extractor_output(
        text=PROJECT_MANAGER_TEXT,
        role_family="IT",
        technology=None,
        stack=["SQL", "Excel"],
        location="Ukraine",
        must_have=["banking domain experience"],
        domain_experience=["banking domain experience"],
    )
    validated, errors = extractor.validate_search_brief_extractor_output(
        raw,
        role_understanding=role_result,
    )
    if errors or validated is None:
        raise RoleUnderstandingSmokeError(f"Expected recovered brief: {errors!r}")
    normalized_brief = validated["normalized_brief"]
    expected = {
        "brief_status": "ready_for_planning",
        "role_family": "Project Manager",
        "technology": "Banking",
        "stack": ["SQL", "Excel"],
        "location": "Ukraine",
        "missing_fields": [],
    }
    actual = {
        field: normalized_brief.get(field)
        for field in (
            "brief_status",
            "role_family",
            "technology",
            "stack",
            "location",
            "missing_fields",
        )
    }
    if actual != expected:
        raise RoleUnderstandingSmokeError(f"Unexpected recovered brief: {actual!r}")
    if validated.get("role_understanding", {}).get("resolver_version") != (
        role_understanding.ROLE_UNDERSTANDING_RESOLVER_VERSION
    ):
        raise RoleUnderstandingSmokeError("Validated result did not retain resolver metadata.")


def assert_ambiguous_it_adjacent_role_asks_role_scope() -> None:
    role_result, role_errors = role_understanding.validate_role_understanding_output(
        ambiguous_project_manager_understanding(),
        latest_message="Find Project Manager in Ukraine",
    )
    if role_errors or role_result is None:
        raise RoleUnderstandingSmokeError(
            f"Expected valid ambiguous role understanding: {role_errors!r}"
        )

    raw = raw_extractor_output(
        text="Find Project Manager in Ukraine",
        role_family="Project Manager",
        technology=None,
        stack=[],
        location="Ukraine",
    )
    validated, errors = extractor.validate_search_brief_extractor_output(
        raw,
        role_understanding=role_result,
    )
    if errors or validated is None:
        raise RoleUnderstandingSmokeError(f"Expected clarification brief: {errors!r}")
    normalized_brief = validated["normalized_brief"]
    if normalized_brief.get("brief_status") != "needs_clarification":
        raise RoleUnderstandingSmokeError(f"Expected clarification state: {normalized_brief!r}")
    if normalized_brief.get("missing_fields", [None])[0] != "role_family":
        raise RoleUnderstandingSmokeError(f"Expected role first missing field: {normalized_brief!r}")
    next_question = (normalized_brief.get("clarifying_questions") or [""])[0]
    if "IT/software Project Manager" not in next_question:
        raise RoleUnderstandingSmokeError(f"Unexpected role question: {normalized_brief!r}")


def assert_non_it_role_understanding_rejects_brief() -> None:
    role_result, role_errors = role_understanding.validate_role_understanding_output(
        rejected_plumber_understanding(),
        latest_message="Find Plumber in Ukraine with Excel",
    )
    if role_errors or role_result is None:
        raise RoleUnderstandingSmokeError(
            f"Expected valid rejected role understanding: {role_errors!r}"
        )
    raw = raw_extractor_output(
        text="Find Plumber in Ukraine with Excel",
        role_family="Plumber",
        technology=None,
        stack=["Excel"],
        location="Ukraine",
    )
    validated, errors = extractor.validate_search_brief_extractor_output(
        raw,
        role_understanding=role_result,
    )
    if validated is not None:
        raise RoleUnderstandingSmokeError(f"Expected rejected brief: {validated!r}")
    if not any(error["field"] == "role_family" for error in errors):
        raise RoleUnderstandingSmokeError(f"Expected role error: {errors!r}")


def assert_spoofed_supported_role_lacks_source_evidence() -> None:
    spoofed = supported_project_manager_understanding()
    role_result, role_errors = role_understanding.validate_role_understanding_output(
        spoofed,
        latest_message="Find Dentist in Ukraine with Excel",
    )
    if role_result is not None:
        raise RoleUnderstandingSmokeError(f"Expected spoofed role rejection: {role_result!r}")
    if not any(error["field"] == "role_label" for error in role_errors):
        raise RoleUnderstandingSmokeError(f"Expected role evidence error: {role_errors!r}")


async def fail_legacy_chat(*args: Any, **kwargs: Any):
    raise RoleUnderstandingSmokeError("Legacy recruiter-chat parser should not run.")


async def no_live_intent(*args: Any, **kwargs: Any):
    return None, "role_understanding_no_live_intent"


async def no_live_wording(*args: Any, **kwargs: Any):
    return None, "role_understanding_no_live_wording"


async def assert_conversation_uses_role_understanding_for_it_adjacent_role() -> None:
    calls = {"role_understanding": 0}

    async def fake_extractor(**kwargs: Any):
        if kwargs.get("latest_message") != PROJECT_MANAGER_TEXT:
            raise RoleUnderstandingSmokeError(f"Unexpected extractor text: {kwargs!r}")
        return raw_extractor_output(
            text=PROJECT_MANAGER_TEXT,
            role_family="IT",
            technology=None,
            stack=["SQL", "Excel"],
            location="Ukraine",
            must_have=["banking domain experience"],
            domain_experience=["banking domain experience"],
        ), None

    async def fake_role_understanding(**kwargs: Any):
        calls["role_understanding"] += 1
        if kwargs.get("latest_message") != PROJECT_MANAGER_TEXT:
            raise RoleUnderstandingSmokeError(f"Unexpected role text: {kwargs!r}")
        return supported_project_manager_understanding(), None

    original_extractor = main.run_openai_json_search_brief_extractor
    original_role_understanding = main.run_openai_json_role_understanding
    main.run_openai_json_search_brief_extractor = fake_extractor
    main.run_openai_json_role_understanding = fake_role_understanding
    try:
        response = await main.recruiter_chat_turn_response(chat_request(PROJECT_MANAGER_TEXT))
    finally:
        main.run_openai_json_search_brief_extractor = original_extractor
        main.run_openai_json_role_understanding = original_role_understanding

    if calls["role_understanding"] != 1:
        raise RoleUnderstandingSmokeError("Expected one role-understanding call.")
    normalized_brief = response["normalized_brief"]
    if response["state"] != "ready_for_planning":
        raise RoleUnderstandingSmokeError(f"Expected ready state: {response!r}")
    expected = {
        "role_family": "Project Manager",
        "technology": "Banking",
        "stack": ["SQL", "Excel"],
        "location": "Ukraine",
    }
    actual = {field: normalized_brief.get(field) for field in expected}
    if actual != expected:
        raise RoleUnderstandingSmokeError(f"Unexpected ready brief: {actual!r}")
    if "tool_results" in response or "results" in response:
        raise RoleUnderstandingSmokeError("Chat turn must not execute search automatically.")


async def assert_generic_project_manager_conversation_asks_role_scope() -> None:
    message = "Find Project Manager in Ukraine"

    async def fake_extractor(**kwargs: Any):
        return raw_extractor_output(
            text=message,
            role_family="Project Manager",
            technology=None,
            stack=[],
            location="Ukraine",
        ), None

    async def fake_role_understanding(**kwargs: Any):
        return ambiguous_project_manager_understanding(), None

    original_extractor = main.run_openai_json_search_brief_extractor
    original_role_understanding = main.run_openai_json_role_understanding
    main.run_openai_json_search_brief_extractor = fake_extractor
    main.run_openai_json_role_understanding = fake_role_understanding
    try:
        response = await main.recruiter_chat_turn_response(chat_request(message))
    finally:
        main.run_openai_json_search_brief_extractor = original_extractor
        main.run_openai_json_role_understanding = original_role_understanding

    if response["state"] != "needs_clarification":
        raise RoleUnderstandingSmokeError(f"Expected role clarification: {response!r}")
    if "IT/software Project Manager" not in (response.get("next_question") or ""):
        raise RoleUnderstandingSmokeError(f"Unexpected next question: {response!r}")
    if response.get("can_build_plan"):
        raise RoleUnderstandingSmokeError(f"Ambiguous role should not build plan: {response!r}")


async def assert_standard_it_role_skips_role_understanding() -> None:
    calls = {"role_understanding": 0}

    async def fake_extractor(**kwargs: Any):
        return raw_extractor_output(
            text="Find Backend Developer in Ukraine with Java and Spring",
            role_family="Backend Developer",
            technology="Java",
            stack=["Spring"],
            location="Ukraine",
        ), None

    async def unexpected_role_understanding(**kwargs: Any):
        calls["role_understanding"] += 1
        raise RoleUnderstandingSmokeError("Backend Developer should skip role resolver.")

    original_extractor = main.run_openai_json_search_brief_extractor
    original_role_understanding = main.run_openai_json_role_understanding
    main.run_openai_json_search_brief_extractor = fake_extractor
    main.run_openai_json_role_understanding = unexpected_role_understanding
    try:
        response = await main.recruiter_chat_turn_response(
            chat_request("Find Backend Developer in Ukraine with Java and Spring")
        )
    finally:
        main.run_openai_json_search_brief_extractor = original_extractor
        main.run_openai_json_role_understanding = original_role_understanding

    if calls["role_understanding"] != 0:
        raise RoleUnderstandingSmokeError("Unexpected role-understanding call.")
    if response["state"] != "ready_for_planning":
        raise RoleUnderstandingSmokeError(f"Expected ready developer brief: {response!r}")


async def assert_conversation_paths() -> None:
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }
    original_legacy_chat = main.run_openai_json_recruiter_chat
    original_intent = main.run_openai_json_recruiter_intent
    original_wording = main.run_openai_json_agent_wording

    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)
    main.run_openai_json_recruiter_chat = fail_legacy_chat
    main.run_openai_json_recruiter_intent = no_live_intent
    main.run_openai_json_agent_wording = no_live_wording
    try:
        await assert_conversation_uses_role_understanding_for_it_adjacent_role()
        await assert_generic_project_manager_conversation_asks_role_scope()
        await assert_standard_it_role_skips_role_understanding()
    finally:
        main.run_openai_json_recruiter_chat = original_legacy_chat
        main.run_openai_json_recruiter_intent = original_intent
        main.run_openai_json_agent_wording = original_wording
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


async def main_smoke() -> None:
    assert_prompt_contract()
    assert_role_understanding_trigger_scope()
    assert_supported_it_adjacent_role_can_recover_generic_extractor_role()
    assert_ambiguous_it_adjacent_role_asks_role_scope()
    assert_non_it_role_understanding_rejects_brief()
    assert_spoofed_supported_role_lacks_source_evidence()
    await assert_conversation_paths()
    print("P9.12 role understanding smoke passed.")


if __name__ == "__main__":
    asyncio.run(main_smoke())
