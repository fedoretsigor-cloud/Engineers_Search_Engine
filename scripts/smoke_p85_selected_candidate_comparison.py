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
if (!cw || typeof cw.buildSelectedCandidateComparison !== "function") {{
  throw new Error("missing buildSelectedCandidateComparison");
}}

const raw = [
  {{
    normalized_url: "https://www.linkedin.com/in/strong",
    quality_score: 91,
    current_location_status: "target_location",
    stack_fit: "confirmed",
    selected_stack_terms_found: ["Spring", "Kafka"],
    query_sources: [{{ id: "Q01", category: "role_based" }}],
    result: {{
      name: "Strong Candidate",
      headline: "Senior Java Backend Developer",
      url: "https://www.linkedin.com/in/strong",
      role_display: "Backend Developer",
      role_fit: "target_or_close_role",
      technology_display: "Java",
      technology_fit: "exact",
      stack_evidence: [{{ term: "Spring", source: "snippet" }}, {{ term: "Kafka", source: "snippet" }}],
      current_location_line: "Kyiv, Ukraine",
      current_location_status: "target_location",
    }},
  }},
  {{
    normalized_url: "https://www.linkedin.com/in/review",
    quality_score: 78,
    current_location_status: "target_location",
    stack_fit: "query_source_only",
    query_sources: [{{ id: "Q02", category: "stack_focused" }}],
    review_flag_details: [{{ code: "stack_query_source_only", label: "Stack query source only", severity: "medium" }}],
    result: {{
      name: "Review Candidate",
      headline: "Java Software Engineer",
      url: "https://www.linkedin.com/in/review",
      role_display: "Java Software Engineer",
      role_fit: "target_or_close_role",
      technology_display: "Java",
      technology_fit: "exact",
      current_location_line: "Lviv, Ukraine",
      current_location_status: "target_location",
    }},
  }},
  {{
    normalized_url: "https://www.linkedin.com/in/foreign",
    quality_score: 88,
    current_location_status: "foreign_current_location",
    stack_fit: "confirmed",
    selected_stack_terms_found: ["Spring"],
    query_sources: [{{ id: "Q03", category: "role_based" }}],
    result: {{
      name: "Foreign Candidate",
      headline: "Senior Java Developer",
      url: "https://www.linkedin.com/in/foreign",
      role_display: "Backend Developer",
      role_fit: "target_or_close_role",
      technology_display: "Java",
      technology_fit: "exact",
      stack_evidence: [{{ term: "Spring", source: "snippet" }}],
      current_location_line: "Warsaw, Poland",
      current_location_status: "foreign_current_location",
    }},
  }},
  {{
    normalized_url: "https://www.linkedin.com/in/rejected",
    quality_score: 99,
    current_location_status: "target_location",
    stack_fit: "confirmed",
    selected_stack_terms_found: ["Spring"],
    query_sources: [{{ id: "Q04", category: "role_based" }}],
    result: {{
      name: "Rejected Candidate",
      headline: "Lead Java Backend Developer",
      url: "https://www.linkedin.com/in/rejected",
      role_display: "Backend Developer",
      role_fit: "target_or_close_role",
      technology_display: "Java",
      technology_fit: "exact",
      current_location_line: "Kyiv, Ukraine",
      current_location_status: "target_location",
    }},
  }},
  {{
    normalized_url: "https://www.linkedin.com/in/url-only",
    quality_score: 60,
    current_location_status: "unknown_current_location",
    stack_fit: "not_visible",
    result: {{
      title: "https://www.linkedin.com/in/url-only",
      url: "https://www.linkedin.com/in/url-only",
      role_fit: "missing_role",
      technology_display: "Java",
      technology_fit: "exact",
      current_location_status: "unknown_current_location",
    }},
  }},
];

const candidates = cw.mapDedupedResultsToWorkspaceCandidates(raw);
const reviewState = cw.createReviewStateForCandidates(candidates);
reviewState[candidates[0].candidate_id] = {{ ...reviewState[candidates[0].candidate_id], status: cw.REVIEW_STATUSES.SHORTLISTED, note: "private recruiter note" }};
reviewState[candidates[1].candidate_id] = {{ ...reviewState[candidates[1].candidate_id], status: cw.REVIEW_STATUSES.SHORTLISTED, note: "another private note" }};
reviewState[candidates[2].candidate_id] = {{ ...reviewState[candidates[2].candidate_id], status: cw.REVIEW_STATUSES.SHORTLISTED }};
reviewState[candidates[3].candidate_id] = {{ ...reviewState[candidates[3].candidate_id], status: cw.REVIEW_STATUSES.NOT_A_FIT }};

