# Project Status

## Current phase

Phase 1 POC completed successfully and was accepted as a proof of concept.

Phase 1.1 - POC behavior tuning is completed.

Phase 2 - Multi-query Search + Baseline Query Planner is completed.

Completed through `P2-013`: Phase 2 conclusions are documented, local structured-search snapshots are available, and the Ukraine `Location filter` now uses current-location classification instead of a finite foreign-location blacklist.

Phase 3 - Candidate Quality Layer is completed.

Phase 4 - AI Agent Foundation is completed.

Current phase: `Phase 5 - Recruiter Chat UX + Search Brief conversation`.

Completed through `P5-007.1`: Phase 4 is closed as an AI Agent Foundation, and Phase 5 now has its recruiter chat contract, backend chat-to-brief adapter, primary recruiter chat frontend, approvable `Build Plan` path, first human-approved Agent v0 slice for the Java/Ukraine baseline, deterministic post-results Agent Response in chat, bounded LLM-assisted wording for Agent Plan/Response with deterministic fallback, and synchronized Phase 5 documentation/guardrails. The backend has Search Brief validation/adapter, Agent Tools v0 metadata, explicit AI planner mode, deterministic AI QueryPlan validation/fallback, planner explanation UI, backend approval before Tavily execution, AI planner baseline evaluation, AI planner coverage policy/repair behavior, `POST /api/recruiter-chat/turn`, `POST /api/agent/plan`, and `agent_response` on approved search responses. This is still not a complete autonomous recruiter agent.

Completed Phase 5 tasks: `P5-001 Define recruiter chat and Search Brief conversation contract`, `P5-002 Add backend chat-to-brief adapter`, `P5-003 Replace structured form with recruiter chat UI`, `P5-004 Make Build Plan produce an approvable Search Plan`, `P5-005 Instantiate human-approved Agent v0 for Java/Ukraine baseline`, `P5-006 Add post-results Agent Response in chat`, `P5-007 Add LLM-assisted Agent Plan/Response with deterministic fallback`, `P5-007.1 Sync Phase 5 docs and tighten Agent Plan guardrail`.

Next task to review: `P5-008 Chat onboarding and clarification quality`.

Current agreed strategy:

- finish one narrow high-quality flow first: `Backend Developer + Java + Ukraine`;
- do not expand countries or technologies yet;
- finish Phase 5 by making chat collect, clarify, refine, plan, run approved search, summarize results, guide the next iteration, and present a coherent AI Agent visual style;
- add Phase 5.5 after Phase 5 to modularize the backend before the Phase 6 tool-calling runtime;
- keep ordinary LLM-assisted agent conversation wording for Phase 7, after the runtime message taxonomy is stable;
- keep candidate workspace/shortlist for Phase 8 and database/persistent memory for Phase 9.

Planned Phase 5 order:

1. `P5-008 Chat onboarding and clarification quality`.
2. `P5-009 Search Brief refinement through chat`.
3. `P5-010 Result-to-next-iteration loop`.
4. `P5-011 Apply AI Agent visual direction / dark workspace refresh`.
5. `P5-012 Close Phase 5 with narrow Java/Ukraine agent UX decision`.

Planned Phase 5.5 order: technical modularization before Agent Runtime, with no product behavior changes.

Planned later phases:

- Phase 6: `Human-approved Tool-Calling Agent Runtime`.
- Phase 7: `Agent Conversation Wording Layer`.
- Phase 8: `Candidate Workspace/Table + Shortlist`.
- Phase 9: `Persistent Memory + Saved Searches`.

`P5-001` is completed as a docs-only contract task. The approved recruiter chat contract supports Russian and English input, asks one clarifying question at a time, replaces the structured form as the primary UX over time, shows a normalized brief summary before `Build Plan`, and keeps `Build Plan` separate from Tavily execution. After `P5-004`, primary chat `Build Plan` defaults to `rule_based` so supported briefs produce an approvable Search Plan. Tavily execution remains behind explicit backend approval. Direct web-search bypass, direct LinkedIn access/automation, LinkedIn login, LinkedIn scraping/restriction bypass, candidate messaging/automatic outreach, autonomous execution, and user or third-party account actions remain prohibited behavior.

