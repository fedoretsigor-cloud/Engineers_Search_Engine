import asyncio
import os
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main


APP_JS = PROJECT_DIR / "app" / "static" / "app.js"
INDEX_HTML = PROJECT_DIR / "app" / "static" / "index.html"
STYLES_CSS = PROJECT_DIR / "app" / "static" / "styles.css"


def extract_js_function(source: str, function_name: str) -> str:
    signature = f"function {function_name}"
    start = source.index(signature)
    brace_start = source.index("{", start)
    depth = 0
    for index in range(brace_start, len(source)):
        character = source[index]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"Could not extract {function_name}.")


def missing_stack_brief() -> main.SearchBrief:
    return main.SearchBrief(
        source_text="I need QA Automation in Spain with Java.",
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


def chat_request(text: str, draft_brief: main.SearchBrief | None = None) -> main.RecruiterChatTurnRequest:
    return main.RecruiterChatTurnRequest(
        language="en",
        draft_brief=draft_brief,
        messages=[main.RecruiterChatMessage(role="user", content=text)],
    )


def assert_frontend_phase_96_contract() -> None:
    app_js = APP_JS.read_text(encoding="utf-8")
    index_html = INDEX_HTML.read_text(encoding="utf-8")
    styles_css = STYLES_CSS.read_text(encoding="utf-8")

    candidate_row = extract_js_function(app_js, "renderWorkspaceCandidate")
    candidate_table = extract_js_function(app_js, "renderWorkspaceCandidateTable")
    render_chat_messages = extract_js_function(app_js, "renderChatMessages")

    if "candidate-table-profile-link" not in candidate_row:
        raise AssertionError("Candidate rows must render the profile link under identity.")
    if "renderWorkspaceProfileLink(candidate)" not in candidate_row:
        raise AssertionError("Candidate rows must use the existing safe profile link renderer.")
    if "location_status" in candidate_row:
        raise AssertionError("Primary Candidate Results row must not render location status column.")
    if "selectedStack" in candidate_row or "stack_fit" in candidate_row:
        raise AssertionError("Primary Candidate Results row must not render stack column.")

    for hidden_header in ["Location", "Stack"]:
        if f"<th scope=\"col\">{hidden_header}</th>" in candidate_table:
            raise AssertionError(f"Primary Candidate Results table must not render {hidden_header} header.")

    for required_header in ["Score", "Name", "Role", "Source", "Status"]:
        if f"<th scope=\"col\">{required_header}</th>" not in candidate_table:
            raise AssertionError(f"Primary Candidate Results table lost {required_header} header.")

    for required_js_term in [
        "chat-messages-empty",
        "chatMessagesElement.classList.add",
        "chatMessagesElement.classList.remove",
    ]:
        if required_js_term not in render_chat_messages:
            raise AssertionError(f"Missing empty chat helper class handling: {required_js_term}")

    for required_css_term in [
        ".chat-messages-empty",
        ".chat-empty-message",
        "font-style: italic;",
        ".chat-form textarea",
        "min-height: 208px;",
        ".chat-form .actions button",
        "min-height: 34px;",
        ".candidate-table-profile-link",
        "min-width: 720px;",
    ]:
        if required_css_term not in styles_css:
            raise AssertionError(f"Missing Phase 9.6 CSS term: {required_css_term}")

    if 'rows="8"' not in index_html:
        raise AssertionError("Recruiter Chat textarea should expose a taller default row count.")


async def assert_pending_stack_java_is_accepted_without_llm() -> None:
    original_stack_classifier = main.run_openai_json_stack_signal_classifier

    async def fail_if_called(terms: list[str], current_brief: Any = None) -> tuple[dict | None, str | None]:
        raise AssertionError("Known stack/technology terms should not require LLM fallback.")

    main.run_openai_json_stack_signal_classifier = fail_if_called
    try:
        response = await main.recruiter_chat_turn_response(
            chat_request("Java", draft_brief=missing_stack_brief())
        )
    finally:
        main.run_openai_json_stack_signal_classifier = original_stack_classifier

    assert response["ok"] is True, response
    assert response["state"] == "ready_for_planning", response
    assert response["normalized_brief"]["stack"] == ["Java"], response
    assert response["can_build_plan"] is True, response


async def assert_non_hardcoded_stack_can_be_accepted_by_bounded_llm() -> None:
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }
    original_stack_classifier = main.run_openai_json_stack_signal_classifier
    calls: list[list[str]] = []

    async def fake_stack_classifier(
        terms: list[str],
        current_brief: Any = None,
    ) -> tuple[dict | None, str | None]:
        calls.append(terms)
        return {
            "accepted_terms": [
                {
                    "input": "Playwright",
                    "normalized": "Playwright",
                    "reason_code": "qa_tool",
                },
                {
                    "input": "Selenium",
                    "normalized": "Selenium",
                    "reason_code": "qa_tool",
                },
            ],
            "rejected_terms": [],
            "confidence": "high",
        }, None

    os.environ["OPENAI_API_KEY"] = "fake-openai-key"
    os.environ["OPENAI_MODEL"] = "fake-model"
    main.run_openai_json_stack_signal_classifier = fake_stack_classifier
    try:
        response = await main.recruiter_chat_turn_response(
            chat_request("Playwright and Selenium", draft_brief=missing_stack_brief())
        )
    finally:
        main.run_openai_json_stack_signal_classifier = original_stack_classifier
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert calls == [["Playwright", "Selenium"]], calls
    assert response["ok"] is True, response
    assert response["state"] == "ready_for_planning", response
    assert response["normalized_brief"]["stack"] == ["Playwright", "Selenium"], response


