from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing {label}: {needle}")


def main() -> None:
    contract = read("docs/phase-8-5-agentic-candidate-review-contract.md")
    tasks = read("Tasks.md")
    project_status = read("ProjectStatus.md")
    roadmap = read("Roadmap.md")
    agents = read("AGENTS.md")
    app_js = read("app/static/app.js")
    workspace_js = read("app/static/candidate_workspace.js")
    check_all = read("scripts/check_all.ps1")

    require(tasks, "- [x] P8.5-001 Define agentic candidate review contract", "P8.5-001 done item")
    require(tasks, "## Task: P8.5-001 Define agentic candidate review contract", "P8.5-001 task section")
    require(tasks, "Implemented / completed.", "P8.5-001 implemented status")
    require(project_status, "P8.5-001 Define agentic candidate review contract", "ProjectStatus P8.5 task")
    require(roadmap, "Phase 8.5", "Roadmap Phase 8.5")
    require(agents, "Phase 8.5 agentic candidate review", "AGENTS Phase 8.5 direction")

    required_contract_terms = [
        "The agent may analyze already returned current-run workspace facts",
        "must not execute searches",
        "call Tavily",
        "direct web-search bypass",
        "direct LinkedIn access",
        "LinkedIn login",
        "LinkedIn scraping or restriction bypass",
        "candidate messaging or outreach",
        "user or third-party account actions",
        "persistence, saved searches, saved candidates",
        "There is no backend-owned candidate workspace database in v0",
        "Review state is workflow state, not candidate evidence",
        "Recruiter notes remain local/private",
        "`P8.5-001` adds no LLM call",
        "The LLM may only synthesize wording from allowlisted current-run facts",
        "Future Phase 8.5 LLM payloads must not include",
        "profile URLs",
        "raw snippets/content",
        "runtime approval state",
        "execution fingerprints",
        "P8.5-002",
        "P8.5-003",
        "P8.5-004",
        "P8.5-005",
    ]
    for term in required_contract_terms:
        require(contract, term, "contract boundary")

    required_current_workspace_terms = [
        "let latestWorkspaceRun = null;",
        "let workspaceCandidates = [];",
        "let visibleWorkspaceCandidates = [];",
        "let workspaceReviewStateByCandidateId = {};",
        "candidateWorkspace.buildCandidateExplanation(candidate)",
    ]
    for term in required_current_workspace_terms:
        require(app_js, term, "current workspace source")

    required_workspace_helper_terms = [
        "function buildCandidateExplanation(candidate)",
        "source: \"deterministic_workspace_facts\"",
        "function buildWorkspaceExportModel(options)",
        "function applyWorkspaceView(candidates, viewState, reviewStateByCandidateId)",
    ]
    for term in required_workspace_helper_terms:
        require(workspace_js, term, "workspace helper source")

    require(
        check_all,
        "scripts/smoke_p85_agentic_candidate_review_contract.py",
        "check_all P8.5 smoke wiring",
    )

    print("P8.5 agentic candidate review contract smoke passed")


if __name__ == "__main__":
    main()
