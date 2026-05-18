# Phase 5 Agent Stabilization Notes

Date: 2026-05-18

Task: `P5-007.1 Sync Phase 5 docs and tighten Agent Plan guardrail`

## Why this exists

After pulling work from another computer, the code and smoke checks were healthy, but the project handoff was not fully clear:

- `ProjectStatus.md`, `Roadmap.md`, and `Tasks.md` already treated `P5-007` as implemented.
- `README.md` and `AGENTS.md` still described `P5-007` as not yet approved or implemented.
- Frontend `Build Plan` used the correct Agent v0 flow, but backend `/api/agent/query-plan` still allowed a direct plan build without the current Agent Plan action/fingerprint.

This stabilization task makes the documentation and backend guardrail match the approved Agent v0 contract.

## Current Phase 5 status

Completed through `P5-007.1`.

Implemented Phase 5 tasks:

- `P5-001 Define recruiter chat and Search Brief conversation contract`
- `P5-002 Add backend chat-to-brief adapter`
- `P5-003 Replace structured form with recruiter chat UI`
- `P5-004 Make Build Plan produce an approvable Search Plan`
- `P5-005 Instantiate human-approved Agent v0 for Java/Ukraine baseline`
- `P5-006 Add post-results Agent Response in chat`
- `P5-007 Add LLM-assisted Agent Plan/Response with deterministic fallback`
- `P5-007.1 Sync Phase 5 docs and tighten Agent Plan guardrail`

Next task to review:

- `P5-008 Improve recruiter chat conversational tone and greeting behavior`

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
