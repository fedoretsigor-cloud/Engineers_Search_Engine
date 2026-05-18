# Phase 5 Agent Stabilization Notes

Date: 2026-05-18

Task: `P5-007.1 Sync Phase 5 docs and tighten Agent Plan guardrail`

Latest update: `P5-012 Close Phase 5 with narrow Java/Ukraine agent UX decision`

## Why this exists

After pulling work from another computer, the code and smoke checks were healthy, but the project handoff was not fully clear:

- `ProjectStatus.md`, `Roadmap.md`, and `Tasks.md` already treated `P5-007` as implemented.
- `README.md` and `AGENTS.md` still described `P5-007` as not yet approved or implemented.
- Frontend `Build Plan` used the correct Agent v0 flow, but backend `/api/agent/query-plan` still allowed a direct plan build without the current Agent Plan action/fingerprint.

This stabilization task makes the documentation and backend guardrail match the approved Agent v0 contract.

## Current Phase 5 status

Completed through `P5-012`.

Implemented Phase 5 tasks:

- `P5-001 Define recruiter chat and Search Brief conversation contract`
- `P5-002 Add backend chat-to-brief adapter`
- `P5-003 Replace structured form with recruiter chat UI`
- `P5-004 Make Build Plan produce an approvable Search Plan`
- `P5-005 Instantiate human-approved Agent v0 for Java/Ukraine baseline`
- `P5-006 Add post-results Agent Response in chat`
- `P5-007 Add LLM-assisted Agent Plan/Response with deterministic fallback`
- `P5-007.1 Sync Phase 5 docs and tighten Agent Plan guardrail`
- `P5-008 Chat onboarding and clarification quality`
- `P5-009 Search Brief refinement through chat`
- `P5-010 Result-to-next-iteration loop`
- `P5-011 Apply AI Agent visual direction / dark workspace refresh`
- `P5-012 Close Phase 5 with narrow Java/Ukraine agent UX decision`

Next task to review:

- `P5.5-001 Define backend module boundaries and migration order`

Agreed next direction:

- keep the product focused on one narrow Java/Ukraine flow first;
- Phase 5 is closed as the narrow Java/Ukraine Agent UX foundation;
- add Phase 5.5 technical modularization before Phase 6;
- keep ordinary LLM-assisted agent conversation wording for Phase 7, after the runtime message taxonomy is stable;
- do not expand countries/technologies, add database, or start tool-calling runtime before Phase 5.5 prepares the backend for the approved runtime path.

## Current approved Agent v0 flow

The supported Java/Ukraine baseline flow is:

```text
Recruiter Chat
-> Search Brief
-> Agent Plan
-> proposed Agent Action
-> Build Search Plan
-> Approval
-> Search
-> Agent Response
-> Next iteration suggestion
```

Important guardrail:

`Build Plan` must go through the current Agent Plan. Backend `/api/agent/query-plan` now requires:

- `agent_plan_brief_fingerprint`
- `agent_plan_action`

Missing, stale, mismatched, or unsupported Agent Plan context must be rejected.

## Current OpenAI configuration rule

`OPENAI_API_KEY` and `OPENAI_MODEL` are required for the current primary recruiter chat / AI planner paths.

LLM-assisted Agent Plan/Response wording remains optional in behavior because it has deterministic fallback if OpenAI is unavailable or if LLM output fails validation.

The backend OpenAI Chat Completions requests use `max_completion_tokens`, not the older `max_tokens`, for compatibility with `gpt-5.4-mini` and newer models.

## Execution boundary

No Tavily execution happens during recruiter chat, Agent Plan, or Build Plan.

Tavily execution still requires explicit approval bound to:

- execution action;
- rule-based planner mode;
- query count;
- current `QueryPlan` fingerprint.

AI-generated plans remain non-executable until a later reviewed task explicitly enables that path through deterministic validation and approval.

## Verification

Checks used for this stabilization:

```powershell
.\.venv\Scripts\python.exe -m compileall app scripts
node --check app/static/app.js
.\.venv\Scripts\python.exe scripts\smoke_p5_chat_adapter.py
.\.venv\Scripts\python.exe scripts\smoke_p5_agent_plan.py
.\.venv\Scripts\python.exe scripts\smoke_p5_agent_response.py
.\.venv\Scripts\python.exe scripts\smoke_p5_llm_wording.py
git diff --check
```

`scripts/smoke_p5_agent_plan.py` now verifies that `/api/agent/query-plan` rejects missing Agent Plan action/fingerprint.

`P5-008` added deterministic RU/EN onboarding before OpenAI extraction for greeting-only and near-empty recruiter chat turns. Those turns do not call OpenAI, do not create a ready `Search Brief`, and preserve an existing draft brief. The verification set now also includes chat adapter checks for RU/EN greetings, near-empty input, prohibited refusal, partial/complete intent, and draft preservation.

`P5-009` added deterministic-first Search Brief refinement through `brief_patch.operations`. Supported baseline refinements include Java stack add/remove/replace, seniority, and search depth. Patches are atomic, unsupported mixed patches do not partially apply, last-stack removal without replacement is blocked, and no-op changes preserve downstream state. The frontend now clears stale Agent Plan, Build Plan, QueryPlan, approval/results UI, and Agent Response only when backend returns `stale_state_should_clear = true`.

`P5-010` added deterministic `agent_response.next_iteration_options` after approved search results. Options are grounded only in returned QueryPlan/report/results/quality data, carry `proposed_brief_patch` operations, require approval before any future execution, and are not executable now. Frontend renders them as readable text with no Apply/action buttons. `search_depth` is now preserved as structured-search metadata so `deep` suggestions are grounded. LLM wording does not generate or mutate these options.

`P5-011` applied a CSS-first/UI-only dark AI Agent visual refresh. It updated `app/static/styles.css` with layered dark workspace surfaces, teal/cyan action/status accents, dark controls, compact cards, report metrics, candidate cards, review flags, and score details. It did not change backend code, `index.html`, `app.js`, API contracts, request payloads, state semantics, event flow, search behavior, or product logic.

`P5-012` closed Phase 5 as a docs-only decision. The supported `Backend Developer + Java + Ukraine` flow is ready for Phase 5.5 technical modularization and later Phase 6 human-approved tool runtime, but it is not a complete autonomous recruiter agent. Broader communication scenarios and ordinary LLM-assisted recruiter chat wording are intentionally carried forward to Phase 7 after the Phase 6 runtime/message taxonomy is stable. See `docs/phase-5-closeout.md`.
