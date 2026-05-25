# Phase 8.75 UAT Report

Generated: 2026-05-25 19:25:34 UTC

## No-Live Acceptance Run

Status: `green`

| Metric | Count |
| --- | ---: |
| total no-live checks | 326 |
| passed | 326 |
| failed | 0 |

## No-Live Category Coverage

| Category | Checks |
| --- | ---: |
| agent_plan | 25 |
| brief_validation | 24 |
| chat_clarification | 18 |
| chat_guardrails | 30 |
| chat_ready | 112 |
| chat_refinement | 21 |
| query_plan | 9 |
| runtime | 11 |
| static_contracts | 18 |
| workspace_js | 58 |

## Live Acceptance Run

Generated: 2026-05-25 19:26:44 UTC

Status: `green`

| Metric | Count |
| --- | ---: |
| live checks | 30 |
| passed | 30 |
| failed | 0 |
| approved backend runtime executions | 2 |

| Scenario | Mode | Queries succeeded | Unique profiles | Displayed | Waves | Stop reason |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| LIVE-EN-SINGLE-001 | single_wave | 10/10 | 43 | 65 | n/a | n/a |
| LIVE-RU-MULTI-001 | multi_wave | 20/20 | 45 | 140 | 2 | low_incremental_gain |

Live UAT used only the existing backend Agent Runtime prepare -> explicit approval -> execute_approved path. It did not call Tavily directly, did not open LinkedIn profiles, did not log in, did not scrape, did not message candidates, and did not commit raw result payloads or candidate URLs.


## Failures

None.

## Analysis

The no-live gate covers recruiter chat behavior, Search Brief validation, Agent Plan and QueryPlan boundaries, runtime approval guardrails, Candidate Workspace mapping/view/review/export helpers, Phase 8.5 agentic review helpers, and static product boundaries. It is deterministic and safe to run in CI.

The live gate covered one approved single-wave execution and one approved multi-wave execution through the existing backend Agent Runtime. Both scenarios produced unique candidates and completed without direct Tavily calls from the test harness, LinkedIn opening/login/scraping, candidate messaging, account actions, or raw payload disclosure in this report.

Issues found during UAT were fixed before the green report:

- the workspace UAT export checks were aligned with the current export contract: `allCandidates`/`visibleCandidates`, `candidates` export rows, snake_case CSV headers, and the current Markdown title;
- the no-live runner now requires at least 100 deterministic checks instead of an obsolete narrow upper bound, because the final gate covers 326 checks;
- the live compact-response assertion now accepts localized RU/EN wording while still requiring the candidate count and strong/review/weak counts and rejecting verbose internal/search-detail wording.

Decision: Phase 8.75 is green. Phase 9 can start only through reviewed persistence/privacy/session-boundary tasks.
