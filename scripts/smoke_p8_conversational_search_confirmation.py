import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import agent_wording, main


def extract_js_function_body(source: str, function_name: str) -> str:
    signature = f"function {function_name}"
    start = source.index(signature)
    paren_start = source.index("(", start)
    paren_depth = 0
    signature_end = -1
    for index in range(paren_start, len(source)):
        character = source[index]
        if character == "(":
            paren_depth += 1
        elif character == ")":
            paren_depth -= 1
            if paren_depth == 0:
                signature_end = index
                break
    if signature_end < 0:
        raise AssertionError(f"Could not extract {function_name} signature.")

    brace_start = source.index("{", signature_end)
    depth = 0
    for index in range(brace_start, len(source)):
        character = source[index]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return source[brace_start + 1 : index]
    raise AssertionError(f"Could not extract {function_name} body.")


def assert_frontend_confirmation_path() -> None:
    source = (PROJECT_DIR / "app" / "static" / "app.js").read_text(encoding="utf-8")
    assert "let searchConfirmationInFlight = false;" in source
    assert "function currentSearchRunConfirmationIdentity()" in source
    assert 'type: "start_search"' in source
    assert "runAction: currentRunSearchAction()" in source
    assert "executionMode: currentRunSearchExecutionMode()" in source
    assert "multiWaveEnabled: multiWaveInput.checked" in source
    assert "function pendingSearchRunConfirmationIsCurrent()" in source
    assert "SEARCH_RUN_CONFIRMATIONS" in source
    assert "SEARCH_RUN_REFINEMENTS" in source
    assert "SEARCH_RUN_AMBIGUOUS_REPLIES" in source

    send_body = extract_js_function_body(source, "sendChatTurn")
    assert "await handlePendingSearchRunChatAction(userText)" in send_body
    assert "handlePendingBuildPlanChatAction" not in send_body

    ensure_body = extract_js_function_body(source, "ensureSearchReadyForConfirmedRun")
    assert "await buildPlanFromChat({ autoPrepareRuntime: false })" in ensure_body
    assert "await prepareRuntimeSearchAction()" in ensure_body

    confirmation_body = extract_js_function_body(source, "handlePendingSearchRunChatAction")
    assert "await ensureSearchReadyForConfirmedRun()" in confirmation_body
    assert "await runStructuredSearch()" in confirmation_body
    assert 'fetch("/api/recruiter-chat/turn"' not in confirmation_body
    assert "isSearchRunAmbiguousReply(userText)" in confirmation_body
    assert "isSearchRunRefinementRequest(userText)" in confirmation_body

    run_body = extract_js_function_body(source, "runStructuredSearch")
    assert "fetch(AGENT_RUNTIME_TURN_ENDPOINT" in run_body
    assert "/api/structured-search" not in run_body
    assert "/api/structured-search/multi-wave" not in run_body

    update_action_body = extract_js_function_body(source, "updateActionState")
    assert "searchConfirmationInFlight" in update_action_body

    multi_wave_change_body = source[source.index('multiWaveInput.addEventListener("change"') :]
    assert "clearPendingChatAction();" in multi_wave_change_body
    assert "clearRuntimeApproval();" in multi_wave_change_body


def assert_recruiter_facing_agent_plan_wording() -> None:
    normalized_request = {
        "role_family": "Backend Developer",
        "technology": "Java",
        "location": "Ukraine",
        "stack": ["Spring", "Kafka"],
    }
    message = main.agent_plan_supported_message("en", normalized_request)
    lowered = message.lower()
    assert "confirm" in lowered
    assert "start the search" in lowered
    for forbidden in [
        "backend planner",
        "build plan",
        "prepare search",
        "search plan",
        "queryplan",
        "fingerprint",
        "approval",
        "run search",
    ]:
        assert forbidden not in lowered

    old_llm_message = {
        "message": (
            "I understood the Java Backend Developer search in Ukraine. "
            "Prepare search can create the details, and Run search is still required."
        ),
        "warnings": [],
        "limitations": [],
    }
    validated, reason = agent_wording.validate_agent_wording_output(
        old_llm_message,
        language="en",
        allowed_numbers=set(),
        wording_use_case=agent_wording.AGENT_WORDING_USE_CASE_AGENT_PLAN,
    )
    assert validated is None
    assert reason == "llm_output_agent_plan_disallowed_visible_content"


if __name__ == "__main__":
    assert_frontend_confirmation_path()
    assert_recruiter_facing_agent_plan_wording()
    print("P8 conversational search confirmation smoke passed")