`P5-002` is implemented as a backend chat-to-brief adapter. The guardrail is preserved: `chat messages -> draft Search Brief -> validation -> one assistant response`. It adds `POST /api/recruiter-chat/turn`, strict OpenAI/ChatGPT JSON extraction, deterministic prohibited-request refusal, deterministic supported-signal hints, Ukraine alias normalization, conservative draft merge, existing Search Brief validation, one next clarification question, default `recommended_planner_mode = rule_based`, and a no-Tavily smoke script. It does not build `QueryPlan`, call `/api/agent/query-plan`, call Tavily, execute search, or change frontend UI.

`P5-003` is implemented. The primary frontend input is now recruiter chat. The implemented path is `chat -> normalizedBrief -> Build Plan -> adapted_structured_request/query_plan -> Approve & Search`, and search execution uses `adapted_structured_request` from the planner response, not old structured-form DOM fields. AI draft `validated_not_executable` plans remain visible but non-executable; rule-based and rule-based fallback plans remain the only executable frontend path.

`P5-004` is implemented. The primary recruiter-chat flow is now `Chat -> Search Brief -> Build Plan -> Review Search Plan -> Approve & Search -> Results`. `Build Plan` produces an approvable deterministic backend plan for supported briefs by using `planner_mode = rule_based`; `Approve & Search` is enabled only after a visible fingerprinted Search Plan exists. This is not a retreat from AI planning: it gives the future AI Agent a safe executable bridge through the existing backend planner and approval gate, while the existing AI planner capability remains available for the next reviewed step toward AI-assisted executable planning.

`P5-005` is implemented. After a ready supported Java/Ukraine Search Brief, the frontend calls `POST /api/agent/plan`, shows an Agent Plan as a chat message, and enables `Build Plan` only when a supported `agent_plan.proposed_action` exists. `Build Plan` now sends the action and Search Brief fingerprint to `/api/agent/query-plan`; the backend rejects stale or mismatched Agent Plan actions instead of falling back to a non-agent path. No Tavily execution, post-results Agent Response, new LLM behavior, generic tool loop, persistent backend state, direct LinkedIn access/automation, or role/country expansion was added.

`P5-006` is implemented. Approved search responses now include deterministic backend-generated `agent_response` grounded only in already returned search data: executed `QueryPlan` input snapshot, normalized structured request, report counts, deduped candidates, quality signals, review flags, and known limitations. The frontend passes minimal `agent_language` and renders the response as a local-only `AI Agent` chat message after results. Suggested next actions stay inert text. No broad `agent_context`, full chat history, extra Tavily/LLM/web/LinkedIn calls, executable next-action buttons, persistence, or autonomous behavior was added.

`P5-007` is implemented. Agent Plan and Agent Response now support LLM-assisted wording as an optional backend overlay after deterministic objects are built. The LLM receives bounded payloads only, with no raw candidate URLs or full candidate records. Backend validation rejects unsafe, wrong-language, fact-changing, action-changing, or number-inventing output and falls back to deterministic wording with provenance metadata. The LLM has no execution authority and cannot change `QueryPlan`, approval, Tavily execution, filters, scoring, dedupe, location logic, fingerprints, suggested next actions, or candidate ordering.

`P5-007.1` is implemented as a stabilization task. `README.md`, `AGENTS.md`, `ProjectStatus.md`, `Roadmap.md`, and `Tasks.md` now agree that `P5-007` is implemented. The docs clarify that `OPENAI_API_KEY` and `OPENAI_MODEL` are required for the current primary recruiter chat / AI planner paths, while LLM-assisted Agent Plan/Response wording has deterministic fallback. OpenAI Chat Completions requests use `max_completion_tokens`, not legacy `max_tokens`, for `gpt-5.4-mini` compatibility. Backend `/api/agent/query-plan` now requires the current Agent Plan action and Search Brief fingerprint instead of allowing a direct Build Plan call without Agent Plan context.

Latest Phase 3 quality baseline used `Backend Developer + Java + Spring/Kafka + Ukraine` with visible profile/location filters enabled:

- Queries succeeded: 10/10
- Raw Tavily results: 200
- Displayed occurrences: 102
- Unique candidates: 57
- Duplicates removed: 45
- Hidden by profile filter: 13
- Hidden by location filter: 85
- Quality score average: 76.3

Main Phase 3 baseline conclusion: the Candidate Quality Layer is useful for ranking and review, but selected stack evidence remains weak in public Tavily/LinkedIn snippets. See `docs/phase-3-quality-baseline.md`.

