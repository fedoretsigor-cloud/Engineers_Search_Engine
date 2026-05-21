# Codex Project Context

## Project

Engineers Search Engine is an AI-assisted recruiter sourcing search engine. It uses FastAPI to serve a static UI and Tavily-backed public LinkedIn X-ray search flows.

## Stack

- Python FastAPI backend in `app/main.py`, with route wrappers in `app/routes.py` and extracted shared modules in `app/schemas.py`, `app/domain_config.py`, `app/text_utils.py`, `app/search_validation.py`, `app/search_brief.py`, `app/planning.py`, `app/ai_planning.py`, `app/search_execution.py`, `app/search_snapshots.py`, `app/candidate_quality.py`, `app/agent_tools.py`, `app/agent_runtime.py`, `app/agent_plan.py`, `app/brief_patch.py`, `app/agent_response.py`, `app/agent_messages.py`, and `app/agent_wording.py`
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
- Phase 5.5: `Technical modularization before Agent Runtime` - completed through `P5.5-009`
- Phase 6: `Tool-Calling Agent Runtime` - completed and closed as `AI Agent Runtime v0 baseline`
- Phase 7: `Agent Conversation Wording Layer` - completed and closed as `Agent Conversation Wording Layer v0 baseline`
- Phase 7.5: `Recruiter Simulation QA & Flow Hardening` - current active phase
- Phase 8: `Candidate Workspace/Table + Shortlist` - planned after Phase 7.5 readiness decision
- Phase 9: `Persistent Memory + Saved Searches`
- Phase 4 is completed as `AI Agent Foundation` through `P4-011`.
- `P4-003` through `P4-010` are implemented in code.
- `P4-009` is completed as a no-Tavily planner evaluation; `P4-010` added AI planner coverage diagnosis, policy validation, and one bounded repair attempt.
- The backend has Search Brief validation/adapter endpoints, recruiter chat-to-brief endpoint, Agent Tools v0 metadata, `POST /api/agent/runtime/turn`, explicit AI planner mode, deterministic AI QueryPlan validation/fallback, non-executable planner responses, and approval-gated rule-based Tavily execution.
- The frontend has recruiter chat as the primary input, a `Search Brief` summary, `Build Plan`, planner explanation UI, Agent Action Review Queue, and Agent Runtime-backed `Approve & Search`.
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
- `P5.5-003` extracted rule-based planner, QueryPlan fingerprint helpers, planner explanation, deterministic AI QueryPlan prompt/validation/coverage helpers, and related shared planner config without behavior changes.
- `P5.5-004` extracted Tavily/query-wave execution and structured-search snapshot helpers into focused modules without behavior changes.
- `P5.5-005` extracted Candidate Quality producer logic, constants, and shared text/ordering helpers into focused modules without behavior changes.
- `P5.5-006` extracted Agent Tools v0 contract/approval helpers and deterministic Agent Plan helpers into focused modules without behavior changes.
- `P5.5-006.1` added `scripts/check_all.ps1` and GitHub Actions CI for the current compile/frontend/smoke regression baseline.
- `P5.5-007` extracted shared brief patch helpers, deterministic Agent Response logic, and bounded Agent Plan/Response wording logic into focused modules without behavior changes.
- `P5.5-008` split FastAPI path decorators and thin route wrappers into `app/routes.py` behind `RouteDependencies`, while preserving `app/main.py` service compatibility, route path/method set, endpoint names, and smoke-test monkeypatch paths without behavior changes.
- `P5.5-009` added permanent route/import/no-network HTTP smoke coverage to `scripts/check_all.ps1`, closed Phase 5.5, and confirmed Phase 6 as the next active phase at that point.
- `P6-001` is completed as the approved docs-only human-approved Agent Runtime v0 contract: runtime states/transitions, backend-owned tool-call envelopes, runtime turn response envelope, approval/fingerprint/stale-context rules, deny-by-default registry behavior, idempotency expectations for stateless v0, error taxonomy, and Phase 7 wording boundary.
- `P6-002` is completed as a backend-only typed registry/envelope foundation: typed Agent Tool definitions, internal Agent Runtime states/envelopes, deterministic fingerprints/idempotency keys, deny-by-default proposal normalization, and no-network smoke coverage were added without adding a runtime endpoint, Tavily/OpenAI calls, tool execution, or structured-search approval behavior changes.
- `P6-003` is completed as a frontend-only/status-only Agent Action Review Queue: the UI shows `Build Search Plan` and `Run Search` action state/context while preserving existing `Build Plan` and `Approve & Search` controls, backend approval boundaries, API contracts, and no-autonomy rules.
- `P6-004` is completed as the first approved Agent Runtime execution slice for the Java/Ukraine baseline: `POST /api/agent/runtime/turn` supports stateless `prepare` and `execute_approved` for `run_single_wave_search` and `run_multi_wave_search`, validates backend-owned fingerprints/context, bridges valid runtime approval into existing `ExecutionApproval`, and frontend `Approve & Search` uses the runtime path without direct structured-search fallback.
- `P6-005` is completed as runtime guardrail hardening: `scripts/smoke_p6_runtime_guardrails.py` is included in `scripts/check_all.ps1` and covers stale/mutated approval rejection, runtime context mismatch, unsafe frontend-owned runtime fields, frontend runtime-only execution path, mocked approved single/multi-wave execution, prepare-without-execution, and missing Tavily key during approved execution.
- `P6-005.1` is completed as a runtime wrapper repair: `main.execute_single_wave_structured_search_response` and `main.execute_multi_wave_structured_search_response` now call the existing approved single/multi-wave pipelines instead of recursing, and `scripts/smoke_p6_runtime_unmocked_execution.py` verifies real `prepare -> execute_approved -> observed` without monkeypatching those wrappers.
- `P6-006` is completed as the docs-only Phase 6 closeout: Phase 6 is closed as `AI Agent Runtime v0 baseline`, not as a complete autonomous recruiter agent, and `docs/phase-6-closeout.md` records the decision.
- `P7-009` is completed as no-network golden conversation scenario regression coverage: `scripts/smoke_p7_golden_conversations.py` covers recruiter chat, Search Brief refinement, Agent Plan, Build Plan, runtime prepare, Agent Response, wording fallback/provenance, and frontend typed-message contract scenarios, and it is included in `scripts/check_all.ps1`.
- `P7-010` is completed as the docs-only Phase 7 closeout: Phase 7 is closed as `Agent Conversation Wording Layer v0 baseline`, `docs/phase-7-closeout.md` records wording quality evaluation, guardrail evaluation, residual gaps, verification evidence, and the original Phase 8 handoff.
- Next agreed direction: keep the product focused on one narrow Java/Ukraine flow and run Phase 7.5 `Recruiter Simulation QA & Flow Hardening` before Phase 8 implementation. `P7.5-001 Define Phase 7.5 QA gate and pause Phase 8 implementation` is approved as a docs-only gate definition. `P7.5-002 Define RU/EN recruiter simulation scenarios` created `docs/phase-7-5-recruiter-simulation-scenarios.md` with the full 104-scenario QA bank, QA result capture fields, severity/evidence fields, and disciplined approved-flow Tavily usage. `P7.5-003 Prepare safe browser QA checklist with approved Tavily execution when needed` created `docs/phase-7-5-browser-qa-checklist.md`, assigned all 104 scenarios to QA batches, limited live Tavily to two approved single-wave searches, and defined evidence/status/severity capture. `P7.5-004 Run RU browser QA with approved Tavily execution when needed` completed the 47-scenario RU pass in `docs/phase-7-5-ru-browser-qa-results.md`. `P7.5-006 Create recruiter simulation QA findings report` created `docs/phase-7-5-qa-findings-report.md` as an initial RU findings report. Current blockers are runtime approval preparation after Build Plan, RU safety/prohibited-intent detection, and clean-state initial request vs refinement classification. Next task is `P7.5-007 Review and approve current-flow fixes`; `P7.5-005` EN/mixed QA should wait until the approved-search blocker is reviewed/fixed unless the user explicitly chooses to run it against the known broken state. Phase 7.5 should simulate a live recruiter in the local browser, cover RU and EN, allow OpenAI live calls only for existing configured chat/planning/wording paths, and allow Tavily-backed execution when a scenario requires it only through the existing approved backend pipeline and explicit `Approve & Search` flow. All scenarios stay in scope, but Tavily should run only for `required_for_scenario` or deliberately selected `allowed_if_approved` scenarios. Findings should be documented first; fixes require separate review and approval. Phase 8 remains paused until Phase 7.5 closes with a readiness decision: `ready`, `ready after approved fixes`, or `not ready`. Phase 8 should later turn search results into the recruiter's working artifact while preserving human approval, backend tool boundaries, and the absolute product restrictions. Candidate workspace, shortlist, notes/statuses, and export belong to Phase 8; persistence/memory/saved searches remain Phase 9. Do not add autonomous execution, direct LinkedIn access/automation, LinkedIn login, scraping or restriction bypass, automatic candidate messaging, user/third-party account actions, or new countries/technologies without separate reviewed tasks.

