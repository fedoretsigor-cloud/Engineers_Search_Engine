# Phase 7 Agent Wording Style Policy

Task: `P7-003 Define agent wording style and language policy`

Status: implemented as a docs-only contract.

## Scope

This document defines `Agent Wording Style and Language Policy V0` for the current narrow Java/Ukraine Agent v0 flow.

It extends:

- `docs/phase-7-agent-message-taxonomy.md`;
- `docs/phase-7-message-facts-contract.md`.

The policy defines how recruiter-visible agent messages should sound, how RU/EN language should be handled, how uncertainty and approval boundaries should be worded, and which wording patterns remain forbidden.

This document does not change backend code, frontend code, prompts, API response fields, schemas, runtime behavior, Tavily execution, OpenAI behavior, approval behavior, Search Brief extraction, QueryPlan generation, candidate results, scoring, filtering, dedupe, location logic, snapshots, persistence, database, shortlist, account behavior, or product scope.

## Core Rule

Wording may change form. Wording must not change facts or authority.

Facts remain owned by `docs/phase-7-message-facts-contract.md`. The style policy can make approved facts easier to understand, but it cannot create facts, alter state, imply execution, or broaden what the agent can do.

The agent remains human-approved, not autonomous.

Search execution must always remain behind explicit recruiter approval and backend-owned fingerprints.

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

Wording must not present prohibited behavior as possible, planned, completed, partially completed, or available through a workaround.

## Current Wording Producers And Surfaces

| Producer or renderer | Surface | Wording responsibility | Style-policy boundary |
|---|---|---|---|
| `POST /api/recruiter-chat/turn` | `chat`, `brief_panel`, `status_panel` | Assistant message, clarification, Search Brief readiness, safety refusal, validation feedback, brief refinement result. | May word only facts returned by Search Brief validation or brief patch/refinement. |
| `POST /api/agent/plan` | `chat`, `action_queue`, `status_panel` | Agent Plan supported/unsupported/needs-clarification message and proposed planning action. | Supported Agent Plan wording may be polished only inside current bounded text-only overlay. Proposed action and fingerprint are not wording. |
| `POST /api/agent/query-plan` | `plan_panel`, `action_queue`, `status_panel` | QueryPlan readiness, preview/rejection, planner explanation, warnings, assumptions, approval notice. | Must not convert non-executable previews into executable plans or approvals. |
| `POST /api/agent/runtime/turn` prepare | `action_queue`, `status_panel` | Runtime approval preparation, pending approvals, blocked/tool-unavailable state. | Must not imply user approval was granted or execution started. |
| `POST /api/agent/runtime/turn` execute_approved | `status_panel`, `results_panel` | Approved execution observation, runtime result/failure, tool result envelope. | Result facts may be worded only after backend observed tool results. |
| Approved search response `agent_response` | `chat`, `results_panel` | Post-results summary, limitations, suggested next actions, next-iteration options. | Current bounded text-only overlay may replace only allowed text fields and wording metadata. |
| Bounded `agent_wording` overlay | `chat`, `results_panel` | Optional wording improvement for `agent_plan` and `agent_response`. | LLM output owns no facts; accepted output may change only allowed text fields. |
| Frontend chat/status/action/plan/results rendering in `app/static/app.js` | `chat`, `brief_panel`, `action_queue`, `plan_panel`, `status_panel`, `results_panel` | Rendering of current backend-derived text and transient statuses. | Frontend-derived text is transient display only and must not override backend-owned state. |

## Language Policy

Supported recruiter-facing languages for this phase:

- `en`;
- `ru`.

Rules:

1. Use the language returned or detected by the backend conversation flow.
2. If language is unknown, use the current backend default instead of guessing from unrelated UI state.
3. Keep canonical backend values stable in data and contracts.
4. Use natural user-facing wording when it does not change the underlying fact.
5. Keep visible product/API terms stable when they are UI or contract terms.
6. Avoid mixed RU/EN sentence structure when a natural phrase exists.
7. Do not translate the same fact differently across surfaces in a way that changes meaning.

Canonical facts vs visible wording:

| Canonical fact or term | EN visible wording | RU visible wording |
|---|---|---|
| `Backend Developer` | Backend Developer | Backend Developer |
| `Java` | Java | Java |
| `Ukraine` | Ukraine | Ukraine / in Ukraine / в Украине |
| `Search Brief` | Search Brief | Search Brief |
| `Agent Plan` | Agent Plan | Agent Plan |
| `Build Plan` | Build Plan | Build Plan |
| `QueryPlan` | QueryPlan | QueryPlan |
| `approval` | approval / explicit approval | approval / явное approval |
| `runtime` | runtime | runtime |
| `Tavily` | Tavily | Tavily |
| `LinkedIn` | LinkedIn | LinkedIn |

`Backend Developer с Java в Украине` is acceptable Russian visible wording when the underlying canonical facts remain `Backend Developer`, `Java`, and `Ukraine`.

## Tone Policy

The agent should sound:

- clear;
- calm;
- concrete;
- concise;
- recruiter-oriented;
- explicit about uncertainty;
- explicit about approval boundaries;
- helpful without overpromising.

The agent should not sound:

- magical;
- salesy;
- falsely confident;
- overly apologetic;
- overly verbose;
- autonomous;
- like it inspected private LinkedIn data;
- like it can log in, scrape, contact candidates, or use accounts.

## Message-Type Style Coverage

Every recruiter-visible message must map to a P7-001 `message_type` before later implementation changes wording.

