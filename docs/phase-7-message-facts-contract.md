# Phase 7 Agent Message Facts Contract

Task: `P7-002 Define message facts and source-of-truth contract`

Status: implemented as a docs-only contract.

## Scope

This document defines `Agent Message Facts Contract V0` for the current narrow Java/Ukraine Agent v0 flow.

It extends `docs/phase-7-agent-message-taxonomy.md` by defining which facts every `message_type` may communicate, which backend/frontend producer owns those facts, which derived claims are allowed, and which facts remain forbidden by default.

This document does not change backend code, frontend code, prompts, API response fields, schemas, runtime behavior, Tavily execution, OpenAI behavior, approval behavior, Search Brief extraction, QueryPlan generation, candidate results, scoring, filtering, dedupe, location logic, snapshots, or product scope.

## Core Rule

Message wording may be improved later, but facts remain backend-/contract-owned.

LLM wording never owns facts. It may only rewrite approved text fields when a later approved routing, payload, validation, fallback, and provenance task allows that specific message type.

Any fact or derived claim not explicitly allowed by this contract is forbidden by default.

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

## Contract Shape

Every allowed fact must be represented using this shape, either in the whitelist table below or in a future schema derived from it:

```text
message_type
allowed_fact_key
source_object
source_owner
required_or_optional
nullable_or_default
allowed_derived_claims
forbidden_derived_claims
freshness_or_fingerprint_rule
llm_payload_eligibility_later
notes
```

`llm_payload_eligibility_later` values:

- `never`;
- `current_bounded_text_only`;
- `candidate_for_future_bounded_payload`;
- `frontend_transient_only`;
- `diagnostic_only`.

## Source Owners

| Source owner | Owns |
|---|---|
| Search Brief backend validation | `normalized_brief`, readiness, missing fields, clarifying questions, supported-flow validation, Search Brief assumptions, Search Brief summary. |
| deterministic brief patch/refinement backend | `brief_patch`, patch validation result, `brief_changed`, `stale_state_should_clear`, normalized brief diff after safe patching. |
| Agent Plan backend | `agent_plan_status`, `agent_plan`, `agent_plan.brief_fingerprint`, `agent_plan.proposed_action`, Agent Plan supported/unsupported/needs-clarification facts. |
| QueryPlan/planner backend | QueryPlan rows, planner mode, plan status, validation/fallback state, warnings, assumptions, plan fingerprint, adapted structured request, approval notice. |
| Agent Runtime backend | Runtime state, tool calls, pending approvals, runtime approval validation, runtime errors, tool result envelopes, runtime observations. |
| approved backend search executor/report builder | Approved search responses, report counts, query success/failure, dedupe metrics, filter metrics, candidate result facts, snapshots. |
| deterministic Agent Response backend | `agent_response.summary_facts`, `quality_notes`, `limitations`, `suggested_next_actions`, `next_iteration_options`, `source`, `requires_approval_for_execution`. |
| backend service/config availability check | OpenAI/LLM availability and Tavily availability facts. |
| frontend transient UI derived from current backend data | Temporary status such as preparing Agent Plan, building plan, preparing approval, running approved search, idle/empty display. |
| frontend exception/catch display derived from current request failure | Temporary catch-path display text when no more specific backend error was returned. |
| diagnostic/legacy backend route output | Diagnostic route facts that are not part of the primary Agent v0 UI path unless explicitly whitelisted. |
| disabled legacy route output | Disabled raw search route error facts only. |
| structured error envelope | `field`, `code`, `message`, classification, and user-correctable status for validation/runtime/system errors. |
| wording/provenance metadata | `message_type`, `surface`, `language`, `taxonomy_version`, `facts_contract_version`, `wording_mode`, `fallback_reason`, `llm_warnings`, source/debug/version facts. |

## Producer Inventory

### Primary Agent V0 UI Path

```text
/api/recruiter-chat/turn
-> /api/agent/plan
-> /api/agent/query-plan
-> /api/agent/runtime/turn prepare
-> /api/agent/runtime/turn execute_approved
-> runtime tool result / approved search response / agent_response
```