const comparison = cw.buildSelectedCandidateComparison(candidates, reviewState, {{
  limit: 4,
  scope: "visible_shortlisted_candidates",
}});

const oneSelectedState = cw.createReviewStateForCandidates(candidates);
oneSelectedState[candidates[0].candidate_id] = {{ ...oneSelectedState[candidates[0].candidate_id], status: cw.REVIEW_STATUSES.SHORTLISTED }};
const oneSelected = cw.buildSelectedCandidateComparison(candidates, oneSelectedState, {{
  limit: 4,
  scope: "visible_shortlisted_candidates",
}});

console.log(JSON.stringify({{ comparison, oneSelected }}));
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
    comparison = payload["comparison"]
    one_selected = payload["oneSelected"]

    assert comparison["version"] == "selected_candidate_comparison_v1"
    assert comparison["source"] == "deterministic_workspace_facts"
    assert comparison["scope"] == "visible_shortlisted_candidates"
    assert comparison["candidates_analyzed"] == 5
    assert comparison["selected_count"] == 3
    assert comparison["compared_count"] == 3
    assert comparison["ready"] is True
    assert len(comparison["candidates"]) == 3

    serialized = json.dumps(comparison).lower()
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
        "another private note",
        "rejected candidate",
    ]:
        if forbidden in serialized:
            raise AssertionError(f"Comparison model leaked forbidden term: {forbidden}")

    names = [candidate["display_name"] for candidate in comparison["candidates"]]
    assert names == ["Strong Candidate", "Review Candidate", "Foreign Candidate"]
    assert all("candidate_id" not in candidate for candidate in comparison["candidates"])
    foreign = comparison["candidates"][2]
    assert foreign["location_group"] == "foreign"
    assert "outside the target location" in " ".join(foreign["cautions"])
    assert "Stack query source only" in " ".join(comparison["candidates"][1]["review_flags"])
    assert any("Stack visibility differs" in item for item in comparison["differences"])

    assert one_selected["selected_count"] == 1
    assert one_selected["ready"] is False
    assert len(one_selected["candidates"]) == 1


def assert_static_wiring() -> None:
    app_js = APP_JS.read_text(encoding="utf-8")
    workspace_js = WORKSPACE_JS.read_text(encoding="utf-8")
    styles_css = STYLES_CSS.read_text(encoding="utf-8")
    check_all = CHECK_ALL.read_text(encoding="utf-8")

    require(workspace_js, "SELECTED_CANDIDATE_COMPARISON_VERSION", "comparison version")
    require(workspace_js, "function buildSelectedCandidateComparison(", "comparison helper")
    require(workspace_js, "source: \"deterministic_workspace_facts\"", "deterministic source")
    require(workspace_js, "\"visible_shortlisted_candidates\"", "visible shortlisted scope")
    require(workspace_js, "isWorkspaceCandidateShortlisted(reviewState)", "shortlist selection")
    require(workspace_js, "reviewState.status === REVIEW_STATUSES.NOT_A_FIT", "not-a-fit exclusion")
    require(workspace_js, "comparisonSafeText", "URL-safe comparison text")
    require(workspace_js, "buildSelectedCandidateComparison,", "helper export")

    require(app_js, "function renderSelectedCandidateComparison()", "UI renderer")
    require(app_js, "visible_shortlisted_candidates", "visible shortlisted UI scope")
    require(app_js, "Based on visible shortlisted candidates.", "scope wording")
    require(app_js, "${renderSelectedCandidateComparison()}", "renderer insertion")
    require(app_js, "workspace-selected-comparison", "comparison block markup")

    require(styles_css, ".workspace-selected-comparison-grid", "comparison grid CSS")
    require(styles_css, ".workspace-comparison-card", "comparison card CSS")
    require(styles_css, ".workspace-comparison-summary", "comparison summary CSS")

    for function_name in ["buildSelectedCandidateComparison", "renderSelectedCandidateComparison"]:
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
        ]:
            if forbidden in source:
                raise AssertionError(f"{function_name} must not contain {forbidden}")

    require(check_all, "scripts/smoke_p85_selected_candidate_comparison.py", "check_all wiring")


def main() -> None:
    assert_helper_behavior()
    assert_static_wiring()
    print("P8.5 selected-candidate comparison smoke passed")


if __name__ == "__main__":
    main()
