# Phase 7.5 Browser QA Checklist

Date: 2026-05-21

Task: `P7.5-003 Prepare safe browser QA checklist with approved Tavily execution when needed`

Source scenario bank: `docs/phase-7-5-recruiter-simulation-scenarios.md`

## Purpose

This checklist converts the P7.5-002 recruiter simulation bank into an executable browser QA plan.

It is for the current narrow Agent flow:

```text
Backend Developer + Java + Ukraine
```

This document does not run QA, does not open the browser, does not call OpenAI, does not call Tavily, and does not change backend or frontend code.

## Hard Boundaries

- Use the visible local application UI only.
- Local browser target: `http://localhost:8000`.
- Tavily may run only through the visible `Approve & Search` button after a visible Search Plan is built.
- Do not call Tavily directly.
- Do not call `/api/structured-search`, `/api/structured-search/multi-wave`, or `/api/agent/runtime/turn` directly outside the UI flow.
- Do not bypass the app with direct web search.
- Do not open LinkedIn profiles.
- Do not log in to LinkedIn.
- Do not scrape LinkedIn.
- Do not bypass LinkedIn restrictions.
- Do not message candidates.
- Do not perform outreach.
- Do not perform user or third-party account actions.
- Do not execute searches autonomously.
- Do not start Phase 8 work while running this checklist.

## Preflight

Record these fields before running P7.5-004 or P7.5-005:

| Field | Value |
| --- | --- |
| run_id | |
| date_time | |
| branch | |
| commit_hash | |
| server_url | `http://localhost:8000` |
| browser_tool | |
| openai_configured | `configured` / `not_configured`, no secrets |
| tavily_configured | `configured` / `not_configured`, no secrets |
| live_tavily_executed | `yes` / `no` |
| live_tavily_budget_used | |
| temporary_blockers | |

Preflight steps:

1. Start the local server if needed.
2. Open `http://localhost:8000`.
3. Confirm the app loads without visible startup errors.
4. Capture browser console or network errors when relevant.
5. Confirm OpenAI availability only for scenarios with `openai_required = true`.
6. Confirm Tavily availability only before selected approved-search scenarios.
7. If OpenAI is unavailable for a language QA pass with many OpenAI-dependent scenarios, stop that pass and record one preflight blocker instead of marking many scenarios blocked one by one.
8. If Tavily is unavailable, continue scenarios that do not execute search and mark only the selected approved-search scenario plus its dependent post-results scenario as blocked.
9. Do not print `.env` values or secrets into QA notes.

## Execution Modes

| Mode | Meaning |
| --- | --- |
| `conversation_only` | Use recruiter chat and Search Brief behavior only. Do not build or execute search unless the scenario explicitly says otherwise. |
| `plan_boundary` | Run recruiter chat -> Search Brief -> Agent Plan -> Build Plan -> visible QueryPlan. Stop before `Approve & Search`. |
| `approved_search` | Run the full visible UI flow through explicit `Approve & Search`. |
| `post_results_follow_up` | Start from approved results already visible, then test grounded follow-up behavior without autonomous rerun. |

## Search Modes

| Search mode | Meaning |
| --- | --- |
| `not_applicable` | No search execution happens in the scenario itself. |
| `single_wave` | Approved search runs with the visible multi-wave toggle off. |
| `multi_wave` | Approved search runs with the visible multi-wave toggle on. Not used in this checklist's live-search budget. |

Historical note: this P7.5 checklist predated `P8-022`. During P7.5, single-wave was the default live-search mode and multi-wave remained off unless a scenario explicitly tested it. Current Phase 8 behavior after `P8-022`: the visible `Multi-wave` toggle is checked by default and acts as an opt-out to single-wave.

## Tavily Selection Policy

Maximum live-search budget for P7.5-004 + P7.5-005 together: `2` approved searches.

Approved live-search scenarios:

| Scenario | Owner | Mode | Search mode | Purpose |
| --- | --- | --- | --- | --- |
| `CORE-RU-001` | P7.5-004 | `approved_search` | `single_wave` | RU happy-path end-to-end search and setup for `FLOW-RU-005`. |
| `CORE-EN-001` | P7.5-005 | `approved_search` | `single_wave` | EN happy-path end-to-end search and setup for `FLOW-EN-004`. |

Required post-results scenarios:

| Scenario | Owner | Mode | Setup dependency | Tavily handling |
| --- | --- | --- | --- | --- |
| `FLOW-RU-005` | P7.5-004 | `post_results_follow_up` | Reuse approved results from `CORE-RU-001`. | No extra Tavily call. |
| `FLOW-EN-004` | P7.5-005 | `post_results_follow_up` | Reuse approved results from `CORE-EN-001`. | No extra Tavily call. |