| Producer | Classification | Recruiter-visible fact source |
|---|---|---|
| `POST /api/recruiter-chat/turn` | Primary UI path | Yes, for chat state, Search Brief facts, assistant message, clarification, safety refusal, brief patch/refinement state, validation errors, and stale-state clearing. |
| `POST /api/agent/plan` | Primary UI path | Yes, for Agent Plan status, supported action, unsupported/needs-clarification state, brief fingerprint, and current bounded Agent Plan wording metadata. |
| `POST /api/agent/query-plan` | Primary UI path | Yes, for executable backend Search Plan, non-executable preview/rejection, planner explanation, validation/fallback, plan fingerprint, adapted structured request, warnings, assumptions, and approval notice. |
| `POST /api/agent/runtime/turn` prepare | Primary UI path | Yes, for runtime approval preparation, tool call metadata, pending approval, runtime blocked/tool unavailable errors. |
| `POST /api/agent/runtime/turn` execute_approved | Primary UI path | Yes, for observed execution, tool result envelope, runtime errors, approved search result/report, and runtime observations. |
| Approved single-wave/multi-wave search response inside runtime tool result | Primary UI path through runtime | Yes, for report/result facts after explicit approval. Raw query results are not general wording facts. |
| Deterministic Agent Response builder | Primary UI path after results | Yes, for post-results summary facts, quality notes, limitations, non-executable suggested actions, and next-iteration options. |
| Bounded Agent Plan/Agent Response wording overlay | Primary UI path when configured and validated | Yes, but only for allowed text fields and wording/provenance metadata. |
| Frontend Search Brief, actions, plan, status, results render paths | Primary UI path rendering | Yes, only as transient display facts derived from current backend data. |

### Diagnostic, Legacy, And Disabled Producers

| Producer | Classification | Recruiter-visible fact source |
|---|---|---|
| `POST /api/search-brief/validate` | Diagnostic/internal validation route | Not part of current Agent v0 UI path. May inform contract examples for Search Brief validation only. |
| `POST /api/structured-search/validate` | Diagnostic/internal validation route | Not part of current Agent v0 UI path. May inform structured validation examples only. |
| `POST /api/query-plan` | Legacy/direct QueryPlan route | Not part of current Agent v0 UI path. Must not bypass Agent Plan action/fingerprint facts. |
| `POST /api/ai-query-plan/validate` | Diagnostic AI plan validation route | May inform non-executable `query_plan_preview` / `query_plan_rejected` examples only. It is not an executable product path. |
| `GET /api/agent/tools` | Diagnostic/internal tool contract route | May inform tool metadata docs only. It does not create user-visible action authority. |
| Direct `POST /api/structured-search` | Legacy/backward-compatible approved search route | Not the current frontend execution path. If referenced, facts must match approved backend search response boundaries. |
| Direct `POST /api/structured-search/multi-wave` | Legacy/backward-compatible approved search route | Not the current frontend execution path. If referenced, facts must match approved backend search response boundaries. |
| Disabled legacy `POST /api/search` | Disabled/out of product path | Only its disabled-route error can be represented as `system_error`/`validation_feedback` depending on surface. It must not become a search source. |

## Fact Groups

- Search Brief facts;
- brief patch/refinement facts;
- Agent Plan facts;
- QueryPlan/planner facts;
- approval/runtime facts;
- execution/tool-result facts;
- report/count facts;
- candidate/result summary facts;
- service/tool availability facts;
- frontend transient facts;
- frontend exception/catch-display facts;
- diagnostic/legacy route facts;
- structured error facts;
- wording/provenance facts.

## Message-Type Fact Whitelist

Unless a row explicitly allows a fact, that fact is forbidden for the message type.

