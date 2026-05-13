# Phase 1 POC Findings

## Phase 1.1 update

Phase 1.1 keeps the Phase 1 POC result as historical evidence, but changes the current product behavior.

Current behavior after Phase 1.1:

- Editable Boolean query is the source of truth for search.
- Form fields only help build the editable query.
- Backend no longer applies hidden required-condition filtering by role, anchors, stack, or location fields.
- UI shows `Search results`, not `Relevant results`.
- Score is neutral and non-filtering.
- `LinkedIn profiles only` is an explicit toggle, off by default.
- `Ukraine LinkedIn domain only` is an explicit toggle, off by default.

The Phase 1 numbers below still describe the original POC run with strict required-condition filtering. They should not be read as the current UI behavior after Phase 1.1.

### Phase 1.1 test conclusion

For the same Java/Ukraine target profile, the strongest single query after Phase 1.1 was:

```text
site:linkedin.com/in AND "Java Software Engineer" AND "Ukraine"
```

With `LinkedIn profiles only` and `Ukraine LinkedIn domain only` enabled, it returned 16 Ukrainian LinkedIn profiles from 20 raw Tavily results.

Across 10 tested query variants, Phase 1.1 found 53 unique `ua.linkedin.com/in/...` profiles. This suggests that Phase 2 should focus on sequential multi-query search with dedupe rather than one broad universal query.

Recommended first multi-query set:

- `site:linkedin.com/in AND "Java Software Engineer" AND "Ukraine"`
- `site:linkedin.com/in AND "Java Programmer" AND "Ukraine"`
- `site:linkedin.com/in AND ("Java Developer" OR "Java Engineer" OR "Backend Java") AND ("Ukraine" OR "Kyiv" OR "Lviv")`

Expected result based on current tests: approximately 24-30 unique Ukrainian LinkedIn profiles in one pass after dedupe.

## Test scenario

Recruiter searches for public LinkedIn profiles of Java specialists in Ukraine.

## Search input

- Main anchor: `Java`
- Additional anchors: `Developer`, `Engineer`
- Stack: `Java`, `Spring`
- Location: `Ukraine`
- Original target: 20 relevant candidates

## Boolean query

```text
site:linkedin.com/in AND "Java" AND ("Developer" OR "Engineer") AND ("Java" OR "Spring") AND "Ukraine"
```

## Results summary

- Raw Tavily results: 20
- Normalized results: 20
- Relevant results after required filters: 10
- Filtered out: 10
- Phase 1 POC status: successful and accepted

## Relevant candidates

Examples of relevant results returned by the POC:

| Score | Name | Title | URL |
| --- | --- | --- | --- |
| 89 | unknown | Maksym Nakonechnyi - Java Software Engineer (Java 8-21) - LinkedIn | https://ua.linkedin.com/in/gembrilus/en |
| 89 | unknown | Ruslan Miroshnichenko - Team Lead/Senior Java Developer at ... | https://ua.linkedin.com/in/ruslanmiroshnichenko |
| 86 | unknown | Tetiana Koval - Java Software Engineer - LinkedIn | https://ua.linkedin.com/in/hehetenya |
| 86 | unknown | Artem Sobko - Middle Java Software Engineer \| LinkedIn | https://ua.linkedin.com/in/artem-sobko-60a368279 |
| 86 | unknown | Viktor K. - Java/Scala Developer - LinkedIn | https://www.linkedin.com/in/victorkosh |

## What worked

- FastAPI served the static UI and health endpoint locally.
- The editable Boolean query was generated from the agreed POC fields.
- Tavily returned LinkedIn-like public profile results.
- Normalization preserved raw fields and produced a consistent result shape.
- Required-condition filtering removed results that did not satisfy the POC constraints.
- Relevance scoring was transparent and explainable.

## What did not work

- The Phase 1 POC was accepted as successful with 10 relevant candidates from a single Tavily query.
- Changing stack matching from AND to OR improved recall from 7 relevant candidates to 10.
- `name` could not be reliably extracted from Tavily title/snippet/url, so it remained `unknown`.
- Some LinkedIn results had potentially relevant titles but did not include the literal location term in the title/snippet, so they were filtered out by the current strict location rule.
- Tavily returned some profiles from other LinkedIn country domains, which were correctly filtered when location did not match.

## Limitations

- The POC uses public web search/cache/snippets only.
- No LinkedIn login, direct automation, scraping, profile opening, or restriction bypass is used.
- Title/snippet data is incomplete and inconsistent.
- The strict AND filter improves precision but can reduce recall.
- The current name extraction rule is intentionally conservative.

## Risks

- LinkedIn snippets may be too sparse for stable location and stack detection.
- A strict literal location match may exclude relevant Ukraine candidates.
- Stack OR improves recall. The 20-candidate target remains a useful tuning target for the next iteration.
- Tavily search behavior can vary between runs.
- The POC may need query tuning or a later enrichment step to reach 20 relevant candidates reliably in future iterations.

## Recommendation

Treat Phase 1 as successfully completed and Phase 1.1 as a successful behavior correction. Continue from the current implementation, then move to sequential multi-query search with dedupe before expanding the product scope.

Recommended next adjustment: keep the no-scraping constraint and implement multi-query search using visible filters such as `LinkedIn profiles only` and `Ukraine LinkedIn domain only`.

## Next steps

- Use `ua.linkedin.com/in/...` as an explicit Ukraine-domain signal when the user enables the visible filter.
- Decide whether name extraction can use a conservative title pattern in a later task.
- Implement multiple query variations and deduplication because a single Tavily query is not the best strategy for candidate coverage.
- Keep AI agent, database, shortlist, and multi-source search out of scope until the search engine is proven.
