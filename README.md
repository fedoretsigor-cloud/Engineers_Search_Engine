# Engineers_Search_Engine
AI-powered sourcing search engine

## Current Status

Planner-based Tavily/LinkedIn X-ray sourcing prototype.

Status:

- Phase 1 POC completed successfully.
- Phase 1.1 behavior tuning completed.
- Phase 2 multi-query search + baseline query planner completed.
- Phase 3 Candidate Quality Layer completed.
- Phase 4 AI Agent Foundation completed.
- Phase 4 `P4-003`-`P4-011` are completed: Search Brief validation/adapter, Agent Tools v0 metadata, explicit AI planner mode, deterministic AI QueryPlan validation/fallback, planner explanation UI, backend approval gate before Tavily execution, AI planner baseline evaluation, AI planner coverage diagnosis/improvement, and Phase 4 closeout.
- Current active phase: Phase 8 `Candidate Workspace/Table + Shortlist`.
- Phase 6 `Human-approved Tool-Calling Agent Runtime` is completed through `P6-006 Close Phase 6 with AI Agent v0 decision` and closed as `AI Agent Runtime v0 baseline`.
- Phase 5.5 `Technical modularization before Agent Runtime` is completed through `P5.5-009`.
- Phase 5 `Recruiter Chat UX + Search Brief conversation` is completed and closed as a narrow Java/Ukraine Agent UX foundation.
- Completed Phase 5 tasks: `P5-001 Define recruiter chat and Search Brief conversation contract`, `P5-002 Add backend chat-to-brief adapter`, `P5-003 Replace structured form with recruiter chat UI`, `P5-004 Make Build Plan produce an approvable Search Plan`, `P5-005 Instantiate human-approved Agent v0 for Java/Ukraine baseline`, `P5-006 Add post-results Agent Response in chat`, `P5-007 Add LLM-assisted Agent Plan/Response with deterministic fallback`, `P5-007.1 Sync Phase 5 docs and tighten Agent Plan guardrail`, `P5-008 Chat onboarding and clarification quality`, `P5-009 Search Brief refinement through chat`, `P5-010 Result-to-next-iteration loop`, `P5-011 Apply AI Agent visual direction / dark workspace refresh`, and `P5-012 Close Phase 5 with narrow Java/Ukraine agent UX decision`.
- `P5-002` added `POST /api/recruiter-chat/turn` and is limited to `chat messages -> draft Search Brief -> validation -> one assistant response`.
- `P5-003` made recruiter chat the primary frontend input and keeps execution tied to planner response `adapted_structured_request`.
- `P5-004` made primary chat `Build Plan` produce an approvable deterministic backend Search Plan as a safe executable bridge toward the AI Agent flow. AI planner capability remains in the product and should be evolved through reviewed tasks.
- `P5-005` added `POST /api/agent/plan`, shows Agent Plan in chat for the supported Java/Ukraine baseline, and makes `Build Plan` execute the current `agent_plan.proposed_action` with backend fingerprint validation.
- `P5-006` added backend-generated `agent_response` to approved search responses and renders it as a local-only `AI Agent` chat message after results.
- `P5-007` added optional LLM-assisted wording for Agent Plan/Response with deterministic fallback.
- `P5-007.1` synchronized Phase 5 docs and tightened `/api/agent/query-plan` so Build Plan requires the current Agent Plan action and brief fingerprint.
- `P5-008` added deterministic RU/EN chat onboarding for greeting-only and near-empty turns without calling OpenAI, while preserving existing draft briefs.
- `P5-009` added deterministic-first Search Brief refinement through atomic `brief_patch.operations` and frontend stale-state clearing only when backend returns `stale_state_should_clear = true`.
- `P5-010` added deterministic non-executable `agent_response.next_iteration_options` after approved search results, displayed in chat with no Apply/action buttons.
- `P5-011` applied a CSS-first/UI-only dark AI Agent visual refresh without changing backend code, frontend logic, API contracts, or product flow.
- `P5-012` closed Phase 5 as a docs-only decision: the Java/Ukraine Agent UX foundation is ready for Phase 5.5 technical modularization, while broader conversation scenarios and ordinary LLM-assisted chat wording move to Phase 7.
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
- `P6-001` defined the human-approved Agent Runtime v0 contract: runtime states/transitions, backend-owned tool-call envelopes, runtime turn response envelope, approval/fingerprint/stale-context rules, deny-by-default registry behavior, idempotency expectations for stateless v0, error taxonomy, and Phase 7 wording boundary.
- `P6-002` added typed Agent Tool definitions and internal Agent Runtime envelope helpers in `app/agent_tools.py` and `app/agent_runtime.py`, with no-network smoke coverage in `scripts/check_all.ps1`. It did not add a runtime endpoint, frontend action queue, Tavily/OpenAI calls, tool execution, or structured-search approval behavior changes.
- `P6-003` added a frontend-only Agent Action Review Queue showing `Build Search Plan` and `Run Search` status/context while preserving the existing `Build Plan` and `Approve & Search` controls. It did not add backend routes, runtime execution, Tavily/OpenAI calls, API contract changes, new execution handlers, or autonomous execution.
- `P6-004` added the first approved Agent Runtime execution slice for the Java/Ukraine baseline: `POST /api/agent/runtime/turn` supports stateless `prepare` and `execute_approved`, validates backend-owned fingerprints/context, bridges approved runtime execution into the existing safe search pipeline, and routes frontend `Approve & Search` through the runtime path.
- `P6-005` added runtime guardrail regression coverage for stale/mutated approval rejection, runtime context mismatch, unsafe frontend-owned runtime fields, frontend runtime-only execution, mocked approved single/multi-wave execution, prepare-without-execution, and missing Tavily key during approved execution.
- `P6-005.1` repaired real single/multi runtime execution wrappers so they call the existing approved pipelines instead of recursing, with unmocked-wrapper no-network smoke coverage in `scripts/check_all.ps1`.
- `P6-006` closed Phase 6 as `AI Agent Runtime v0 baseline`, not as a complete autonomous recruiter agent. See `docs/phase-6-closeout.md`.
- `P7-004` added the backend-first deterministic source-message helper layer in `app/agent_messages.py`, including an explicit coverage matrix and no-network smoke coverage for chat, Agent Plan, QueryPlan/runtime, and Agent Response source messages.
- `P7-005` added the docs-only `LLM Routing and Gating Policy V0` in `docs/phase-7-llm-routing-gating-policy.md`, keeping LLM wording default-deny and preserving the current bounded overlay only for Agent Plan and Agent Response.
- `P7-006` added the docs-only `Bounded LLM Wording Payload and Prompt Contract V0` in `docs/phase-7-bounded-llm-payload-prompt-contract.md`, defining current `agent_plan`/`agent_response` payload and prompt boundaries without changing code or behavior.
- `P7-007` added wording validation, deterministic fallback/no-call metadata, and nested `wording_provenance` for current bounded Agent Plan/Response wording paths.
- `P7-008` added frontend-only typed rendering for current agent chat messages, local-only system errors, and inert structured rendering for `agent_response.next_iteration_options` without backend/API/runtime/search changes.
- `P7-009` added no-network golden conversation scenario regression coverage in `scripts/smoke_p7_golden_conversations.py` and wired it into `scripts/check_all.ps1`.
- `P7-010` closed Phase 7 as `Agent Conversation Wording Layer v0 baseline` in `docs/phase-7-closeout.md`.
- Phase 7.5 was inserted after Phase 7 as a recruiter simulation QA gate before Phase 8. It is now closed with the decision `ready after approved fixes completed`; see `docs/phase-7-5-closeout.md`.
- `P7.5-002` created `docs/phase-7-5-recruiter-simulation-scenarios.md` with the full 104-scenario QA bank for RU/EN, noisy, negative, multilingual, off-topic, safety, and state-stress recruiter simulations, including QA result capture fields and disciplined approved-flow Tavily usage.
- `P7.5-003` created `docs/phase-7-5-browser-qa-checklist.md`, assigning all 104 scenarios to RU/EN QA batches, limiting live Tavily to two approved single-wave searches, and defining evidence/status/severity capture for P7.5-004 and P7.5-005.
- `P7.5-004` completed RU browser QA in `docs/phase-7-5-ru-browser-qa-results.md`: 47 scenarios run, 39 pass, 7 fail, 1 blocked, and 0 live Tavily executions because runtime approval preparation did not reach `Approve & Search`.
- `P7.5-006` created `docs/phase-7-5-qa-findings-report.md` as an initial RU findings report. Current blockers are runtime approval preparation after Build Plan, latest-turn RU safety/prohibited-intent detection that preserves the current Search Brief while clearing stale executable state, and clean-state initial request vs refinement classification.
- `P7.5-007` completed the docs-only current-flow fixes decision and approved the exact implementation scope for P7.5-008 plus regression scope for P7.5-009.
- `P7.5-008` implemented the approved current-flow fixes: runtime approval preparation now happens after `Build Plan` settles, latest-turn RU/EN prohibited-intent refusal is tightened, refusals preserve the visible Search Brief while clearing stale executable state, and clean-state recruiter messages use initial extraction instead of refinement blocking.
- `P7.5-009` added no-network regression coverage for the fixed current-flow issues and wired it into `scripts/check_all.ps1`.
- `P7.5-005` completed EN/mixed browser QA in `docs/phase-7-5-en-browser-qa-results.md`: 57 scenarios run, 37 pass, 20 fail, 0 blocked, and 1 live Tavily execution through visible `Approve & Search` for `CORE-EN-001`. New findings are `P75-QA-008` through `P75-QA-014`.
- `P7.5-011` implemented immediate EN/mixed hardening for `P75-QA-008` through `P75-QA-014`: safer EN refusals, deterministic off-topic/meta/reset/ambiguity/contradiction handling, typo normalization, LLM draft sanitization, and local grounded post-results follow-up.
- `P7.5-010` closed Phase 7.5 as `ready after approved fixes completed`, documented closure for `P75-QA-001` through `P75-QA-014`, and handed off to Phase 8.
- `P8-001` completed the docs-only Candidate Workspace v0 contract in `docs/phase-8-candidate-workspace-contract.md`: approved search results are the source of truth, shortlist/notes/statuses are browser in-memory session/local UI state until Phase 9, `review_status` is the workflow source of truth, `workspace_run_id` needs a per-run component, and profile links are manual user-click only after safe LinkedIn URL validation.
- `P8-002`, `P8-003`, and `P8-004` implemented the first frontend-only Candidate Workspace batch: approved search results now render as a recruiter workspace list, workspace view controls sort/filter returned candidates only, and local review status/derived shortlist/escaped notes stay browser in-memory with no backend/API/search/runtime behavior changes.

