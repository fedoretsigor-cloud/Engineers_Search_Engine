# Phase 4 AI Planner Baseline Evaluation

Date: 2026-05-16

Task: `P4-009 Compare AI planner vs rule-based baseline`

## Scope

This evaluation compares planning behavior only.

No Tavily execution was performed. No direct web-search, LinkedIn login, LinkedIn scraping, candidate messaging, or account actions were performed.

The check used the backend agent planner endpoint through FastAPI `TestClient`:

- `planner_mode = rule_based`
- `planner_mode = ai`
- `planner_mode = ai_with_fallback`

The AI modes used the configured live OpenAI/ChatGPT planner call.

## Baseline Search Brief

```json
{
  "brief_status": "ready_for_planning",
  "role_family": "Backend Developer",
  "technology": "Java",
  "stack": ["Spring", "Kafka"],
  "location": "Ukraine",
  "search_depth": "standard",
  "profile_sources": ["linkedin_public"]
}
```

The intended recruiter scenario is:

Recruiter searches for `Backend Developer` with main skill `Java` in `Ukraine`, using public LinkedIn profiles, with `Spring` and `Kafka` as stack signals.

## Result: Rule-Based Planner

Status:

- HTTP status: `200`
- planner mode: `rule_based`
- plan status: `validated_not_executable`
- execution allowed: `false`
- approval required for execution: `true`
- validation errors: none
- query count: `10`

The rule-based planner produced the current baseline 10-query plan:

1. `Java Developer`
2. `Java Software Engineer`
3. `Java Backend Engineer`
4. `Java Engineer`
5. `Java Programmer`
6. `Java Application Developer`
7. `Java Developer` with `Spring` or `Kafka`
8. `Java Engineer` with `Spring` or `Kafka`
9. `Java Backend Engineer` with `Spring` or `Kafka`
10. `Java Application Developer` with `Spring` or `Kafka`

Conclusion:

The rule-based planner still gives the strongest baseline coverage for the current Java/Ukraine flow. It creates a predictable mix of role-based and stack-focused query slots.

## Result: AI Planner

Status:

- HTTP status: `200`
- planner mode: `ai`
- plan status: `validated_not_executable`
- execution allowed: `false`
- approval required for execution: `true`
- validation errors: none
- query count: `1`

The live AI planner returned one query:

```text
site:linkedin.com/in AND "Backend Developer" AND "Java" AND "Ukraine"
```

The planner explanation was useful at a high level: it correctly recognized Backend Developers with Java expertise in Ukraine and mentioned stack signals.

However, the generated plan was too narrow for the current baseline. It did not preserve the tested 10-slot coverage pattern and did not create separate focused role/stack query slots.

## Result: AI With Fallback

Status:

- HTTP status: `200`
- planner mode: `ai`
- plan status: `validated_not_executable`
- execution allowed: `false`
- approval required for execution: `true`
- validation errors: none
- fallback reason: none
- query count: `3`

The live `ai_with_fallback` run returned three AI queries:

1. `Backend Developer` + `Java` + `Ukraine`
2. `Backend Developer` + `Spring` + `Ukraine`
3. `Backend Developer` + `Kafka` + `Ukraine`

This is better than the single-query AI plan, but still below the rule-based baseline coverage.

Important observation:

Fallback did not trigger because the current deterministic validator checks structure, safety, and alignment, but does not yet enforce baseline coverage quality.

## Decision

Keep `RuleBasedQueryPlanner v1` as the default and only executable planner for now.

The AI planner is useful for:

- interpreting recruiter intent;
- explaining a plan;
- drafting possible search strategy;
- supporting the future recruiter chat flow.

The AI planner is not yet reliable enough to execute or replace the rule-based baseline because it can return a formally valid but under-covered plan.

## P4-010 Follow-Up Result

P4-010 implemented the follow-up:

- preserve the diagnostic finding that the current prompt says `max_queries = 10`, shows a one-query output example, and the validator currently accepts `1..10` queries;
- improve the AI planner prompt to request the expected 10-query standard baseline explicitly;
- include the expected `6` role-based plus `4` stack-focused shape;
- implement strict thresholds through a minimal `AIPlannerCoveragePolicy v0` with the current Java/Ukraine baseline as the first supported policy;
- return a visible `coverage_policy_not_configured` warning for unsupported briefs instead of pretending strict coverage was checked;
- for `search_depth = standard`, require baseline-level query coverage or an explicit minimum coverage threshold;
- require both role-based and stack-focused slots when stack signals are present;
- require enough role phrase diversity for the Java Backend baseline;
- allow at most one AI plan repair attempt when the initial plan is structurally valid but under-covered;
- trigger visible fallback when an AI plan is valid structurally but too narrow for the baseline;
- rerun the same no-Tavily baseline evaluation after the quality gate is implemented.

Implementation notes:

- AI-generated plans remain non-executable.
- Tavily is not called by planner validation, repair, or evaluation.
- Unsupported briefs return a visible `coverage_policy_not_configured` warning instead of pretending strict coverage was checked.

Re-evaluation after P4-010:

- `rule_based`: 10 queries, expected baseline coverage.
- live `ai`: 10 queries, `validated_not_executable`, `repair_attempts = 0`, coverage policy `java_backend_ukraine_standard_v0`.
- live `ai_with_fallback`: 10 queries, `validated_not_executable`, `repair_attempts = 0`, coverage policy `java_backend_ukraine_standard_v0`.
- mocked no-Tavily smoke confirmed one repair attempt for under-covered plans and rule-based fallback after failed repair.

`P4-011` closed Phase 4 as AI Agent Foundation and moved the active product focus to Phase 5 recruiter chat/Search Brief conversation.