async def assert_invalid_stack_terms_are_rejected_safely() -> None:
    original_stack_classifier = main.run_openai_json_stack_signal_classifier

    async def fake_rejecting_stack_classifier(
        terms: list[str],
        current_brief: Any = None,
    ) -> tuple[dict | None, str | None]:
        return {
            "accepted_terms": [],
            "rejected_terms": [{"input": terms[0], "reason_code": "non_it"}],
            "confidence": "high",
        }, None

    main.run_openai_json_stack_signal_classifier = fake_rejecting_stack_classifier
    try:
        response = await main.recruiter_chat_turn_response(
            chat_request("banana", draft_brief=missing_stack_brief())
        )
    finally:
        main.run_openai_json_stack_signal_classifier = original_stack_classifier

    assert response["state"] == "needs_clarification", response
    assert response["can_build_plan"] is False, response
    assert response["normalized_brief"]["stack"] == [], response
    assert "English IT/software stack signal" in response["assistant_message"], response


async def assert_llm_unavailable_fallback_is_safe() -> None:
    original_stack_classifier = main.run_openai_json_stack_signal_classifier

    async def fake_unavailable_stack_classifier(
        terms: list[str],
        current_brief: Any = None,
    ) -> tuple[dict | None, str | None]:
        return None, "openai_not_configured"

    main.run_openai_json_stack_signal_classifier = fake_unavailable_stack_classifier
    try:
        response = await main.recruiter_chat_turn_response(
            chat_request("Playwright", draft_brief=missing_stack_brief())
        )
    finally:
        main.run_openai_json_stack_signal_classifier = original_stack_classifier

    assert response["state"] == "needs_clarification", response
    assert response["can_build_plan"] is False, response
    assert response["normalized_brief"]["stack"] == [], response
    assert "English IT/software stack signal" in response["assistant_message"], response


async def assert_cyrillic_stack_is_still_rejected() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("РґР¶Р°РІР°", draft_brief=missing_stack_brief())
    )
    assert response["ok"] is False, response
    assert any("English input only" in error["message"] for error in response["validation_errors"]), response


async def assert_pending_location_spain_is_accepted() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("Spain", draft_brief=missing_location_brief())
    )
    assert response["ok"] is True, response
    assert response["state"] == "ready_for_planning", response
    assert response["normalized_brief"]["location"] == "Spain", response
    assert response["can_build_plan"] is True, response


async def assert_pending_location_remote_is_accepted() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("Remote", draft_brief=missing_location_brief())
    )
    assert response["ok"] is True, response
    assert response["state"] == "ready_for_planning", response
    assert response["normalized_brief"]["location"] == "Remote", response
    assert response["can_build_plan"] is True, response


async def assert_pending_location_prefixed_city_is_accepted() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("location is Madrid", draft_brief=missing_location_brief())
    )
    assert response["ok"] is True, response
    assert response["state"] == "ready_for_planning", response
    assert response["normalized_brief"]["location"] == "Madrid", response


async def assert_pending_location_java_is_rejected() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("Java", draft_brief=missing_location_brief())
    )
    assert response["state"] == "needs_clarification", response
    assert response["can_build_plan"] is False, response
    assert response["normalized_brief"]["location"] is None, response
    assert "English target location" in response["assistant_message"], response
    assert "current baseline" not in response["assistant_message"], response


async def assert_pending_location_role_is_rejected() -> None:
    response = await main.recruiter_chat_turn_response(
        chat_request("QA Automation", draft_brief=missing_location_brief())
    )
    assert response["state"] == "needs_clarification", response
    assert response["can_build_plan"] is False, response
    assert response["normalized_brief"]["location"] is None, response


async def main_smoke() -> None:
    assert_frontend_phase_96_contract()
    await assert_pending_stack_java_is_accepted_without_llm()
    await assert_non_hardcoded_stack_can_be_accepted_by_bounded_llm()
    await assert_invalid_stack_terms_are_rejected_safely()
    await assert_llm_unavailable_fallback_is_safe()
    await assert_cyrillic_stack_is_still_rejected()
    await assert_pending_location_spain_is_accepted()
    await assert_pending_location_remote_is_accepted()
    await assert_pending_location_prefixed_city_is_accepted()
    await assert_pending_location_java_is_rejected()
    await assert_pending_location_role_is_rejected()


if __name__ == "__main__":
    asyncio.run(main_smoke())
    print("P9.6 post-deploy polish smoke passed")
