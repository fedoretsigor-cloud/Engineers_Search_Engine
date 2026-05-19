# Phase 7 Agent Message Taxonomy

Task: `P7-001 Define agent message taxonomy and lifecycle mapping`

Status: implemented as a docs-only contract.

## Scope

This document defines `Agent Message Taxonomy V0` for the current narrow Java/Ukraine Agent v0 flow.

The taxonomy covers recruiter-visible agent messages across chat, Search Brief, Agent Actions, plan, status, and results surfaces. It defines message types, lifecycle mapping, source-of-truth ownership, deterministic-only boundaries, and future LLM wording eligibility.

This document does not change backend code, frontend code, prompts, runtime behavior, Tavily execution, OpenAI behavior, approval behavior, Search Brief extraction, QueryPlan generation, candidate results, scoring, filtering, dedupe, location logic, snapshots, or product scope.

## Product Boundary

The Agent remains human-approved, not autonomous.

Allowed behavior:

- suggest;
- prepare;
- explain;
- validate;
- analyze;
- summarize;
- propose non-executable next iterations.

Prohibited behavior:

- direct web-search by the agent outside the approved backend search pipeline;
- LinkedIn login;
- LinkedIn scraping or restriction bypass;
- automatic candidate messaging;
- user or third-party account actions;
- autonomous execution.

Search execution must remain behind explicit recruiter approval and backend-owned fingerprints.

## Surfaces

| Surface | Meaning |
|---|---|
| `chat` | Assistant/recruiter conversation messages. |
| `brief_panel` | Visible Search Brief summary, assumptions, missing fields, and readiness state. |
| `action_queue` | `Agent Actions` items such as Build Search Plan and Run Search. |
| `plan_panel` | Visible QueryPlan/Search Plan, planner explanation, validation/fallback state, and approval notice. |
| `status_panel` | Compact status text such as chat, plan, results, and report statuses. |
| `results_panel` | Result/report outcome messaging. |

The same lifecycle event may render on multiple surfaces, but every rendered message must map back to a stable `message_type` and backend-owned source-of-truth facts.

## Existing State Sources

The taxonomy maps to existing states. It does not create a parallel runtime state machine.

Recruiter chat states:

- `needs_clarification`;
- `ready_for_planning`;
- `refused`.

Agent Plan statuses:

- `needs_clarification`;
- `unsupported`;
- `supported`.

Planner statuses:

- `validated_not_executable`;
- `rejected`;
- `rule_based`;
- `rule_based_fallback`;
- related current planner response states.

Agent Runtime states:

- `brief_draft`;
- `brief_ready`;
- `tool_proposed`;
- `approval_pending`;
- `approved`;
- `executing`;
- `observed`;
- `blocked`;
- `error`.

Frontend action display states:

- `blocked`;
- `ready`;
- `ready_for_approval`;
- `running`;
- `completed`;
- `stale`;
- `failed`.

## Source Of Truth Owners

| Source of truth | Owns |
|---|---|
| Search Brief validation | Brief readiness, missing fields, normalized brief values, supported-flow validation. |
| Deterministic brief patch/refinement result | `brief_patch`, patch validation result, normalized brief diff, `brief_changed`, `stale_state_should_clear`. |
| Agent Plan backend response | Agent Plan status, supported/unsupported/needs-clarification state, proposed action, brief fingerprint. |
| QueryPlan/planner response | QueryPlan/Search Plan rows, planner mode, plan status, validation/fallback state, warnings, assumptions, plan fingerprint. |
| Backend runtime response envelope | Runtime state, pending approvals, runtime errors, tool call metadata, runtime approval state. |
| Backend tool result/report | Search report counts, query success/failure, deduped candidates, filters, dedupe metrics, result observations. |
| Backend service/tool/configuration availability check | OpenAI/LLM and Tavily service/configuration availability. |
| Frontend transient UI state derived from current backend data | Temporary processing/status messages while preparing a plan, preparing approval, or running an approved request. |
| Structured error envelope | Validation/runtime/system errors returned by backend contracts. |

## Happy Path