## Product Rules

- Every product step should move the system toward a real AI Agent experience: dialogue, intent understanding, planning, tool boundaries, approval gates, execution, result analysis, and iterative follow-up.
- The AI Agent must stay human-approved, not autonomous. It may suggest, prepare, explain, validate, and analyze, but it must not independently execute searches, deep/multi-wave runs, outreach, account actions, or other externally meaningful actions.
- Current frontend search starts from recruiter chat that produces a validated `Search Brief`.
- Current product focus is one high-quality supported flow first: `Backend Developer + Java + Ukraine`; do not expand countries or technologies without a separate reviewed task.
- Current recruiter chat and AI planner paths require `OPENAI_API_KEY` and `OPENAI_MODEL`; LLM-assisted Agent Plan/Response wording falls back to deterministic wording when configuration or validation fails.
- During Phase 7.5 QA, OpenAI live calls are allowed for current configured chat/planning/wording paths. Tavily-backed execution is allowed when a scenario requires it, but only through the existing approved application flow and explicit `Approve & Search`; direct Tavily calls, direct structured-search/runtime execution outside the app flow, and direct web-search bypass remain prohibited. Do not use Phase 7.5 QA as an implicit start of Phase 8.
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
- Frontend `Approve & Search` must use `POST /api/agent/runtime/turn`; runtime execution is stateless, execution-tools-only, and validates backend-owned pending approval before bridging into `ExecutionApproval`.
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
powershell -ExecutionPolicy Bypass -File .\scripts\check_all.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\push_and_watch_ci.ps1
```

After any successful push made by Codex, wait for GitHub Actions CI and report `CI passed` or `CI failed` with the failed workflow/job/step when available. Use `scripts/push_and_watch_ci.ps1` for push operations, or `scripts/watch_ci.ps1` after a manual push.
