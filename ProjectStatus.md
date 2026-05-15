# Project Status

## Current phase

Phase 1 POC completed successfully and was accepted as a proof of concept.

Phase 1.1 - POC behavior tuning is completed.

Phase 2 - Multi-query Search + Baseline Query Planner is completed.

Completed through `P2-013`: Phase 2 conclusions are documented, local structured-search snapshots are available, and the Ukraine `Location filter` now uses current-location classification instead of a finite foreign-location blacklist.

Current phase: `Phase 3 - Candidate Quality Layer`.

Later phase: `Phase 4 - AI Query Planner v0`.

Completed through `P3-010.2`: backend candidates now include seniority, normalized review flag details, explainable `quality_score`, the frontend renders a hybrid candidate quality view, the first real Java/Ukraine quality baseline is documented, the `missing_selected_stack` group has been reviewed, and stack evidence display labels are clearer. Next recommended task: `P3-011 Add adaptive multi-wave runner for quality evaluation`.

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

- Phase 2 search is driven by structured inputs: `Role Family`, `Technology`, `Stack`, and `Location`.
- `QueryPlanner v1` builds a visible 10-query `QueryPlan` from those inputs.
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

- Phase 3: `Candidate Quality Layer`, focused on name extraction, location confidence, stack/seniority scoring, ranking quality, and an adaptive multi-wave runner for quality evaluation.
- Phase 4: `AI Query Planner v0`, focused on replacing rule-based query generation while preserving the `QueryPlan` contract.

Phase 3 direction is selected: Candidate Quality Layer. AI Query Planner is deferred to Phase 4.

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

## Current known limitations

- LinkedIn public snippets remain incomplete and inconsistent.
- Tavily search behavior can vary between runs.
- `LinkedIn profiles only` filters by URL pattern only.
- `Location filter` currently has only the first country config: `Ukraine`.
- Future countries need their own country-domain and `target_location_terms` mapping; they should reuse current-location classification instead of introducing finite negative-location blacklists.
- Header/location detection uses Tavily public snippets/content only and is not equivalent to verified profile enrichment.
- `ua.linkedin.com/in/...` is not a guaranteed current physical location.
- Current-location extraction is conservative and can keep ambiguous snippets unknown.
- `RuleBasedQueryPlanner v1` is still the active planner; AI planner is not implemented yet.
- Candidate quality score is a deterministic v1 signal and should not be treated as final recruiting quality.
- No database, shortlist, authentication, AI agent, LinkedIn login, scraping, or direct LinkedIn automation is included.

## Reference documents

- `Roadmap.md`
- `Tasks.md`
- `docs/phase-1-poc-findings.md`
- `docs/phase-3-quality-baseline.md`
