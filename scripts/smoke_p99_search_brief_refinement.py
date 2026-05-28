import asyncio
import os
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main, search_brief_refinement as refinement
from app.brief_patch import (
    BRIEF_PATCH_ADD_STACK,
    BRIEF_PATCH_RECONFIRM_FIELD,
    BRIEF_PATCH_REMOVE_MUST_HAVE,
    BRIEF_PATCH_REPLACE_STACK,
    BRIEF_PATCH_SET_LOCATION,
)


class RefinementSmokeError(AssertionError):
    pass


LLM_CALLS: list[str] = []
LEGACY_CALLS: list[str] = []


def ready_brief(
    *,
    role_family: str = "Backend Developer",
    technology: str = "Java",
    stack: list[str] | None = None,
    location: str = "Ukraine",
    must_have: list[str] | None = None,
) -> main.SearchBrief:
    selected_stack = stack or ["Spring", "Kafka"]
    selected_must_have = must_have or ["Java", "banking"]
    return main.SearchBrief(
        source_text="Find candidates.",
        brief_status="ready_for_planning",
        role_family=role_family,
        technology=technology,
        stack=selected_stack,
        location=location,
        seniority=None,
        must_have=selected_must_have,
        nice_to_have=selected_stack,
        exclusions=[],
        search_depth="standard",
        profile_sources=["linkedin_public"],
        assumptions=[],
    )


def chat_request(text: str, draft_brief: main.SearchBrief | None = None) -> main.RecruiterChatTurnRequest:
    return main.RecruiterChatTurnRequest(
        language="en",
        draft_brief=draft_brief or ready_brief(),
        messages=[main.RecruiterChatMessage(role="user", content=text)],
    )


def raw_refinement(
    *,
    text: str,
    intent: str = "patch",
    operations: list[dict[str, Any]] | None = None,
    confidence: str = "high",
) -> dict[str, Any]:
    return {
        "schema_version": refinement.SEARCH_BRIEF_REFINEMENT_PROMPT_VERSION,
        "intent": intent,
        "operations": operations or [],
        "confidence": confidence,
        "reason_codes": ["smoke_fixture"],
    }


FIXTURES: dict[str, dict[str, Any]] = {
    "change location to Canada": raw_refinement(
        text="change location to Canada",
        operations=[
            {
                "operation": BRIEF_PATCH_SET_LOCATION,
                "field": "location",
                "value": "Canada",
            }
        ],
    ),
    "Java only": raw_refinement(
        text="Java only",
        operations=[
            {
                "operation": BRIEF_PATCH_REPLACE_STACK,
                "field": "stack",
                "values": ["Java"],
            }
        ],
    ),
    "add Selenium": raw_refinement(
        text="add Selenium",
        operations=[
            {
                "operation": BRIEF_PATCH_ADD_STACK,
                "field": "stack",
                "value": "Selenium",
            }
        ],
    ),
    "remove banking": raw_refinement(
        text="remove banking",
        operations=[
            {
                "operation": BRIEF_PATCH_REMOVE_MUST_HAVE,
                "field": "must_have",
                "value": "banking",
            }
        ],
    ),
    "I meant QA, not developer": raw_refinement(
        text="I meant QA, not developer",
        operations=[
            {
                "operation": BRIEF_PATCH_RECONFIRM_FIELD,
                "field": "role_family",
                "value": "QA Automation",
            }
        ],
    ),
    "make it remote": raw_refinement(
        text="make it remote",
        operations=[
            {
                "operation": BRIEF_PATCH_SET_LOCATION,
                "field": "location",
                "value": "Remote",
            }
        ],
    ),
    "make it confidential": raw_refinement(
        text="make it confidential",
        intent="unsafe",
        operations=[],
    ),
    "change something": {
        "schema_version": refinement.SEARCH_BRIEF_REFINEMENT_PROMPT_VERSION,
        "intent": "patch",
        "operations": [
            {
                "operation": "rewrite_everything",
                "field": "search_brief",
                "value": "unsafe",
            }
        ],
        "confidence": "high",
        "reason_codes": ["invalid_fixture"],
    },
}


