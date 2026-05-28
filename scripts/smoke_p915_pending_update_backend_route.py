from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
APP_JS = PROJECT_DIR / "app" / "static" / "app.js"


class PendingUpdateRouteSmokeError(AssertionError):
    pass


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
    raise PendingUpdateRouteSmokeError(f"Could not extract {function_name}.")


def assert_pending_update_routes_semantic_text_to_backend() -> None:
    source = APP_JS.read_text(encoding="utf-8")
    handler = extract_js_function(source, "handlePendingSearchSummaryUpdateAction")
    send_turn = extract_js_function(source, "sendChatTurn")

    old_frontend_fallback = (
        "Which field should I update: role, technology, stack, location, seniority, or depth?"
    )
    if old_frontend_fallback in handler:
        raise PendingUpdateRouteSmokeError(
            "Pending update handler must not ask the broad field question for semantic update text."
        )

    required_terms = [
        'pendingChatAction.type === "update_search_summary"',
        "updateIntent === \"restart\"",
        "updateIntent === \"cancel\"",
        "updateIntent === \"select_field\"",
        "setPendingSearchSummaryUpdateFieldAction(selectedField)",
        "pendingUpdateFieldQuestion(selectedField, responseLanguage)",
        "clearPendingChatAction();\n    updateActionState();\n    return false;",
    ]
    for term in required_terms:
        if term not in handler:
            raise PendingUpdateRouteSmokeError(f"Missing pending update routing term: {term}")

    if "markChatMessageForBackend(optimisticUserMessage);" not in send_turn:
        raise PendingUpdateRouteSmokeError(
            "sendChatTurn must mark routed semantic update text for backend history."
        )
    if "pending_update_field: pendingUpdateFieldForRequest" not in send_turn:
        raise PendingUpdateRouteSmokeError(
            "Selected-field update values must still pass pending_update_field to backend."
        )


if __name__ == "__main__":
    assert_pending_update_routes_semantic_text_to_backend()
    print("P9.15 pending update backend-route smoke passed")
