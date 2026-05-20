# Phase 7 Bounded LLM Wording Payload And Prompt Contract

Task: `P7-006 Add bounded LLM wording payloads and prompt contract`

Status: implemented as a docs-only contract.

## Contract Versions

```text
payload_contract_version = phase_7_bounded_llm_payload_contract_v0
prompt_contract_version = phase_7_bounded_llm_prompt_contract_v0
```

These are contract identifiers only. This task does not add public API fields, response provenance fields, telemetry, analytics, persistence, or user tracking.

## Scope

This document defines `Bounded LLM Wording Payload and Prompt Contract V0` for the current Phase 7 Agent Conversation Wording Layer.

It extends:

- `docs/phase-7-agent-message-taxonomy.md`;
- `docs/phase-7-message-facts-contract.md`;
- `docs/phase-7-agent-wording-style-policy.md`;
- `docs/phase-7-llm-routing-gating-policy.md`;
- the deterministic source-message layer in `app/agent_messages.py`;
- the current bounded wording overlay in `app/agent_wording.py`.

This task does not change backend code, frontend code, prompts, payload builders, validation code, API response fields, OpenAI calls, runtime behavior, Tavily execution, Search Brief extraction, QueryPlan generation, candidate results, scoring, filtering, dedupe, location logic, snapshots, persistence, database, shortlist, account behavior, or product scope.

## Core Rule

LLM wording payloads are bounded fact containers, not agent authority.

The LLM may only rewrite approved user-facing wording for message types that are already allowed by the Phase 7 routing policy. It must not own facts, state, actions, approval, Search Brief values, QueryPlan rows, runtime transitions, candidate data, counts, filters, scoring, dedupe, location logic, next-iteration options, or execution claims.

The product remains human-approved. Search execution must stay behind explicit recruiter approval and backend-owned fingerprints.

## Current Allowed Paths

The only current LLM wording payload/prompt paths are:

- `agent_plan`;
- `agent_response`.

These correspond to `current_bounded_text_only` in `docs/phase-7-llm-routing-gating-policy.md`.

All other message types remain disabled unless later approved work changes routing, payload, validation, fallback, provenance, rendering, and regression coverage.

## Shared Payload Contract

Allowed current payloads must have this shared shape:

| Field | Required | Meaning |
|---|---|---|
| `wording_use_case` | Yes | Must be one of `agent_plan` or `agent_response`. |
| `language` | Yes | Must be `en` or `ru`. |
| `deterministic_message` | Yes | Backend-owned source text to rewrite. |
| `hard_boundaries` | Yes | Product safety and no-mutation rules. |
| `allowed_numbers` | Yes | The only numbers the LLM may repeat. |
| source facts | Use-case specific | Must come only from facts allowed by the P7 facts contract. |

Payloads must be built only after the deterministic source object already exists.

Payloads must not be the source of truth for state. They only package already-approved facts for wording.

## Freshness Gate

Freshness is backend-owned and must be checked before payload construction.

The LLM must not decide whether context is fresh.

Required freshness rules:

- `agent_plan.brief_fingerprint` must match the current Search Brief for Agent Plan wording.
- `agent_response` facts must belong to the current completed approved result/report/search plan.
- Stale Search Brief, Agent Plan, QueryPlan, runtime approval, result, or Agent Response context must use deterministic fallback or no-call behavior.

`P7-006` documents this gate only. `P7-007` should enforce or make provenance/fallback behavior explicit where needed.

## Agent Plan Payload

`agent_plan` payloads may include:

- `wording_use_case = agent_plan`;
- `language`;
- `deterministic_message`;
- normalized brief / input snapshot;
- normalized structured request;
- proposed action as read-only context;
- approval requirement text;
- hard boundaries;
- allowed numbers.

Allowed LLM output effect:

- replace `agent_plan.message`;
- set allowed wording metadata/warnings through the existing bounded overlay path.

Forbidden LLM output effect:

- change `proposed_action`;
- change `brief_fingerprint`;
- change input snapshot;
- change normalized structured request;
- change approval facts;
- change planner mode;
- create or change QueryPlan;
- create or change runtime state;
- claim execution started or completed;
- add result facts, counts, candidates, filters, scoring, dedupe, location, or search behavior.

### Agent Plan Limitations Gap

Current `app/agent_wording.py` uses a generic output shape that includes `limitations`.

For `agent_plan`, `limitations` must not be treated as a semantic output channel. Agent Plan wording may explain the supported next planning action, but it must not add hidden limitation facts.

`P7-007` should enforce or normalize this use-case-specific rule so Agent Plan wording has no hidden limitations channel.

## Agent Response Payload

`agent_response` payloads may include:

- `wording_use_case = agent_response`;
- `language`;
- `deterministic_message`;
- `summary_facts`;
- `quality_notes`;
- existing `limitations`;
- `suggested_next_actions` as read-only context;
- `requires_approval_for_execution`;
- hard boundaries;
- allowed numbers.

Allowed LLM output effect:

- replace `agent_response.message`;
- optionally rewrite wording inside existing `limitations` only;
- set optional `llm_warnings`;
- set allowed wording metadata through the existing bounded overlay path.

Forbidden LLM output effect:

- change `summary_facts`;
- change `quality_notes`;
- add, remove, reorder, select, or mutate `suggested_next_actions`;
- add, remove, reorder, select, or mutate `next_iteration_options`;
- change proposed brief patches;
- change counts;
- change candidates;
- change filters;
- change scoring;
- change dedupe;
- change location logic;
- change candidate ordering;
- make any next step executable;
- claim direct profile inspection or verified candidate quality.

## Forbidden Payload Content

Payloads must not include:

- raw candidate URLs;
- LinkedIn profile URLs;
- raw candidate snippets;
- full candidate records;
- raw Tavily payloads;
- raw `query_results`;
- raw generated query text;
- mutable `brief_patch` operations;
- executable next-action instructions;
- account action instructions;
- LinkedIn login, scraping, restriction-bypass, messaging, outreach, or direct web-search instructions.

Aggregate facts already allowed by the P7 facts contract may be included for `agent_response`, such as counts in `summary_facts`, quality distribution, strong signal counts, high-level limitations, and approved report-derived summary facts.

## Prompt Contract

The wording prompt must:

1. Say the model is a bounded wording helper, not an agent executor.
2. Require one valid JSON object only.
3. Require the requested language.
4. Allow rewriting only approved user-facing text fields.
5. Require use of payload facts only.
6. Forbid new numbers outside `allowed_numbers`.
7. Forbid query text, candidate URLs, candidate names as new facts, raw snippets, and raw results.
8. Forbid creating or changing suggested next actions.
9. Forbid making any next step executable.
10. Forbid claims of direct LinkedIn inspection, LinkedIn login, scraping, restriction bypass, messaging, outreach, account use, direct web-search bypass, or autonomous execution.
11. Require deterministic fallback when output cannot pass validation.

The prompt output shape may be generic for compatibility, but the accepted semantic effect must be use-case specific:

- `agent_plan`: message plus allowed warnings/metadata only.
- `agent_response`: message, optional existing limitation wording, optional warnings/metadata.

## Example Rules

Any examples in this contract or later prompt/validation docs must follow `P7-002` and `P7-003`.

Examples must not introduce:

- candidate URLs;
- raw snippets;
- raw query text;
- invented counts;
- executable next steps;
- direct LinkedIn inspection claims;
- LinkedIn login, scraping, restriction bypass, messaging, outreach, account use, or autonomous execution claims.

Allowed `agent_plan` example:

```text
I understood the Java Backend Developer search in Ukraine. Build Plan can prepare the approved backend plan, and search execution still needs approval.
```

Forbidden `agent_plan` example:

```text
I will run Tavily and find candidates now.
```

Allowed `agent_response` example:

```text
The approved backend search returned 57 unique candidates from returned public-search data. Review the strongest candidates manually before changing the brief.
```

Forbidden `agent_response` example:

```text
I inspected the LinkedIn profiles directly and selected the best candidates.
```