Agreed next direction:

- keep the product focused on one narrow high-quality flow first: `Backend Developer + Java + Ukraine`;
- Phase 5.5 technical modularization is complete; the current backend is split into focused modules without product behavior changes;
- Phase 6 human-approved tool-calling runtime is complete as Agent Runtime v0 baseline;
- Phase 7 is completed and closed as `Agent Conversation Wording Layer v0 baseline`; completed Phase 7 tasks: `P7-001 Define agent message taxonomy and lifecycle mapping`, `P7-002 Define message facts and source-of-truth contract`, `P7-003 Define agent wording style and language policy`, `P7-004 Build deterministic source messages for approved message types`, `P7-005 Define LLM routing and gating policy for conversation wording`, `P7-006 Add bounded LLM wording payloads and prompt contract`, `P7-007 Add wording validation, fallback, and provenance metadata`, `P7-008 Add frontend rendering for typed agent messages`, `P7-009 Add golden conversation scenario regression tests`, `P7-010 Close Phase 7 with wording quality and guardrail evaluation`;
- first candidate-workspace implementation batch is completed through `P8-004`; next Phase 8 review should continue from candidate-level explanations/export/backlog tasks rather than changing persistence or backend search behavior implicitly;
- Phase 8 is active after the Phase 7.5 closeout decision `ready after approved fixes completed`;
- keep candidate workspace/shortlist for Phase 8 and persistence/memory for Phase 9.