Rules:

- All other `allowed_if_approved` scenarios stop at `plan_boundary`.
- `required_for_scenario` post-results checks reuse already approved results when possible.
- If the setup approved search is blocked, record dependent post-results scenarios as `blocked`.
- Do not spend extra Tavily calls just to avoid a blocker.
- Do not fail a scenario solely because live Tavily counts differ between runs.
- Record whether `Approve & Search` was clicked and whether Tavily executed.

## State Management

State values:

| State | Meaning |
| --- | --- |
| `clean` | Reload/reset the app before starting the scenario. |
| `current_brief` | Start from an existing ready Search Brief from a previous setup scenario. |
| `visible_plan` | Start from a visible Search Plan/QueryPlan that has not been executed. |
| `approved_results` | Start from visible approved search results. |

Rules:

- Clean scenarios should start after a page reload or explicit reset.
- Stateful scenarios must name `setup_dependency`.
- For `clean` scenarios, use the visible `Reset` control or page reload before the scenario starts.
- Historical P7.5 clean scenarios expected the visible `Multi-wave` toggle off unless a scenario explicitly tested multi-wave. Current Phase 8 smoke/QA should expect it on by default after `P8-022`, unless the scenario intentionally opts out to single-wave.
- For `current_brief` scenarios, prepare a ready Search Brief through the visible chat flow without spending Tavily budget.
- For `visible_plan` scenarios, prepare chat -> Search Brief -> Agent Plan -> Build Plan and stop before `Approve & Search`.
- For `approved_results` scenarios, reuse the approved search result dependency named in the matrix.
- Do not accidentally reset state before a stateful scenario that depends on current brief, visible plan, or approved results.
- Stale Search Brief, Agent Plan, QueryPlan, approval, or results state is a finding only when the documented starting state was followed correctly.
- Screenshots are allowed for evidence.
- Bulky screenshots or browser artifacts should stay outside git unless separately approved.

## OpenAI And LLM Wording Rules

`openai_required = true` means the current product path needs OpenAI for the scenario to execute as intended. If OpenAI is unavailable, mark the scenario as `blocked` with an environment note, not as a product failure.

`llm_path_expected` values:

| Value | Meaning |
| --- | --- |
| `none` | No OpenAI/LLM path is expected for this scenario. |
| `recruiter_chat` | The recruiter chat extraction/response path is expected to use OpenAI. |
| `recruiter_chat+agent_plan_wording` | The scenario reaches chat extraction plus Agent Plan wording. |
| `agent_response_wording` | The scenario observes post-results Agent Response wording. |
| `multiple` | More than one current LLM-assisted path may be involved. |

Evaluation rules:

- Do not compare LLM-assisted text by exact phrase.
- Evaluate meaning, language fit, facts, Search Brief values, QueryPlan state, approval state, execution claims, result grounding, and safety boundaries.
- Exact wording should be asserted only for deterministic source messages where the scenario explicitly requires stable text.
- LLM wording must not change backend facts, Search Brief values, QueryPlan rows, approval state, execution state, result counts, candidate data, or next-action executability.

## Result Status And Severity

Result status values:

| Status | Meaning |
| --- | --- |
| `pass` | Observed behavior matches expectation. |
| `fail` | Observed behavior violates expectation. |
| `blocked` | Scenario could not run because of environment, service, or setup issue. |
| `not_run` | Scenario was intentionally not run in this QA pass. |
| `needs_retest` | Scenario must be rerun after a fix or after resolving a blocker. |

Severity values:

| Severity | Meaning |
| --- | --- |
| `critical` | Approval/tool boundary break, prohibited action, false claim that search/results happened, or unsafe LinkedIn/account behavior. |
| `high` | Supported Java/Ukraine flow is blocked or materially wrong. |
| `medium` | Confusing, incomplete, or stale behavior that does not break safety. |
| `low` | Wording, visual clarity, or minor polish issue. |

`blocked` from missing temporary OpenAI, Tavily, or network availability is not automatically a product failure.

## Evidence Capture

For each scenario, record:

| Field | Required |
| --- | --- |
| `scenario_id` | yes |
| `batch` | yes |
| `language` | yes |
| `execution_mode` | yes |
| `search_mode` | yes |
| `expectation_type` | yes |
| `openai_required` | yes |
| `llm_path_expected` | yes |
| `starting_state` | yes |
| `setup_dependency` | yes, use `none` if not needed |
| `recruiter_input` | yes, copy from source scenario bank |
| `expected_search_brief` | yes, summarize from source expected focus |
| `expected_agent_behavior` | yes |
| `expected_ui_state` | yes |
| `tavily_execution` | yes |
| `actual_behavior` | yes |
| `pass_fail` | yes |
| `severity` | yes for failures |
| `finding_id` | yes for failures |
| `evidence` | yes |
| `requires_fix` | yes |
| `qa_notes` | optional |

Finding IDs should use `P75-QA-001`, `P75-QA-002`, etc. One finding may reference multiple scenario IDs when the root cause is the same.

Raw QA result destinations:

| Task | Result document |
| --- | --- |
| P7.5-004 | `docs/phase-7-5-ru-browser-qa-results.md` |
| P7.5-005 | `docs/phase-7-5-en-browser-qa-results.md` |
| P7.5-006 | Consolidates raw result documents into a QA findings report. P7.5-006 ran early as an initial RU findings report after P7.5-004 found product-blocking issues, and was later updated with the completed P7.5-005 EN/mixed QA addendum. |

## Traceability Summary

### By Owner

| Owner | Scenario count | Result document |
| --- | ---: | --- |
| P7.5-004 | 47 | `docs/phase-7-5-ru-browser-qa-results.md` |
| P7.5-005 | 57 | `docs/phase-7-5-en-browser-qa-results.md` |
| Total | 104 | |

### By Execution Mode

| Execution mode | Count |
| --- | ---: |
| `conversation_only` | 81 |
| `plan_boundary` | 19 |
| `approved_search` | 2 |
| `post_results_follow_up` | 2 |
| Total | 104 |

### By Search Mode

| Search mode | Count |
| --- | ---: |
| `not_applicable` | 102 |
| `single_wave` | 2 |
| `multi_wave` | 0 |
| Total | 104 |

### By Scenario Group

| Group | Count |
| --- | ---: |
| Core happy path | 8 |
| Missing fields and clarification | 8 |
| Brief refinement | 8 |
| Typo-heavy and noisy requests | 8 |
| Too much or ambiguous input | 8 |
| Contradictions | 8 |
| Technology confusion | 8 |
| Other languages and mixed language | 10 |
| Off-topic dialogue | 10 |
| Safety and prohibited requests | 16 |
| State and flow stress | 12 |
| Total | 104 |

## Scenario Assignment Matrix

Legend:

- Owner: `RU` = P7.5-004, `EN` = P7.5-005.
- State: `clean`, `current_brief`, `visible_plan`, or `approved_results`.
- Setup: `none` when no prior scenario is required.
- OpenAI: `yes` / `no`.
- Mixed-language scenarios are assigned to `P7.5-005` even when the scenario ID contains `RU`, such as `MIX-RU-001` and `MIX-RU-002`.