`P3-010.1` conclusion: `missing_selected_stack` mostly means the selected stack is not visible in Tavily public snippets, not that the candidate lacks the stack. The current backend behavior is honest, but the frontend wording `Stack: n/a` was too blunt. The agreed display label is now `Not visible` for selected-but-unconfirmed stack while keeping `selected_stack_missing` as a ranking penalty, not a hard filter.

`P3-010.2` implemented the agreed frontend display semantics: direct evidence shows actual stack terms, `missing_selected_stack` shows `Not visible`, `stack_query_source_only` shows `Not confirmed`, and future no-stack-requested state is reserved as `N/A`. Quality scoring and backend search/filter logic were not changed.

`P3-011` added `/api/structured-search/multi-wave` as an experimental backend endpoint. It repeats the same validated `QueryPlan`, dedupes across waves, preserves existing `query_sources`, adds separate `wave_sources`, stops on low incremental unique gain, and writes `structured-search-multi-wave` snapshots. The normal `/api/structured-search` endpoint remains the stable single-wave path.

`P3-012` evaluated the multi-wave runner with one real Tavily run. It ran 4 waves, executed 40 queries, stopped on `low_incremental_gain`, and produced 67 final unique candidates. Compared with wave 1 inside the same run, multi-wave added 7 unique candidates, including 3 high-quality candidates and 1 direct-stack candidate, after 30 extra Tavily queries. Recommendation: do not make multi-wave default; keep it backend-only for now or consider an explicit advanced/deeper-search control in `P3-013`.

`P3-013` added the explicit frontend control: default Search remains single-wave through `/api/structured-search`; enabling the `Multi-wave` toggle calls `/api/structured-search/multi-wave` with approved defaults and shows waves, executed queries, stop reason, and new candidates per wave when returned.

`P3-014` closed Phase 3 as a docs-only handoff. Phase 4 should preserve the `QueryPlan` contract, structured request, visible filters, executor/dedupe/report pipeline, snapshots, and Candidate Quality Layer while adding the AI Agent Foundation: `Search Brief`, agent tool boundaries, AI-assisted planning, explanations, and approval gates before Tavily execution.

`P4-001` is approved as the AI Agent Foundation contract. Phase 4 should use an LLM/ChatGPT layer for recruiter intent understanding, Search Brief creation, planning, clarification, and explanations, while keeping execution inside the existing validated backend pipeline. The approved flow is `Search Brief -> Agent Plan -> Agent Action -> optional Approval Gate -> validated Tool Call -> Agent Response`.

`P4-002` is approved as the `Search Brief v0` schema contract. The brief is a dialogue state, not just a form copy. It supports `needs_clarification` and `ready_for_planning`, keeps `source_text`, `missing_fields`, `clarifying_questions`, and `assumptions`, leaves `target_titles` to the planner, and uses `exclusions` only for explicit recruiter constraints, not location blacklists.

`P4-003` is approved as the Search Brief validation/adapter contract. It should bridge `Search Brief -> Search Brief validation/normalization -> StructuredSearchRequest adapter -> existing structured-search validation`, reuse `normalize_structured_search_request(...)` as the authoritative search validation layer, reject `target_titles`, preserve `search_depth` as metadata, and avoid LLM calls, Tavily calls, query-plan generation, or search execution.

`P4-004` is approved as the Agent Tools v0 contract. The approved tools are `validate_search_brief`, `adapt_brief_to_structured_request`, `build_query_plan`, `validate_query_plan`, `run_single_wave_search`, `run_multi_wave_search`, `analyze_candidate_quality`, `summarize_search_results`, and `suggest_next_iteration`. Planning/analysis tools do not require approval; search execution tools require explicit approval.

`P4-005` is approved as the AI Query Planner v0 contract behind explicit mode. A real LLM/ChatGPT call is used for planning/explanation only, with `rule_based` remaining default. AI output is a non-executable `draft_query_plan`; deterministic validation exists in `P4-006`, and AI-generated plan execution remains out of scope until a later task.

`P4-006` is approved as the deterministic AI QueryPlan validation/fallback contract. Validation uses `normalized_brief + normalized_structured_request` as source of truth, marks valid AI plans as `validated_not_executable`, returns structured errors for rejected plans, and provides visible fallback to `RuleBasedQueryPlanner` when supported. No Tavily execution is introduced.