Current pipeline:

- recruiter chat collects a validated `Search Brief` from natural-language recruiter messages;
- the supported Java/Ukraine baseline gets a current Agent Plan in chat before planning;
- `Build Plan` executes the Agent Plan's proposed backend action and converts the chat-produced brief into a visible approvable Search Plan;
- an `Agent Actions` queue shows the current planning/search action status and approval context without executing actions itself;
- `Approve & Search` uses `POST /api/agent/runtime/turn` and executes only after explicit approval tied to backend-owned runtime fingerprints;
- approved search responses include a grounded deterministic Agent Response in chat;
- Agent Response includes structured next-iteration options that can propose future `brief_patch` operations but do not execute anything;
- the UI uses a dark AI Agent workspace visual direction with layered dark surfaces and teal/cyan action/status accents;
- `RuleBasedQueryPlanner v1` generates a visible 10-query `QueryPlan`;
- optional explicit AI planner mode can draft and explain a plan for backend validation/fallback;
- backend validates AI draft plans deterministically and can show rule-based fallback;
- rule-based Tavily execution requires explicit approval bound to action, query count, and current `QueryPlan` fingerprint;
- Tavily executes the generated queries;
- LinkedIn profile URLs are normalized and deduped;
- visible `LinkedIn profiles only` and `Location filter` controls are applied;
- Ukraine location filtering uses current-location classification instead of a finite negative-location blacklist;
- Candidate Quality Layer adds role/tech/stack/seniority signals, review flags, and explainable quality score;
- local structured-search snapshots are saved under `logs/search-runs/` and ignored by git.