| message_type | allowed_fact_key | source_object | source_owner | required_or_optional | nullable_or_default | allowed_derived_claims | forbidden_derived_claims | freshness_or_fingerprint_rule | llm_payload_eligibility_later | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `onboarding` | `language`, `assistant_message`, optional preserved `normalized_brief.brief_status` | `/api/recruiter-chat/turn` onboarding response | Search Brief backend validation | `language` and `assistant_message` required | `normalized_brief` may be null | Greeting/near-empty input needs initial brief details. Current saved ready brief may be preserved only if backend returned it. | Search Brief exists, plan exists, tools ran, execution is possible. | Current chat turn only. | `candidate_for_future_bounded_payload` | Must not create Search Brief facts from greeting text. |
| `clarification_question` | `state`, `language`, `next_question`, `missing_fields`, `clarifying_questions`, `normalized_brief` | `/api/recruiter-chat/turn` | Search Brief backend validation | `state`, `language`, and one question required | `normalized_brief` may be partial | Ask one backend-selected missing-field question. | Invented missing fields, multiple unrelated questions, planner readiness. | Current normalized brief only. | `candidate_for_future_bounded_payload` | Question wording may later be improved, but missing field remains backend-selected. |
| `brief_summary` | `state`, `language`, `normalized_brief`, `summary`, `assumptions`, `can_build_plan`, `recommended_planner_mode` | `/api/recruiter-chat/turn`; Search Brief summary renderer | Search Brief backend validation | `normalized_brief` required when ready | `summary` may be null only outside ready state | Search Brief is ready only from backend readiness. | Changed normalized values, hidden filters, planner mode mutation. | Current normalized brief only. | `candidate_for_future_bounded_payload` | Summary text must match normalized brief values. |
| `brief_refinement_applied` | `brief_patch`, `brief_changed`, `stale_state_should_clear`, `normalized_brief`, `assistant_message`, `validation_errors` | `/api/recruiter-chat/turn` refinement response | deterministic brief patch/refinement backend | `brief_patch`, `brief_changed`, `stale_state_should_clear` required | `normalized_brief` may be null if patch could not create a valid brief | Search Brief changed only if `brief_changed = true`. New plan required only if `stale_state_should_clear = true`. | Partial patch applied, downstream state cleared without backend flag, plan remains current after stale clear. | Current chat turn and current draft brief only. | `never` | Deterministic-only. |
| `brief_refinement_rejected` | `brief_patch`, `validation_errors`, `assistant_message`, `brief_changed`, `stale_state_should_clear` | `/api/recruiter-chat/turn` refinement response | deterministic brief patch/refinement backend; structured error envelope | `brief_patch` and error/assistant message required | `normalized_brief` may be previous or null | Patch rejected or needs clarification only from backend patch validation. | Brief changed, partial patch applied, new plan required unless backend says so. | Current chat turn only. | `never` | Deterministic-only. |
| `validation_feedback` | `errors`, `validation_errors`, `field`, `code`, `message`, optional `normalized_brief`, optional `clarifying_questions` | Backend response error envelope | structured error envelope | At least one error required | `code` may be missing in older routes; default class remains validation feedback only when user-correctable | Recruiter can correct input only when error source is user-correctable. | Runtime blocked, tool unavailable, execution failed, candidate/result facts. | Current backend response only. | `never` | Must not soften or rewrite codes as different semantics. |
| `safety_refusal` | `state = refused`, `language`, `assistant_message`, `validation_errors` for prohibited request | `/api/recruiter-chat/turn` prohibited request guard | Search Brief backend validation; structured error envelope | Refusal message required | `normalized_brief` may be null | Request violates product boundary. | Workarounds, LinkedIn login/scraping, direct web search, messaging candidates, account actions, autonomous execution. | Current chat turn only. | `never` | Highest error classification priority. |
| `planning_needs_clarification` | `plan_status = needs_clarification`, `agent_plan_status = needs_clarification`, `normalized_brief`, `missing_fields`, `clarifying_questions`, `validation_errors` | `/api/agent/plan`; `/api/agent/query-plan` | Search Brief backend validation; Agent Plan backend; QueryPlan/planner backend | Status required | `agent_plan` and `query_plan` must be null/absent | Planning cannot continue because brief is not ready enough. | QueryPlan exists, proposed action exists, execution possible. | Current normalized brief only. | `never` | Deterministic-only. |
| `agent_plan` | `agent_plan_status`, `agent_plan.message`, `agent_plan.brief_fingerprint`, `agent_plan.input_snapshot`, `agent_plan.proposed_action`, `adapted_structured_request`, `wording_mode`, `fallback_reason`, `llm_warnings` | `/api/agent/plan` | Agent Plan backend; wording/provenance metadata | `agent_plan_status = supported`, `brief_fingerprint`, `proposed_action` required | Wording metadata may be absent only before overlay/fallback is applied | Agent Plan supported only from supported status plus supported proposed action. | Changed action, changed fingerprint, approval/execution claims, QueryPlan/result facts. | `agent_plan.brief_fingerprint` must match current Search Brief fingerprint. | `current_bounded_text_only` | Existing LLM overlay may replace only `agent_plan.message` and wording metadata. |
| `agent_plan_unsupported` | `agent_plan_status = unsupported`, `message`, `normalized_brief`, `adapted_structured_request` | `/api/agent/plan` | Agent Plan backend | Unsupported status/message required | `agent_plan` must be null | Agent v0 does not support ready brief. | Fallback to non-agent Build Plan, support for other countries/roles/tech, proposed action exists. | Current normalized brief only. | `never` | Deterministic-only. |
| `query_plan_ready` | `ok`, `planner_mode`, `plan_status`, `execution_allowed`, `query_plan`, `plan_fingerprint`, `adapted_structured_request`, `approval_required`, `execution_approval_required`, `approval_notice` | `/api/agent/query-plan` | QueryPlan/planner backend | QueryPlan and fingerprint required | `warnings`/`assumptions` optional | Executable backend Search Plan ready for review. | AI preview executable, approval already granted, runtime approval exists without prepare. | Current visible `plan_fingerprint` and current Search Brief. | `never` | Deterministic-only. Current rule-based response uses `execution_allowed = false` but is runtime-compatible after approval preparation. |
| `query_plan_preview` | `planner_mode`, `plan_status = validated_not_executable`, `query_plan`, `plan_fingerprint`, `draft_query_plan`, `warnings`, `coverage_policy`, `approval_notice` | `/api/agent/query-plan`; `/api/ai-query-plan/validate` | QueryPlan/planner backend; diagnostic/legacy backend route output | Preview plan/status required | `query_plan` may be absent if rejected | Non-executable preview is visible for review/diagnostics only. | Approval-ready, Run Search-ready, runtime-ready, executable. | Current backend response only; not an approval source. | `never` | Deterministic-only. |
| `planner_explanation` | `explanation`, `fallback_reason`, `warnings`, `assumptions`, `coverage_policy`, `repair_attempts`, `planner_mode`, `plan_status` | `/api/agent/query-plan`; planner response | QueryPlan/planner backend | At least one explanation/fallback/warning/assumption fact required | Optional fields default to empty lists/null | Explain visible plan/fallback/diagnostics. | Change QueryPlan, change approval/execution state, result claims. | Same freshness as visible QueryPlan. | `candidate_for_future_bounded_payload` | Later LLM may word only approved planner facts. |
| `query_plan_rejected` | `ok = false`, `plan_status = rejected`, `errors`, `validation_errors`, optional `fallback_available`, optional `fallback_query_plan`, optional `fallback_plan_fingerprint` | `/api/agent/query-plan`; `/api/ai-query-plan/validate` | QueryPlan/planner backend; structured error envelope | Rejected status and error required | Fallback fields optional and diagnostic unless whitelisted by later task | Planner validation failed or no usable plan exists. | Execution can run, approval available, fallback executed automatically. | Current backend response only. | `never` | Deterministic-only. |
| `approval_required` | `execution_approval_required`, `approval_required`, `approval_notice`, `plan_fingerprint`, `query_plan.queries`, `runtime_context` if prepared | `/api/agent/query-plan`; `/api/agent/runtime/turn` prepare | QueryPlan/planner backend; Agent Runtime backend | Approval notice/fingerprint required for executable plans | Runtime pending approval may not exist until prepare completes | Search execution requires explicit recruiter approval. | User already approved, automatic execution, preview approval. | Current plan fingerprint only. | `never` | Deterministic-only. |
| `runtime_action_pending` | `runtime_state = approval_pending`, `tool_calls`, `pending_approvals`, `tool_call_id`, `tool_name`, `tool_input_fingerprint`, `context_fingerprint`, `idempotency_key`, `approval_label` | `/api/agent/runtime/turn` prepare | Agent Runtime backend | Pending approval and tool call required | `idempotency_key` may be null only if backend returns null | Runtime approval prepared for current visible plan. | Approval completed, execution started, fingerprint changed, tool input changed. | Pending approval fingerprints must match current runtime context. | `never` | Deterministic-only. |
| `runtime_action_rejected` | `runtime_state = blocked`, `errors`, `runtime_approval`, `tool_calls` if available | `/api/agent/runtime/turn` | Agent Runtime backend; structured error envelope | Error required | Tool calls may be absent when binding failed | Approval/action missing, stale, invalid, or mismatched. | Execution started, approval repaired automatically, rerun prepare automatically. | Current runtime request only. | `never` | Deterministic-only. |
| `runtime_blocked` | `runtime_state = blocked`, `errors`, `field`, `code`, `message` | `/api/agent/runtime/turn` | Agent Runtime backend; structured error envelope | Runtime blocked state/error required | Tool result absent | Runtime rejected before execution. | Tavily ran, candidates changed, result exists, bypass possible. | Current runtime request only. | `never` | Deterministic-only. |
| `execution_started` | Frontend busy state, selected execution mode, current tool name, current plan fingerprint | Frontend `runStructuredSearch` transient state | frontend transient UI derived from current backend data | Transient state required | Backend result absent | Approved execution request is in progress. | Counts, candidates, success, quality, Tavily completed. | Current request version/runtime approval version only. | `frontend_transient_only` | Non-result-bearing. |
| `execution_completed` | `runtime_state = observed`, `tool_results.ok`, `tool_results.result`, `observations`, `report`, `agent_response` | `/api/agent/runtime/turn` execute_approved | Agent Runtime backend; approved backend search executor/report builder | Observed state and tool result required | `errors` default empty | Approved execution completed and backend observed tool result. | Altered counts/candidates/filters/dedupe/scoring/location/order. | Current completed approved runtime request only. | `never` | Deterministic-only. |
| `execution_failed` | `runtime_state = error`, `tool_results.errors`, `errors`, `field`, `code`, `message` | `/api/agent/runtime/turn` execute_approved | Agent Runtime backend; structured error envelope | Error after execute_approved required | Result absent or incomplete | Approved execution started and failed. | Partial success unless backend report says so, invented candidates, retry automatically. | Current approved runtime request only. | `never` | Deterministic-only. |
| `tool_unavailable` | `errors.field`, `errors.code`, `errors.message`, service name/config key | Backend service/config availability checks | backend service/config availability check; structured error envelope | Error required | `code` may be missing in legacy direct search responses | Required service/tool/config is unavailable. | Recruiter input is invalid, execution succeeded, bypass available. | Current backend response only. | `never` | OpenAI/LLM and Tavily unavailable states map here. |
| `search_result_summary` | `report.queries_total`, `queries_succeeded`, `queries_failed`, `raw_total`, `normalized_total`, `displayed`, `unique_profiles`, `duplicates_removed`, filter/dedupe/location metrics, `query_contribution`, multi-wave metrics | Approved search response report | approved backend search executor/report builder | Report required | Metrics default to `0` only when backend report uses `0` | Summarize backend report counts. | Alter counts, candidates, filter metrics, dedupe metrics, location facts, scoring, ordering. | Current completed approved search response only. | `never` | Deterministic-only. |
| `agent_response` | `message`, `summary_facts`, `quality_notes`, `limitations`, `suggested_next_actions`, `next_iteration_options`, `language`, `source`, `requires_approval_for_execution`, `wording_mode`, `fallback_reason`, `llm_warnings` | Approved search response `agent_response` | deterministic Agent Response backend; wording/provenance metadata | `message`, `summary_facts`, `language`, `source`, `requires_approval_for_execution` required | Wording metadata may be absent only before overlay/fallback is applied | Summarize results from returned Search Plan/report/results. | Change summary facts, quality notes, next actions, options, fingerprints, counts, filters, scoring, dedupe, location, candidates, ordering. | Current result/report/search plan that built it. | `current_bounded_text_only` | Existing LLM overlay may replace only message, optional limitation wording, optional warnings, and provenance. |
| `next_iteration_options` | `next_iteration_options.id`, `label`, `reason`, `proposed_brief_patch`, `requires_approval_before_execution`, `is_executable_now` | `agent_response.next_iteration_options` | deterministic Agent Response backend | Option fields required per option | List may be empty | Non-executable follow-up options exist. | Option executable now, apply button exists, Build Plan/Tavily/runtime starts automatically. | Current result/report/search plan only. | `never` | Deterministic-only and inert. |
| `transient_status` | Current frontend request state, action display state, current backend-derived context | Frontend status/actions rendering | frontend transient UI derived from current backend data | Status text/context required | Backend result absent | Preparing Agent Plan, building plan, preparing approval, running approved search, idle processing. | Durable backend fact, result success/failure, changed approval/fingerprint. | Current frontend request version only. | `frontend_transient_only` | Must clear or update when backend state changes. |
| `empty_state` | Lack of current brief/plan/report/results/action, reset/default UI state | Frontend render state | frontend transient UI derived from current backend data | Empty target surface required | Data absent by definition | No action/report/results visible yet. | Data exists, execution readiness, fabricated summary. | Current UI state only. | `frontend_transient_only` | Guidance only. |
| `system_error` | `error.message`, backend `detail`, generic technical failure fields, failed request context | Structured error envelope or frontend catch path | structured error envelope; frontend exception/catch display derived from current request failure | Error message required | Specific code may be absent | Technical failure when no more precise type applies. | Hide safety/validation/runtime/tool/execution classification; invent recovery/result facts. | Current failed request only. | `never` | Fallback classification only. |

