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


def main() -> None:
    app_js = (PROJECT_DIR / "app" / "static" / "app.js").read_text(encoding="utf-8")
    backend_main = (PROJECT_DIR / "app" / "main.py").read_text(encoding="utf-8")

    render_report_body = extract_js_function_body(app_js, "renderReport")
    forbidden_report_terms = [
        "Query contribution details",
        "contributionMarkup",
        "report.query_contribution",
        "contribution-details-list",
        "raw ${escapeHtml(item.raw)}",
        "filtered ${escapeHtml(item.filtered)}",
        "new ${escapeHtml(item.new_unique_profiles)}",
        "duplicates ${escapeHtml(item.duplicates)}",
    ]
    for term in forbidden_report_terms:
        if term in render_report_body:
            raise AssertionError(f"renderReport still exposes query contribution UI: {term}")

    if 'contributionList.innerHTML = "";' not in render_report_body:
        raise AssertionError("renderReport should clear the contribution list")

    if "<span>Detailed metrics</span>" not in render_report_body:
        raise AssertionError("Detailed aggregate metrics should remain available")

    if "reportStatus.textContent" not in render_report_body or "unique" not in render_report_body:
        raise AssertionError("Compact unique-candidate report summary should remain")

    if '"query_contribution": query_contribution' not in backend_main:
        raise AssertionError("Backend report query_contribution field should remain")

    if "query_contribution: list[dict] = []" not in backend_main:
        raise AssertionError("Backend query contribution collection should remain")


if __name__ == "__main__":
    main()
    print("P8 query contribution hidden smoke passed")