`P4-007` is approved as the planner explanation UI contract. It should extend the existing `Generated QueryPlan` preview with planner mode, Search Brief summary, planner explanation, validation/fallback state, structured errors/warnings, and an approval-needed notice, while remaining backward-compatible with the current rule-based QueryPlan preview.

`P4-003` through `P4-007` are implemented in code. The backend now supports `SearchBrief` validation/adapter endpoints, Agent Tools v0 metadata, explicit AI planner mode through OpenAI/ChatGPT for planning only, deterministic AI QueryPlan validation/fallback, and non-executable planner responses. The frontend now has a `Planner mode` control and renders Search Brief summary, planner explanation, validation/fallback state, and approval-needed notices.

`P4-008` is implemented as the real backend approval gate before Tavily execution. `/api/structured-search` and `/api/structured-search/multi-wave` now require explicit execution approval, bind approval to the concrete action and current QueryPlan fingerprint, reject missing/stale/wrong-action approval before Tavily, log approval metadata in search snapshots, and keep AI-generated plans non-executable. The legacy raw `/api/search` Tavily path is disabled so execution cannot bypass the approval-gated structured pipeline. Rule-based single-wave and multi-wave are the supported execution targets.

`P4-009` is completed as a no-Tavily planner evaluation. For the baseline `Backend Developer + Java + Spring/Kafka + Ukraine`, the rule-based planner produced the expected 10-query coverage. A live AI planner run produced a formally valid but too narrow 1-query plan, and `ai_with_fallback` produced a 3-query AI plan without triggering fallback. Conclusion: AI is useful for intent understanding and explanation, but current validation does not yet enforce baseline coverage quality. `RuleBasedQueryPlanner v1` remains the default and only executable planner. See `docs/phase-4-ai-planner-baseline.md`.

`P4-010` is implemented. The root cause was confirmed: the old AI planner prompt said `max_queries = 10`, showed a one-query output example, and the validator accepted `1..10` queries. The AI planner prompt now requests the tested 10-query standard baseline shape, `AIPlannerCoveragePolicy v0` applies strict coverage checks for the current Java/Ukraine baseline, `ai_with_fallback` can make one bounded repair attempt, and under-covered plans fall back visibly to `RuleBasedQueryPlanner`. AI-generated plans remain non-executable and Tavily is not called by this flow.

`P4-011` is completed as a docs-only closeout. Phase 4 is closed as an AI Agent Foundation, not as a complete autonomous recruiter agent. The closeout decision: the backend foundation is ready for Phase 5 because Search Brief, AI planning, deterministic validation/fallback, coverage policy, explanations, and approval-gated execution boundaries exist. Full recruiter chat, human-approved tool runtime, candidate workspace, and persistence remain later phases. Autonomous execution is prohibited: the agent may suggest, prepare, explain, validate, and analyze, but externally meaningful execution must require explicit approval. Direct LinkedIn access/automation, LinkedIn login, LinkedIn scraping/restriction bypass, candidate messaging/automatic outreach, and user or third-party account actions remain absolute prohibited behavior.

## What was built in Phase 1

- FastAPI backend.
- Static HTML/CSS/JS frontend.
- Editable X-ray Boolean query builder.
- Tavily search endpoint.
- Raw Tavily result display.
- Normalized result format.
- Initial relevance scoring.
- Initial required-condition filtering.
- Phase 1 findings document.

## Phase 1 POC result

- Raw Tavily results: 20
- Normalized results: 20
- Relevant results after required filters: 10
- Original target: 20 relevant candidates
- Status: successful POC accepted for Phase 1

## What Phase 1.1 changed

Phase 1.1 corrected the product behavior discovered during real frontend testing.

Implemented:

- Frontend sends only the final editable Boolean query and `max_results` when the user clicks `Search`.
- Form fields are only helpers for building the editable Boolean query.
- Backend no longer uses `main_anchor`, `additional_anchors`, `stack`, or `location` as hidden filters.
- UI shows `Search results` instead of `Relevant results`.
- Scoring is neutral and non-filtering.
- Results are sorted by neutral score but are not hidden by score.
- `LinkedIn profiles only` is an explicit frontend toggle and is off by default.
- `Ukraine LinkedIn domain only` is an explicit frontend toggle and is off by default.
- URL/profile filtering is applied only when the user enables the relevant visible toggle.

