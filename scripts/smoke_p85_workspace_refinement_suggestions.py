from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_JS = REPO_ROOT / "app" / "static" / "app.js"
WORKSPACE_JS = REPO_ROOT / "app" / "static" / "candidate_workspace.js"
STYLES_CSS = REPO_ROOT / "app" / "static" / "styles.css"
CHECK_ALL = REPO_ROOT / "scripts" / "check_all.ps1"


def node_executable() -> str:
    configured = os.environ.get("NODE_EXE")
    if configured:
        return configured
    bundled = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "bin"
        / "node.exe"
    )
    if bundled.exists():
        return str(bundled)
    return "node"


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


def run_node_helper_check() -> dict:
    workspace_path = str(WORKSPACE_JS).replace("\\", "\\\\")
    script = f"""
require("{workspace_path}");
const cw = globalThis.CandidateWorkspace;
if (!cw || typeof cw.buildWorkspaceRefinementSuggestions !== "function") {{
  throw new Error("missing buildWorkspaceRefinementSuggestions");
}}

const raw = [
  {{
    normalized_url: "https://www.linkedin.com/in/strong",
    quality_score: 91,
    current_location_status: "target_location",
    stack_fit: "confirmed",
    selected_stack_terms_found: ["Spring", "Kafka"],
    result: {{
      name: "Strong Candidate",
      headline: "Senior Java Backend Developer",
      url: "https://www.linkedin.com/in/strong",
      role_display: "Backend Developer",
      role_fit: "target_or_close_role",
      technology_display: "Java",
      technology_fit: "exact",
      stack_evidence: [{{ term: "Spring", source: "snippet" }}],
      current_location_status: "target_location",
    }},
  }},
  {{
    normalized_url: "https://www.linkedin.com/in/stack-review",
    quality_score: 73,
    current_location_status: "target_location",
    stack_fit: "query_source_only",
    review_flag_details: [{{ code: "stack_query_source_only", label: "Stack query source only", severity: "medium" }}],
    result: {{
      name: "Stack Review Candidate",
      headline: "Java Software Engineer",
      url: "https://www.linkedin.com/in/stack-review",
      role_display: "Java Software Engineer",
      role_fit: "target_or_close_role",
      technology_display: "Java",
      technology_fit: "exact",
      current_location_status: "target_location",
    }},
  }},
  {{
    normalized_url: "https://www.linkedin.com/in/location-review",
    quality_score: 67,
    current_location_status: "unknown_current_location",
    stack_fit: "not_visible",
    result: {{
      name: "Location Review Candidate",
      headline: "Java Developer",
      url: "https://www.linkedin.com/in/location-review",
      role_display: "Java Developer",
      role_fit: "target_or_close_role",
      technology_display: "Java",
      technology_fit: "exact",
      current_location_status: "unknown_current_location",
    }},
  }},
  {{
    normalized_url: "https://www.linkedin.com/in/rejected",
    quality_score: 82,
    current_location_status: "target_location",
    stack_fit: "confirmed",
    selected_stack_terms_found: ["Spring"],
    result: {{
      name: "Rejected Candidate",
      headline: "Java Backend Developer",
      url: "https://www.linkedin.com/in/rejected",
      role_display: "Backend Developer",
      role_fit: "target_or_close_role",
      technology_display: "Java",
      technology_fit: "exact",
      current_location_status: "target_location",
    }},
  }},
];

const candidates = cw.mapDedupedResultsToWorkspaceCandidates(raw);
const reviewState = cw.createReviewStateForCandidates(candidates);
reviewState[candidates[0].candidate_id] = {{ ...reviewState[candidates[0].candidate_id], status: cw.REVIEW_STATUSES.SHORTLISTED, note: "private recruiter note" }};
reviewState[candidates[3].candidate_id] = {{ ...reviewState[candidates[3].candidate_id], status: cw.REVIEW_STATUSES.NOT_A_FIT, note: "rejected private note" }};

const guidance = cw.buildWorkspaceRefinementSuggestions(candidates, reviewState, {{
  limit: 5,
  scope: "visible_candidates",
}});
const emptyGuidance = cw.buildWorkspaceRefinementSuggestions([], {{}}, {{
  limit: 3,
  scope: "all_candidates",
}});

console.log(JSON.stringify({{ guidance, emptyGuidance }}));
"""
    completed = subprocess.run(
        [node_executable(), "-e", script],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def assert_helper_behavior() -> None:
    payload = run_node_helper_check()
    guidance = payload["guidance"]
    empty_guidance = payload["emptyGuidance"]

    assert guidance["version"] == "workspace_refinement_suggestions_v1"
    assert guidance["source"] == "deterministic_workspace_facts"
    assert guidance["scope"] == "visible_candidates"
    assert guidance["candidates_analyzed"] == 4
    assert guidance["stats"]["visible_candidates"] == 4
    assert guidance["stats"]["shortlisted"] == 1
    assert guidance["stats"]["not_a_fit"] == 1
    assert guidance["stats"]["stack_needs_review"] == 2
    assert len(guidance["suggestions"]) >= 3

    suggestion_types = {item["suggestion_type"] for item in guidance["suggestions"]}
    assert "shortlist_for_comparison" in suggestion_types
    assert "review_strong_candidates" in suggestion_types
    assert "review_stack_visibility" in suggestion_types

    serialized = json.dumps(guidance).lower()
    for forbidden in [
        "candidate_id",
        "normalized_url",
        "profile_url",
        "linkedin.com",
        "https://",
        "/in/",
        "raw_content",
        "snippet",
        "private recruiter note",
        "rejected private note",
        "brief_patch",
        "proposed_action",
        "endpoint",
        "approve",
        "approval",
    ]:
        if forbidden in serialized:
            raise AssertionError(f"Refinement guidance leaked forbidden term: {forbidden}")

    empty_types = {item["suggestion_type"] for item in empty_guidance["suggestions"]}
    assert empty_guidance["stats"]["visible_candidates"] == 0
    assert empty_guidance["scope"] == "visible_candidates"
    assert "adjust_view" in empty_types


def assert_static_wiring() -> None:
    app_js = APP_JS.read_text(encoding="utf-8")
    workspace_js = WORKSPACE_JS.read_text(encoding="utf-8")
    styles_css = STYLES_CSS.read_text(encoding="utf-8")
    check_all = CHECK_ALL.read_text(encoding="utf-8")

    require(workspace_js, "WORKSPACE_REFINEMENT_SUGGESTIONS_VERSION", "suggestions version")
    require(workspace_js, "function buildWorkspaceRefinementSuggestions(", "suggestions helper")
    require(workspace_js, "source: \"deterministic_workspace_facts\"", "deterministic source")
    require(workspace_js, "\"visible_candidates\"", "visible scope")
    require(workspace_js, "workspaceRefinementStats", "stats helper")
    require(workspace_js, "write the exact stack requirement in chat", "manual chat wording")
    require(workspace_js, "buildWorkspaceRefinementSuggestions,", "helper export")

    require(app_js, "function renderWorkspaceRefinementSuggestions()", "UI renderer")
    require(app_js, "Based on current visible candidates.", "scope wording")
    require(app_js, "workspace-refinement-guidance", "guidance block markup")

    require(styles_css, ".workspace-refinement-grid", "guidance grid CSS")
    require(styles_css, ".workspace-refinement-card", "guidance card CSS")

    for function_name in ["buildWorkspaceRefinementSuggestions", "renderWorkspaceRefinementSuggestions"]:
        source = extract_function(workspace_js if function_name.startswith("build") else app_js, function_name)
        for forbidden in [
            "fetch(",
            "XMLHttpRequest",
            "CANDIDATE_EXPLANATION_WORDING_ENDPOINT",
            "OPENAI",
            "TAVILY",
            "localStorage",
            "sessionStorage",
            "indexedDB",
            "window.open",
            ".click(",
            ".note",
            "brief_patch",
            "proposed_action",
            "<button",
        ]:
            if forbidden in source:
                raise AssertionError(f"{function_name} must not contain {forbidden}")

    require(check_all, "scripts/smoke_p85_workspace_refinement_suggestions.py", "check_all wiring")


def main() -> None:
    assert_helper_behavior()
    assert_static_wiring()
    print("P8.5 workspace refinement suggestions smoke passed")


if __name__ == "__main__":
    main()
