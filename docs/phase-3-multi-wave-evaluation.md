# Phase 3 Multi-Wave Evaluation

## Run

Task: `P3-012 Evaluate adaptive multi-wave results`.

Date/time: 2026-05-15, 16:37:00-16:37:53 local time.

This was a measurement task. No code changes were made as part of the run.

Snapshot:

```text
logs/search-runs/2026-05-15T13-37-53Z_structured-search-multi-wave_backend-developer-java-ukraine.json
```

## Input

```json
{
  "role_family": "Backend Developer",
  "technology": "Java",
  "stack": ["Spring", "Kafka"],
  "location": "Ukraine",
  "linkedin_profiles_only": true,
  "location_filter_enabled": true,
  "max_waves": 5,
  "min_new_unique_per_wave": 3,
  "patience": 2
}
```

## Search Result

| Metric | Value |
| --- | ---: |
| Waves run | 4 |
| Planned max waves | 5 |
| Stop reason | `low_incremental_gain` |
| Queries executed | 40 |
| Queries succeeded | 40 |
| Queries failed | 0 |
| Raw Tavily results | 754 |
| Displayed occurrences | 457 |
| Final unique candidates | 67 |
| Duplicates removed | 390 |
| Duplicates across waves | 176 |
| Hidden by profile filter | 41 |
| Hidden by location filter | 256 |
| Hidden by foreign current location | 216 |

## Per-Wave Gain

| Wave | Raw | Displayed | Wave unique | New unique | Cumulative unique |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 176 | 109 | 60 | 60 | 60 |
| 2 | 179 | 109 | 60 | 6 | 66 |
| 3 | 199 | 119 | 62 | 1 | 67 |
| 4 | 200 | 120 | 61 | 0 | 67 |

The runner stopped after wave 4 because waves 3 and 4 were both below the threshold of 3 new unique candidates.

## Comparison

Historical `P3-010` single-wave baseline:

- 57 unique candidates
- 200 raw Tavily results
- quality score average 76.3

Wave 1 inside this run:

- 60 unique candidates
- 176 raw Tavily results

Final cumulative multi-wave result:

- 67 unique candidates
- 754 raw Tavily results
- quality score average 76.6

Incremental gain over same-run wave 1:

- +7 unique candidates
- +3 high-quality candidates with `quality_score >= 80`
- +1 direct-stack candidate
- +1 query-source-only stack candidate
- +5 missing-stack candidates
- +3 technology-missing candidates
- +3 low-score candidates under 60

## Cumulative Quality

| Metric | Value |
| --- | ---: |
| Quality score average | 76.6 |
| Quality score min | 38 |
| Quality score max | 100 |
| Candidates with score 80-100 | 28 |
| Candidates with score 60-79 | 32 |
| Candidates with score 40-59 | 6 |
| Candidates with score 0-39 | 1 |
| Target/close role | 51 |
| Similar role | 15 |
| Missing role | 1 |
| Exact Java technology | 61 |
| Missing technology | 6 |
| Direct selected stack | 13 |
| Stack query-source only | 7 |
| Missing selected stack | 47 |
| Seniority found | 35 |
| Seniority missing | 31 |
| Seniority ambiguous | 1 |

## Conclusion

Multi-wave execution works and the stop condition behaved correctly.

The gain was real but modest: compared with wave 1 in the same run, the final result added 7 unique candidates after 30 additional Tavily queries. The incremental candidates included some useful profiles, but also added noisy results.

Recommendation for `P3-013`:

- Do not make multi-wave the default.
- Keep it backend-only for now, or expose it later as an explicit advanced/deeper-search control with cost and latency warning.
- If exposed, the UI should show `waves_run`, `queries_executed`, `new_unique_profiles_per_wave`, and `stop_reason` so the recruiter understands the cost/gain tradeoff.
