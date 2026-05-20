# Phase 7 LLM Routing And Gating Policy

Task: `P7-005 Define LLM routing and gating policy for conversation wording`

Status: implemented as a docs-only contract.

## Scope

This document defines `LLM Routing and Gating Policy V0` for Phase 7 conversation wording.

It extends:

- `docs/phase-7-agent-message-taxonomy.md`;
- `docs/phase-7-message-facts-contract.md`;
- `docs/phase-7-agent-wording-style-policy.md`;
- the deterministic source-message layer in `app/agent_messages.py`;
- the current bounded wording overlay in `app/agent_wording.py`.

This document does not change backend code, frontend code, prompts, payload schemas, API response fields, runtime behavior, Tavily execution, OpenAI behavior, approval behavior, Search Brief extraction, QueryPlan generation, candidate results, scoring, filtering, dedupe, location logic, snapshots, persistence, database, shortlist, account behavior, or product scope.

## Core Rule

LLM wording is forbidden unless this routing policy explicitly allows it and all gates pass.

The LLM never owns facts, state, actions, approval, Search Brief values, QueryPlan rows, runtime transitions, candidate data, counts, filters, scoring, dedupe, location logic, or next-iteration executability.

The current product remains human-approved. Search execution must stay behind explicit recruiter approval and backend-owned fingerprints.

## Product Boundary

Allowed agent behavior:

- suggest;
- prepare;
- explain;
- validate;
- summarize;
- analyze returned results;
- propose non-executable next iterations.

Prohibited behavior:

- direct web-search by the agent outside the approved backend search pipeline;
- LinkedIn login;
- LinkedIn scraping or restriction bypass;
- automatic candidate messaging;
- user or third-party account actions;
- autonomous execution.

LLM wording must not present prohibited behavior as available, planned, completed, partially completed, or available through a workaround.

## Routing Categories

Routing category names follow `llm_payload_eligibility_later` from `docs/phase-7-message-facts-contract.md`.

| Category | Meaning |
|---|---|
| `current_bounded_text_only` | The current bounded wording overlay may run for approved text fields only. |
| `candidate_for_future_bounded_payload` | A later task may define bounded payload/prompt contracts, but the type remains non-LLM until validation, fallback, provenance, and a later routing approval exist. |
| `frontend_transient_only` | Frontend-derived temporary UI state only; not an LLM wording target. |
| `never` | No LLM wording for this message type in current Phase 7 policy. |

`diagnostic_only` exists in the facts contract for producer inventory. It is not a recruiter-visible message routing category in this policy.

## Routing Matrix

Every P7 message type has exactly one routing category.

