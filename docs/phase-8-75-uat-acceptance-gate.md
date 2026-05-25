# Phase 8.75 Recruiter UAT Acceptance Gate

Task: `P8.75-001 Run recruiter UAT acceptance gate before persistence`

Status: completed

## Decision

Before starting Phase 9 persistence, the current stateless AI Agent v0 flow must pass a recruiter-facing UAT gate.

The gate validates that the current flow is worth preserving before database-backed sessions, saved searches, saved candidates, and cross-session continuation are added.

## Scope

The UAT gate covers the current narrow supported flow:

```text
Backend Developer + Java + Ukraine
```

It covers:

- recruiter chat onboarding, small talk, unclear/noise handling, off-topic handling, and prohibited-boundary refusals;
- Search Brief extraction, missing-field clarification, and refinement;
- Agent Plan and QueryPlan boundaries;
- runtime approval preparation and execution guardrails;
- multi-wave default behavior and approved backend runtime execution;
- Candidate Workspace table state, filtering/sorting, review status, shortlist, notes, export, candidate explanations, selected comparison, fit/gap, and refinement guidance;
- visible UI/static contract checks that preserve recruiter-facing language and product boundaries.

## Execution Strategy

The gate has two layers.

### No-live acceptance layer

The no-live layer is deterministic and safe for local and CI runs.

It uses:

- mocked recruiter-chat LLM output for Search Brief extraction cases;
- disabled OpenAI wording calls;
- mocked runtime execution for approved execution guardrail cases;
- Node-based Candidate Workspace helper checks;
- static contract checks over docs/frontend source.

It does not call OpenAI, Tavily, LinkedIn, direct web search, or any external service.

### Limited live acceptance layer

The live layer is intentionally small and is not wired into CI.

It uses only:

```text
Agent Plan -> QueryPlan -> Agent Runtime prepare -> explicit approval payload -> Agent Runtime execute_approved
```

It must not:

- call Tavily directly;
- call the legacy raw search endpoint;
- bypass backend runtime approval;
- open LinkedIn profiles;
- log in to LinkedIn;
- scrape or automate profiles;
- message candidates;
- perform account actions;
- commit raw Tavily result payloads, profile URLs, candidate URLs, secrets, or screenshots.

## Acceptance Criteria

- No-live UAT has at least 100 deterministic acceptance checks and all pass.
- No-live UAT is included in `scripts/check_all.ps1`.
- Live UAT runs a limited set of approved backend runtime executions after no-live is green.
- Live UAT reports only aggregate counts and safe status metadata.
- Any blocker found by UAT is fixed immediately, failed cases are rerun, and the report is updated.
- The final report says the gate is green before Phase 9 starts.
- Product boundaries remain intact: no direct web-search bypass, no direct LinkedIn access/login/scraping, no candidate messaging, no account actions, no autonomous execution, and no persistence.

## Verification

Required local commands:

```powershell
.\.venv\Scripts\python.exe scripts\uat_phase_8_75_no_live.py --write-report docs\phase-8-75-uat-report.md
.\.venv\Scripts\python.exe scripts\uat_phase_8_75_live.py --write-report docs\phase-8-75-uat-report.md
powershell -ExecutionPolicy Bypass -File .\scripts\check_all.ps1
```

The live command requires `TAVILY_API_KEY` in the local environment. It is intentionally not part of CI.