Execution boundary:

- AI planner output is planning/explanation only and is not executable.
- AI Agent behavior must stay human-approved, not autonomous: it may suggest, prepare, explain, validate, and analyze, but search/deep/multi-wave execution requires explicit approval.
- Tavily execution must stay inside the approved backend pipeline.
- The legacy raw `/api/search` Tavily path is disabled.
- AI-generated plans remain non-executable until a later reviewed task explicitly enables that path.
- AI plan validation includes strict `AIPlannerCoveragePolicy v0` coverage checks for the Java/Ukraine standard baseline; unsupported briefs return a visible coverage-policy warning.
- Direct LinkedIn access/automation is prohibited: no LinkedIn login, no scraping, no restriction bypass, no direct profile automation/opening, no candidate messaging, and no account actions.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
uvicorn app.main:app --reload
```

`python -m playwright install chromium` is required for local browser sanity QA. It downloads Playwright's Chromium binary outside the repo.

Required AI configuration for the current recruiter chat and AI planner paths:

```powershell
$env:OPENAI_API_KEY="..."
$env:OPENAI_MODEL="..."
```

If these values are not configured, the primary recruiter chat-to-brief flow cannot call the LLM adapter. LLM-assisted Agent Plan/Response wording still falls back to deterministic wording when configuration or validation fails.

The backend uses `max_completion_tokens` for OpenAI Chat Completions requests, which is compatible with `gpt-5.4-mini`.

Open:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/api/health
```

Run the local regression baseline:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_all.ps1
```

Push and wait for GitHub Actions CI:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\push_and_watch_ci.ps1
```

Watch CI for the current commit after a manual push:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\watch_ci.ps1
```

## Project Documents

- `ProjectStatus.md`
- `Roadmap.md`
- `Tasks.md`
- `docs/phase-5-agent-stabilization.md`
- `docs/phase-4-ai-planner-baseline.md`
- `docs/phase-1-poc-findings.md`
- `docs/phase-3-quality-baseline.md`
- `docs/phase-3-multi-wave-evaluation.md`