```text
onboarding
-> clarification_question
-> brief_summary
-> agent_plan
-> query_plan_ready
-> planner_explanation
-> approval_required
-> runtime_action_pending
-> execution_started
-> execution_completed
-> search_result_summary
-> agent_response
-> next_iteration_options
```

## Interrupt And Side Paths

```text
brief_refinement_applied
brief_refinement_rejected
validation_feedback
safety_refusal
planning_needs_clarification
agent_plan_unsupported
query_plan_preview
query_plan_rejected
planner_explanation
runtime_action_rejected
runtime_blocked
tool_unavailable
execution_failed
search_result_summary
transient_status
empty_state
system_error
```

## Taxonomy Table

| message_type | surface | allowed_state_or_lifecycle_group | source_of_truth | deterministic_only | llm_overlay_allowed_later | forbidden_claims_or_mutations |
|---|---|---|---|---|---|---|
| `onboarding` | `chat` | Empty, greeting-only, or near-empty recruiter chat before enough Search Brief facts exist. | Search Brief validation; deterministic onboarding guard. | No | Candidate later after P7 routing/style policy. | Must not imply a Search Brief exists, call tools, create a plan, execute search, or bypass clarification. |
| `clarification_question` | `chat` | Recruiter chat `needs_clarification`. | Search Brief validation. | No | Candidate later, but only for wording around one backend-selected missing field. | Must not invent missing fields, ask multiple unrelated questions, mutate Search Brief, create Agent Plan, build QueryPlan, or imply execution readiness. |
| `brief_summary` | `chat`, `brief_panel` | Recruiter chat `ready_for_planning` or visible Search Brief review. | Search Brief validation. | No | Candidate later with facts contract. | Must not change normalized brief values, supported values, readiness, assumptions, missing fields, filters, or planner mode. |
| `brief_refinement_applied` | `chat`, `brief_panel`, `status_panel` | Existing Search Brief was safely changed by a supported deterministic patch. | Deterministic brief patch/refinement result. | Yes | No | Must not change `brief_patch.operations`, `normalized_brief`, `brief_changed`, `stale_state_should_clear`, missing fields, planner state, Agent Plan, QueryPlan, approval, runtime state, results, or downstream clearing facts. |
| `brief_refinement_rejected` | `chat`, `brief_panel`, `status_panel` | Requested Search Brief change was not safely applicable. | Deterministic brief patch/refinement result; structured error envelope. | Yes | No | Must not imply the brief changed, state was cleared, new plan is required, or a partial patch was applied unless backend explicitly returned those facts. |
| `validation_feedback` | `chat`, `brief_panel`, `plan_panel`, `status_panel`, `results_panel` | User-correctable backend `validation_errors` or `errors`. | Structured error envelope. | Yes | No | Must not soften/change error codes, stale facts, fingerprints, approval facts, executable state, planner state, runtime state, Search Brief values, QueryPlan content, tool calls, candidates, counts, or result facts. |
| `safety_refusal` | `chat`, `status_panel` | Recruiter request violates absolute product boundaries. | Search Brief validation; product safety guard. | Yes | No | Must not propose workarounds for direct web-search bypass, LinkedIn login/scraping, candidate messaging, account actions, or autonomous execution. |
| `planning_needs_clarification` | `chat`, `plan_panel`, `status_panel` | Agent Plan or QueryPlan was requested before the Search Brief was ready enough. | Search Brief validation; Agent Plan backend response; QueryPlan/planner response. | Yes | No | Must not invent missing fields, mutate brief, create Agent Plan, create QueryPlan, create proposed actions, change approval state, or imply execution is possible. |
| `agent_plan` | `chat`, `action_queue` | Agent Plan status `supported`; ready brief has a supported proposed planning action. | Agent Plan backend response. | No | Current bounded overlay exists for `agent_plan.message` and wording provenance only. | Must not change `proposed_action`, brief fingerprint, supported state, approval state, executable flags, planner mode, tool calls, QueryPlan, filters, counts, candidates, or execution claims. |
| `agent_plan_unsupported` | `chat`, `action_queue`, `status_panel` | Agent Plan status `unsupported` for a ready brief outside Agent v0 scope. | Agent Plan backend response. | Yes | No | Must not silently fall back to non-agent Build Plan, create proposed actions, broaden countries/roles/technologies, or imply execution support. |
| `query_plan_ready` | `plan_panel`, `action_queue`, `status_panel` | Executable backend Search Plan is visible and reviewable before explicit approval. | QueryPlan/planner response. | Yes | No | Must not change QueryPlan rows, planner mode, plan fingerprint, adapted request, approval requirement, runtime readiness, filters, scoring, dedupe, or location logic. |
| `query_plan_preview` | `plan_panel`, `status_panel` | Non-executable QueryPlan preview, usually AI `validated_not_executable`. | QueryPlan/planner response. | Yes | No | Must not present the preview as approval-ready, runtime-ready, Run Search-ready, or executable. |
| `planner_explanation` | `plan_panel`, `chat` | Visible plan explanation, fallback reason, warnings, assumptions, or diagnostics. | QueryPlan/planner response. | No | Candidate later with strict planner facts payload. | Must not change QueryPlan content, planner status, approval state, execution state, fingerprints, runtime readiness, or result claims. |
| `query_plan_rejected` | `plan_panel`, `status_panel` | Planner validation failed or produced no usable plan. | QueryPlan/planner response; structured error envelope. | Yes | No | Must not create fallback execution, mark approval available, hide validation errors, or imply a rejected plan can run. |
| `approval_required` | `plan_panel`, `action_queue`, `status_panel` | Executable backend Search Plan requires explicit recruiter approval. | Backend runtime response envelope; QueryPlan/planner response. | Yes | No | Must not approve on behalf of user, imply automatic execution, mutate approval state, or make `query_plan_preview` actionable. |
| `runtime_action_pending` | `action_queue`, `status_panel` | Backend-owned pending runtime approval exists for the current visible plan. | Backend runtime response envelope. | Yes | No | Must not change pending approval, fingerprints, idempotency key, tool name, tool input, runtime context, or approval status. |
| `runtime_action_rejected` | `action_queue`, `status_panel`, `results_panel` | Approval/action is missing, mismatched, stale, invalid, or rejected before execution. | Backend runtime response envelope; structured error envelope. | Yes | No | Must not imply execution started, mutate approval, refresh fingerprints, rerun prepare automatically, or bypass runtime validation. |
| `runtime_blocked` | `action_queue`, `status_panel`, `results_panel` | Runtime rejected or blocked the action before execution. | Backend runtime response envelope; structured error envelope. | Yes | No | Must not imply Tavily ran, candidates changed, results exist, or the block can be bypassed. |
| `execution_started` | `status_panel`, `results_panel` | Approved execution request is in progress. | Frontend transient UI state derived from current backend data. | Yes | No | Must not include counts, candidates, success, quality, result claims, or statements that Tavily completed. |
| `execution_completed` | `status_panel`, `results_panel` | Backend runtime returned an observed successful tool result. | Backend runtime response envelope; backend tool result/report. | Yes | No | Must not alter report facts, candidates, counts, query success/failure, filters, dedupe, scoring, location logic, ordering, or Agent Response facts. |
| `execution_failed` | `status_panel`, `results_panel` | Approved execution started but backend runtime/tool execution failed. | Backend runtime response envelope; structured error envelope. | Yes | No | Must not imply partial success, invent candidates, retry automatically, hide failure fields, or call Tavily again. |
| `tool_unavailable` | `chat`, `plan_panel`, `status_panel`, `results_panel` | Required backend service, tool, or configuration is unavailable. | Backend service/tool/configuration availability check. | Yes | No | Must not present missing OpenAI/LLM or Tavily configuration as recruiter input error, system success, or bypassable state. |
| `search_result_summary` | `results_panel`, `status_panel` | Search/report summary after backend returned result facts. | Backend tool result/report. | Yes | No | Must not alter raw/unique/duplicate/failed counts, candidates, filter metrics, dedupe metrics, location facts, scores, ordering, or report mode. |
| `agent_response` | `chat`, `results_panel` | Post-results agent summary grounded in returned Search Plan/report/results. | Backend tool result/report; deterministic Agent Response builder. | No | Current bounded overlay exists for `agent_response.message`, optional wording inside existing limitations, optional `llm_warnings`, and provenance only. | Must not change summary facts, quality notes, suggested next actions, next iteration options, proposed actions, fingerprints, counts, filters, scoring, dedupe, location logic, candidates, or result ordering. |
| `next_iteration_options` | `chat`, `results_panel` | Non-executable suggestions after results. | Backend tool result/report; current Search Brief metadata. | Yes | No | Must not add, remove, reorder, select, mutate, or execute options, `proposed_brief_patch`, operations, approval flags, executable flags, Build Plan, Tavily, LinkedIn, web search, multi-wave, or runtime execution. |
| `transient_status` | `status_panel`, `action_queue` | Temporary UI status while preparing Agent Plan, building plan, preparing approval, or running approved execution. | Frontend transient UI state derived from current backend data. | Yes | No | Must not create durable backend facts, imply success/failure, mutate state, or make unavailable actions available. |
| `empty_state` | `brief_panel`, `plan_panel`, `action_queue`, `results_panel`, `status_panel` | Idle/no-data guidance, such as no action/report/results yet. | Frontend transient UI state derived from current backend data. | Yes | No | Must not imply data exists, fabricate summaries, create plans, or suggest execution readiness. |
| `system_error` | `chat`, `plan_panel`, `status_panel`, `results_panel` | User-visible technical failure when no more precise type applies. | Structured error envelope. | Yes | No | Must not hide more specific safety, validation, runtime, execution, or tool-unavailable states; must not invent recovery or result facts. |