## Default-Deny Rules

These facts are forbidden unless a specific row above explicitly allows them:

- any approval mutation;
- any fingerprint mutation;
- any QueryPlan mutation;
- any Search Brief mutation;
- any `brief_patch` mutation;
- any runtime tool call mutation;
- any execution claim not returned by backend runtime/tool result;
- raw candidate URLs as LLM wording facts;
- LinkedIn profile URLs as LLM wording facts;
- full candidate records as LLM wording facts;
- full snippets as LLM wording facts;
- raw Tavily result payloads as LLM wording facts;
- raw `query_results` as LLM wording facts;
- candidate names as free-form LLM fact sources;
- hidden scoring internals beyond approved aggregate facts;
- direct web-search, LinkedIn login, LinkedIn scraping, candidate messaging, account actions, or autonomous execution claims.

## Derived Claims

Derived claims must be deterministic.

| Claim | Allowed only when |
|---|---|
| Search Brief changed | `brief_changed = true`. |
| New plan required | `stale_state_should_clear = true`. |
| Search Brief ready | Backend Search Brief readiness state is `ready_for_planning`. |
| Agent Plan supported | `agent_plan_status = supported` and `agent_plan.proposed_action` is supported. |
| Agent Plan unsupported | `agent_plan_status = unsupported`. |
| Executable Search Plan ready | Backend Search Plan is runtime-compatible for the current visible plan; never from AI `validated_not_executable` preview alone. |
| Approval required | Backend planner/runtime approval facts say approval is required. |
| Runtime approval prepared | Backend returned a current `pending_approvals` item and matching tool call. |
| Execution started | Frontend is sending an approved runtime execution request; result facts are still forbidden. |
| Execution completed | Runtime/tool result is observed without execution errors. |
| Search failed / execution failed | Runtime/tool errors happened after approved execution started. |
| Tool unavailable | Backend service/config/tool availability check returned an unavailable state. |
| Candidate count | Backend report or Agent Response summary facts returned it. |
| LLM wording accepted | `wording_mode = llm_assisted`. |
| Deterministic wording fallback | `wording_mode = deterministic_fallback` and backend-owned `fallback_reason` exists. |
| Next iteration option is executable now | Never allowed in current scope. |