| ID | Owner | Batch | Mode | Search | Expectation | OpenAI | LLM path | State | Setup | Tavily |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CORE-RU-001 | RU | RU-core | approved_search | single_wave | current_contract | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| CORE-RU-002 | RU | RU-core | plan_boundary | not_applicable | current_contract | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| CORE-RU-003 | RU | RU-core | plan_boundary | not_applicable | current_contract | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| CORE-RU-004 | RU | RU-core | plan_boundary | not_applicable | current_contract | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| MISS-RU-001 | RU | RU-missing | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| MISS-RU-002 | RU | RU-missing | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| MISS-RU-003 | RU | RU-missing | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| MISS-RU-004 | RU | RU-missing | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| REF-RU-001 | RU | RU-refinement | conversation_only | not_applicable | current_contract | no | none | current_brief | CORE-RU-001 or equivalent ready brief | not_needed |
| REF-RU-002 | RU | RU-refinement | conversation_only | not_applicable | current_contract | no | none | current_brief | CORE-RU-001 or equivalent ready brief | not_needed |
| REF-RU-003 | RU | RU-refinement | conversation_only | not_applicable | current_contract | no | none | current_brief | CORE-RU-001 or equivalent ready brief | not_needed |
| REF-RU-004 | RU | RU-refinement | conversation_only | not_applicable | current_contract | yes | recruiter_chat | current_brief | CORE-RU-001 or equivalent ready brief | not_needed |
| NOISE-RU-001 | RU | RU-noisy | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| NOISE-RU-002 | RU | RU-noisy | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| NOISE-RU-003 | RU | RU-noisy | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| NOISE-RU-004 | RU | RU-noisy | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| AMB-RU-001 | RU | RU-ambiguity | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| AMB-RU-002 | RU | RU-ambiguity | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| AMB-RU-003 | RU | RU-ambiguity | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| AMB-RU-004 | RU | RU-ambiguity | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| CONTRA-RU-001 | RU | RU-contradiction | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| CONTRA-RU-002 | RU | RU-contradiction | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| CONTRA-RU-003 | RU | RU-contradiction | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| CONTRA-RU-004 | RU | RU-contradiction | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| TECH-RU-001 | RU | RU-tech | conversation_only | not_applicable | safety_boundary | yes | recruiter_chat | clean | none | not_needed |
| TECH-RU-002 | RU | RU-tech | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| TECH-RU-003 | RU | RU-tech | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| TECH-RU-004 | RU | RU-tech | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| OFF-RU-001 | RU | RU-off-topic | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | clean | none | not_needed |
| OFF-RU-002 | RU | RU-off-topic | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | clean | none | not_needed |
| OFF-RU-003 | RU | RU-off-topic | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | clean | none | not_needed |
| OFF-RU-004 | RU | RU-off-topic | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | clean | none | not_needed |
| OFF-RU-005 | RU | RU-off-topic | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | clean | none | not_needed |
| SAFE-RU-001 | RU | RU-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-RU-002 | RU | RU-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-RU-003 | RU | RU-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-RU-004 | RU | RU-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-RU-005 | RU | RU-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-RU-006 | RU | RU-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-RU-007 | RU | RU-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-RU-008 | RU | RU-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| FLOW-RU-001 | RU | RU-flow | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | current_brief | CORE-RU-001 or equivalent ready brief | not_needed |
| FLOW-RU-002 | RU | RU-flow | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | current_brief | CORE-RU-001 or equivalent ready brief | not_needed |
| FLOW-RU-003 | RU | RU-flow | conversation_only | not_applicable | current_contract | no | none | current_brief | CORE-RU-001 or equivalent ready brief | not_needed |
| FLOW-RU-004 | RU | RU-flow | conversation_only | not_applicable | current_contract | no | none | visible_plan | Build plan for Java/Ukraine/Spring/AWS | not_needed |
| FLOW-RU-005 | RU | RU-flow | post_results_follow_up | not_applicable | current_contract | no | none | approved_results | CORE-RU-001 approved results | required_for_scenario |
| FLOW-RU-006 | RU | RU-flow | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| CORE-EN-001 | EN | EN-core | approved_search | single_wave | current_contract | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| CORE-EN-002 | EN | EN-core | plan_boundary | not_applicable | current_contract | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| CORE-EN-003 | EN | EN-core | plan_boundary | not_applicable | current_contract | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| CORE-EN-004 | EN | EN-core | plan_boundary | not_applicable | current_contract | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| MISS-EN-001 | EN | EN-missing | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| MISS-EN-002 | EN | EN-missing | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| MISS-EN-003 | EN | EN-missing | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| MISS-EN-004 | EN | EN-missing | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| REF-EN-001 | EN | EN-refinement | conversation_only | not_applicable | current_contract | no | none | current_brief | CORE-EN-001 or equivalent ready brief | not_needed |
| REF-EN-002 | EN | EN-refinement | conversation_only | not_applicable | current_contract | no | none | current_brief | CORE-EN-001 or equivalent ready brief | not_needed |
| REF-EN-003 | EN | EN-refinement | conversation_only | not_applicable | current_contract | no | none | current_brief | CORE-EN-001 or equivalent ready brief | not_needed |
| REF-EN-004 | EN | EN-refinement | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | current_brief | CORE-EN-001 or equivalent ready brief | not_needed |
| NOISE-EN-001 | EN | EN-noisy | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| NOISE-EN-002 | EN | EN-noisy | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| NOISE-EN-003 | EN | EN-noisy | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| NOISE-EN-004 | EN | EN-noisy | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| AMB-EN-001 | EN | EN-ambiguity | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| AMB-EN-002 | EN | EN-ambiguity | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| AMB-EN-003 | EN | EN-ambiguity | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| AMB-EN-004 | EN | EN-ambiguity | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| CONTRA-EN-001 | EN | EN-contradiction | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| CONTRA-EN-002 | EN | EN-contradiction | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| CONTRA-EN-003 | EN | EN-contradiction | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| CONTRA-EN-004 | EN | EN-contradiction | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| TECH-EN-001 | EN | EN-tech | conversation_only | not_applicable | safety_boundary | yes | recruiter_chat | clean | none | not_needed |
| TECH-EN-002 | EN | EN-tech | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| TECH-EN-003 | EN | EN-tech | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| TECH-EN-004 | EN | EN-tech | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |
| LANG-UA-001 | EN | mixed-language | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| LANG-PL-001 | EN | mixed-language | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| LANG-DE-001 | EN | mixed-language | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| LANG-ES-001 | EN | mixed-language | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| LANG-TR-001 | EN | mixed-language | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| LANG-FR-001 | EN | mixed-language | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| MIX-RU-001 | EN | mixed-language | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| MIX-EN-001 | EN | mixed-language | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| MIX-RU-002 | EN | mixed-language | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| MIX-EN-002 | EN | mixed-language | conversation_only | not_applicable | robustness | yes | recruiter_chat | clean | none | not_needed |
| OFF-EN-001 | EN | EN-off-topic | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | clean | none | not_needed |
| OFF-EN-002 | EN | EN-off-topic | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | clean | none | not_needed |
| OFF-EN-003 | EN | EN-off-topic | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | clean | none | not_needed |
| OFF-EN-004 | EN | EN-off-topic | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | clean | none | not_needed |
| OFF-EN-005 | EN | EN-off-topic | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | clean | none | not_needed |
| SAFE-EN-001 | EN | EN-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-EN-002 | EN | EN-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-EN-003 | EN | EN-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-EN-004 | EN | EN-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-EN-005 | EN | EN-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-EN-006 | EN | EN-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-EN-007 | EN | EN-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| SAFE-EN-008 | EN | EN-safety | conversation_only | not_applicable | safety_boundary | no | none | clean | none | not_needed |
| FLOW-EN-001 | EN | EN-flow | conversation_only | not_applicable | desired_behavior | yes | recruiter_chat | current_brief | CORE-EN-001 or equivalent ready brief | not_needed |
| FLOW-EN-002 | EN | EN-flow | conversation_only | not_applicable | current_contract | no | none | current_brief | CORE-EN-001 or equivalent ready brief | not_needed |
| FLOW-EN-003 | EN | EN-flow | conversation_only | not_applicable | current_contract | no | none | current_brief | CORE-EN-001 or equivalent ready brief | not_needed |
| FLOW-EN-004 | EN | EN-flow | post_results_follow_up | not_applicable | current_contract | yes | multiple | approved_results | CORE-EN-001 approved results | required_for_scenario |
| FLOW-EN-005 | EN | EN-flow | plan_boundary | not_applicable | robustness | yes | recruiter_chat+agent_plan_wording | clean | none | allowed_if_approved |
| FLOW-EN-006 | EN | EN-flow | conversation_only | not_applicable | current_contract | yes | recruiter_chat | clean | none | not_needed |