## Deterministic-Only Rules

These message types are deterministic-only in Phase 7 unless a later approved task explicitly changes them with routing, bounded payloads, validation, fallback, and provenance:

- `safety_refusal`;
- `brief_refinement_applied`;
- `brief_refinement_rejected`;
- `validation_feedback`;
- `planning_needs_clarification`;
- `agent_plan_unsupported`;
- `query_plan_ready`;
- `query_plan_preview`;
- `query_plan_rejected`;
- `approval_required`;
- `runtime_action_pending`;
- `runtime_action_rejected`;
- `runtime_blocked`;
- `execution_started`;
- `execution_completed`;
- `execution_failed`;
- `tool_unavailable`;
- `search_result_summary`;
- `next_iteration_options`;
- `transient_status`;
- `empty_state`;
- `system_error`.

Any message that communicates approval, fingerprints, stale context, execution state, tool availability, policy boundaries, backend-owned executable state, counts, candidate counts, filter metrics, dedupe metrics, report metrics, brief mutation state, downstream stale-state clearing, or next-option executability is deterministic-only.

LLM wording must not create message types, change lifecycle state, change surfaces, change approval state, alter fingerprints, alter executable flags, alter tool calls, alter QueryPlan, alter Search Brief, alter brief refinement results, alter stale-state clearing, alter counts, alter candidates, alter scoring, alter filters, alter dedupe, alter location logic, alter next-iteration options, or claim execution/result success not returned by backend.

