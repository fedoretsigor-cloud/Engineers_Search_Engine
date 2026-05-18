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

- Phase 5: `Recruiter Chat UX + Search Brief conversation` - completed and closed
- Phase 5.5: `Technical modularization before Agent Runtime` - current active phase, completed through `P5.5-002`
- Phase 6: `Tool-Calling Agent Runtime`
- Phase 7: `Agent Conversation Wording Layer`
- Phase 8: `Candidate Workspace/Table + Shortlist`
- Phase 9: `Persistent Memory + Saved Searches`
- Phase 4 is completed as `AI Agent Foundation` through `P4-011`.
- `P4-003` through `P4-010` are implemented in code.
- `P4-009` is completed as a no-Tavily planner evaluation; `P4-010` added AI planner coverage diagnosis, policy validation, and one bounded repair attempt.
- The backend has Search Brief validation/adapter endpoints, recruiter chat-to-brief endpoint, Agent Tools v0 metadata, explicit AI planner mode, deterministic AI QueryPlan validation/fallback, non-executable planner responses, and approval-gated rule-based Tavily execution.
- The frontend has recruiter chat as the primary input, a `Search Brief` summary, `Build Plan`, planner explanation UI, and approval-gated search controls.
- Completed Phase 5 tasks: `P5-001 Define recruiter chat and Search Brief conversation contract`, `P5-002 Add backend chat-to-brief adapter`, `P5-003 Replace structured form with recruiter chat UI`, `P5-004 Make Build Plan produce an approvable Search Plan`, `P5-005 Instantiate human-approved Agent v0 for Java/Ukraine baseline`, `P5-006 Add post-results Agent Response in chat`, `P5-007 Add LLM-assisted Agent Plan/Response with deterministic fallback`, `P5-007.1 Sync Phase 5 docs and tighten Agent Plan guardrail`, `P5-008 Chat onboarding and clarification quality`, `P5-009 Search Brief refinement through chat`, `P5-010 Result-to-next-iteration loop`, `P5-011 Apply AI Agent visual direction / dark workspace refresh`, and `P5-012 Close Phase 5 with narrow Java/Ukraine agent UX decision`.
- `P5-002` guardrail: `chat messages -> draft Search Brief -> validation -> one assistant response`; do not let it grow into an agent loop.
- `P5-003` made recruiter chat the primary frontend input.
- `P5-003` guardrail: search execution uses `adapted_structured_request` from the planner response, not old structured-form DOM fields.
- `P5-004` made primary chat `Build Plan` use `planner_mode = rule_based` so supported briefs produce an approvable Search Plan. This is an AI Agent step: the agent now has a safe executable planning bridge behind an approval gate while AI planning capability remains available for the next agent-planning evolution.
- `P5-005` added `POST /api/agent/plan`, Agent Plan chat rendering for the supported Java/Ukraine baseline, and Build Plan execution through the current `agent_plan.proposed_action` with backend fingerprint validation.
- `P5-006` added backend-generated post-results `agent_response` grounded only in already returned search data and rendered as a local-only `AI Agent` chat message.
- `P5-007` added optional LLM-assisted wording with deterministic fallback for Agent Plan/Response.
- `P5-007.1` tightened `/api/agent/query-plan`: Build Plan now requires the current Agent Plan action and brief fingerprint at the backend boundary.
- `P5-008` added deterministic RU/EN chat onboarding for greeting-only and near-empty turns without calling OpenAI, while preserving existing draft briefs.
- `P5-009` added deterministic-first Search Brief refinement through atomic `brief_patch.operations` and frontend stale-state clearing only when backend returns `stale_state_should_clear = true`.
- `P5-010` added deterministic non-executable `agent_response.next_iteration_options` after approved search results. Options are grounded only in returned search data and displayed without Apply/action buttons.
- `P5-011` applied a CSS-first/UI-only dark AI Agent visual refresh without changing backend code, frontend logic, API contracts, or product flow.
- `P5.5-001` defined backend module boundaries and migration order.
- `P5.5-002` extracted shared schemas, domain config, text helpers, structured search validation, and Search Brief validation/adapter/fingerprinting into focused modules without behavior changes.
- Next agreed direction: keep the product focused on one narrow Java/Ukraine flow, continue Phase 5.5 technical modularization with `P5.5-003 Extract planner and AI planner validation modules`, then move to Phase 6 tool-calling runtime, and keep ordinary LLM-assisted agent conversation wording after the Phase 6 runtime baseline, in Phase 7.