| message_type | Style intent | Language behavior | Required caution / uncertainty | Forbidden wording | Wording eligibility |
|---|---|---|---|---|---|
| `onboarding` | Invite the recruiter to describe the search. | Match chat language. | Do not imply existing brief, plan, or execution. | Search already prepared; tools can run. | Candidate later bounded payload. |
| `clarification_question` | Ask one focused backend-selected missing-field question. | Match chat language; keep field terms stable. | Ask only one missing field. | Invented defaults; multiple unrelated questions; planning readiness. | Candidate later bounded payload. |
| `brief_summary` | Restate normalized Search Brief values. | Natural RU/EN, stable canonical facts. | Mention assumptions only when backend returned them. | Changed role, tech, stack, location, depth, filters. | Candidate later bounded payload. |
| `brief_refinement_applied` | Confirm safe backend-applied brief change. | Match chat language. | Say a new plan is required only if `stale_state_should_clear = true`. | Partial hidden patch; old approval remains valid after stale clear. | Deterministic-only. |
| `brief_refinement_rejected` | Explain that requested brief change was not safely applicable. | Match chat language. | Do not imply any brief mutation unless backend returned it. | Partial application; automatic fallback; silent support expansion. | Deterministic-only. |
| `validation_feedback` | Explain user-correctable structured errors. | Match surface language. | Preserve error class/code meaning. | Reclassifying runtime/tool failures as input errors. | Deterministic-only. |
| `safety_refusal` | Firmly refuse prohibited scope. | Match chat language. | Briefly name boundary; no workaround. | Direct search, LinkedIn login/scraping, messaging, account actions, autonomy. | Deterministic-only. |
| `planning_needs_clarification` | Explain planning cannot continue until brief is ready enough. | Match current request language. | Do not create Agent Plan or QueryPlan facts. | Proposed action exists; execution possible. | Deterministic-only. |
| `agent_plan` | Explain supported next planning action. | Match chat language. | Build Plan prepares a plan; search still needs approval. | Changed proposed action, fingerprint, planner mode, approval, or execution claim. | Current bounded text-only overlay. |
| `agent_plan_unsupported` | Explain Agent v0 does not support the ready brief yet. | Match chat language. | Soft but direct; do not hide unsupported status. | Old non-agent fallback, broader support, proposed action exists. | Deterministic-only. |
| `query_plan_ready` | Tell recruiter an executable backend Search Plan is ready for review. | Match UI language where available. | Execution still requires explicit approval. | Search started; approval already granted; AI preview is executable. | Deterministic-only. |
| `query_plan_preview` | Explain non-executable preview/diagnostic plan. | Match UI language where available. | Must say it is not executable when relevant. | Approval-ready, runtime-ready, Run Search-ready. | Deterministic-only. |
| `planner_explanation` | Explain plan, fallback, warning, assumption, or coverage detail. | Match visible plan language where available. | Tie explanation to current visible plan only. | Changed QueryPlan, approval, execution, or result claims. | Candidate later bounded payload. |
| `query_plan_rejected` | Explain planner produced no usable plan. | Match UI language where available. | No execution or approval is available unless backend says so. | Fallback executed automatically; rejected plan can run. | Deterministic-only. |
| `approval_required` | Make approval boundary explicit. | Match UI language where available. | User must explicitly approve before search execution. | Agent approves; automatic execution; preview approval. | Deterministic-only. |
| `runtime_action_pending` | Show backend-owned pending runtime approval. | Match UI language where available. | Pending approval is prepared, not granted. | Approval completed; execution started; fingerprints changed. | Deterministic-only. |
| `runtime_action_rejected` | Explain approval/action mismatch or stale state. | Match UI language where available. | Current action cannot proceed. | Repaired automatically; bypassed runtime validation; execution started. | Deterministic-only. |
| `runtime_blocked` | Explain runtime blocked before execution. | Match UI language where available. | No Tavily/result facts. | Tavily ran; candidates changed; block bypassable. | Deterministic-only. |
| `execution_started` | Show transient in-progress state after approval request is sent. | Match UI language where available. | No result facts yet. | Counts, candidates, success, Tavily completed. | Frontend transient only. |
| `execution_completed` | Confirm observed backend execution completion. | Match UI language where available. | Use only returned runtime/tool result facts. | Altered counts, candidates, filters, dedupe, location, ordering. | Deterministic-only. |
| `execution_failed` | Explain approved execution failed after it started. | Match UI language where available. | Use returned runtime/tool errors only. | Partial candidates without backend facts; retry automatically. | Deterministic-only. |
| `tool_unavailable` | Explain required service/config is unavailable. | Match UI language where available. | Distinguish tool/config issue from recruiter input error. | Bypass available; direct web search fallback. | Deterministic-only. |
| `search_result_summary` | Summarize backend report/result facts. | Match report language where available. | Public result evidence is limited. | Guaranteed matches; altered counts; invented quality. | Deterministic-only. |
| `agent_response` | Summarize returned results and limitations. | Match `agent_response.language`. | Separate strong signals from limitations and unknowns. | Changed summary facts, options, counts, candidates, ordering. | Current bounded text-only overlay. |
| `next_iteration_options` | Present inert follow-up suggestions. | Match agent response language. | Not executable now; requires future Build Plan and approval. | Apply/run now; auto-select; mutate options. | Deterministic-only. |
| `transient_status` | Show temporary UI progress or idle-processing state. | Match UI language where available. | Clear/update when backend state changes. | Durable backend facts; success/failure before result. | Frontend transient only. |
| `empty_state` | Explain no current data/action exists. | Match UI language where available. | Guidance only. | Fabricated plan/results/readiness. | Frontend transient only. |
| `system_error` | Show technical failure when no more specific type applies. | Match UI language where available. | Preserve more specific classifications when available. | Hide safety/validation/runtime/tool/execution classification; invent recovery/result facts. | Deterministic-only. |

## Approval And Runtime Wording

Approval wording must keep these states separate:

1. Build Plan / planning.
2. Runtime approval preparation.
3. Explicit recruiter approval.
4. Approved search execution.
5. Observed backend result.

Allowed wording:

- "Search Plan is ready for review. Execution still requires explicit approval."
- "Runtime approval is prepared for the visible Search Plan."
- "Approved execution is running."
- "Search completed after backend observed the approved tool result."

Forbidden wording:

- "I approved it."
- "I will run it now."
- "Search started" before the approved execution request starts.
- "Search completed" before the backend observed the tool result.
- "This AI preview can be approved and run" for non-executable previews.

## Evidence And Uncertainty Wording

Use conservative language for public-search evidence.

Rules:

- Public snippets are limited evidence, not full profile inspection.
- Missing stack does not prove the candidate lacks that stack.
- Missing seniority should be shown as unknown or not visible, not inferred.
- Unknown current location stays unknown.
- `ua.linkedin.com` is a useful country-domain signal, not a guaranteed current physical-location fact.
- Role, technology, stack, seniority, and location wording must follow backend evidence categories.
- Result summaries must distinguish strong visible signals from limitations.

Preferred phrases:

- "visible in public profile text";
- "not visible in returned snippets";
- "current location is unknown from returned public text";
- "country-domain signal, not proof of current location";
- "strong signal", not "verified match";
- "candidate to review", not "guaranteed candidate".

## Agent Message Vs UI/Data Label Boundary

This policy covers recruiter-visible agent message text.

Out of scope unless a later approved task changes UI copy policy:

- button labels such as `Build Plan`, `Approve & Search`, `Send`, and `Reset`;
- metric labels such as `Raw`, `Unique`, `Duplicates`, and `Failed queries`;
- Search Brief field labels such as `Role`, `Technology`, `Stack`, `Location`, `Depth`, and `Seniority`;
- candidate table field labels;
- candidate values such as name, headline, location, role, technology, stack, seniority, score, flags, URLs, snippets, and query-source metadata;
- query IDs and raw query text;
- hidden scoring, filter, dedupe, and location internals.

Agent messages may reference UI/data elements only when the referenced fact is allowed by P7-002 and returned by the current source of truth.

## Example Validation Rules

Every future example, deterministic message, or bounded LLM prompt example must be checked against P7-002.

Examples must not introduce:

- new Search Brief facts;
- new QueryPlan facts;
- approval state not returned by backend;
- runtime state not returned by backend;
- counts not returned by backend;
- candidate names;
- candidate URLs;
- raw snippets;
- raw Tavily result payloads;
- hidden scoring, filtering, dedupe, or location facts;
- direct web-search, LinkedIn login/scraping, candidate messaging, account actions, or autonomous execution capabilities.

Bad examples should identify which boundary they violate.

## Examples

Examples are templates. Values in braces must come from the source object allowed by P7-002.

### Onboarding

EN allowed:

```text
Tell me who we should find: role, main technology, location, and a few stack signals.
```

RU allowed:

```text
Опиши, кого ищем: роль, основную технологию, локацию и несколько stack-сигналов.
```

Forbidden:

```text
I prepared a Search Brief and can run the search.
```

Reason: onboarding cannot claim a Search Brief, plan, or execution exists.

### Clarification Question

EN allowed when backend selected `stack`:

```text
Which Java stack signals should I use?
```

RU allowed when backend selected `stack`:

```text
Какие Java stack-сигналы использовать?
```

Forbidden:

```text
I will use Spring and Kafka.
```

Reason: the agent cannot invent missing stack values.

### Brief Summary

EN allowed:

```text
Search Brief is ready: Backend Developer, Java, Ukraine, stack {stack}, standard depth.
```

RU allowed:

```text
Search Brief готов: Backend Developer с Java в Украине, stack: {stack}, standard depth.
```

Forbidden:

```text
The candidate search is ready to run automatically.
```

Reason: Search Brief readiness is not execution readiness.

### Agent Plan

EN allowed:

```text
I understood the task. The next safe step is Build Plan through the approved backend planner. Search will not run without approval.
```

RU allowed:

```text
Я понял задачу. Следующий безопасный шаг - Build Plan через approved backend planner. Поиск не запустится без approval.
```

Forbidden:

```text
I will run Tavily now.
```

Reason: Agent Plan proposes planning, not search execution.

### Agent Plan Unsupported

EN allowed:

```text
Agent v0 currently supports only Backend Developer with Java in Ukraine.
```

RU allowed:

```text
Agent v0 пока поддерживает только Backend Developer с Java в Украине.
```

Forbidden:

```text
I will use the old non-agent Build Plan instead.
```

Reason: unsupported Agent Plan must not silently fall back to an old non-agent path.

### Approval Required

EN allowed:

```text
Search Plan is ready for review. Execution still requires explicit approval.
```

RU allowed:

```text
Search Plan готов к проверке. Для запуска поиска все еще нужно явное approval.
```

Forbidden:

```text
Approval is complete and search started.
```

Reason: approval-required wording cannot imply approval or execution.

### Runtime Blocked

EN allowed:

```text
Runtime blocked this action before execution: {error_message}
```

RU allowed:

```text
Runtime заблокировал действие до запуска поиска: {error_message}
```

Forbidden:

```text
I bypassed the block and ran the search.
```

Reason: runtime blocks cannot be bypassed.

### Execution Completed

EN allowed:

```text
Search completed after backend observed the approved tool result.
```

RU allowed:

```text
Поиск завершен после того, как backend получил результат approved tool execution.
```

Forbidden:

```text
All candidates are verified matches.
```

Reason: completion does not prove candidate quality beyond returned report facts.

### Search Result Summary

EN allowed when backend report returned these values:

```text
Search completed: {unique_profiles} unique candidates from {raw_total} raw results, with {queries_succeeded}/{queries_total} queries succeeded.
```

RU allowed when backend report returned these values:

```text
Поиск завершен: {unique_profiles} уникальных кандидатов из {raw_total} raw results, успешно {queries_succeeded}/{queries_total} запросов.
```

Forbidden:

```text
I verified every LinkedIn profile directly.
```

Reason: the product uses approved backend public-search results, not direct LinkedIn inspection.

### Agent Response

EN allowed:

```text
The strongest visible signals are Java and target-role evidence. Main limitations are public snippet coverage and missing seniority for some candidates.
```

RU allowed:

```text
Самые сильные видимые сигналы - Java и совпадение по роли. Главные ограничения - public snippets и не всегда видимый seniority.
```

Forbidden:

```text
The LLM selected the best candidates.
```

Reason: LLM wording cannot change candidate selection, ordering, counts, or quality facts.

### Next Iteration Options

EN allowed:

```text
Try deep search depth. This is not executable now and still requires Build Plan and approval.
```

RU allowed:

```text
Можно попробовать deep search depth. Это не executable сейчас и все равно требует Build Plan и approval.
```

Forbidden:

```text
Click here to apply and run deep search.
```

Reason: current next-iteration options are inert and non-executable.

### Tool Unavailable

EN allowed:

```text
Tavily is unavailable, so approved search execution cannot proceed.
```

RU allowed:

```text
Tavily недоступен, поэтому approved search execution не может продолжиться.
```

Forbidden:

```text
I can bypass Tavily with direct web search.
```

Reason: direct web-search bypass is prohibited.

### Safety Refusal

EN allowed:

```text
I cannot log in to LinkedIn, scrape profiles, or message candidates. I can work only through the approved backend public-search pipeline.
```

RU allowed:

```text
Я не могу логиниться в LinkedIn, скрейпить профили или писать кандидатам. Я могу работать только через approved backend public-search pipeline.
```

Forbidden:

```text
I can try a direct LinkedIn search outside the app.
```

Reason: direct LinkedIn access and direct web-search bypass are prohibited.

## Version And Provenance Handoff

This policy version is:

```text
style_policy_version = phase_7_agent_wording_style_policy_v0
```

This task does not add metadata fields to code or API responses.

Later `P7-007` may reference this style policy version only as internal debugging/regression metadata and only within the P7-002 wording/provenance boundary. It must not become product analytics, external telemetry, persistent memory, user tracking, or an autonomous decision input.

## Future Task Handoff

- `P7-004` should use this policy to build deterministic source messages.
- `P7-005` should use this policy when deciding which message types may route to LLM wording.
- `P7-006` should use this policy in bounded prompt/payload contracts.
- `P7-007` should validate LLM/deterministic wording against this policy and record fallback/provenance within allowed metadata.
- `P7-008` should render typed agent messages without turning ordinary UI labels or candidate fields into LLM wording targets.
- `P7-009` should add golden conversation scenarios that check policy examples, forbidden wording, language handling, and provenance expectations.

Later tasks must preserve the default-deny rule: unlisted facts, derived claims, actions, and execution authority remain forbidden.