## Existing Bounded LLM Overlay

`P5-007` already allows bounded LLM-assisted wording for `agent_plan` and `agent_response` after deterministic objects are built.

Current wording/provenance metadata:

- `wording_mode`;
- `fallback_reason`;
- `llm_warnings`.

For `agent_plan`, accepted LLM output may replace only:

- `agent_plan.message`;
- wording provenance metadata.

For `agent_response`, accepted LLM output may replace only:

- `agent_response.message`;
- optional wording inside existing `limitations`;
- optional `llm_warnings`;
- wording provenance metadata.

The overlay must not change facts, summary facts, quality notes, suggested next actions, next iteration options, proposed actions, fingerprints, counts, approval state, executable flags, planner mode, filters, scoring, dedupe, location logic, candidates, or result ordering.

All other message types remain non-LLM until a later approved Phase 7 task adds routing, bounded payloads, validation, fallback, and provenance for that type.

## Executable Plan Vs Preview

`query_plan_ready` applies only when the visible plan is a backend executable Search Plan according to current planner/runtime rules, such as `rule_based` or `rule_based_fallback` planner data with:

- valid plan fingerprint;
- adapted structured request;
- approval requirement;
- runtime-compatible execution path.

`query_plan_preview` applies when a visible QueryPlan is shown for review, diagnostics, or comparison but is not executable, such as AI `validated_not_executable`.