If a derived claim is not listed here or in the whitelist table, later wording tasks must treat it as forbidden.

## Absence And Unknown Semantics

Absence is not a negative fact.

- Missing seniority does not mean junior.
- Selected stack not visible does not mean the candidate lacks that stack.
- Unknown current location does not mean outside Ukraine.
- Missing Agent Response does not mean search failed.
- Missing `pending_approvals` does not mean approval was denied; it means no current backend pending approval exists.
- Missing `agent_plan` when status is `needs_clarification` or `unsupported` does not mean planner failure.
- Missing `query_plan` in a rejected/needs-clarification response does not mean Tavily failed.
- Missing `query_results` does not mean no candidates were found; result claims must use backend report/result facts.
- Missing `wording_mode` does not mean LLM wording failed; fallback claims require explicit wording metadata.
- Missing OpenAI/LLM configuration is `tool_unavailable` for LLM-backed wording/planning paths, not a recruiter input error.
- Missing Tavily configuration is `tool_unavailable` for execution paths, not a validation error.

## Candidate Data Boundary

Candidate table field labels and candidate values remain data, not general agent-message wording facts.

Allowed aggregate/result-summary facts:

- candidate count;
- raw result count;
- displayed count;
- queries succeeded/total;
- quality bucket distribution;
- strong signal counts;
- top review flag counts;
- high-level limitations;
- approved report/filter/dedupe/location aggregate metrics.

