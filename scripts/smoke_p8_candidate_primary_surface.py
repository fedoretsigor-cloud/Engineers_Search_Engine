from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "app" / "static" / "index.html"
APP_JS = REPO_ROOT / "app" / "static" / "app.js"
STYLES_CSS = REPO_ROOT / "app" / "static" / "styles.css"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing {label}: {needle}")


def main() -> None:
    index_html = INDEX_HTML.read_text(encoding="utf-8")
    app_js = APP_JS.read_text(encoding="utf-8")
    styles_css = STYLES_CSS.read_text(encoding="utf-8")

    results_panel_index = index_html.find('class="results-panel"')
    report_panel_index = index_html.find('class="report-panel"')
    if results_panel_index == -1 or report_panel_index == -1:
        raise AssertionError("Expected both results and report panels")
    if results_panel_index > report_panel_index:
        raise AssertionError("Candidate results panel must render before search summary")

    require(index_html, "<h2>Candidate Results</h2>", "primary candidate heading")
    require(app_js, "<span>Candidate Results</span>", "candidate toolbar heading")
    require(app_js, "candidate-result-row workspace-candidate-row", "dense candidate row markup")
    require(app_js, "candidate-row-main", "candidate row main grid")
    require(app_js, "renderWorkspaceRowField", "candidate row field helper")
    require(app_js, 'data-workspace-action="status"', "review status control")
    require(app_js, 'data-workspace-action="shortlist"', "shortlist control")
    require(app_js, 'data-workspace-action="note"', "notes control")
    require(app_js, 'data-workspace-action="improve-wording"', "wording control")
    require(app_js, 'data-workspace-export-action="download"', "export control")
    require(app_js, "workspaceCandidates = candidates;", "workspace source of truth")
    require(app_js, "latestWorkspaceRun = {", "workspace run source of truth")

    require(styles_css, "grid-template-columns: minmax(360px, 0.5fr) minmax(620px, 1fr);", "candidate-favoring desktop grid")
    require(styles_css, ".candidate-result-row", "dense row CSS")
    require(styles_css, ".candidate-row-main", "row grid CSS")
    require(styles_css, ".candidate-row-field", "row field CSS")
    require(styles_css, ".candidate-row-review", "row review CSS")
    require(styles_css, ".candidate-notes-details .workspace-note", "collapsed notes CSS")
    require(styles_css, "@media (max-width: 1180px)", "responsive stacking breakpoint")

    print("P8 candidate primary surface smoke passed")


if __name__ == "__main__":
    main()