`approval_required` must not be rendered as actionable for `query_plan_preview`.

LLM wording must not reinterpret:

- `execution_allowed`;
- `execution_approval_required`;
- `planner_mode`;
- `plan_status`;
- `latestExecutablePlan`;
- plan fingerprints;
- approval availability;
- runtime readiness;
- whether a plan can execute.

## Brief Refinement

`brief_refinement_applied` and `brief_refinement_rejected` are grounded only in:

- backend `brief_patch`;
- patch validation result;
- normalized Search Brief diff;
- `brief_changed`;
- `stale_state_should_clear`.

`brief_refinement_applied` may say the Search Brief changed only when backend returned `brief_changed = true`.

It may say a new plan is required only when backend returned `stale_state_should_clear = true`.

`brief_refinement_rejected` may explain why the patch was rejected, but it must not imply the brief changed, downstream state was cleared, or a new plan is required unless backend explicitly returned those facts.

## Next Iteration Options

`next_iteration_options` is deterministic-only and inert.

Options are grounded only in:

- returned Search Plan / QueryPlan;
- report;
- results;
- quality data;
- current Search Brief metadata.

Options may propose future `brief_patch` operations, but the options themselves are not accepted, applied, or executed.

Every option must preserve:

- `requires_approval_before_execution = true`;
- `is_executable_now = false`;
- no frontend Apply/action button;
- no automatic Build Plan;
- no `/api/agent/query-plan` call;
- no Tavily call;
- no LinkedIn access;
- no web search;
- no multi-wave execution;
- no runtime execution.

LLM wording may mention deterministic next-iteration options only as text. It must not add, remove, reorder, select, mutate, or make executable any option or proposed patch.

## Result And Execution Claims

`execution_started` is transient and non-result-bearing.

It must not include:

- counts;
- candidates;
- success claims;
- quality claims;
- result claims;
- statements that Tavily completed.

Counts, candidates, success/failure, quality, and result conclusions are allowed only after `execution_completed` / `agent_response`, when the backend returned a tool result/report.

## Message Text Vs Data Labels

The taxonomy covers recruiter-visible agent message text. It does not turn every frontend label or data value into an LLM wording target.

Out of scope for LLM wording unless a later task explicitly changes UI copy policy:

- metric labels such as `Raw`, `Unique`, `Duplicates`, `Failed queries`;
- candidate fields such as name, headline, location, role, technology, stack, seniority, score, flags, snippets, and query-source metadata;
- Search Brief field labels such as `Role`, `Technology`, `Stack`, `Location`, `Depth`, `Seniority`;
- button labels such as `Build Plan`, `Approve & Search`, `Send`, and `Reset`;
- query IDs;
- candidate URLs;
- candidate snippets;
- quality scores;
- filters;
- dedupe/location/scoring facts.

## Error Classification Priority

Use this order when multiple classifications could apply:

1. `safety_refusal` for prohibited product behavior.
2. `tool_unavailable` for missing/unavailable required backend service, tool, or configuration.
3. `validation_feedback` for recruiter-correctable structured validation errors.
4. `runtime_blocked` for runtime rejection before execution.
5. `execution_failed` only after approved execution started and failed.
6. `system_error` only as fallback when no more specific message type applies.

Do not collapse these into `system_error`. The recruiter needs different wording and next-step expectations for each case.

## Future Task Handoff

This document is the stable taxonomy input for the next Phase 7 tasks:

- `P7-002` defines the exact message facts and source-of-truth contract.
- `P7-003` defines wording style and language policy.
- `P7-004` builds deterministic source messages for approved message types.
- `P7-005` defines LLM routing and gating policy.
- `P7-006` defines bounded LLM wording payloads and prompt contract.
- `P7-007` adds wording validation, fallback, and provenance metadata.
- `P7-008` adds frontend rendering for typed agent messages.
- `P7-009` adds golden conversation scenario regression tests.
- `P7-010` closes Phase 7 with wording quality and guardrail evaluation.
