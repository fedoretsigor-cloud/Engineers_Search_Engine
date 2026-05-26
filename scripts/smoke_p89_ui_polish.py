from __future__ import annotations

from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
APP_JS = PROJECT_DIR / "app" / "static" / "app.js"
STYLES_CSS = PROJECT_DIR / "app" / "static" / "styles.css"
WORKSPACE_JS = PROJECT_DIR / "app" / "static" / "candidate_workspace.js"


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


def main() -> None:
    app_js = APP_JS.read_text(encoding="utf-8")
    styles_css = STYLES_CSS.read_text(encoding="utf-8")
    workspace_js = WORKSPACE_JS.read_text(encoding="utf-8")

    append_reply = extract_js_function(app_js, "appendSearchConfirmationReply")
    if "clearAssistantThinkingMessage();" not in append_reply:
        raise AssertionError("Search confirmation replies must clear transient thinking first.")

    send_turn = extract_js_function(app_js, "sendChatTurn")
    if "appendOutgoingUserMessage" not in send_turn or "appendAssistantThinkingMessage" not in send_turn:
        raise AssertionError("Chat turn must keep immediate user echo plus bounded thinking state.")
    if "chatMessagesForBackend()" not in send_turn:
        raise AssertionError("Chat turn should still use sanitized backend history.")

    backend_history = extract_js_function(app_js, "chatMessagesForBackend")
    if "localOnly" not in backend_history:
        raise AssertionError("Transient/local chat messages must stay out of backend history.")

    if "sort_mode: SORT_MODES.QUALITY_DESC" not in workspace_js:
        raise AssertionError("Candidate Results should default to score-desc ordering.")

    required_app_terms = [
        "renderWorkspaceCandidateTable",
        "candidate-results-table",
        "candidate-score-table-pill",
        "workspaceCandidateStatus",
    ]
    for term in required_app_terms:
        if term not in app_js:
            raise AssertionError(f"Missing table UI term: {term}")

    required_css_terms = [
        ".candidate-results-table",
        ".candidate-score-table-pill",
        "align-items: stretch;",
        "height: 100%;",
        "min-height: 0;",
        "nth-child(even)",
    ]
    for term in required_css_terms:
        if term not in styles_css:
            raise AssertionError(f"Missing UI polish CSS term: {term}")


if __name__ == "__main__":
    main()
    print("P8.9 UI polish smoke passed")