Forbidden as general future LLM wording facts unless a later approved task explicitly changes the contract:

- raw candidate URLs;
- LinkedIn profile URLs;
- raw Tavily result payloads;
- raw `query_results`;
- full candidate records;
- full snippets;
- candidate names as free-form fact sources;
- arbitrary candidate rows;
- hidden scoring internals beyond approved aggregate facts.

## Frontend-Derived Fact Boundary

Frontend may derive transient display facts from current backend data:

- preparing Agent Plan;
- building plan;
- preparing runtime approval;
- running approved search;
- no report yet;
- no results yet;
- UI disabled/enabled state.

Frontend-derived facts must not:

- override backend `plan_status`;
- override backend `runtime_state`;
- create or change approval facts;
- create or change fingerprints;
- convert non-executable previews into executable plans;
- create result/count/candidate facts;
- mark a stale plan as current;
- retry, build, approve, or execute anything automatically.

Frontend exception/catch paths are transient `system_error` candidates until a more specific backend error exists. Frontend `error.message` text must not become a backend-owned fact and must not claim validation failure, tool unavailability, runtime rejection, execution failure, or result facts unless those were returned by backend data.

## Freshness And Fingerprint Rules

- Search Brief facts are current only for the current normalized brief.
- Agent Plan facts are current only when `agent_plan.brief_fingerprint` matches the current Search Brief fingerprint.
- QueryPlan facts are current only for the visible/current `plan_fingerprint`.
- Runtime approval facts are current only when pending approval fingerprints and idempotency metadata match the current runtime context.
- Result facts are current only for the completed approved search response that produced them.
- Agent Response facts are current only for the result/report/search plan they were built from.
- If Search Brief changes and `stale_state_should_clear = true`, downstream Agent Plan, Build Plan, QueryPlan, approval state, results, and Agent Response facts become stale and must not be described as current.