## Current product rule

- Current frontend search starts from recruiter chat that produces a validated `Search Brief`.
- Backend execution is still driven by the adapted structured request fields: `Role Family`, `Technology`, `Stack`, and `Location`.
- `QueryPlanner v1` builds a visible 10-query `QueryPlan` from the adapted structured request.
- Tavily receives only the generated queries from the visible `QueryPlan`.
- `LinkedIn profiles only` is an explicit visible filter.
- `Location filter` is an explicit visible filter and currently has the first config for `Ukraine`.
- `ua.linkedin.com/in/...` is treated as a country-domain signal, not a guaranteed current physical-location signal.
- The Ukraine `Location filter` uses `target_location_terms` and extracts a conservative `current_location_line` from Tavily public LinkedIn header/snippet text.
- Current-location classification is `target_location`, `foreign_current_location`, or `unknown_current_location`.
- Explicit foreign current location, for example `Warsaw, Mazowieckie, Poland`, hides the candidate even if the URL is `ua.linkedin.com/in/...`.
- Unknown current location can still fall back to softer signals: `country_domain`, `rescued_header_location`, `weak_history_only`, or `unknown_non_country_domain`.
- Non-UA LinkedIn profiles can be rescued only when the Tavily public header/current-location signal contains supported Ukraine target-location terms.

## Phase 1.1 test results

Target profile: Java programmer in Ukraine.

Test setup:

- `max_results`: 20
- `LinkedIn profiles only`: on
- `Ukraine LinkedIn domain only`: on
- Final displayed result shape: only `ua.linkedin.com/in/...` profile-like URLs.

10 tested query variants produced 53 unique `ua.linkedin.com/in/...` profiles in total.

Best single-query result:

```text
site:linkedin.com/in AND "Java Software Engineer" AND "Ukraine"
```

Result: 16 Ukrainian LinkedIn profiles from 20 raw Tavily results.

Other useful variants:

- `site:linkedin.com/in AND "Java Programmer" AND "Ukraine"`: 12 Ukrainian LinkedIn profiles from 20 raw results.
- `site:linkedin.com/in AND ("Java Developer" OR "Java Engineer" OR "Backend Java") AND ("Ukraine" OR "Kyiv" OR "Lviv")`: 10 Ukrainian LinkedIn profiles from 20 raw results.
- `site:linkedin.com/in AND ("Senior Java Developer" OR "Middle Java Developer") AND "Ukraine"`: 9 Ukrainian LinkedIn profiles from 20 raw results.

Weak result:

```text
site:linkedin.com/in AND "Java" AND ("Developer" OR "Engineer") AND ("Java" OR "Spring") AND "Ukraine"
```

Result: 0 Ukrainian LinkedIn profiles after both visible filters were enabled. The query can return role-like profiles, but too many results are outside `ua.linkedin.com/in/...` or are not usable after the Ukraine-domain filter.

## Main conclusion

Phase 1.1 improved the product substantially, but mainly by making the search behavior honest, visible, and controllable.

It did not prove that one broad universal query is the best strategy. The tests suggest the opposite: several focused queries produce better candidate coverage than one broad query.

## Phase 2 recommendation

Start Phase 2 with sequential multi-query search:

1. Run several focused Tavily queries.
2. Merge all returned results.
3. Normalize LinkedIn URLs.
4. Dedupe by normalized URL.
5. Apply visible filters such as `LinkedIn profiles only` and `Ukraine LinkedIn domain only`.
6. Show one combined candidate list.

Recommended first multi-query set:

- U02: `site:linkedin.com/in AND "Java Software Engineer" AND "Ukraine"`
- U10: `site:linkedin.com/in AND "Java Programmer" AND "Ukraine"`
- U08: `site:linkedin.com/in AND ("Java Developer" OR "Java Engineer" OR "Backend Java") AND ("Ukraine" OR "Kyiv" OR "Lviv")`

Expected result based on current tests: approximately 24-30 unique Ukrainian LinkedIn profiles in one pass. The simple sum is 38, but duplicates are expected across queries.

## Phase 2 baseline result

Baseline input:

- Role Family: `Backend Developer`
- Technology: `Java`
- Stack: `Spring`, `Kafka`, `AWS`
- Location: `Ukraine`
- `LinkedIn profiles only`: on
- `Ukraine LinkedIn domain only`: on

Measured result from one `POST /api/structured-search` run:

- Queries total: 10
- Queries succeeded: 10
- Queries failed: 0
- Raw Tavily results: 190
- Normalized results: 190
- Displayed before dedupe: 75
- Unique profiles after dedupe: 51
- Duplicates removed: 24
- Hidden by profile filter: 40
- Hidden by location-domain filter: 75

Phase 2 baseline criterion passed: 51 unique `ua.linkedin.com/in/...` profiles vs target 20.

Best query contributor:

- Q02 `site:linkedin.com/in AND "Java Software Engineer" AND "Ukraine"` added 13 new unique profiles.

Important limitation:

- `ua.linkedin.com/in/...` remains a useful Ukraine-domain signal, not a guaranteed current-location signal. At least one top result had a Ukraine-domain URL while the public snippet showed `Prague, Czechia`.
- Future work should add explicit location quality logic instead of relying only on country-specific LinkedIn subdomains.

## Phase 2 location filter result

`P2-009.1` replaced the hard `Ukraine LinkedIn domain only` structured contract with `location_filter_enabled`.

`P2-012` and `P2-013` then superseded the initial blacklist-style `negative_terms` logic. The current runtime behavior is:

- config stores Ukraine `target_location_terms`, not a finite list of bad countries/cities;
- the filter extracts a conservative `current_location_line` from multiline and one-line Tavily snippets;
- `target_location` is displayed;
- `foreign_current_location` becomes `excluded_foreign_current_location` and is hidden before `country_domain` can allow it;
- `unknown_current_location` falls back to country-domain/header/weak/unknown signals;
- frontend report shows `Foreign location` via `hidden_by_foreign_current_location`.

Current baseline input:

- Role Family: `Backend Developer`
- Technology: `Java`
- Stack: `Spring`, `Kafka`, `AWS`
- Location: `Ukraine`
- `LinkedIn profiles only`: on
- `Location filter`: on

Historical `P2-009.1` measured result from one `POST /api/structured-search` run before `P2-012`:

- Queries total: 10
- Queries succeeded: 10
- Queries failed: 0
- Raw Tavily results: 200
- Normalized results: 200
- Displayed before dedupe: 85
- Unique profiles after dedupe: 58
- Duplicates removed: 27
- Hidden by profile filter: 53
- Hidden by location filter: 62
- Rescued by header/location: 13 occurrences, 9 unique profiles
- Hidden by negative header/location: 3 occurrences, 2 unique profiles
- Weak history-only location signal: 26 occurrences, 18 unique profiles
- Unknown non-country-domain location: 33 occurrences, 21 unique profiles

Location filter unique breakdown:

- `country_domain`: 49
- `rescued_header_location`: 9
- `excluded_negative_header_location`: 2
- `weak_history_only`: 18
- `unknown_non_country_domain`: 21

Conclusion from `P2-009.1`: the first `Location filter` improved Phase 2 quality compared with strict domain-only filtering because it kept the Ukraine-domain signal, rescued strong non-UA profiles with Ukraine in header/location, and excluded some explicit foreign-current-location matches.

Current `P2-012`/`P2-013` replay on local snapshot `2026-05-14T17-12-12Z_structured-search_backend-developer-java-ukraine.json`:

- Raw Tavily results: 197
- Displayed occurrences: 105
- Unique profiles after dedupe: 73
- Displayed unique status breakdown: `target_location = 71`, `country_domain = 2`
- Known `ua.linkedin.com` false positives with `Warsaw, Mazowieckie, Poland` are hidden as `excluded_foreign_current_location`

Live Tavily runs are not stable. Recent runs for `Backend Developer + Java + Spring/Kafka + Ukraine` produced roughly `55-60` unique profiles in a single wave. Multi-wave experiments showed limited incremental gain:

- 1 wave: 60 cumulative unique profiles
- 3 waves: 64 cumulative unique profiles
- 5 waves: 61 cumulative unique profiles in one fresh block
- 10 waves: 60 cumulative unique profiles in one fresh block

Conclusion: multi-wave can add candidates, but returns diminish quickly. A future implementation should stop based on incremental unique gain rather than always running a fixed high number of waves.

## Phase 2 final conclusion

