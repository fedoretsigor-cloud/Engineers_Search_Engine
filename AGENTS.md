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

- Phase 5: `Recruiter Chat UX + Search Brief conversation`
- Phase 4 is completed as `AI Agent Foundation` through `P4-011`.
- `P4-003` through `P4-010` are implemented in code.
- `P4-009` is completed as a no-Tavily planner evaluation; `P4-010` added AI planner coverage diagnosis, policy validation, and one bounded repair attempt.
- The backend has Search Brief validation/adapter endpoints, recruiter chat-to-brief endpoint, Agent Tools v0 metadata, explicit AI planner mode, deterministic AI QueryPlan validation/fallback, non-executable planner responses, and approval-gated rule-based Tavily execution.
- The frontend has recruiter chat as the primary input, a `Search Brief` summary, `Build Plan`, planner explanation UI, and approval-gated search controls.
- Completed Phase 5 tasks: `P5-001 Define recruiter chat and Search Brief conversation contract`, `P5-002 Add backend chat-to-brief adapter`, and `P5-003 Replace structured form with recruiter chat UI`.
- `P5-002` guardrail: `chat messages -> draft Search Brief -> validation -> one assistant response`; do not let it grow into an agent loop.
- `P5-003` made recruiter chat the primary frontend input.
- `P5-003` guardrail: search execution uses `adapted_structured_request` from the planner response, not old structured-form DOM fields.

## Product Rules

- Current frontend search starts from recruiter chat that produces a validated `Search Brief`.
- Backend execution is still driven by the adapted structured request fields: `Role Family`, `Technology`, `Stack`, and `Location`.
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
- Rule-based Tavily execution requires explicit approval bound to action, query count, and the current `QueryPlan` fingerprint.
- `POST /api/recruiter-chat/turn` can prepare a `Search Brief`, but it must not build `QueryPlan`, call Tavily, execute search, or change frontend UI.
- AI QueryPlan validation checks safety, alignment, and strict coverage for the Java/Ukraine standard baseline through `AIPlannerCoveragePolicy v0`; unsupported briefs return a visible coverage-policy warning.
- `P4-010` diagnosed the AI planner coverage gap, improved the AI prompt toward the tested 10-query baseline, added one bounded repair attempt, and kept deterministic fallback for structurally valid but under-covered AI plans.
- AI-generated plans must remain non-executable until a later reviewed task explicitly enables that path through deterministic validation and approval.
- Local structured-search snapshots are written under `logs/search-runs/` and ignored by git.
- Tavily live result sets vary between runs; use snapshots for deterministic analysis and treat live unique counts as a range, not a fixed guarantee.
- Tavily execution must stay inside the approved backend pipeline.
- The legacy raw `/api/search` Tavily path is disabled.
- Absolute product boundaries: no direct web-search bypass, no LinkedIn login, no LinkedIn scraping or restriction bypass, no automatic candidate messaging, and no user/third-party account actions.

## Working Rules

- Read `instructions`, `ProjectStatus.md`, `Roadmap.md`, `Tasks.md`, `docs/phase-1-poc-findings.md`, `docs/phase-3-quality-baseline.md`, and `docs/phase-3-multi-wave-evaluation.md` before changing behavior.
- Follow the collaboration rules in `instructions`.
- Do not change files or behavior without explicit user approval.
- Keep the project within the public-search scope. LinkedIn login, LinkedIn scraping or restriction bypass, candidate messaging/automatic outreach, and user or third-party account actions are absolute prohibited behavior. Database, shortlist, authentication, and autonomous agent behavior require separate explicit approval.
- Prefer focused, small changes with verification.

## Verification

Useful checks:

```powershell
.\.venv\Scripts\python.exe -m compileall app
node --check app/static/app.js
```
