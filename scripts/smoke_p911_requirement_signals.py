import asyncio
import os
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main, search_brief_extractor as extractor
from app.schemas import RecruiterChatMessage, RecruiterChatTurnRequest, SearchBrief


PROJECT_MANAGER_TEXT = (
    "I need Project Manager with banking domain experience, "
    "strong English and Excel skils"
)
PROJECT_MANAGER_REQUIREMENTS = [
    "banking domain experience",
    "strong English skills",
    "strong Excel skills",
]


class RequirementSignalError(AssertionError):
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


def raw_extractor_output(
    *,
    role_family: str,
    technology: str | None,
    stack: list[str] | None,
    location: str | None,
    must_have: list[str] | None = None,
    domain_experience: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
        "draft_brief": {
            "source_text": PROJECT_MANAGER_TEXT,
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
        "reason_codes": ["requirement_signal_fixture"],
    }


def project_manager_requirement_raw(location: str | None = None) -> dict[str, Any]:
    return raw_extractor_output(
        role_family="Project Manager",
        technology=None,
        stack=[],
        location=location,
        must_have=PROJECT_MANAGER_REQUIREMENTS,
        domain_experience=["banking domain experience"],
    )


def assert_prompt_contract_mentions_requirement_signals() -> None:
    prompt = extractor.search_brief_extractor_user_prompt(
        latest_message=PROJECT_MANAGER_TEXT,
        language="en",
    )
    if extractor.REQUIREMENT_SEARCH_SIGNAL_RESOLVER_VERSION != (
        "requirement_search_signal_resolver_v1"
    ):
        raise RequirementSignalError("Unexpected requirement resolver version.")
    for expected in (
        "primary domain/search anchor",
        "work-skill search signals",
        "Project Manager",
        "English or Excel",
    ):
        if expected not in prompt:
            raise RequirementSignalError(f"Prompt is missing {expected!r}.")


def assert_project_manager_requirements_resolve_to_search_signals() -> dict:
    validated, errors = extractor.validate_search_brief_extractor_output(
        project_manager_requirement_raw()
    )
    if errors or validated is None:
        raise RequirementSignalError(f"Expected valid project manager brief: {errors!r}")

    normalized_brief = validated["normalized_brief"]
    expected_assumption = (
        "Derived executable search signals from explicit recruiter requirements."
    )
    expected_values = {
        "brief_status": "needs_clarification",
        "role_family": "Project Manager",
        "technology": "Banking",
        "stack": ["English", "Excel"],
        "location": None,
        "missing_fields": ["location"],
        "next_question": "What target location should the search use?",
    }
    actual_values = {
        "brief_status": normalized_brief.get("brief_status"),
        "role_family": normalized_brief.get("role_family"),
        "technology": normalized_brief.get("technology"),
        "stack": normalized_brief.get("stack"),
        "location": normalized_brief.get("location"),
        "missing_fields": normalized_brief.get("missing_fields"),
        "next_question": (normalized_brief.get("clarifying_questions") or [None])[0],
    }
    if actual_values != expected_values:
        raise RequirementSignalError(
            f"Unexpected requirement resolution: {actual_values!r}"
        )
    for requirement in PROJECT_MANAGER_REQUIREMENTS:
        if requirement not in (normalized_brief.get("must_have") or []):
            raise RequirementSignalError(f"Requirement was not preserved: {requirement!r}")
    if expected_assumption not in (normalized_brief.get("assumptions") or []):
        raise RequirementSignalError("Resolver assumption was not recorded.")
    return normalized_brief


def assert_non_developer_raw_domain_technology_is_allowed() -> None:
    raw = raw_extractor_output(
        role_family="Project Manager",
        technology="Banking",
        stack=["Excel"],
        location="Ukraine",
        must_have=PROJECT_MANAGER_REQUIREMENTS,
        domain_experience=["banking domain experience"],
    )
    validated, errors = extractor.validate_search_brief_extractor_output(raw)
    if errors or validated is None:
        raise RequirementSignalError(
            f"Expected raw non-developer domain technology to pass: {errors!r}"
        )
    normalized_brief = validated["normalized_brief"]
    if normalized_brief.get("technology") != "Banking":
        raise RequirementSignalError(f"Unexpected technology: {normalized_brief!r}")
    if normalized_brief.get("brief_status") != "ready_for_planning":
        raise RequirementSignalError(f"Expected ready brief: {normalized_brief!r}")


def assert_developer_roles_do_not_resolve_requirements() -> None:
    raw = raw_extractor_output(
        role_family="Backend Developer",
        technology=None,
        stack=[],
        location="Ukraine",
        must_have=[
            "banking domain experience",
            "strong English skills",
            "strong Excel skills",
        ],
        domain_experience=["banking domain experience"],
    )
    validated, errors = extractor.validate_search_brief_extractor_output(raw)
    if errors or validated is None:
        raise RequirementSignalError(f"Expected incomplete developer brief: {errors!r}")
    normalized_brief = validated["normalized_brief"]
    if normalized_brief.get("technology") is not None:
        raise RequirementSignalError("Developer technology was inferred from domain.")
    if normalized_brief.get("stack"):
        raise RequirementSignalError("Developer stack was inferred from requirements.")
    if normalized_brief.get("missing_fields") != ["technology", "stack"]:
        raise RequirementSignalError(f"Unexpected developer missing fields: {normalized_brief!r}")


async def fail_legacy_chat(*args: Any, **kwargs: Any):
    raise RequirementSignalError("Legacy recruiter-chat parser should not run.")


async def no_live_intent(*args: Any, **kwargs: Any):
    return None, "requirement_signal_no_live_intent"


async def no_live_wording(*args: Any, **kwargs: Any):
    return None, "requirement_signal_no_live_wording"


async def assert_conversation_asks_location_then_becomes_ready() -> None:
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }
    original_extractor = main.run_openai_json_search_brief_extractor
    original_legacy_chat = main.run_openai_json_recruiter_chat
    original_intent = main.run_openai_json_recruiter_intent
    original_wording = main.run_openai_json_agent_wording

    async def fake_extractor(**kwargs: Any):
        if kwargs.get("latest_message") != PROJECT_MANAGER_TEXT:
            raise RequirementSignalError(f"Unexpected extractor text: {kwargs!r}")
        return project_manager_requirement_raw(), None

    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)
    main.run_openai_json_search_brief_extractor = fake_extractor
    main.run_openai_json_recruiter_chat = fail_legacy_chat
    main.run_openai_json_recruiter_intent = no_live_intent
    main.run_openai_json_agent_wording = no_live_wording
    try:
        first_response = await main.recruiter_chat_turn_response(
            chat_request(PROJECT_MANAGER_TEXT)
        )
        first_brief = first_response["normalized_brief"]
        if first_response["state"] != "needs_clarification":
            raise RequirementSignalError(f"Expected location clarification: {first_response!r}")
        if first_response["next_question"] != "What target location should the search use?":
            raise RequirementSignalError(f"Unexpected first question: {first_response!r}")
        if first_brief.get("technology") != "Banking":
            raise RequirementSignalError(f"Missing Banking technology: {first_brief!r}")
        if first_brief.get("stack") != ["English", "Excel"]:
            raise RequirementSignalError(f"Missing English/Excel stack: {first_brief!r}")
        first_message = (first_response.get("assistant_message") or "").lower()
        if "main technology" in first_message or "stack signals" in first_message:
            raise RequirementSignalError(f"Asked stale tech/stack question: {first_response!r}")

        second_response = await main.recruiter_chat_turn_response(
            chat_request("Ukraine", draft_brief=SearchBrief(**first_brief))
        )
        second_brief = second_response["normalized_brief"]
        if second_response["state"] != "ready_for_planning":
            raise RequirementSignalError(f"Expected ready after location: {second_response!r}")
        if second_response.get("missing_fields"):
            raise RequirementSignalError(f"Expected no missing fields: {second_response!r}")
        expected_ready_values = {
            "role_family": "Project Manager",
            "technology": "Banking",
            "stack": ["English", "Excel"],
            "location": "Ukraine",
        }
        actual_ready_values = {
            field: second_brief.get(field)
            for field in ("role_family", "technology", "stack", "location")
        }
        if actual_ready_values != expected_ready_values:
            raise RequirementSignalError(f"Unexpected ready brief: {actual_ready_values!r}")
        if not second_response.get("can_build_plan"):
            raise RequirementSignalError(f"Expected build-plan gate only: {second_response!r}")
        if "tool_results" in second_response or "results" in second_response:
            raise RequirementSignalError("Chat turn must not execute search automatically.")
        second_message = (second_response.get("assistant_message") or "").lower()
        if "main technology" in second_message or "stack signals" in second_message:
            raise RequirementSignalError(f"Asked stale tech/stack question: {second_response!r}")
    finally:
        main.run_openai_json_search_brief_extractor = original_extractor
        main.run_openai_json_recruiter_chat = original_legacy_chat
        main.run_openai_json_recruiter_intent = original_intent
        main.run_openai_json_agent_wording = original_wording
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


async def main_smoke() -> None:
    assert_prompt_contract_mentions_requirement_signals()
    assert_project_manager_requirements_resolve_to_search_signals()
    assert_non_developer_raw_domain_technology_is_allowed()
    assert_developer_roles_do_not_resolve_requirements()
    await assert_conversation_asks_location_then_becomes_ready()
    print("P9.11 requirement-to-search-signal smoke passed.")


if __name__ == "__main__":
    asyncio.run(main_smoke())