Phase 2 is completed successfully.

What Phase 2 proved:

- Multi-query search gives stronger coverage than one broad query for the tested Java/Ukraine scenario.
- `QueryPlan` is the right architectural contract for the next product steps.
- The executor, dedupe, report, and frontend can stay stable while planner logic evolves.
- Visible filters are the right product behavior; hidden backend filtering caused confusion earlier.
- Location should be treated as a confidence signal, not a single hard URL-domain rule.

Final baseline numbers remain above the Phase 2 success criterion:

- Historical `P2-009.1` single run: 58 unique candidates vs target 20
- Current `P2-012`/`P2-013` local replay: 73 unique candidates vs target 20
- Recent live single-wave runs: roughly 55-60 unique candidates vs target 20
- The exact Tavily count is not stable and should not be treated as a deterministic product guarantee

Recommended next steps:

- Phase 5: `Recruiter Chat UX + Search Brief conversation`, focused on one narrow Java/Ukraine flow where chat collects and refines a validated `Search Brief`, uses Phase 4 planner/approval contracts, guides a next iteration after results, and gets a coherent AI Agent visual style. `P5-001` through `P5-007.1` are completed; `P5-008` through `P5-012` are planned next.
- Phase 5.5: `Technical modularization before Agent Runtime`, focused on splitting `app/main.py` into focused modules without changing product behavior before the tool-calling runtime.
- Phase 6: `Tool-Calling Agent Runtime`, focused on a bounded, human-approved agent loop that can choose approved backend tools, inspect results, and suggest next iterations without autonomous execution.
- Phase 7: `Agent Conversation Wording Layer`, focused on LLM-assisted wording after the runtime message taxonomy is stable.
- Phase 8: `Candidate Workspace/Table + Shortlist`.
- Phase 9: `Persistent Memory + Saved Searches`.

Phase 4 is completed as AI Agent Foundation. Recruiter Chat UX + Search Brief conversation is now the active Phase 5 direction. Every following task should intentionally move the product toward a real AI Agent experience while preserving backend tool boundaries and explicit approval before execution.

## Verification

