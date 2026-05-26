from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "app" / "static" / "index.html"
APP_JS = REPO_ROOT / "app" / "static" / "app.js"
STYLES_CSS = REPO_ROOT / "app" / "static" / "styles.css"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing {label}: {needle}")


def extract_function(text: str, name: str) -> str:
    marker = f"function {name}("
    start = text.find(marker)
    if start == -1:
        raise AssertionError(f"Missing function {name}")
    brace_start = text.find("{", start)
    if brace_start == -1:
        raise AssertionError(f"Missing function body for {name}")
    depth = 0
    for index in range(brace_start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise AssertionError(f"Could not parse function body for {name}")


def main() -> None:
    index_html = INDEX_HTML.read_text(encoding="utf-8")
    app_js = APP_JS.read_text(encoding="utf-8")
    styles_css = STYLES_CSS.read_text(encoding="utf-8")

    results_panel_index = index_html.find('class="results-panel"')
    report_panel_index = index_html.find("report-panel")
    if results_panel_index == -1 or report_panel_index == -1:
        raise AssertionError("Expected both results and report panels")
    if results_panel_index > report_panel_index:
        raise AssertionError("Candidate results panel must render before search summary")
    if 'class="report-panel recruiter-hidden-technical"' not in index_html:
        raise AssertionError("Search summary report panel should be hidden from recruiter-facing flow")

    require(index_html, "<h2>Candidate Results</h2>", "primary candidate heading")
    require(app_js, "<span>Candidate Results</span>", "candidate toolbar heading")
    require(app_js, "candidate-result-row workspace-candidate-row", "dense candidate row markup")
    require(app_js, "candidate-row-main", "candidate row main grid")
    require(app_js, "renderWorkspaceRowField", "candidate row field helper")
    require(app_js, "renderWorkspacePaginationControls", "candidate pagination controls")
    require(app_js, 'data-workspace-page-action="next"', "next page action")
    require(app_js, 'data-workspace-page-action="previous"', "previous page action")
    require(app_js, "workspaceCandidates = candidates;", "workspace source of truth")
    require(app_js, "latestWorkspaceRun = {", "workspace run source of truth")

    render_candidate = extract_function(app_js, "renderWorkspaceCandidate")
    forbidden_candidate_markup = [
        'data-workspace-action="status"',
        'data-workspace-action="shortlist"',
        'data-workspace-action="note"',
        'data-workspace-action="improve-wording"',
        "Candidate details",
        "Quality details",
        "Query sources",
        "flag-badges",
        "workspace-subtle-note",
        "candidate-row-review",
    ]
    for forbidden in forbidden_candidate_markup:
        if forbidden in render_candidate:
            raise AssertionError(f"Primary candidate row should not render {forbidden}")

    render_results = extract_function(app_js, "renderWorkspaceResults")
    forbidden_primary_blocks = [
        "renderTopCandidateRecommendation()",
        "renderWorkspaceRefinementSuggestions()",
        "renderWorkspaceExportBlock()",
    ]
    for forbidden in forbidden_primary_blocks:
        if forbidden in render_results:
            raise AssertionError(f"Primary results view should not render {forbidden}")
    require(render_results, "renderWorkspacePaginationControls", "results pagination render")

    require(styles_css, "grid-template-columns: minmax(300px, 420px) minmax(0, 1fr);", "right-dominant desktop grid")
    require(styles_css, ".candidate-result-row", "dense row CSS")
    require(styles_css, ".candidate-row-main", "row grid CSS")
    require(styles_css, ".candidate-row-field", "row field CSS")
    require(styles_css, ".candidate-workspace-page", "fixed-height results page CSS")
    require(styles_css, ".candidate-workspace-pagination", "pagination CSS")
    require(styles_css, "@media (max-width: 1180px)", "responsive stacking breakpoint")

    print("P8 candidate primary surface smoke passed")


if __name__ == "__main__":
    main()