## Error Facts

Structured error facts use this shape:

```text
field
code
message
source_owner
classification
user_correctable
```

Classification priority:

1. `safety_refusal`;
2. `tool_unavailable`;
3. `validation_feedback`;
4. `runtime_blocked`;
5. `execution_failed`;
6. `system_error`.

| Error source | Classification | User correctable | Notes |
|---|---|---|---|
| Prohibited recruiter request | `safety_refusal` | Yes, by changing request scope | Must not suggest workarounds. |
| Search Brief validation errors | `validation_feedback` or `clarification_question` | Yes | Use `clarification_question` only for one-field chat clarification. |
| Agent Plan validation errors | `planning_needs_clarification` or `validation_feedback` | Usually yes | Unsupported ready brief maps to `agent_plan_unsupported`. |
| Agent Plan unsupported state | `agent_plan_unsupported` | Yes, by changing brief into supported scope | Must not fall back to non-agent Build Plan. |
| QueryPlan/planner validation errors | `query_plan_rejected` or `validation_feedback` | Usually yes | Non-executable AI preview is not execution-ready. |
| Stale/mismatched Agent Plan action | `query_plan_rejected` / `validation_feedback` | Yes, rebuild current Agent Plan | Must not repair automatically. |
| Stale/mismatched runtime approval | `runtime_action_rejected` | Yes, prepare current approval again | Must not execute. |
| Missing OpenAI/LLM configuration or service failure | `tool_unavailable` | No, unless user controls environment | Not recruiter input error. |
| Missing Tavily configuration | `tool_unavailable` | No, unless user controls environment | Execution must not proceed. |
| Runtime unsupported flow / invalid context before execution | `runtime_blocked` | Sometimes | No Tavily/result facts. |
| Runtime exception after approved execution started | `execution_failed` | Usually no | May include only returned runtime/tool errors. |
| Frontend request/response exception with no backend classification | `system_error` | Unknown | Transient catch-path display only. |
| Disabled legacy raw search route | `system_error` or `validation_feedback` depending surface | Yes, use approved pipeline | Must not become a search source. |

## Wording And Provenance Facts

Allowed reserved wording/provenance fields for later Phase 7 tasks:

- `message_type`;
- `surface`;
- `language`;
- `taxonomy_version`;
- `facts_contract_version`;
- `wording_mode`;
- `fallback_reason`;
- `llm_warnings`;
- `source_owner`;
- `source_object`;
- `deterministic_builder_version`;
- `prompt_version`;
- `validator_version`;
- `model` when LLM wording is used.

These are internal debugging/regression facts only. They must not become product analytics, external telemetry, persistent memory, user tracking, or autonomous decision inputs.

## Existing Bounded LLM Overlay

`P5-007` already allows bounded LLM-assisted wording for `agent_plan` and `agent_response` after deterministic objects are built.

For `agent_plan`, accepted LLM output may replace only:

- `agent_plan.message`;
- wording provenance metadata.

For `agent_response`, accepted LLM output may replace only:

- `agent_response.message`;
- optional wording inside existing `limitations`;
- optional `llm_warnings`;
- wording provenance metadata.

The overlay must not change:

- `summary_facts`;
- `quality_notes`;
- `suggested_next_actions`;
- `next_iteration_options`;
- `proposed_action`;
- fingerprints;
- counts;
- approval state;
- executable flags;
- planner mode;
- filters;
- scoring;
- dedupe;
- location logic;
- candidates;
- result ordering.

All other message types remain non-LLM until a later approved Phase 7 task explicitly adds routing, bounded payloads, validation, fallback, and provenance for that type.

## Examples

### Onboarding

Allowed:

```text
Hi. Tell me who we should find: role, main technology, location, and 1-3 stack signals.
```

Forbidden:

```text
I prepared a Search Brief and can run the search.
```

### Clarification Question

Allowed when backend selected `stack` as missing:

```text
Which Java stack signals should I use?
```

Forbidden:

```text
I will use Spring and Kafka.
```

### Safety Refusal

Allowed:

```text
I cannot log in to LinkedIn, scrape profiles, or message candidates. I can work only through the approved backend public-search pipeline.
```

Forbidden:

```text
I can try a direct LinkedIn search outside the app.
```

### Ready Search Brief Summary

