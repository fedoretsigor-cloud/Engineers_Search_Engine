from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


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


def run_smoke() -> None:
    html = (PROJECT_DIR / "app" / "static" / "index.html").read_text(encoding="utf-8")
    source = (PROJECT_DIR / "app" / "static" / "app.js").read_text(encoding="utf-8")

    assert (
        '<input id="multi-wave-enabled" name="multiWaveEnabled" type="checkbox" checked />'
        in html
    )
    assert "const DEFAULT_MULTI_WAVE_ENABLED = true;" in source

    reset_body = extract_js_function_body(source, "resetChat")
    assert "multiWaveInput.checked = DEFAULT_MULTI_WAVE_ENABLED;" in reset_body

    current_action_body = extract_js_function_body(source, "currentRunSearchAction")
    assert "AGENT_ACTION_RUN_MULTI_WAVE" in current_action_body
    assert "AGENT_ACTION_RUN_SINGLE_WAVE" in current_action_body
    assert "multiWaveInput.checked" in current_action_body

    runtime_context_body = extract_js_function_body(source, "buildRuntimeContext")
    assert "tool_name: currentRunSearchAction()" in runtime_context_body
    assert "execution_mode: currentRunSearchExecutionMode()" in runtime_context_body
    assert "multi_wave_enabled: multiWaveInput.checked" in runtime_context_body
    assert "...MULTI_WAVE_DEFAULTS" in runtime_context_body

    runtime_input_body = extract_js_function_body(source, "buildRuntimeToolInput")
    assert "...MULTI_WAVE_DEFAULTS" in runtime_input_body

    confirmation_identity_body = extract_js_function_body(
        source,
        "currentSearchRunConfirmationIdentity",
    )
    assert "runAction: currentRunSearchAction()" in confirmation_identity_body
    assert "executionMode: currentRunSearchExecutionMode()" in confirmation_identity_body
    assert "multiWaveEnabled: multiWaveInput.checked" in confirmation_identity_body

    multi_wave_change_body = source[source.index('multiWaveInput.addEventListener("change"') :]
    assert "clearPendingChatAction();" in multi_wave_change_body
    assert "clearRuntimeApproval();" in multi_wave_change_body
    assert "void prepareRuntimeSearchAction();" in multi_wave_change_body


if __name__ == "__main__":
    run_smoke()
    print("P8 multi-wave default smoke passed")