async def fake_refinement_interpreter(**kwargs: Any) -> tuple[dict[str, Any] | None, str | None]:
    text = kwargs["latest_message"]
    LLM_CALLS.append(text)
    if text not in FIXTURES:
        raise RefinementSmokeError(f"Unexpected refinement fixture: {text!r}")
    return FIXTURES[text], None


async def forbidden_legacy_chat(request: main.RecruiterChatTurnRequest):
    LEGACY_CALLS.append(request.messages[-1].content)
    raise RefinementSmokeError("Legacy recruiter chat parser must not handle general refinements.")


async def run_case(
    text: str,
    *,
    expected_field: str,
    expected_value: Any,
    draft_brief: main.SearchBrief | None = None,
) -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request(text, draft_brief=draft_brief)
    )
    if response["ok"] is not True:
        raise RefinementSmokeError(f"{text}: expected ok response, got {response}")
    normalized_brief = response["normalized_brief"]
    if normalized_brief.get(expected_field) != expected_value:
        raise RefinementSmokeError(
            f"{text}: expected {expected_field}={expected_value!r}, got {normalized_brief.get(expected_field)!r}"
        )
    if response.get("brief_changed") is not True:
        raise RefinementSmokeError(f"{text}: expected brief_changed true.")


async def run_no_mutation_case(text: str) -> None:
    original_brief = ready_brief()
    response = await main.recruiter_chat_turn_response(
        chat_request(text, draft_brief=original_brief)
    )
    normalized_brief = response["normalized_brief"]
    if normalized_brief["role_family"] != original_brief.role_family:
        raise RefinementSmokeError(f"{text}: role changed unexpectedly.")
    if normalized_brief["technology"] != original_brief.technology:
        raise RefinementSmokeError(f"{text}: technology changed unexpectedly.")
    if normalized_brief["stack"] != original_brief.stack:
        raise RefinementSmokeError(f"{text}: stack changed unexpectedly.")
    if normalized_brief["location"] != original_brief.location:
        raise RefinementSmokeError(f"{text}: location changed unexpectedly.")
    if response.get("brief_changed") is True:
        raise RefinementSmokeError(f"{text}: expected no brief mutation.")


async def run_smoke() -> None:
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }
    original_refinement = main.run_openai_json_search_brief_refinement_interpreter
    original_legacy = main.run_openai_json_recruiter_chat
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)
    main.run_openai_json_search_brief_refinement_interpreter = fake_refinement_interpreter
    main.run_openai_json_recruiter_chat = forbidden_legacy_chat
    try:
        await run_case(
            "change location to Canada",
            expected_field="location",
            expected_value="Canada",
        )
        await run_case(
            "Java only",
            expected_field="stack",
            expected_value=["Java"],
        )
        await run_case(
            "add Selenium",
            expected_field="stack",
            expected_value=["Spring", "Kafka", "Selenium"],
        )
        await run_case(
            "remove banking",
            expected_field="must_have",
            expected_value=["Java"],
        )
        await run_case(
            "I meant QA, not developer",
            expected_field="role_family",
            expected_value="QA Automation",
        )
        await run_case(
            "make it remote",
            expected_field="location",
            expected_value="Remote",
        )
        await run_no_mutation_case("make it confidential")
        await run_no_mutation_case("change something")
    finally:
        main.run_openai_json_search_brief_refinement_interpreter = original_refinement
        main.run_openai_json_recruiter_chat = original_legacy
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    if LEGACY_CALLS:
        raise RefinementSmokeError(f"Legacy parser was called: {LEGACY_CALLS!r}")
    if len(LLM_CALLS) != 8:
        raise RefinementSmokeError(f"Expected 8 refinement interpreter calls, got {len(LLM_CALLS)}.")
    print("P9.9 Search Brief refinement smoke passed")


if __name__ == "__main__":
    asyncio.run(run_smoke())