| message_type | Routing category | Decision |
|---|---|---|
| `onboarding` | `candidate_for_future_bounded_payload` | Future candidate only. It may become more natural later, but must not imply a brief, plan, tool call, approval, or execution exists. |
| `clarification_question` | `candidate_for_future_bounded_payload` | Future candidate only. It may later reword one backend-selected missing-field question, but must not invent fields or ask unrelated questions. |
| `brief_summary` | `candidate_for_future_bounded_payload` | Future candidate only. It may later make normalized brief facts more natural, but must not change role, technology, stack, location, readiness, assumptions, filters, or planner mode. |
| `brief_refinement_applied` | `never` | Deterministic-only. Patch, `brief_changed`, and `stale_state_should_clear` must stay exact. |
| `brief_refinement_rejected` | `never` | Deterministic-only. Must not imply partial application or hidden mutation. |
| `validation_feedback` | `never` | Deterministic-only. Error semantics and codes must not drift. |
| `safety_refusal` | `never` | Must stay precise and must not suggest workarounds. |
| `planning_needs_clarification` | `never` | Deterministic-only. Must not invent readiness, Agent Plan, QueryPlan, proposed action, or execution possibility. |
| `agent_plan` | `current_bounded_text_only` | Existing bounded overlay may replace only `agent_plan.message` and wording metadata. |
| `agent_plan_unsupported` | `never` | Deterministic-only. Must not broaden Agent v0 scope or create proposed actions. |
| `query_plan_ready` | `never` | Deterministic-only. Search Plan readiness, approval facts, and fingerprints must stay backend-owned. |
| `query_plan_preview` | `never` | Deterministic-only. Non-executable preview must not become approval-ready or runnable through wording. |
| `planner_explanation` | `candidate_for_future_bounded_payload` | Future candidate only. It may later word backend planner facts, warnings, assumptions, fallback reasons, or coverage policy only. |
| `query_plan_rejected` | `never` | Deterministic-only. Must not imply rejected plans can run or fallback executed automatically. |
| `approval_required` | `never` | Approval boundary must be exact. The agent must not approve or imply automatic execution. |
| `runtime_action_pending` | `never` | Backend-owned pending approval and fingerprints must stay exact. |
| `runtime_action_rejected` | `never` | Deterministic-only. Stale/mismatched approval wording must stay exact. |
| `runtime_blocked` | `never` | Deterministic-only. Must not imply Tavily ran, results changed, or the block can be bypassed. |
| `execution_started` | `frontend_transient_only` | Frontend transient state only. No counts, candidates, quality, success, or result claims. |
| `execution_completed` | `never` | Deterministic-only. Completion facts, counts, candidates, and report metrics must stay backend-owned. |
| `execution_failed` | `never` | Deterministic-only. Must not imply partial success, invent candidates, or retry automatically. |
| `tool_unavailable` | `never` | Deterministic-only. Must not present missing configuration as recruiter input error or suggest bypass. |
| `search_result_summary` | `never` | Deterministic-only. Counts/report facts must stay exact. |
| `agent_response` | `current_bounded_text_only` | Existing bounded overlay may replace only `agent_response.message`, optional wording inside existing `limitations`, optional `llm_warnings`, and wording metadata. |
| `next_iteration_options` | `never` | Deterministic-only and inert. Must not add, remove, reorder, select, mutate, or execute options. |
| `transient_status` | `frontend_transient_only` | Frontend request state only. Must clear/update when backend state changes. |
| `empty_state` | `frontend_transient_only` | UI guidance only. Must not imply data, plans, or results exist. |
| `system_error` | `never` | Deterministic-only fallback classification. Must not hide more specific safety, validation, runtime, execution, or tool-unavailable states. |

## Current Allowed Bounded Overlay

The only current LLM-assisted wording paths are:

- `agent_plan`;
- `agent_response`.

For `agent_plan`, accepted LLM output may replace only:

- `agent_plan.message`;
- wording metadata: `wording_mode`, `fallback_reason`, `llm_warnings`.

For `agent_response`, accepted LLM output may replace only:

- `agent_response.message`;
- optional wording inside existing `limitations`;
- optional `llm_warnings`;
- wording metadata: `wording_mode`, `fallback_reason`, `llm_warnings`.

The overlay must not change:

- `proposed_action`;
- Search Brief values;
- fingerprints;
- approval state;
- executable flags;
- planner mode;
- QueryPlan rows;
- runtime state;
- tool calls;
- summary facts;
- quality notes;
- suggested next actions;
- next-iteration options;
- counts;
- filters;
- scoring;
- dedupe;
- location logic;
- candidates;
- result ordering.

## Gating Policy

LLM wording may be attempted only when all gates pass.

Required gates:

1. `message_type` is known in `docs/phase-7-agent-message-taxonomy.md`.
2. `message_type` is `current_bounded_text_only` in this policy.
3. Source facts are allowed by `docs/phase-7-message-facts-contract.md`.
4. A deterministic source message/object exists before LLM wording.
5. The wording surface is allowed by `docs/phase-7-agent-wording-style-policy.md`.
6. Language is supported: `en` or `ru`.
7. `OPENAI_API_KEY` and `OPENAI_MODEL` are configured.
8. Source context is fresh:
   - `agent_plan.brief_fingerprint` matches the current Search Brief for Agent Plan wording;
   - Agent Response facts belong to the current completed approved result/report/search plan.
9. The message does not carry approval, runtime, execution, candidate, QueryPlan, Search Brief mutation, or next-option mutation authority.
10. The output can be validated by the current bounded validation layer.

If any gate fails, deterministic source text must be used.

## No-Call Reasons

These are stable internal policy reasons for future implementation and regression tests.

