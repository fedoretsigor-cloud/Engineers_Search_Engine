from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
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
    app_js = APP_JS.read_text(encoding="utf-8")
    styles_css = STYLES_CSS.read_text(encoding="utf-8")

    require(app_js, "let workspaceExportState = defaultWorkspaceExportState();", "current-run export state")
    require(app_js, 'scope: candidateWorkspace.normalizeExportScope("visible")', "default visible scope")
    require(app_js, 'format: candidateWorkspace.normalizeExportFormat("csv")', "default CSV format")
    require(app_js, "workspaceExportState = defaultWorkspaceExportState();", "export state reset")
    require(app_js, 'data-workspace-export-control="scope"', "export scope control")
    require(app_js, 'data-workspace-export-control="format"', "export format control")
    require(app_js, 'data-workspace-export-action="download"', "export action")
    require(app_js, 'data-workspace-export-status', "export status target")
    require(app_js, 'role="status"', "accessible status role")
    require(app_js, 'aria-live="polite"', "polite live region")
    require(app_js, 'event.target.closest("[data-workspace-export-control]")', "delegated export controls")
    require(app_js, 'event.target.closest("[data-workspace-export-action]")', "delegated export actions")
    require(app_js, "recomputeVisibleWorkspaceCandidates()", "click-time visible recompute helper")
    require(app_js, "visibleCandidates: recomputeVisibleWorkspaceCandidates()", "export model visible recompute")
    require(app_js, "candidateWorkspace.buildWorkspaceExportModel", "export model helper usage")
    require(app_js, "candidateWorkspace.serializeWorkspaceExportCsv", "CSV serializer usage")
    require(app_js, "candidateWorkspace.serializeWorkspaceExportMarkdown", "Markdown serializer usage")
    require(app_js, "candidateWorkspace.workspaceExportMimeType(format)", "MIME helper usage")
    require(app_js, "candidateWorkspace.buildWorkspaceExportFilename(exportedAt, scope, format)", "filename helper usage")
    require(app_js, "new Blob([serialized]", "local Blob download")
    require(app_js, "URL.createObjectURL(blob)", "object URL creation")
    require(app_js, "URL.revokeObjectURL(urlToRevoke)", "object URL cleanup")
    require(app_js, "temporaryAnchor.remove();", "temporary anchor cleanup")
    require(app_js, 'setWorkspaceExportStatus("No candidates to export for selected scope.")', "zero-candidate bounded status")
    require(app_js, 'setWorkspaceExportStatus("Export failed. Try again.")', "failure bounded status")
    require(app_js, "clearWorkspaceExportStatus(false);", "stale status clear without forced rerender")
    require(app_js, "candidate-workspace-export", "grouped export block markup")

    export_function = extract_function(app_js, "triggerWorkspaceExportDownload")
    forbidden_export_terms = [
        "fetch(",
        "XMLHttpRequest",
        "alert(",
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "open(",
    ]
    for term in forbidden_export_terms:
        if term in export_function:
            raise AssertionError(f"Export download function must not contain {term}")

    input_function = extract_function(app_js, "handleWorkspaceInput")
    if "renderWorkspaceResults(" in input_function:
        raise AssertionError("Note input handler must not rerender the full workspace")
    require(input_function, "clearWorkspaceExportStatus(false);", "note input stale status clear")

    require(styles_css, ".candidate-workspace-export", "export block CSS")
    require(styles_css, ".candidate-workspace-export-controls", "export controls CSS")
    require(styles_css, ".candidate-workspace-export-status", "export status CSS")
    require(styles_css, ".workspace-export-button", "export button CSS")

    print("P8 export UI wiring smoke passed")


if __name__ == "__main__":
    main()
