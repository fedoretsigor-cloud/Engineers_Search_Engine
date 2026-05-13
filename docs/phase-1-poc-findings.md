# Phase 1 POC Findings

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

Treat Phase 1 as successfully completed. Continue from the current implementation, then tune the location rule and query strategy before expanding the product scope.

Recommended next adjustment: keep the no-scraping constraint, but consider a less brittle location rule for LinkedIn country domains such as `ua.linkedin.com`.

## Next steps

- Review whether `ua.linkedin.com` should satisfy the Ukraine location condition.
- Decide whether name extraction can use a conservative title pattern in a later task.
- Consider multiple query variations and deduplication if a single Tavily query cannot reliably return 20 relevant candidates in the next iteration.
- Keep AI agent, database, shortlist, and multi-source search out of scope until the search engine is proven.