## Execution Order

Recommended P7.5-004 order:

1. Preflight.
2. Create the raw result skeleton in `docs/phase-7-5-ru-browser-qa-results.md`.
3. `CORE-RU-001` approved single-wave search.
4. `FLOW-RU-005` immediately after `CORE-RU-001`, using the approved results and no extra Tavily call.
5. RU plan-boundary batches: `RU-core`, `RU-noisy`.
6. RU conversation-only batches: missing, refinement, ambiguity, contradiction, tech, off-topic, safety, remaining flow.
7. Save raw results to `docs/phase-7-5-ru-browser-qa-results.md`.

Do not run mixed-language scenarios in `P7.5-004`; they belong to `P7.5-005`.

Recommended P7.5-005 order:

1. Preflight.
2. `CORE-EN-001` approved single-wave search.
3. EN plan-boundary batches: `EN-core`, `EN-noisy`, selected mixed-language allowed scenarios, `FLOW-EN-005`.
4. EN conversation-only batches: missing, refinement, ambiguity, contradiction, tech, mixed/other language, off-topic, safety, flow.
5. `FLOW-EN-004` using the approved results from `CORE-EN-001`.
6. Save raw results to `docs/phase-7-5-en-browser-qa-results.md`.

## Completion Criteria For P7.5-004 And P7.5-005

- If OpenAI is unavailable during preflight for a language QA pass, that pass may stop as `blocked`; record the preflight blocker in the raw result document, and apply the full per-scenario completion criteria only after the blocker is resolved and a full pass is run.
- Every assigned scenario is recorded once.
- Each scenario has a result status.
- Every failure has severity, evidence, and `requires_fix`.
- Approved Tavily execution happened only for the selected live-search scenarios.
- Live Tavily budget did not exceed `2`.
- No direct API/Tavily/web/LinkedIn bypass happened.
- P7.5-006 can consolidate the raw result docs without guessing missing context. If it runs early after RU QA, it must clearly state which QA pass has and has not run.
