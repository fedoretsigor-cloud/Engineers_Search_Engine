# Codex Project Context

## Project

Engineers Search Engine is an AI-assisted recruiter sourcing search engine. It uses FastAPI to serve a static UI and Tavily-backed public LinkedIn X-ray search flows.

## Stack

- Python FastAPI backend in `app/main.py`
- Static frontend in `app/static/index.html`, `app/static/styles.css`, and `app/static/app.js`
- Dependencies are listed in `requirements.txt`
- Local secrets are loaded from `.env`

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000`.

Health check: `http://localhost:8000/api/health`.

## Current Status

Phase 1 POC, Phase 1.1 behavior tuning, Phase 2, and Phase 3 are complete.

Phase 2 closed as a working planner-based multi-query search pipeline:

- structured inputs: `Role Family`, `Technology`, `Stack`, and `Location`
- `RuleBasedQueryPlanner v1`
- visible `QueryPlan`
- sequential Tavily query execution
- LinkedIn URL normalization and dedupe
- candidate `query_sources`
- configurable visible `Location filter`
- backend report/counts
- frontend diagnostic UI

The Phase 2 baseline for `Backend Developer + Java + Spring/Kafka/AWS + Ukraine` passed: 58 unique candidates vs a target of 20. After `P2-012`/`P2-013`, the current location filter replayed a saved `Spring/Kafka` snapshot at 73 unique candidates, while recent live Tavily single-wave runs are around 55-60 unique candidates.

Current product direction:

- Phase 4: `AI Agent Foundation`
- `P4-003` through `P4-007` are implemented in code.
- The backend has Search Brief validation/adapter endpoints, Agent Tools v0 metadata, explicit AI planner mode, deterministic AI QueryPlan validation/fallback, and non-executable planner responses.
- The frontend has a `Planner mode` control and planner explanation UI.
- `P4-008` is approved as the next execution-safety task: add a real backend approval gate before Tavily execution.

## Product Rules

- Current structured search is driven by `Role Family`, `Technology`, `Stack`, and `Location`.
- `RuleBasedQueryPlanner v1` builds the visible `QueryPlan`.
- Tavily receives only generated queries from the visible `QueryPlan`.
- `LinkedIn profiles only` is an explicit visible filter.
- `Location filter` is an explicit visible filter.
- `ua.linkedin.com/in/...` is a useful Ukraine country-domain signal, not a guaranteed current physical-location signal.
- Ukraine location filtering uses `target_location_terms` and conservative current-location extraction from Tavily public LinkedIn header/snippet text.
- Current-location classification is `target_location`, `foreign_current_location`, or `unknown_current_location`.
- Explicit foreign current location hides a candidate as `excluded_foreign_current_location`, even if the URL is `ua.linkedin.com/in/...`.
- Non-UA LinkedIn profiles can be rescued only when Tavily public header/current-location text contains supported target-location terms.
- Unknown current location falls back to country-domain/header/weak/unknown signals.
- `QueryPlan` is the contract between planner and executor. `RuleBasedQueryPlanner v1` remains the default execution planner; explicit AI planner mode can draft non-executable plans for backend validation/fallback.
- AI-generated plans must remain non-executable until deterministic validation and approval gates allow a future execution path.
- Local structured-search snapshots are written under `logs/search-runs/` and ignored by git.
- Tavily live result sets vary between runs; use snapshots for deterministic analysis and treat live unique counts as a range, not a fixed guarantee.
- Tavily execution must stay inside the approved backend pipeline.
- Absolute product boundaries: no direct web-search bypass, no LinkedIn login, no LinkedIn scraping or restriction bypass, no automatic candidate messaging, and no user/third-party account actions.

## Working Rules

- Read `instructions`, `ProjectStatus.md`, `Roadmap.md`, `Tasks.md`, `docs/phase-1-poc-findings.md`, `docs/phase-3-quality-baseline.md`, and `docs/phase-3-multi-wave-evaluation.md` before changing behavior.
- Follow the collaboration rules in `instructions`.
- Do not change files or behavior without explicit user approval.
- Keep the project within the public-search scope: no LinkedIn login automation, scraping, restriction bypass, direct LinkedIn profile automation, database, shortlist, authentication, or autonomous agent behavior unless explicitly agreed.
- Prefer focused, small changes with verification.

## Verification

Useful checks:

```powershell
.\.venv\Scripts\python.exe -m compileall app
node --check app/static/app.js
```
