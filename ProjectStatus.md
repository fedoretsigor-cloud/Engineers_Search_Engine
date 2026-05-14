# Project Status

## Current phase

Phase 1 POC completed successfully and was accepted as a proof of concept.

Phase 1.1 - POC behavior tuning is completed.

Phase 2 - Multi-query Search + Baseline Query Planner is completed.

Completed through `P2-010`: Phase 2 conclusions are documented. Next decision: choose Phase 3 direction between `AI Query Planner v0` and `Candidate Quality Layer`.

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
- `ua.linkedin.com/in/...` is treated as one location signal, not the only location signal and not a perfect current-location guarantee.
- Non-UA LinkedIn profiles can be rescued only when the Tavily public header/location text contains Ukraine location terms.
- Profiles with explicit negative header/location terms such as `Prague`/`Czechia` are hidden when the location filter is enabled.

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

Current baseline input:

- Role Family: `Backend Developer`
- Technology: `Java`
- Stack: `Spring`, `Kafka`, `AWS`
- Location: `Ukraine`
- `LinkedIn profiles only`: on
- `Location filter`: on

Measured result from one `POST /api/structured-search` run:

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

Conclusion: the new `Location filter` improved Phase 2 quality compared with strict domain-only filtering because it kept the Ukraine-domain signal, rescued strong non-UA profiles with Ukraine in header/location, and excluded explicit foreign-current-location matches.

## Phase 2 final conclusion

Phase 2 is completed successfully.

What Phase 2 proved:

- Multi-query search gives stronger coverage than one broad query for the tested Java/Ukraine scenario.
- `QueryPlan` is the right architectural contract for the next product steps.
- The executor, dedupe, report, and frontend can stay stable while planner logic evolves.
- Visible filters are the right product behavior; hidden backend filtering caused confusion earlier.
- Location should be treated as a confidence signal, not a single hard URL-domain rule.

Final baseline numbers:

- Raw Tavily results: 200
- Unique candidates: 58
- Rescued by header/location: 9 unique profiles
- Excluded by negative header/location: 2 unique profiles
- Success criterion: passed, 58 unique candidates vs target 20

Recommended next decision:

- Option A: `Phase 3A - AI Query Planner v0`, focused on replacing rule-based query generation while preserving the `QueryPlan` contract.
- Option B: `Phase 3B - Candidate Quality Layer`, focused on name extraction, location confidence, stack/seniority scoring, and ranking quality.

No Phase 3 direction has been selected yet.

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

## Current known limitations

- `name` is still `unknown` because reliable name extraction has not been implemented.
- LinkedIn public snippets remain incomplete and inconsistent.
- Tavily search behavior can vary between runs.
- `LinkedIn profiles only` filters by URL pattern only.
- `Location filter` currently has only the first country config: `Ukraine`.
- Future countries need their own country-domain, include-term, and negative-term mapping.
- Header/location detection uses Tavily public snippets/content only and is not equivalent to verified profile enrichment.
- `ua.linkedin.com/in/...` is not a guaranteed current physical location.
- `RuleBasedQueryPlanner v1` is still the active planner; AI planner is not implemented yet.
- Candidate ranking is still baseline-quality and should not be treated as final recruiting quality.
- No database, shortlist, authentication, AI agent, LinkedIn login, scraping, or direct LinkedIn automation is included.

## Reference documents

- `Roadmap.md`
- `Tasks.md`
- `docs/phase-1-poc-findings.md`