## Product Rules

- Every product step should move the system toward a real AI Agent experience: dialogue, intent understanding, planning, tool boundaries, approval gates, execution, result analysis, and iterative follow-up.
- The AI Agent must stay human-approved, not autonomous. It may suggest, prepare, explain, validate, and analyze, but it must not independently execute searches, deep/multi-wave runs, outreach, account actions, or other externally meaningful actions.
- Current frontend search starts from recruiter chat that produces a validated `Search Brief`.
- Current product focus is one high-quality supported flow first: `Backend Developer + Java + Ukraine`; do not expand countries or technologies without a separate reviewed task.
- Current recruiter chat and AI planner paths require `OPENAI_API_KEY` and `OPENAI_MODEL`; LLM-assisted Agent Plan/Response wording falls back to deterministic wording when configuration or validation fails.
- Backend execution is still driven by the adapted structured request fields: `Role Family`, `Technology`, `Stack`, and `Location`.
- Primary chat `Build Plan` uses `planner_mode = rule_based` and produces an approvable Search Plan.
- Phase 5 UI visual styling is CSS-first/UI-only; visual refreshes must not change backend code, frontend behavior, API contracts, request payloads, state semantics, or event flow unless separately approved.
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
- `QueryPlan` is the contract between planner and executor. `RuleBasedQueryPlanner v1` is the current approved executable tool for the agent; explicit AI planner mode can draft plans for backend validation/fallback and should be evolved toward safe executable planning through reviewed tasks.
- Rule-based Tavily execution requires explicit approval bound to action, query count, and the current `QueryPlan` fingerprint.
- `POST /api/recruiter-chat/turn` can prepare a `Search Brief`, but it must not build `QueryPlan`, call Tavily, execute search, or change frontend UI.
- `agent_response.next_iteration_options` can propose future `brief_patch` operations but must not execute search, Build Plan, `/api/agent/query-plan`, Tavily, LinkedIn, web search, or multi-wave.
- AI QueryPlan validation checks safety, alignment, and strict coverage for the Java/Ukraine standard baseline through `AIPlannerCoveragePolicy v0`; unsupported briefs return a visible coverage-policy warning.
- `P4-010` diagnosed the AI planner coverage gap, improved the AI prompt toward the tested 10-query baseline, added one bounded repair attempt, and kept deterministic fallback for structurally valid but under-covered AI plans.
- AI-generated plans must remain non-executable until a later reviewed task explicitly enables that path through deterministic validation and approval.
- Local structured-search snapshots are written under `logs/search-runs/` and ignored by git.
- Tavily live result sets vary between runs; use snapshots for deterministic analysis and treat live unique counts as a range, not a fixed guarantee.
- Tavily execution must stay inside the approved backend pipeline.
- The legacy raw `/api/search` Tavily path is disabled.
- Absolute product boundaries: no direct web-search bypass, no direct LinkedIn access/automation, no LinkedIn login, no LinkedIn scraping or restriction bypass, no automatic candidate messaging, no autonomous execution, and no user/third-party account actions.

## Working Rules

- Read `instructions`, `ProjectStatus.md`, `Roadmap.md`, `Tasks.md`, `docs/phase-5-agent-stabilization.md`, `docs/phase-1-poc-findings.md`, `docs/phase-3-quality-baseline.md`, and `docs/phase-3-multi-wave-evaluation.md` before changing behavior.
- Follow the collaboration rules in `instructions`.
- Do not change files or behavior without explicit user approval.
- Keep the project within the public-search scope. Direct LinkedIn access/automation, LinkedIn login, LinkedIn scraping or restriction bypass, candidate messaging/automatic outreach, autonomous execution, and user or third-party account actions are absolute prohibited behavior. Database, shortlist, and authentication require separate explicit approval.
- Prefer focused, small changes with verification.

## Verification

Useful checks:

```powershell
.\.venv\Scripts\python.exe -m compileall app
node --check app/static/app.js
```
