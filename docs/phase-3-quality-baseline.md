# Phase 3 Quality Baseline

## Run

Date/time: 2026-05-15, 13:56:08-13:56:15 local Europe/Kiev time.

Task: `P3-010 Run Java/Ukraine quality baseline`.

This was a measurement task, not a feature task. No backend or frontend code changes were made as part of the baseline run.

## Input

```json
{
  "role_family": "Backend Developer",
  "technology": "Java",
  "stack": ["Spring", "Kafka"],
  "location": "Ukraine",
  "linkedin_profiles_only": true,
  "location_filter_enabled": true
}
```

The stack was the current UI default: `Spring`, `Kafka`.

## Search Counts

| Metric | Value |
| --- | ---: |
| Queries total | 10 |
| Queries succeeded | 10 |
| Queries failed | 0 |
| Raw Tavily results | 200 |
| Normalized results | 200 |
| Displayed occurrences | 102 |
| Unique candidates | 57 |
| Duplicates removed | 45 |
| Hidden by profile filter | 13 |
| Hidden by location filter | 85 |
| Hidden by foreign current location | 74 |
| Weak location history only | 0 |
| Unknown non-country-domain location | 11 |

## Query Contribution

| Query | Category | Raw | Displayed | New unique | Duplicates |
| --- | --- | ---: | ---: | ---: | ---: |
| Q01 | role_based | 20 | 10 | 10 | 0 |
| Q02 | role_based | 20 | 10 | 8 | 2 |
| Q03 | backend_role | 20 | 11 | 10 | 1 |
| Q04 | role_based | 20 | 14 | 8 | 6 |
| Q05 | role_based | 20 | 11 | 3 | 8 |
| Q06 | role_based | 20 | 13 | 4 | 9 |
| Q07 | stack_focused | 20 | 9 | 8 | 1 |
| Q08 | stack_focused | 20 | 9 | 5 | 4 |
| Q09 | stack_focused | 20 | 7 | 1 | 6 |
| Q10 | stack_focused | 20 | 8 | 0 | 8 |

## Quality Distributions

### Role Fit

| Value | Count |
| --- | ---: |
| `target_or_close_role` | 43 |
| `similar_role` | 11 |
| `missing_role` | 3 |

### Technology Fit

| Value | Count |
| --- | ---: |
| `exact` | 52 |
| `missing` | 5 |

### Stack Fit

| Value | Count |
| --- | ---: |
| `missing_selected_stack` | 39 |
| `selected_stack_found` | 13 |
| `stack_query_source_only` | 5 |

### Seniority Fit

| Value | Count |
| --- | ---: |
| `found` | 30 |
| `missing` | 26 |
| `ambiguous` | 1 |

### Review Flags

| Flag | Count |
| --- | ---: |
| `selected_stack_missing` | 44 |
| `seniority_missing` | 26 |
| `role_from_snippet_only` | 13 |
| `role_similar_only` | 11 |
| `seniority_from_snippet_only` | 10 |
| `stack_from_query_source_only` | 5 |
| `technology_missing` | 5 |
| `role_missing` | 3 |
| `seniority_ambiguous` | 1 |

### Quality Score

| Bucket | Count |
| --- | ---: |
| 0-39 | 2 |
| 40-59 | 4 |
| 60-79 | 27 |
| 80-100 | 24 |

Minimum score: 25.

Maximum score: 100.

Average score: 76.3.

## Manual Review Sample

The top quality-score candidates generally looked stronger than the raw first results:

- `Andriy Paliychuk` - `Senior Java Engineer - N-iX`, stack `Spring`, seniority `Senior`, score `100`, no review flags.
- `Vyacheslav Vasyanovich` - `Senior Java Developer | Architecting Scalable Cloud & Microservice Systems | AWS, Spring Boot, Kafka, Distributed Solutions - Lemon.io`, stack `Spring, Kafka`, seniority `Senior`, score `100`, no review flags.
- `Volodymyr Baiun` - `Senior Java/Kotlin Backend Engineer @ N-iX | Java, Spring Boot, AWS, Kafka`, stack `Spring, Kafka`, seniority `Senior`, score `97`, flag `role_from_snippet_only`.
- `Alexander Kuziv` - `Java Software Engineer | Java, Spring Boot, Kafka, RabbitMQ, etc | 17 years experience - LAWA LLC`, stack `Spring, Kafka`, seniority `Senior`, score `97`, flag `seniority_from_snippet_only`.
- `Andrii Didukh` - `Senior Software Engineer | Team Lead | Java | Spring`, stack `Spring`, seniority `Senior Lead`, score `97`, flag `role_from_snippet_only`.

The first returned candidates were still useful, but many lacked direct selected-stack evidence:

- `Serhii Ivanov` displayed as `Java Software Developer`, technology `Java`, stack `n/a`, seniority `n/a`, flags `role_similar_only`, `selected_stack_missing`, `seniority_missing`.
- `Dmitry Solovey` displayed as `Java Developer`, but seniority came from snippet-only evidence, so `seniority_from_snippet_only` was useful.
- `Taras Koval` had score `86`, seniority `Senior`, and only query-source stack evidence, so `stack_from_query_source_only` was useful.

## Findings

Phase 3 quality layer is useful. The new fields make candidate review more honest than the previous raw result cards:

- `name` and `headline` are readable for sampled candidates.
- `role_display`, `technology_display`, `stack_display`, and `seniority_display` are understandable in the UI.
- `quality_score` separates stronger candidates with direct stack/seniority evidence from weaker candidates.
- `review_flags` are useful and explain most uncertainty.

Important quality observations:

- Stack remains the weakest evidence area: `44` of `57` candidates have `selected_stack_missing`, and only `13` have direct selected-stack evidence.
- `stack_query_source_only` is correctly treated as weak evidence because an OR-query does not prove which stack term matched.
- Seniority detection is useful but should stay cautious: `10` candidates have `seniority_from_snippet_only`, and sampled cases show snippet-only seniority can come from lower-confidence history text.
- Technology fit is strong for this baseline: `52` exact Java candidates and `5` missing technology cases.
- Role fit is mostly strong: `43` target/close, `11` similar, `3` missing.

## Follow-Up Notes

- Keep `seniority_from_snippet_only` as a visible flag; do not promote snippet-only seniority to high confidence.
- Consider a future stack-quality tuning task because selected stack is often not visible in Tavily public snippets.
- Do not treat the exact unique count as deterministic; Tavily live results vary between runs.

## P3-010.1 Stack Evidence Review

Reviewed the exact `P3-010` snapshot: `logs/search-runs/2026-05-15T10-56-15Z_structured-search_backend-developer-java-ukraine.json`.

No Tavily rerun was made, no code was changed, and no LinkedIn profiles were opened.

### Missing Selected Stack Group

`missing_selected_stack` candidates are mostly useful Java candidates with missing public stack evidence, not mostly noise:

| Metric | Value |
| --- | ---: |
| Count | 39 |
| Quality score min | 25 |
| Quality score max | 80 |
| Quality score average | 69.3 |
| Target/close role | 28 |
| Similar role | 8 |
| Missing role | 3 |
| Exact Java technology | 34 |
| Missing technology | 5 |

Reviewed sample:

- `Kate Tyshko`, score 80: Senior Java Software Engineer in Ukraine; Spring/Kafka not visible.
- `Lyubomyr Shaydariv`, score 80: Senior Java developer and tech lead in Lviv; Spring/Kafka not visible.
- `Oleksandr Nazarenko`, score 80: Senior Software Java Engineer; Java/backend experience visible, selected stack not visible.
- `Polina Serhiienko`, score 80: Senior Java Backend Engineer in Kyiv; selected stack not visible.
- `Artem Sobolenko`, score 75: Java Software Engineer and Java Backend Developer; selected stack not visible.
- `Illia Sytnyk`, score 75: Java Developer in Kyiv; selected stack not visible.
- `Serhii Avakian`, score 75: Java Developer in Dnipro; selected stack not visible.
- `Tetiana Koval`, score 75: Java Software Engineer in Lviv; selected stack not visible.
- `Alexander Stepanov`, score 46: Full Stack Web Developer; Java and selected stack are not confirmed.
- `Danish Mukhammad`, score 46: Node.js Backend Engineer; weak Java match.
- `Roman Zherebetskyi`, score 25: no useful role, Java, or stack evidence.
- `Andriy Pavlyuk`, score 25: no useful role, Java, or stack evidence.

### Direct Stack Comparison

Direct selected-stack candidates are clearly stronger:

| Metric | Value |
| --- | ---: |
| Count | 13 |
| Quality score min | 86 |
| Quality score max | 100 |
| Quality score average | 96.2 |
| Exact Java technology | 13 |

Examples: `Andriy Paliychuk` with `Stack: Spring`, `Vyacheslav Vasyanovich` with `Stack: Spring, Kafka`, and `Alexander Kuziv` with `Stack: Spring, Kafka`.

### Recommendation

- Keep the backend semantics: do not display selected stack terms as confirmed facts unless they were directly found in candidate text.
- Keep `selected_stack_missing` as a meaningful ranking penalty, not a hard filter.
- `P3-010.2` improved frontend wording: plain `Stack: n/a` is now `Stack: Not visible` when selected stack was requested but not directly found, and query-source-only stack evidence displays as `Not confirmed`.
- Keep `stack_query_source_only` as weak evidence and keep its review flag visible.

### P3-010.2 Implementation

Implemented stack display semantics without changing backend search logic, filters, review flags, or the quality-score formula:

- direct evidence: `Spring`, `Kafka`, or `Spring, Kafka`;
- missing selected stack: `Not visible`;
- query-source-only stack signal: `Not confirmed`;
- future no-stack-requested state: `N/A`.