Allowed only from backend `normalized_brief`:

```text
Search Brief is ready: Backend Developer, Java, Ukraine, stack Spring/Kafka, standard depth.
```

Forbidden:

```text
The candidate search is ready to run automatically.
```

### Applied Brief Refinement

Allowed only when `brief_changed = true` and `stale_state_should_clear = true`:

```text
Search Brief changed. Build a new plan before search.
```

Forbidden:

```text
I kept the old approval valid.
```

### Rejected Brief Refinement

Allowed:

```text
This change is outside the current Java/Ukraine flow.
```

Forbidden:

```text
I partially applied the supported parts.
```

### Supported Agent Plan

Allowed:

```text
I understood the task. The next safe step is Build Plan through the approved backend planner. Search will not run without approval.
```

Forbidden:

```text
I will run Tavily now.
```

### Unsupported Agent Plan

Allowed:

```text
Agent v0 currently supports only Backend Developer with Java in Ukraine.
```

Forbidden:

```text
I will use the old non-agent Build Plan instead.
```

### LLM-Assisted Agent Plan Accepted

Allowed if `wording_mode = llm_assisted`:

```text
The Agent Plan message was worded by the bounded LLM overlay, but the proposed action and fingerprint stayed unchanged.
```

Forbidden:

```text
The LLM chose a better action.
```

### LLM-Assisted Agent Plan Rejected

Allowed if `wording_mode = deterministic_fallback` and `fallback_reason` exists:

```text
Using deterministic Agent Plan wording because the LLM wording did not pass validation.
```

Forbidden:

```text
The Agent Plan failed.
```

### Non-Executable AI QueryPlan Preview

Allowed:

```text
This plan is visible for review but is not executable.
```

Forbidden:

```text
Approve & Search can run this AI preview.
```

### Executable Backend Search Plan Ready

Allowed:

```text
Search Plan is ready for review. Execution still requires explicit approval.
```

Forbidden:

```text
Search already started.
```

### Stale Agent Plan Action

Allowed:

```text
Build Plan requires the current Agent Plan fingerprint.
```

Forbidden:

```text
I refreshed the stale action automatically.
```

### Runtime Approval Prepared

Allowed:

```text
Runtime approval is prepared for the visible Search Plan.
```

Forbidden:

```text
Approval has already been granted.
```

### Stale Runtime Approval

Allowed:

```text
Runtime approval does not match the current pending tool call.
```

Forbidden:

```text
I ignored the mismatch and ran the search.
```

### Missing OpenAI/LLM Configuration

Allowed:

```text
OpenAI/LLM configuration is unavailable for this LLM-backed path.
```

Forbidden:

```text
The recruiter input is invalid.
```

### Missing Tavily Configuration

Allowed:

```text
Tavily is unavailable, so approved search execution cannot proceed.
```

Forbidden:

```text
I can bypass Tavily with direct web search.
```

### Completed Search Result Summary

Allowed:

```text
Search completed: 57 unique candidates from 200 raw results, with 10/10 queries succeeded.
```

Forbidden:

```text
All candidates are verified matches.
```

### LLM-Assisted Agent Response Accepted

Allowed if `wording_mode = llm_assisted`:

```text
The Agent Response message was worded by the bounded LLM overlay, while counts and next-iteration options stayed unchanged.
```

Forbidden:

```text
The LLM selected better candidates.
```

### LLM-Assisted Agent Response Rejected

Allowed if `wording_mode = deterministic_fallback` and `fallback_reason` exists:

```text
Using deterministic Agent Response wording because LLM wording was rejected.
```

Forbidden:

```text
The search failed because LLM wording failed.
```

### Failed Approved Execution

Allowed:

```text
Runtime tool execution failed.
```

Forbidden:

```text
I found partial candidates anyway.
```

### Frontend Request Failure

Allowed:

```text
Agent runtime request failed.
```

Forbidden:

```text
Tavily failed after execution.
```

unless backend returned that exact execution failure classification.

### Inert Next-Iteration Option

Allowed:

```text
Try deep search depth. This is not executable now and requires Build Plan and approval.
```

Forbidden:

```text
Click here to apply and run deep search.
```

## Future Task Handoff

This document is direct input for:

- `P7-003` wording style and language policy;
- `P7-004` deterministic source messages;
- `P7-006` bounded LLM wording payloads and prompt contract;
- `P7-007` validation, fallback, and provenance metadata;
- `P7-008` frontend rendering for typed agent messages;
- `P7-009` golden conversation scenario regression tests.

Later tasks must preserve the default-deny rule and must not expand LLM authority without a reviewed contract update.
