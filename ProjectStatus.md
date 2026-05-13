# Project Status

## Current phase

Phase 1 POC completed successfully and was accepted as a proof of concept.

Phase 1.1 - POC behavior tuning is completed.

Recommended next phase: Phase 2 - sequential multi-query search with dedupe.

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

- Editable Boolean query is the source of truth for search.
- Tavily receives exactly the submitted query.
- Backend normalizes and scores results without hidden role/stack/location filtering.
- Visible user-selected filters are allowed.
- Hidden field-based filters are not allowed.
- `ua.linkedin.com/in/...` is treated as a useful Ukraine-domain signal, not a perfect current-location guarantee.

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

## Verification

- `python -m compileall app`
- `node --check app/static/app.js`
- Backend smoke-check for query-only request behavior.
- Backend smoke-check for neutral scoring.
- Backend smoke-check for LinkedIn profile URL detection and toggle request field.
- Backend smoke-check for Ukraine LinkedIn domain URL detection and counts.
- UI check: `Search results`, `LinkedIn profiles only`, and `Ukraine LinkedIn domain only` are visible; both toggles are off by default.

## Current known limitations

- `name` is still `unknown` because reliable name extraction has not been implemented.
- LinkedIn public snippets remain incomplete and inconsistent.
- Tavily search behavior can vary between runs.
- `LinkedIn profiles only` filters by URL pattern only.
- `Ukraine LinkedIn domain only` filters by URL domain only.
- `ua.linkedin.com/in/...` is not a guaranteed current physical location.
- No database, shortlist, authentication, AI agent, LinkedIn login, scraping, or direct LinkedIn automation is included.

## Reference documents

- `Roadmap.md`
- `Tasks.md`
- `docs/phase-1-poc-findings.md`