## Future-Candidate Message Types

These message types are future candidates only:

- `onboarding`;
- `clarification_question`;
- `brief_summary`;
- `planner_explanation`.

This task does not create complete executable payload schemas for them.

They remain disabled with `payload_contract_not_available` until later approved work explicitly adds:

1. bounded payload/prompt contract for the message type;
2. validation and deterministic fallback;
3. lightweight internal provenance;
4. routing approval that enables the message type;
5. golden scenario coverage.

## Current Implementation Mapping

| Current implementation | Current behavior | Target contract | Owner for enforcement gaps |
|---|---|---|---|
| `agent_wording_system_prompt()` | Describes a bounded wording helper for deterministic Agent Plan or Agent Response text. | Keep this role boundary: wording helper, no tools, no facts/actions/approval mutation. | `P7-007` if stricter validation/provenance is needed. |
| `agent_wording_user_prompt(payload)` | Uses generic required output shape: `message`, `warnings`, `limitations`. | Keep JSON-only and payload-facts-only contract; interpret output by use case. | `P7-007` should enforce no semantic `limitations` channel for `agent_plan`. |
| `agent_plan_wording_payload(...)` | Includes normalized brief, normalized structured request, proposed action, approval requirement, hard boundaries, allowed numbers. | Treat proposed action and inputs as read-only facts. No mutation authority. | `P7-007` should make freshness/fingerprint behavior explicit where needed. |
| `agent_response_wording_payload(...)` | Includes summary facts, quality notes, limitations, suggested next actions, approval requirement, hard boundaries, allowed numbers. | Treat facts/options/actions as read-only. Only message and existing limitation wording can change. | `P7-007` should validate use-case-specific fields and provenance. |
| `validate_agent_wording_output(...)` | Validates shape, language, prohibited content, disallowed keys, numbers, and existing limitation kinds when provided. | Preserve deterministic fallback on invalid output. | `P7-007` should align fallback/provenance/no-call reasons with P7 policy. |
| `main.run_openai_json_agent_wording` wrapper | Preserves monkeypatchable wording runner for smoke tests. | Must stay compatible. | Any future code task touching wording must preserve this path. |

## Non-Goals

This task does not:

- change `app/agent_wording.py` runtime behavior;
- add new OpenAI calls;
- add new LLM-enabled message types;
- enable LLM wording for ordinary onboarding, clarification, brief summary, or planner explanation;
- change existing validation logic;
- add public API response fields;
- add frontend rendering behavior;
- add provenance/version fields to responses;
- change Search Brief extraction/refinement;
- change Agent Plan actions;
- change QueryPlan generation;
- change approval/fingerprint rules;
- change Agent Runtime transitions;
- change Tavily execution;
- change candidate results, counts, scoring, filtering, dedupe, location logic, reports, snapshots, or ordering;
- expand supported roles, countries, technologies, sources, or search modes;
- add persistence, memory, analytics, telemetry, database, shortlist, export, account behavior, or autonomous behavior.

## Handoff

`P7-007 Add wording validation, fallback, and provenance metadata` should:

- enforce `P7-005` routing/gating;
- enforce this payload/prompt contract;
- apply use-case-specific output validation;
- remove or neutralize the hidden `agent_plan.limitations` semantic channel;
- preserve deterministic fallback;
- add lightweight internal provenance/version metadata;
- keep metadata internal for debugging/regression, not product analytics, telemetry, memory, or user tracking.

`P7-008 Add frontend rendering for typed agent messages` should:

- render typed agent messages without treating LLM wording as state authority;
- keep backend facts, approval state, runtime state, and Search Brief state authoritative.

`P7-009 Add golden conversation scenario regression tests` should assert:

- payload boundaries;
- prompt contract boundaries;
- blocked fields;
- no-call/fallback behavior;
- provenance/version expectations from `P7-007`;
- no direct LinkedIn/search bypass, candidate messaging, account actions, or autonomous execution.

## Verification

This task is docs-only.

Required verification:

```powershell
git diff --check
```

No Python/frontend/backend regression checks are required unless later implementation changes code.