- `python -m compileall app`
- `node --check app/static/app.js`
- Backend smoke-check for query-only request behavior.
- Backend smoke-check for neutral scoring.
- Backend smoke-check for LinkedIn profile URL detection and toggle request field.
- Backend smoke-check for Ukraine LinkedIn domain URL detection and counts.
- UI check: `Search results`, `LinkedIn profiles only`, and `Ukraine LinkedIn domain only` are visible; both toggles are off by default.
- Phase 2 `/api/query-plan` smoke: 10 generated queries.
- Phase 2 `/api/structured-search` baseline run: 51 unique profiles.
- Phase 2 `P2-009.1` backend smoke: `location_filter_enabled` contract, no legacy `location_domain_only`, rescue/weak/negative signals, and candidate-level URL merge.
- Phase 2 `P2-009.1` browser smoke: `Location filter` toggle, generated `QueryPlan`, frontend report metrics, and no console errors.
- Phase 2 `P2-009.1` real baseline run: 58 unique profiles with the new location filter.
- Phase 2 `P2-010` documentation closeout completed.
- Phase 2 `P2-011` local structured-search snapshots added under `logs/search-runs/`.
- Phase 2 `P2-012` current-location classification smoke passed: target, foreign, unknown, weak-history-only, duplicate-merge, and filter-off cases.
- Phase 2 `P2-013` conservative one-line current-location extraction smoke passed.
- Phase 2 multi-wave Tavily experiments completed for 1, 3, 5, and 10 waves.
- Phase 3 local smoke checks passed for seniority detection, review flag taxonomy, and quality score.
- Phase 3 browser verification passed for the hybrid candidate quality view on desktop and mobile viewport.
- Phase 3 `P3-010` real Java/Ukraine quality baseline completed: 57 unique candidates from 200 raw Tavily results.
- Phase 3 `P3-010.1` no-code review completed for `missing_selected_stack` candidates from the exact baseline snapshot.
- Phase 3 `P3-010.2` frontend stack display semantics passed syntax, mapping, snapshot-state, render, and compile checks.
- Phase 3 `P3-011` no-Tavily smoke passed for multi-wave validation, early stop, cross-wave dedupe, `wave_sources`, snapshot type, and unchanged single-wave endpoint behavior.
- Phase 3 `P3-012` real adaptive multi-wave evaluation completed: 4 waves, 40 queries, 67 unique candidates, stopped by low incremental gain.
- Phase 3 `P3-013` frontend smoke passed for default single-wave endpoint, toggle-on multi-wave endpoint, multi-wave defaults payload, and report metric rendering.
- Phase 3 `P3-014` docs-only closeout completed and Phase 4 handoff prepared.
- Phase 4 `P4-003`-`P4-007` implementation checks passed: backend compile, frontend syntax, no-Tavily smoke for SearchBrief/tools/rule-based plan/AI validation/mocked AI fallback, browser smoke for planner UI, live OpenAI planner call, and live Tavily single-wave run through the backend.
- Phase 4 `P4-008` implementation checks passed: backend compile, frontend syntax, no-Tavily smoke for missing/wrong/stale approval rejection, approved single-wave, approved multi-wave, and snapshot approval metadata.
- Phase 4 `P4-009` no-Tavily planner evaluation completed: rule-based planner returned 10 baseline queries, live AI planner returned 1 query, and live `ai_with_fallback` returned 3 queries without fallback because the current validator does not yet enforce coverage quality.
- Phase 4 `P4-010` implementation checks passed: backend compile, no-Tavily mocked smoke for coverage gate, one repair attempt, fallback after failed repair, validation endpoint coverage errors, and live no-Tavily OpenAI planner evaluation returning 10 queries for both `ai` and `ai_with_fallback`.
- Phase 4 `P4-011` docs-only closeout completed: Phase 4 is completed as AI Agent Foundation and Phase 5 is the next active phase.
- Phase 5 `P5-004` implementation checks passed: backend compile, frontend syntax, chat adapter smoke, git whitespace check, and browser smoke for RU chat -> Search Brief -> `Build Plan` -> `Search Plan` / `Ready for approval` with 10 rule-based queries and enabled `Approve & Search`. Tavily execution was not triggered.
- Phase 5 `P5-005`-`P5-007` implementation checks passed: backend compile, frontend syntax, no-Tavily Agent Plan smoke, no-Tavily Agent Response smoke, and LLM wording smoke for assisted wording, deterministic fallback, disallowed-number fallback, provenance metadata, and no raw LinkedIn URL/full candidate payload.
- Phase 5 `P5-007.1` stabilization checks passed: backend compile, frontend syntax, Phase 5 smoke scripts, and missing Agent Plan action/fingerprint rejection in `/api/agent/query-plan`.

## Current known limitations

- LinkedIn public snippets remain incomplete and inconsistent.
- Tavily search behavior can vary between runs.
- `LinkedIn profiles only` filters by URL pattern only.
- `Location filter` currently has only the first country config: `Ukraine`.
- Future countries need their own country-domain and `target_location_terms` mapping; they should reuse current-location classification instead of introducing finite negative-location blacklists.
- Header/location detection uses Tavily public snippets/content only and is not equivalent to verified profile enrichment.
- `ua.linkedin.com/in/...` is not a guaranteed current physical location.
- Current-location extraction is conservative and can keep ambiguous snippets unknown.
- `RuleBasedQueryPlanner v1` is still the default execution planner. AI draft planning exists behind explicit mode, but AI-generated plans remain non-executable until a later reviewed task enables AI plan execution through deterministic validation and approval.
- Current AI QueryPlan validation now includes strict `AIPlannerCoveragePolicy v0` coverage checks for the Java/Ukraine standard baseline. Unsupported briefs still need future coverage policies and return a visible `coverage_policy_not_configured` warning.
- Candidate quality score is a deterministic v1 signal and should not be treated as final recruiting quality.
- No database, shortlist, authentication, or autonomous AI agent runtime is included.
- Absolute product boundaries: no direct web-search bypass outside the approved backend pipeline, no direct LinkedIn access/automation, no LinkedIn login, no LinkedIn scraping or restriction bypass, no automatic candidate messaging, no autonomous execution, and no actions with user or third-party accounts.

## Reference documents

- `Roadmap.md`
- `Tasks.md`
- `docs/phase-5-agent-stabilization.md`
- `docs/phase-1-poc-findings.md`
- `docs/phase-3-quality-baseline.md`
- `docs/phase-3-multi-wave-evaluation.md`