They are not product analytics, telemetry, memory, user tracking, or recruiter-facing blame text.

| no_call_reason | Meaning |
|---|---|
| `message_type_not_allowed` | The message type is known, but routing policy does not allow LLM wording for it. |
| `unknown_message_type` | The message type is not in the approved P7 taxonomy. |
| `missing_deterministic_source_message` | There is no backend-owned deterministic source text/object to rewrite. |
| `facts_contract_not_available` | Allowed facts for this message type are not defined or cannot be mapped safely. |
| `style_policy_not_available` | The message surface/language cannot be validated against the wording style policy. |
| `unsupported_language` | The requested message language is not supported by Phase 7 wording policy. |
| `openai_not_configured` | `OPENAI_API_KEY` or `OPENAI_MODEL` is missing. |
| `stale_context` | Search Brief, Agent Plan, QueryPlan, runtime, or result context is stale or fingerprint-mismatched. |
| `forbidden_state_or_surface` | The message represents safety, approval, runtime, execution, tool availability, exact result facts, candidate facts, or executable next actions. |
| `payload_contract_not_available` | `P7-006` has not defined a bounded payload/prompt contract for this message type. |
| `validation_contract_not_available` | `P7-007` has not defined validation, fallback, and provenance for this message type. |
| `llm_response_invalid` | The LLM response fails shape, language, safety, fact, number, action, or mutation validation. |

## Fallback Policy

Use deterministic fallback when:

- OpenAI config is missing;
- request times out;
- request fails;
- response is empty;
- response is not JSON;
- response has the wrong shape;
- response includes unknown or disallowed fields;
- response has the wrong language;
- response includes prohibited content;
- response adds disallowed numbers/facts;
- response tries to change actions, approval, runtime, QueryPlan, Search Brief, candidates, counts, filters, scoring, dedupe, location logic, or next-iteration options;
- source context is stale.

Fallback must not be presented as:

- recruiter input error;
- search failure;
- planner failure;
- proof that OpenAI, Tavily, or the runtime succeeded or failed outside returned backend facts.

Missing OpenAI config for wording is a wording fallback condition, not a recruiter input error and not a search failure.

## Future Candidate Rules

`candidate_for_future_bounded_payload` does not mean LLM wording is enabled.

Future candidates remain disabled until later approved work does all of the following:

1. `P7-006` defines a bounded payload/prompt contract for the message type.
2. `P7-007` defines validation, deterministic fallback, and lightweight provenance.
3. A later approved routing change explicitly enables the message type.
4. Golden scenario tests cover allowed, blocked, fallback, and no-call behavior.

Future candidate message types must still obey all product boundaries and facts/style contracts.

## Frontend Transient Rules

`frontend_transient_only` messages are not LLM wording targets.

They may be rendered by the frontend as temporary UI state derived from current backend data, but they must not:

- create durable backend facts;
- override backend state;
- alter approval;
- alter fingerprints;
- convert a preview into an executable plan;
- create result/count/candidate facts;
- mark stale state as current;
- retry, build, approve, or execute anything automatically.

## Handoff

`P7-006 Add bounded LLM wording payloads and prompt contract`:

- may define payload/prompt contracts only for message types allowed by this policy;
- must keep current `current_bounded_text_only` paths compatible;
- may define payloads for `candidate_for_future_bounded_payload` types, but must not enable execution of those LLM paths by itself.

`P7-007 Add wording validation, fallback, and provenance metadata`:

- must enforce this routing policy;
- must preserve deterministic fallback;
- must add lightweight internal provenance/version metadata without creating product analytics, telemetry, memory, or user tracking.

`P7-008 Add frontend rendering for typed agent messages`:

- may render typed messages;
- must not use LLM routing as state authority;
- must not make blocked/future-candidate messages executable.

`P7-009 Add golden conversation scenario regression tests`:

- should assert routing decisions;
- should assert no-call reasons;
- should assert deterministic fallback behavior;
- should assert that blocked message types do not call LLM wording;
- should assert provenance/version expectations from `P7-007`.

## Verification

This task is docs-only.

Required verification:

```powershell
git diff --check
```

No Python/frontend/backend regression checks are required for this task unless later edits change code.
