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
- Current active phase: Phase 5.5 `Technical modularization before Agent Runtime`, completed through `P5.5-006.1`.
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

Agreed next direction:

- keep the product focused on one narrow high-quality flow first: `Backend Developer + Java + Ukraine`;
- run Phase 5.5 technical modularization before Phase 6, splitting the current backend without changing product behavior;
- next Phase 5.5 task to review: `P5.5-007 Extract Agent Response and bounded wording/OpenAI modules`;
- only then move to Phase 6 human-approved tool-calling runtime;
- add ordinary agent conversation wording as Phase 7 after the runtime message taxonomy is stable;
- keep candidate workspace/shortlist for Phase 8 and persistence/memory for Phase 9.

Current pipeline:

- recruiter chat collects a validated `Search Brief` from natural-language recruiter messages;
- the supported Java/Ukraine baseline gets a current Agent Plan in chat before planning;
- `Build Plan` executes the Agent Plan's proposed backend action and converts the chat-produced brief into a visible approvable Search Plan;
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
uvicorn app.main:app --reload
```

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

## Project Documents

- `ProjectStatus.md`
- `Roadmap.md`
- `Tasks.md`
- `docs/phase-5-agent-stabilization.md`
- `docs/phase-4-ai-planner-baseline.md`
- `docs/phase-1-poc-findings.md`
- `docs/phase-3-quality-baseline.md`
- `docs/phase-3-multi-wave-evaluation.md`
