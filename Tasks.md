# Tasks

## Phase 1 - POC prototype with Tavily

### Backlog


### In Progress

### Done

- [x] P1-001 Определить границы POC
- [x] P1-002 Выбрать минимальный стек
- [x] P1-003 Зафиксировать тестовый сценарий POC
- [x] P1-004 Создать каркас проекта
- [x] P1-005 Собрать X-ray Boolean-запрос из формы
- [x] P1-006 Подключить поиск через Tavily
- [x] P1-007 Показать raw результаты Tavily во фронте
- [x] P1-008 Нормализовать результаты поиска
- [x] P1-009 Добавить базовую оценку релевантности
- [x] P1-010 Описать выводы POC

---

## Phase 1.1 - POC behavior tuning

### Backlog

### In Progress

### Done

- [x] P1.1-001 Сделать editable Boolean query единственным источником поиска
- [x] P1.1-002 Убрать скрытую backend-фильтрацию по полям формы
- [x] P1.1-003 Заменить `Relevant results` на `Search results`
- [x] P1.1-004 Сделать scoring нейтральным и не фильтрующим
- [x] P1.1-005 Добавить явный toggle `LinkedIn profiles only`
- [x] P1.1-006 Зафиксировать результаты Phase 1.1 в документах
- [x] P1.1-007 Добавить видимый фильтр по украинскому LinkedIn-домену

---

## Phase 2 - Multi-query Search + Baseline Query Planner

### Backlog

### In Progress

### Done

- [x] P2-012 Replace blacklist negative_terms with current location classification
- [x] P2-013 Improve one-line LinkedIn snippet current-location extraction
- [x] P2-001 Зафиксировать QueryPlan и baseline planner v1
- [x] P2-002 Добавить входную модель поиска: Role Family, Technology, Stack, Location
- [x] P2-003 Реализовать Rule-based Query Planner v1 для Java Backend
- [x] P2-004 Добавить backend multi-query runner для QueryPlan
- [x] P2-005 Добавить нормализацию LinkedIn URL и dedupe
- [x] P2-006 Добавить query source metadata для кандидатов
- [x] P2-007 Обновить counts/report для multi-query pipeline
- [x] P2-008 Обновить frontend под planner-based search
- [x] P2-009 Прогнать Java/Ukraine baseline и сравнить результаты
- [x] P2-009.1 Add configurable header/location location filter
- [x] P2-010 Зафиксировать выводы Phase 2 и подготовить место под AI Planner
- [x] P2-011 Добавить локальное логирование structured-search результатов для анализа

### Current Phase 2 notes

- `P2-012` supersedes the initial `P2-009.1` blacklist-style `negative_terms` approach.
- Current Ukraine `Location filter` uses `target_location_terms`, conservative `current_location_line` extraction, and current-location classification.
- Current display statuses are `target_location`, `country_domain`, `rescued_header_location`, `excluded_foreign_current_location`, `weak_history_only`, and `unknown_non_country_domain`.
- Current report field for explicit foreign current-location hides is `hidden_by_foreign_current_location`.
- `hidden_by_negative_header_location` and `excluded_negative_header_location` are historical `P2-009.1` names only.
- Tavily live runs are variable. Recent `Backend Developer + Java + Spring/Kafka + Ukraine` checks showed roughly `55-60` unique profiles for one wave; 3/5/10-wave experiments showed limited incremental gain.

---

## Phase 3 - Candidate Quality Layer

### Approved

### Backlog

### In Progress

### Done

- [x] P3-001 Define Candidate Quality model
- [x] P3-002 Improve name/headline extraction
- [x] P3-003 Extract role query config and role_phrase metadata
- [x] P3-004 Add role fit signals
- [x] P3-005 Add technology and stack fit signals
- [x] P3-006 Add seniority detection
- [x] P3-008 Normalize review flags taxonomy
- [x] P3-007 Add explainable candidate quality score
- [x] P3-009 Update frontend candidate quality view
- [x] P3-010 Run Java/Ukraine quality baseline
- [x] P3-010.1 Review `missing_selected_stack` candidates from Java/Ukraine baseline
- [x] P3-010.2 Improve stack evidence display and scoring semantics
- [x] P3-011 Add experimental multi-wave API runner
- [x] P3-012 Evaluate adaptive multi-wave results
- [x] P3-013 Add visible Multi-wave frontend toggle
- [x] P3-014 Close Phase 3 and prepare Phase 4 handoff

### Current Phase 3 implementation order note

Recommended implementation order:

1. `P3-006 Add seniority detection`
2. `P3-008 Normalize review flags taxonomy`
3. `P3-007 Add explainable candidate quality score`

Rationale: `P3-007` should use normalized review flag taxonomy for penalties/breakdown instead of creating ad hoc scoring logic that later needs to be rewritten.

---

## Task: P3-001 Define Candidate Quality model

### Context

Phase 2 can find and dedupe LinkedIn candidates, apply the visible `Location filter`, and show query/source metadata. The next problem is candidate quality: the recruiter needs a readable table that explains what was actually found for each candidate.

The first Phase 3 task should define the Candidate Quality model before implementing extraction, scoring, or frontend changes.

### Goal

Define the candidate-facing quality fields and their display rules.

Important product rule: table cells should show extracted values, not abstract internal labels such as `strong`, `weak`, or `missing`, when a useful value can be extracted.

### Proposed candidate table fields

- `Name`
- `Headline`
- `LinkedIn URL`
- `Location`
- `Role`
- `Tech`
- `Stack`
- `Seniority`
- `Quality score`
- `Review flags`
- `Evidence`
- `Found by query/wave`

### Display rules

#### Location

- If city and country are found, display `City, Country`.
  - Example: `Kyiv, Ukraine`.
  - Example: `Lviv, Ukraine`.
- If only country is found, display only the country.
  - Example: `Ukraine`.
- Normalize noisy public header variants when possible.
  - Example: `Kyiv, Kyiv City, Ukraine` should display as `Kyiv, Ukraine`.
- If location is only inferred from country-domain and no current-location line is extracted, display the best available country-level signal and add a review flag such as `location_by_country_domain_only`.

#### Role

- If a target or close role is found, display the extracted role/title value.
  - Example: `Backend Developer`.
  - Example: `Java Developer`.
  - Example: `Java Software Engineer`.
- If there is no full target-role match but a similar role-like title can be extracted, display that value rather than a generic `unknown`.
  - Example: `Software Engineer`.
  - Example: `Application Developer`.
- Keep the internal fit classification separate from the visible table value if needed.

#### Tech

- If the selected technology is found, display it.
  - Example: `Java`.
- If the selected technology is not found but a related technology can be extracted, display the extracted related value and mark it for review.
  - Example: `Scala`.
  - Example: `Kotlin`.
- If no useful technology evidence is found, display `n/a`.

#### Stack

- If selected stack items are found, display the matched stack values.
  - Example: `Spring`.
  - Example: `Kafka`.
  - Example: `Spring, Kafka`.
- If selected stack items are not found but related stack evidence can be extracted, display the extracted values and mark them for review.
  - Example: `Hibernate`.
  - Example: `REST`.
  - Example: `Microservices`.
  - Example: `AWS`.
- If no useful stack evidence is found, display `n/a`.
- Do not display unclear labels like `missing Spring/Kafka` as the primary table value. Missing selected stack can be represented as a review flag or detail text.

#### Seniority

- If seniority is found, display the extracted seniority.
  - Example: `Junior`.
  - Example: `Middle`.
  - Example: `Senior`.
  - Example: `Lead`.
- If seniority is not found, display `n/a`.

### Internal metadata

The model may still keep internal machine-readable fields for ranking and diagnostics:

- `role_fit`
- `technology_fit`
- `stack_fit`
- `location_fit`
- `quality_score`
- `review_flags`
- `evidence`

These internal values should support sorting, filtering, explanations, and later AI/chat workflows, but the first visible table should prefer extracted human-readable values.

### Constraints

- Do not implement extraction code in this task unless separately approved.
- Do not change Tavily queries.
- Do not change `QueryPlanner v1`.
- Do not change location filter behavior.
- Do not add AI model calls.
- Do not add database storage.
- Use only existing public fields from structured-search results/snapshots when examples are needed.

### Acceptance criteria

- Candidate Quality model fields are documented.
- Location display rule is documented: `City, Country` when city exists, otherwise country.
- Role/Tech/Stack display rules prefer extracted values over abstract fit labels.
- Seniority display rule is documented: extracted seniority or `n/a`.
- Missing selected stack is not shown as the primary cell value; it becomes a review flag/detail.
- Internal fit/scoring metadata is separated from recruiter-facing display values.
- Follow-up implementation tasks can reference this contract.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

- Candidate Quality model accepted as the Phase 3 contract.
- First implementation slice limited to backend metadata: name/headline, role fit, technology fit, stack fit, evidence, and review flags.
- Frontend candidate-quality table remains a later task.

---

## Task: P3-002 Improve name/headline extraction

### Context

Current normalized candidates often keep `name = unknown` or mix the candidate name with the LinkedIn title/headline. For a recruiter-facing Candidate Quality table, `Name` and `Headline` must be readable and separated.

Examples from recent snapshots:

- `Serhii Ivanov - Java Software Developer - LinkedIn`
- `Andrii Malyna - Lead Java Software Engineer at Geniusee - LinkedIn`
- `Illia Sytnyk - Java Developer in B&B Solutions | LinkedIn`
- `Serhii Ivanov. Java Software Developer. Kyiv, Kyiv City, Ukraine. 968 followers 500+ connections.`

### Goal

Extract candidate-facing `name` and `headline` from existing Tavily/LinkedIn public fields without using AI calls or new Tavily searches.

Expected shape:

```json
{
  "name": "Serhii Ivanov",
  "headline": "Java Software Developer"
}
```

### Proposed extraction sources

1. Prefer Tavily/LinkedIn `title`.
2. Fall back to top public header/snippet text.
3. If neither source is confident:
   - `name = "unknown"`;
   - `headline = "n/a"`.

### Parsing patterns

Support common public LinkedIn/Tavily title/header formats:

- `Name - Headline - LinkedIn`
- `Name – Headline | LinkedIn`
- `Name | Headline | Location | connections`
- `Name. Headline. Location. followers/connections`

### Cleanup rules

- Remove trailing `LinkedIn`, `| LinkedIn`, and `- LinkedIn`.
- Decode/normalize common HTML entities such as `&amp;`.
- Trim separators and repeated whitespace.
- Do not let `LinkedIn` appear in either `name` or `headline`.
- Do not move company text out of `headline` if it is part of the public title.
  - Example: `Lead Java Software Engineer at Geniusee`.

### Examples

Input:

```text
Serhii Ivanov - Java Software Developer - LinkedIn
```

Output:

```json
{
  "name": "Serhii Ivanov",
  "headline": "Java Software Developer"
}
```

Input:

```text
Andrii Malyna - Lead Java Software Engineer at Geniusee - LinkedIn
```

Output:

```json
{
  "name": "Andrii Malyna",
  "headline": "Lead Java Software Engineer at Geniusee"
}
```

Input:

```text
Illia Sytnyk - Java Developer in B&B Solutions | LinkedIn
```

Output:

```json
{
  "name": "Illia Sytnyk",
  "headline": "Java Developer in B&B Solutions"
}
```

Input:

```text
Serhii Ivanov. Java Software Developer. Kyiv, Kyiv City, Ukraine. 968 followers 500+ connections.
```

Output:

```json
{
  "name": "Serhii Ivanov",
  "headline": "Java Software Developer"
}
```

### Constraints

- Do not use AI model calls.
- Do not run Tavily.
- Do not open LinkedIn profiles.
- Do not scrape LinkedIn.
- Do not change `QueryPlanner v1`.
- Do not change location filter behavior.
- Use the latest local structured-search snapshots for verification examples.

### Acceptance criteria

- `name` is extracted when title/snippet clearly contains a person name.
- `headline` is extracted separately from `name`.
- `LinkedIn` suffixes do not appear in `name` or `headline`.
- Hyphen, en dash, pipe, and one-line snippet patterns are handled.
- Ambiguous cases remain `unknown` / `n/a` instead of inventing data.
- Verification uses local snapshots without new Tavily credits.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

- `normalize_tavily_result(...)` now extracts `name` and `headline`.
- Supported patterns include dash, pipe, and one-line public snippet formats.
- `LinkedIn` suffix cleanup and basic HTML entity cleanup are applied.
- Ambiguous identity remains `name = "unknown"` and `headline = "n/a"`.

### Verification result

- Local smoke checks passed for the agreed examples:
  - `Serhii Ivanov - Java Software Developer - LinkedIn`;
  - `Andrii Malyna - Lead Java Software Engineer at Geniusee - LinkedIn`;
  - `Illia Sytnyk - Java Developer in B&B Solutions | LinkedIn`;
  - one-line snippet `Serhii Ivanov. Java Software Developer. Kyiv...`.

---

## Task: P3-003 Extract role query config and role_phrase metadata

### Context

`RuleBasedQueryPlannerV1` currently hardcodes Java Backend role phrases directly inside the planner body:

- `Java Developer`;
- `Java Software Engineer`;
- `Java Backend Engineer`;
- `Java Engineer`;
- `Java Programmer`;
- `Java Application Developer`;
- stack-focused repeats of several of those phrases.

These phrases are already the search-time role variants. Phase 3 role quality should not introduce a second independent role alias list. Instead, the role quality layer should be able to reuse the same role phrases that the `QueryPlan` used for search.

Current issue: `role_phrase` is only embedded inside the final Tavily query string, for example:

```json
{
  "id": "Q02",
  "category": "role_based",
  "query": "site:linkedin.com/in AND \"Java Software Engineer\" AND \"Ukraine\""
}
```

That makes later role matching parse a query string or invent its own list. Both are brittle.

### Goal

Move rule-based role query phrases out of hardcoded planner calls into a small config, and include explicit `role_phrase` metadata in each `QueryPlan` query slot.

The output should keep the same generated query strings for the current baseline, but add structured metadata:

```json
{
  "id": "Q02",
  "category": "role_based",
  "role_phrase": "Java Software Engineer",
  "query": "site:linkedin.com/in AND \"Java Software Engineer\" AND \"Ukraine\""
}
```

### Proposed config shape

Use one domain config keyed by the current supported planner inputs:

```text
Role Family -> Technology
```

This config should be prepared for both planner rules and later Candidate Quality rules. `P3-003` only fills the `planner` section. `P3-005` will later add or use the `quality` section for technology/stack matching.

```python
SEARCH_DOMAIN_CONFIG = {
    "Backend Developer": {
        "Java": {
            "planner": {
                "role_based": [
                    {
                        "role_phrase": "Java Developer",
                        "purpose": "Find broad Java Developer profiles for the selected location.",
                    },
                    {
                        "role_phrase": "Java Software Engineer",
                        "purpose": "Find Java Software Engineer profiles for the selected location.",
                    },
                ],
                "stack_focused": [
                    {
                        "role_phrase": "Java Developer",
                        "purpose": "Find Java Developer profiles that mention selected stack signals.",
                    },
                ],
            },
            "quality": {
                # Reserved for P3-005.
            },
        }
    }
}
```

The exact config name can follow existing project style, but it should not create a narrow `ROLE_QUERY_CONFIG` that later has to be replaced by a separate technology quality config. The important rule: planner role phrases and future quality rules should live under the same `Role Family -> Technology` domain.

### Proposed steps

1. Add a local domain config for `Backend Developer + Java`.
2. Add a `planner` section to that config.
3. Move the current 10 role phrase/purpose/category definitions into the `planner` section.
3. Update `build_query_slot(...)` to include `role_phrase` in the returned query slot.
4. Update `RuleBasedQueryPlannerV1.build(...)` to read `Role Family -> Technology -> planner` config entries instead of manually listing 10 `build_query_slot(...)` calls.
5. Preserve current query IDs, categories, purposes, query strings, stack usage, and max results.
6. Add/adjust smoke checks to confirm the generated `QueryPlan` is behaviorally unchanged except for the new `role_phrase` field.
7. Document that `role_phrase` is the future source for `P3-004` role matching.
8. Document that the same domain config is the future place for `P3-005` technology/stack quality rules.

### Constraints

- Do not change the actual Tavily query strings for the current baseline.
- Do not change query count.
- Do not change planner validation.
- Do not implement role fit scoring in this task.
- Do not add AI planner behavior.
- Do not run Tavily for verification.
- Do not change frontend unless needed to tolerate the additional `role_phrase` field.

### Acceptance criteria

- `RuleBasedQueryPlannerV1` no longer hardcodes the role phrase list in the method body.
- Planner role phrases are stored under a shared `Role Family -> Technology` domain config, not a narrow standalone role-only config.
- Generated `QueryPlan.queries[]` includes `role_phrase`.
- Current baseline still generates 10 query slots.
- Current query strings remain unchanged for `Backend Developer + Java + Ukraine`.
- `role_phrase` is available for later Candidate Quality role matching.
- The config shape is compatible with adding `quality.technology` and `quality.stack` rules in `P3-005`.
- Verification uses `/api/query-plan` or direct planner smoke checks without Tavily credits.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

- Added shared `SEARCH_DOMAIN_CONFIG` under `Role Family -> Technology`.
- Moved the current 10 Java Backend planner query definitions into the config.
- `RuleBasedQueryPlannerV1` now builds queries from config instead of listing role phrases in the method body.
- `QueryPlan.queries[]`, query result summaries, and candidate `query_sources` now carry `role_phrase`.
- Stack-focused query metadata carries `uses_stack` as a group signal.

### Verification result

- Direct planner smoke check confirmed current baseline still generates 10 queries.
- Current baseline query strings stayed unchanged.
- `Q01` exposes `role_phrase = "Java Developer"`.
- `Q07` exposes `uses_stack = ["Spring", "Kafka", "AWS"]`.

---

## Task: P3-004 Add role fit signals

### Context

After `P3-003`, every query slot should expose the search-time `role_phrase` that was used to find candidates. `P3-004` should use that metadata to detect and explain candidate role relevance without creating a second independent role alias list.

For example, if a candidate headline is:

```text
Lead Java Software Engineer at Geniusee
```

the recruiter-facing table should show:

```text
Role: Lead Java Software Engineer
```

It should not show only an abstract internal label such as `strong`, `weak`, or `missing`.

### Goal

Add role fit signals to normalized candidates so the product can show a readable role value and keep a separate internal fit classification for later ranking/scoring.

### Proposed inputs

Use existing local candidate fields only:

- candidate `title`;
- extracted `headline` from `P3-002`;
- public snippet/header text already returned by Tavily;
- `query_plan.queries[*].role_phrase` from `P3-003`;
- candidate `query_sources` metadata.

### Proposed output fields

Add role quality fields to each normalized/deduped candidate:

```json
{
  "role_display": "Lead Java Software Engineer",
  "role_fit": "target_or_close_role",
  "role_evidence": [
    {
      "source": "headline",
      "value": "Lead Java Software Engineer at Geniusee"
    }
  ],
  "review_flags": []
}
```

Exact field names can follow the existing project style, but the model should separate recruiter-facing display text from internal fit labels.

### Proposed steps

1. Use `role_phrase` values from the current `QueryPlan` as the search-time role context.
2. Read candidate role evidence from title, extracted headline, and public snippet/header text.
3. Extract the best visible role/title value from candidate text.
4. Set recruiter-facing `role_display` to the extracted role when available.
5. Set internal `role_fit` separately from the display value.
6. Use conservative fit classes such as:
   - `target_or_close_role`;
   - `similar_role`;
   - `missing_role`.
7. Add evidence metadata that explains where the role signal came from.
8. Add review flags for ambiguous cases, for example:
   - `role_from_snippet_only`;
   - `role_similar_only`;
   - `role_missing`.
9. Verify against local structured-search snapshots without new Tavily calls.

### Display rules

- If a target or close role is found, display the extracted role/title value.
  - Example: `Backend Developer`.
  - Example: `Java Developer`.
  - Example: `Java Software Engineer`.
  - Example: `Lead Java Software Engineer`.
- If no full target-role match exists but a similar role-like title can be extracted, display that value.
  - Example: `Software Engineer`.
  - Example: `Application Developer`.
- If no useful role evidence is found, display `n/a`.
- Do not show internal labels such as `strong`, `weak`, or `missing` as the primary table value.

### Constraints

- Do not create a second independent role alias list.
- Do not parse final Tavily query strings when structured `role_phrase` metadata is available.
- Do not change Tavily queries.
- Do not run Tavily for verification.
- Do not change location filtering.
- Do not implement technology, stack, seniority, quality score, or frontend table changes in this task.
- Do not add AI model calls.

### Acceptance criteria

- Candidates can carry a visible role display value.
- Internal `role_fit` is separate from recruiter-facing display text.
- Role matching uses `QueryPlan` role metadata from `P3-003`.
- Candidate headlines like `Lead Java Software Engineer at Geniusee` produce a useful visible role value.
- Ambiguous or similar roles get review flags instead of being silently treated as exact matches.
- Verification uses local snapshots or direct unit/smoke checks without Tavily credits.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

- Deduped structured-search candidates now carry:
  - `role_display`;
  - `role_fit`;
  - `role_evidence`;
  - merged `review_flags`.
- Role matching uses `QueryPlan` / `query_sources` `role_phrase` metadata plus the selected `role_family`, not a separate hardcoded role alias list.
- Similar role display can use role vocabulary derived from the same QueryPlan role phrases.
- Example: `Java Software Developer` displays as `Java Software Developer` with `role_fit = "similar_role"`.

### Verification result

- Local smoke checks confirmed:
  - exact/close roles produce `target_or_close_role`;
  - derived similar roles produce `similar_role` and `role_similar_only`;
  - missing role evidence produces `missing_role` and `role_missing`.

---

## Task: P3-005 Add technology and stack fit signals

### Context

After `P3-001` through `P3-004`, candidates should have a readable quality model, better name/headline extraction, explicit `role_phrase` metadata, and role fit signals.

The next missing quality layer is technology and stack fit. For the current baseline, the user selects:

```json
{
  "technology": "Java",
  "stack": ["Spring", "Kafka", "AWS"]
}
```

The product should show what technology/stack evidence was found for each candidate. This should be a quality signal, not a hidden filter.

### Goal

Add technology and stack fit signals to normalized/deduped candidates so the recruiter can see readable extracted values and later sort/filter by internal fit metadata.

### Config decision

Do not hardcode Java-specific related terms such as `Scala` or `Kotlin` inside matcher logic.

Do not create a totally separate, disconnected `TECHNOLOGY_QUALITY_CONFIG` if `P3-003` introduces a role/technology query config.

Preferred direction: use one domain config keyed by:

```text
Role Family -> Technology
```

The config should keep separate sections for planner rules and quality rules.

Example shape:

```python
SEARCH_DOMAIN_CONFIG = {
    "Backend Developer": {
        "Java": {
            "planner": {
                "role_based": [...],
                "stack_focused": [...],
            },
            "quality": {
                "technology": {
                    "exact_terms": ["Java"],
                    "exclude_terms": ["JavaScript"],
                    "related_terms": ["Kotlin", "Scala"],
                },
                "stack": {
                    "allowed_terms": [
                        "Spring",
                        "Spring Boot",
                        "Hibernate",
                        "Kafka",
                        "PostgreSQL",
                        "AWS",
                        "Docker",
                        "Kubernetes",
                        "Microservices",
                        "REST",
                    ],
                    "related_terms": [],
                },
            },
        }
    }
}
```

The exact config name and shape can follow the implementation from `P3-003`, but the rule is important: Java-specific knowledge belongs in config, not in the matcher algorithm.

Approved conservative Java config for `P3-005`:

- `technology.exact_terms`: `["Java"]`;
- `technology.exclude_terms`: `["JavaScript"]`;
- `technology.related_terms`: `["Kotlin", "Scala"]`;
- `stack.allowed_terms`: current Java stack list from the UI/config;
- `stack.related_terms`: `[]`.

Rationale:

- `Kotlin` and `Scala` are related JVM technology signals, but not exact Java matches.
- Stack related terms stay empty in the first implementation to avoid noisy quality evidence.
- Broader Java ecosystem terms such as `Maven`, `Gradle`, `JPA`, `JUnit`, `RabbitMQ`, `Redis`, etc. are deferred until real candidate-quality errors justify them.

### Proposed inputs

Use existing local candidate/search data:

- `query_plan.input_snapshot.technology`;
- `query_plan.input_snapshot.stack`;
- domain config for selected `Role Family -> Technology`;
- `query_plan.queries[*].uses_stack`;
- candidate `query_sources`;
- candidate `title`;
- extracted `headline` from `P3-002`;
- public `snippet` / `content` / `raw_content`;
- optional `role_phrase` metadata from `P3-003`.

### Proposed output fields

Add candidate-facing display fields:

```json
{
  "technology_display": "Java",
  "stack_display": "Spring, Kafka"
}
```

Add internal quality metadata:

```json
{
  "technology_fit": "exact",
  "technology_evidence": [
    {
      "term": "Java",
      "source": "headline",
      "value": "Senior Java Developer"
    }
  ],
  "stack_fit": "selected_stack_found",
  "stack_evidence": [
    {
      "term": "Spring",
      "source": "snippet"
    },
    {
      "terms": ["Spring", "Kafka", "AWS"],
      "source": "query_source",
      "query_id": "Q07",
      "category": "stack_focused",
      "evidence_type": "stack_query_group"
    }
  ],
  "review_flags": []
}
```

Exact field names can follow existing project style, but recruiter-facing display values must stay separate from internal fit labels.

### Proposed fit classes

Technology fit:

- `exact`;
- `related_only`;
- `missing`;
- `ambiguous`.

Stack fit:

- `selected_stack_found`;
- `stack_query_source_only`;
- `related_stack_only`;
- `missing_selected_stack`;
- `missing`.

### Proposed review flags

- `technology_missing`;
- `technology_related_only`;
- `technology_ambiguous`;
- `selected_stack_missing`;
- `stack_from_query_source_only`;
- `stack_related_only`;
- `possible_technology_false_positive`.

### Proposed steps

1. Reuse or extend the `Role Family -> Technology` config from `P3-003`.
2. Add quality config under that same domain config instead of creating a disconnected config.
3. Use the approved conservative config for `Backend Developer -> Java`:
   - technology exact terms: `["Java"]`;
   - technology exclude terms: `["JavaScript"]`;
   - technology related terms: `["Kotlin", "Scala"]`;
   - stack allowed terms: current Java stack list;
   - stack related terms: `[]` for the first conservative version.
4. Implement a generic technology matcher that reads config, not Java-specific `if` logic.
5. Implement generic exact/exclude precedence:
   - exact and exclude terms are matched as separate token/phrase matches;
   - if only exclude terms are found, do not count an exact match;
   - if an exact term is found separately, it wins even when exclude terms are also present;
   - example pattern: `JavaScript Developer` is not exact Java, but `Java / JavaScript Developer` still has exact Java.
6. Implement a generic stack matcher that reads config:
   - selected stack comes from request input;
   - allowed/related stack terms come from domain config;
   - selected stack matches are stronger than related-only matches;
   - direct candidate text matches produce concrete stack term evidence.
7. Search for direct evidence in ordered candidate sources:
   - extracted `headline`;
   - candidate `title`;
   - public `snippet/content/raw_content`.
8. Search for secondary stack evidence in query source metadata:
   - use candidate `query_sources`;
   - look up corresponding `query_plan.queries[*].uses_stack`;
   - preserve query id/category in `stack_evidence`;
   - store query-source stack evidence as group evidence, not as a confirmed concrete term;
   - evidence shape should include `terms`, `source = "query_source"`, `query_id`, `category`, and `evidence_type = "stack_query_group"`;
   - example: a query with `uses_stack = ["Spring", "Kafka", "AWS"]` proves the candidate came from a stack-focused query, but does not prove which OR term matched.
9. Set candidate-facing display values:
   - `technology_display`: extracted exact/related technology or `n/a`;
   - `stack_display`: direct matched selected/related stack terms or `n/a`;
   - in the first version, do not put query-source-only stack groups into `stack_display`.
10. Set internal fit values and evidence metadata separately from display values.
11. Merge review flags with existing candidate flags:
   - do not overwrite flags produced by earlier tasks such as role fit;
   - append/dedupe new technology/stack flags.
12. Add review flags for missing, related-only, ambiguous, or possible false-positive cases.
13. Verify against local structured-search snapshots without new Tavily calls.
14. Update `Tasks.md` with implementation result and verification result after coding.

### Display rules

- If selected technology is found exactly, display it.
  - Example: `Java`.
- If selected technology is not found but a related configured term is found, display the related term and flag it.
  - Example: `Kotlin`.
  - Example: `Scala`.
- Do not treat an exclude-only match as an exact technology match.
- If exact and exclude terms are both present as separate matches, exact wins.
- If selected stack items are found, display the found selected values.
  - Example: `Spring`.
  - Example: `Spring, Kafka`.
- If selected stack evidence comes only from stack-focused query sources, it can contribute to `stack_fit`, but it should not pretend that a specific OR term was directly observed.
- Query-source-only stack evidence should be represented as group evidence:
  - Example display value: keep `stack_display = "n/a"` in the first version.
  - Example fit: `stack_fit = "stack_query_source_only"`.
  - Example flag: `stack_from_query_source_only`.
- If selected stack is not found but related configured stack evidence is found in a future config version, display that related evidence and flag it.
- In the approved first version, `stack.related_terms = []`, so related-only stack evidence should normally not appear.
- If no useful technology or stack evidence is found, display `n/a`.
- Do not display internal labels such as `exact`, `related_only`, or `missing` as primary table cell values.

### Constraints

- Do not run Tavily for verification.
- Do not open LinkedIn profiles.
- Do not scrape LinkedIn.
- Do not add AI model calls.
- Do not change query generation.
- Do not change `Location filter`.
- Do not implement seniority detection in this task.
- Do not implement final quality score in this task.
- Do not implement frontend table changes unless separately approved.
- Do not create a second independent technology/stack config disconnected from the role/technology domain config.

### Acceptance criteria

- Technology and stack quality rules are config-driven.
- Related JVM signals such as `Kotlin`/`Scala` are not hardcoded inside matcher logic.
- Approved first version uses conservative Java quality config: exact `Java`, exclude `JavaScript`, related `Kotlin`/`Scala`, and empty stack related terms.
- The config is organized under the same `Role Family -> Technology` domain as planner configuration, or clearly prepared to merge with it after `P3-003`.
- Candidates can carry readable `technology_display` and `stack_display` values.
- Internal `technology_fit` and `stack_fit` are separate from recruiter-facing display values.
- `JavaScript` is not counted as exact `Java`.
- Exact/exclude precedence is generic and not hardcoded only for Java/JavaScript.
- Selected stack matches are distinguished from related-only stack evidence.
- Stack-focused query sources with `uses_stack` can contribute valid secondary stack group evidence.
- Query-source stack evidence stores `terms` as a group and does not claim a specific OR term was directly matched.
- `stack_display` is built from direct candidate text matches in the first version; query-source-only stack evidence stays in metadata/review flags.
- Missing selected stack creates a review flag rather than hiding the candidate.
- Technology/stack review flags are merged with existing candidate review flags instead of replacing them.
- Verification uses local snapshots or direct smoke checks without Tavily credits.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

- Added conservative Java quality config under the shared `SEARCH_DOMAIN_CONFIG`.
- Technology matcher is config-driven:
  - exact terms: `Java`;
  - exclude terms: `JavaScript`;
  - related terms: `Kotlin`, `Scala`.
- Stack matcher is config-driven from selected request stack and allowed Java stack terms.
- Direct stack matches populate `stack_display`.
- Stack-focused query-source matches populate group evidence with `source = "query_source"` and `evidence_type = "stack_query_group"`, but do not pretend that a specific OR term was directly observed.
- Technology/stack review flags are merged with existing role review flags.

### Verification result

- Local smoke checks confirmed:
  - `JavaScript Developer` is not counted as exact `Java`;
  - `Scala` is treated as `technology_fit = "related_only"`;
  - direct `Spring` text gives `stack_fit = "selected_stack_found"`;
  - query-source-only stack evidence gives `stack_fit = "stack_query_source_only"` and keeps `stack_display = "n/a"`.
- Full Tavily structured-search run for `Backend Developer + Java + Spring/Kafka/AWS + Ukraine`:
  - queries succeeded: `10/10`;
  - raw Tavily results: `199`;
  - displayed occurrences: `101`;
  - unique profiles: `55`;
  - duplicates removed: `46`;
  - hidden by profile filter: `10`;
  - hidden by location filter: `88`;
  - hidden by foreign current location: `82`.
- Quality breakdown on the Tavily run:
  - `role_fit`: `target_or_close_role = 41`, `similar_role = 10`, `missing_role = 4`;
  - `technology_fit`: `exact = 46`, `missing = 9`;
  - `stack_fit`: `selected_stack_found = 11`, `stack_query_source_only = 4`, `missing_selected_stack = 40`.

---

## Task: P3-006 Add seniority detection

### Context

After `P3-002` through `P3-005`, candidates can carry readable identity, role, technology, and stack quality fields. The next missing candidate-quality field is seniority.

Seniority should be extracted from public Tavily/LinkedIn fields already present in the candidate result. It should be a visible quality signal, not a hidden filter.

### Goal

Add seniority signals to normalized/deduped candidates so the product can show readable seniority values and keep separate internal evidence for later scoring.

### Proposed output fields

```json
{
  "seniority_display": "Senior",
  "seniority_fit": "found",
  "seniority_evidence": [
    {
      "term": "Senior",
      "level": "senior",
      "source": "headline",
      "value": "Senior Java Developer"
    }
  ],
  "review_flags": []
}
```

### Proposed config

Keep seniority terms config-driven instead of hardcoding them inside matcher logic.

Initial conservative config:

- `junior`: `Junior`, `Jr`, `Trainee`, `Intern`
- `middle`: `Middle`, `Mid`, `Mid-level`
- `senior`: `Senior`, `Sr`
- `leadership`: `Lead`, `Team Lead`, `Tech Lead`

`Principal`, `Staff`, `Architect`, and broader leadership/management labels are deferred until real results justify adding them.

### Important Lead rule

`Lead` should be treated as a leadership signal, not simply as a higher version of `Senior`.

- `Senior` means experience level.
- `Lead`, `Team Lead`, and `Tech Lead` mean leadership responsibility.
- If both are found, for example `Senior Team Lead`, the display value may combine them as `Senior Lead`, but evidence must preserve both matched signals.
- This keeps the first version simple while preparing for later quality scoring and filters.

### Proposed steps

1. Add seniority config near the existing Candidate Quality/domain config.
2. Add a generic seniority matcher that reads config terms.
3. Search for evidence in ordered candidate sources:
   - extracted `headline`;
   - candidate `title`;
   - public `snippet/content/raw_content`.
4. Match by token/phrase boundaries so accidental word fragments do not count.
5. Set recruiter-facing `seniority_display`:
   - matched value such as `Junior`, `Middle`, `Senior`, `Lead`, `Senior Lead`;
   - otherwise `n/a`.
6. Set internal `seniority_fit`:
   - `found`;
   - `missing`;
   - `ambiguous`.
7. Preserve all matched evidence, especially when both experience and leadership signals appear.
8. Add review flags without overwriting existing flags:
   - `seniority_missing`;
   - `seniority_ambiguous`;
   - `seniority_from_snippet_only`.
9. Do not use seniority as a filter.
10. Verify with local smoke checks before any Tavily baseline.
11. Update `Tasks.md` with implementation and verification notes after coding.

### Display rules

- `Senior Java Developer` -> `Senior`.
- `Middle Java Software Engineer` -> `Middle`.
- `Team Lead Java Developer` -> `Lead`.
- `Senior Team Lead Java Developer` -> `Senior Lead`, with both signals in evidence.
- If seniority is not found, display `n/a`.
- Do not display internal labels such as `found`, `missing`, or `ambiguous` as the primary table value.

### Constraints

- Do not run Tavily for initial verification.
- Do not open LinkedIn profiles.
- Do not scrape LinkedIn.
- Do not add AI model calls.
- Do not change query generation.
- Do not change location filtering.
- Do not implement final quality score in this task.
- Do not implement frontend table changes unless separately approved.

### Acceptance criteria

- Candidates can carry `seniority_display`, `seniority_fit`, and `seniority_evidence`.
- Seniority detection is config-driven.
- `Lead` is stored as a leadership signal, not merely as a higher seniority level.
- Combined values such as `Senior Lead` preserve both evidence signals.
- Missing seniority does not hide candidates.
- Seniority review flags are merged with existing candidate review flags.
- Verification uses local smoke checks without Tavily credits.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

- Added config-driven seniority detection.
- Added candidate fields:
  - `seniority_display`;
  - `seniority_fit`;
  - `seniority_evidence`.
- `Lead`, `Team Lead`, and `Tech Lead` are stored as `leadership` evidence, not as a higher `Senior` level.
- Combined signals such as `Senior Team Lead` display as `Senior Lead` while preserving both evidence items.
- Missing seniority adds `seniority_missing` but does not hide candidates.

### Verification result

- Local smoke checks passed:
  - `Senior Java Developer` -> `Senior`;
  - `Senior Team Lead Java Developer` -> `Senior Lead`;
  - plain `Java Developer` -> `n/a` with `seniority_missing`.

---

## Task: P3-007 Add explainable candidate quality score

### Context

After `P3-002` through `P3-006`, candidates can carry readable identity, role, technology, stack, seniority, evidence, and review flags.

The next step is an explainable candidate quality score. This score must not become a magic ranking layer. It should be a transparent deterministic summary of already extracted signals.

### Goal

Add a separate `quality_score` v1 to normalized/deduped candidates.

The score should help later sorting, review, and frontend display, but it must not hide candidates or replace existing technical `score`.

### Proposed output fields

```json
{
  "quality_score": 78,
  "quality_score_version": "candidate_quality_v1",
  "quality_score_breakdown": [
    {
      "component": "role",
      "points": 25,
      "reason": "Target or close role matched candidate headline."
    }
  ],
  "quality_score_penalties": [
    {
      "flag": "selected_stack_missing",
      "points": -8,
      "reason": "Selected stack was not directly found in candidate text."
    }
  ]
}
```

Exact field names can follow implementation style, but score, version, breakdown, and penalties must remain separate.

### Guardrails

1. `quality_score` must not replace existing neutral `score`.
2. `quality_score` must not filter candidates.
3. `quality_score` must not change sorting in this task unless separately approved.
4. Do not double-penalize the same issue. For example, `technology_fit = "missing"` and `technology_missing` flag describe the same problem and should not subtract twice.
5. `seniority_missing` must not reduce score while the user has no explicit seniority requirement.
6. Tavily score should not drive candidate quality. If used at all, it must have minimal weight because it is search confidence, not recruiter quality.
7. If `Location filter` is off, location score component should be `not_evaluated`, not treated as a bad location.
8. Score must be deterministic, bounded `0-100`, and explainable.
9. No AI, ML, embeddings, or hidden model calls in this task.

### Proposed scoring inputs

Use only existing candidate metadata:

- `location_signal_status`;
- `role_fit`;
- `technology_fit`;
- `stack_fit`;
- `seniority_fit`;
- `review_flags`;
- direct evidence fields already created by earlier Phase 3 tasks.

### Proposed scoring shape

Initial v1 should be simple and conservative:

- Location confidence: positive only when location was evaluated and passed with a strong signal.
- Role fit: strongest positive weight for `target_or_close_role`, weaker for `similar_role`, no positive for missing.
- Technology fit: strong positive for exact selected technology, weaker for related-only, penalty/low confidence for ambiguous or missing.
- Stack fit: strongest positive for direct selected stack match, weak positive for `stack_query_source_only`, no direct-display credit for query-source-only OR evidence.
- Seniority: bonus/evidence only when found; no penalty for missing.
- Review flags: apply explainable penalties by category, but avoid double counting the same underlying issue.

### Proposed penalty groups

Serious:

- `possible_technology_false_positive`;
- `technology_ambiguous`.

Medium:

- `technology_missing`;
- `role_missing`;
- `selected_stack_missing`.

Light:

- `role_similar_only`;
- `role_from_snippet_only`;
- `seniority_ambiguous`;
- `seniority_from_snippet_only`.

No penalty in v1:

- `seniority_missing`.

### Proposed steps

1. Add a score version constant, for example `candidate_quality_v1`.
2. Add a deterministic score builder that reads existing candidate quality fields.
3. Build score components from location, role, technology, stack, seniority, and review flags.
4. Add breakdown items for every positive component.
5. Add penalty items for review flags that affect score.
6. Prevent double penalties for the same underlying issue.
7. Clamp final `quality_score` to `0-100`.
8. Add fields to each deduped candidate result:
   - `quality_score`;
   - `quality_score_version`;
   - `quality_score_breakdown`;
   - `quality_score_penalties`.
9. Do not change result filtering.
10. Do not change frontend sorting or display unless separately approved.
11. Verify with local smoke checks before any Tavily baseline.
12. Update `Tasks.md` with implementation and verification notes after coding.

### Display rules

- Frontend can later show `quality_score`, but this task only prepares backend data.
- Breakdown should be readable enough for a recruiter/product reviewer to understand why score was assigned.
- Internal labels may exist in breakdown metadata, but visible reason text should be human-readable.

### Constraints

- Do not run Tavily for initial verification.
- Do not open LinkedIn profiles.
- Do not scrape LinkedIn.
- Do not add AI model calls.
- Do not change query generation.
- Do not change location filtering.
- Do not replace existing neutral `score`.
- Do not change default sorting.
- Do not implement frontend table changes unless separately approved.

### Acceptance criteria

- Candidates can carry `quality_score`, `quality_score_version`, `quality_score_breakdown`, and `quality_score_penalties`.
- Score is deterministic and bounded `0-100`.
- Score is separate from existing neutral `score`.
- Score does not filter candidates.
- Score does not change sorting in this task.
- `seniority_missing` does not reduce score.
- Location component is `not_evaluated` when location filter is off.
- Direct stack evidence scores stronger than query-source-only stack evidence.
- Query-source-only stack evidence does not pretend that a specific OR term was directly observed.
- Review flag penalties are explainable and do not double-count the same issue.
- Verification uses local smoke checks without Tavily credits.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation order note

Implement after `P3-008 Normalize review flags taxonomy`.

Rationale: `quality_score` penalties and breakdown should reuse normalized flag metadata instead of introducing ad hoc scoring rules that later need to be rewritten.

### Implementation result

- Added separate `quality_score` without replacing existing neutral `score`.
- Added:
  - `quality_score_version = "candidate_quality_v1"`;
  - `quality_score_breakdown`;
  - `quality_score_penalties`.
- Score is deterministic and bounded `0-100`.
- Score does not filter candidates and does not change backend sorting.
- Location is marked as `not_evaluated` when location filter is off.
- Seniority is an optional bonus signal; `seniority_missing` does not reduce score.
- Penalties are grouped to avoid double-counting the same issue.

### Verification result

- Local smoke checks passed for:
  - strong Java/Spring senior candidate;
  - `Senior Team Lead` combined evidence;
  - missing seniority without penalty;
  - JavaScript false-positive case with technology penalty.

---

## Task: P3-008 Normalize review flags taxonomy

### Context

Review flags already exist or are planned across Phase 3:

- role flags from `P3-004`;
- technology and stack flags from `P3-005`;
- seniority flags from `P3-006`;
- quality-score penalties from `P3-007`;
- location/data-quality flags may be useful later.

Without a shared taxonomy, flags can become noisy, duplicated, or hard to display. `P3-008` should normalize this layer before frontend candidate-quality display.

### Goal

Create a shared review flags taxonomy and normalized flag output for candidates.

Flags should mark uncertainty and review needs. They should not hide candidates and should not become another hidden filter.

### Why flags exist

Review flags let the product keep recall high while being honest about weak evidence.

Examples:

- `selected_stack_missing`: selected stack was not directly found in public candidate text.
- `stack_from_query_source_only`: candidate came from a stack-focused OR query, but no specific stack term was directly observed.
- `technology_ambiguous`: candidate may be a false positive, for example JavaScript vs Java.
- `role_similar_only`: role looks close, but it is not a direct target-role match.
- `seniority_from_snippet_only`: seniority was found only in lower-confidence snippet text.

### Proposed output fields

Keep the compact machine-readable list:

```json
{
  "review_flags": ["selected_stack_missing", "role_similar_only"]
}
```

Add display-ready details:

```json
{
  "review_flag_details": [
    {
      "code": "selected_stack_missing",
      "category": "stack",
      "severity": "medium",
      "label": "Stack not confirmed",
      "description": "Selected stack was not directly found in candidate public text.",
      "affects_quality_score": true
    }
  ]
}
```

### Proposed taxonomy fields

Each known flag should have:

- `code`;
- `category`: `role`, `technology`, `stack`, `seniority`, `location`, `data_quality`;
- `severity`: `info`, `low`, `medium`, `high`;
- `label`;
- `description`;
- `affects_quality_score`;
- optional `score_penalty_group`.

### Proposed first taxonomy

Role:

- `role_missing`: medium
- `role_similar_only`: low
- `role_from_snippet_only`: low

Technology:

- `technology_missing`: medium
- `technology_related_only`: low
- `technology_ambiguous`: high
- `possible_technology_false_positive`: high

Stack:

- `selected_stack_missing`: medium
- `stack_from_query_source_only`: low
- `stack_related_only`: low

Seniority:

- `seniority_missing`: info
- `seniority_ambiguous`: low
- `seniority_from_snippet_only`: low

Location/data quality can be added later when we decide which existing location signals should become review flags.

### Proposed steps

1. Add a shared review flag taxonomy config.
2. Add a normalizer that:
   - dedupes flags;
   - keeps stable order;
   - preserves unknown flag codes and maps them to `category = "unknown"` and `severity = "info"` details;
   - does not overwrite flags from different quality layers.
3. Add `review_flag_details` to candidate result output.
4. Ensure `review_flags` remains a simple list of codes for machine use.
5. Align `P3-007` quality-score penalties with taxonomy metadata instead of scattered ad hoc severity logic where possible.
6. Do not change filtering.
7. Do not change Tavily queries.
8. Verify with local smoke checks.
9. Update `Tasks.md` with implementation and verification notes after coding.

### Constraints

- Do not run Tavily for initial verification.
- Do not open LinkedIn profiles.
- Do not scrape LinkedIn.
- Do not add AI model calls.
- Do not change query generation.
- Do not change location filtering.
- Do not make flags hide candidates.
- Do not implement frontend table changes unless separately approved.

### Acceptance criteria

- A shared review flag taxonomy exists.
- Existing Phase 3 flags map to category, severity, label, and description.
- Candidate results can include `review_flag_details`.
- `review_flags` remains a compact list of codes.
- Flags are deduped and ordered stably.
- Unknown flags do not crash the API and are preserved with `unknown/info` details.
- Flags do not filter candidates.
- Verification uses local smoke checks without Tavily credits.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

- Added shared review flag taxonomy.
- Existing role, technology, stack, and seniority flags now map to:
  - `category`;
  - `severity`;
  - `label`;
  - `description`;
  - `affects_quality_score`;
  - optional `score_penalty_group`.
- Candidate results keep compact `review_flags` and add display-ready `review_flag_details`.
- Flags are deduped and ordered by taxonomy; unknown flags are preserved at the end with `category = "unknown"` and `severity = "info"`.
- Flags remain metadata and do not filter candidates.

### Verification result

- Local smoke checks confirmed:
  - known flags receive taxonomy details;
  - unknown flags are preserved safely;
  - quality score penalties can reuse taxonomy `score_penalty_group`.

### Implementation order note

Implement before `P3-007 Add explainable candidate quality score`.

Rationale: `P3-007` should use normalized review flag taxonomy for score penalties and breakdown.

---

## Task: P3-009 Update frontend candidate quality view

### Context

After `P3-006`, `P3-008`, and `P3-007`, backend structured-search results should include stable candidate-quality fields: identity, role, technology, stack, seniority, review flags/details, and quality score.

The current frontend is still mostly a diagnostic POC view. `P3-009` should turn the candidate results area into a more recruiter-facing quality view while keeping diagnostics available.

### Goal

Update the frontend to show candidate-quality data clearly.

This is a UI-only task. It must not change backend search logic, query generation, filters, scoring rules, Tavily calls, dedupe, or location filtering.

### Proposed candidate view

Show each candidate with:

- Name;
- Headline;
- LinkedIn URL;
- Location signal / current location when available;
- Role;
- Technology;
- Stack;
- Seniority;
- Quality score;
- Review flags;
- Found by query/source metadata.

Preferred first layout: hybrid candidate rows/cards, not a wide dense table.

Rationale: name, headline, evidence, flags, and query source metadata can become too cramped in a pure table. A hybrid layout can show the main candidate identity and score first, then role/technology/stack/seniority/location as compact fields, with flags and query details available in a collapsed or secondary area.

### Diagnostics

Keep diagnostics available but visually separate from the recruiter-facing candidate list:

- generated queries;
- report counts;
- hidden by filters;
- query contribution;
- location filter report.

### Proposed steps

1. Wait until `P3-006`, `P3-008`, and `P3-007` are implemented.
2. Inventory the final backend fields returned by `/api/structured-search`.
3. Design a compact hybrid candidate row/card layout.
4. Display quality fields without changing backend contracts.
5. Display review flags as readable badges or compact details.
6. Display query/source metadata in a compact way.
7. Keep diagnostics/report available separately.
8. Do not add shortlist/database behavior.
9. Do not add AI/chat behavior.
10. Verify in browser against local structured-search output.
11. Update `Tasks.md` with implementation and verification notes after coding.

### Constraints

- UI-only task.
- Do not change backend search logic.
- Do not change Tavily queries.
- Do not change filters or location logic.
- Do not change scoring formulas.
- Do not add database, shortlist, authentication, AI chat, or agent behavior.
- Do not make quality score hide candidates.

### Acceptance criteria

- Frontend shows candidate-quality fields from backend.
- Candidate view is readable for recruiter review.
- Review flags/details are visible without overwhelming the candidate list.
- Generated queries and diagnostic report remain available.
- Backend search logic is unchanged.
- No candidate is hidden by frontend quality score.
- Browser verification is completed.

### Before implementation

Codex must restate the task scope, propose exact UI changes, and wait for explicit approval before changing code.

### Approval status

Approved and completed after `P3-006`, `P3-008`, and `P3-007`.

### Implementation order note

Implement after `P3-006`, `P3-008`, and `P3-007`.

Rationale: frontend should render stable backend quality fields instead of guessing final field names or layout too early.

### Implementation result

- Updated frontend header to Phase 3 quality.
- Reworked result rendering into hybrid candidate rows/cards.
- Candidate card now shows:
  - name;
  - headline;
  - LinkedIn URL;
  - quality score;
  - location;
  - role;
  - technology;
  - stack;
  - seniority;
  - source;
  - review flag badges;
  - query source badges.
- Added expandable quality details with score breakdown, penalties, snippet, and query source metadata.
- Backend search logic, query generation, filters, scoring formulas, Tavily calls, dedupe, and location filtering were not changed by the UI task.

### Verification result

- `node --check app/static/app.js` passed.
- Browser verification completed on local app with a real UI structured-search run using default `Spring/Kafka` stack:
  - queries succeeded: `10/10`;
  - raw Tavily results: `199`;
  - displayed occurrences: `101`;
  - unique candidates: `57`;
  - duplicates removed: `44`;
  - no browser console errors.
- Desktop and mobile viewport checks confirmed the hybrid candidate card renders without visible overlap.

---

## Task: P3-010 Run Java/Ukraine quality baseline

### Context

`P3-006`, `P3-008`, `P3-007`, and `P3-009` added the first Phase 3 Candidate Quality Layer:

- seniority detection;
- normalized review flag details;
- explainable deterministic `quality_score`;
- hybrid frontend candidate quality view.

The next step is to measure whether this layer is useful on the real Java/Ukraine sourcing scenario.

### Goal

Run a real Java/Ukraine quality baseline and document the results.

This is a test/measurement/acceptance task, not a feature task.

### Baseline input

Use the current Java/Ukraine scenario:

- Role family: `Backend Developer`
- Technology: `Java`
- Stack: current agreed test stack, for example `Spring`, `Kafka`, `AWS` or current UI default `Spring`, `Kafka`
- Location: `Ukraine`
- `LinkedIn profiles only`: on
- `Location filter`: on

Record the exact stack used in the result notes.

### What to measure

Search counts:

- queries succeeded/failed;
- raw Tavily results;
- displayed occurrences;
- unique candidates;
- duplicates removed;
- hidden by profile filter;
- hidden by location filter;
- hidden by foreign current location.

Quality distributions:

- `role_fit`;
- `technology_fit`;
- `stack_fit`;
- `seniority_fit`;
- review flag distribution;
- `quality_score` distribution.

Manual review sample:

- inspect top 10-20 candidates;
- check whether names/headlines are readable;
- check whether role/technology/stack/seniority display values are honest;
- check whether review flags are useful or noisy;
- check whether `quality_score` feels explainable.

### Expected output

Update docs with baseline findings:

- `Tasks.md` implementation/result notes;
- `ProjectStatus.md` summary;
- optional dedicated doc such as `docs/phase-3-quality-baseline.md` if the findings are long enough.

### Constraints

- Tavily run is allowed and expected.
- Do not change backend code inside this task.
- Do not change frontend code inside this task.
- Do not change query generation.
- Do not change filters or location logic.
- Do not open LinkedIn profiles.
- Do not scrape LinkedIn.
- Do not add AI model calls.
- If baseline reveals a bug or quality issue, create a separate follow-up task instead of silently fixing it inside `P3-010`.
- Tavily live numbers are not deterministic; record exact date/time and input.

### Acceptance criteria

- Real Java/Ukraine baseline run completed.
- Search count metrics are recorded.
- Candidate quality distributions are recorded.
- Top candidate sample is reviewed manually.
- Findings are documented.
- Any discovered follow-up issues are captured as separate tasks or notes.

### Before implementation

Codex must restate the measurement scope, exact input, and expected documentation updates before running the baseline.

### Approval status

Approved as a test/measurement task.

### Run result

Completed on 2026-05-15, 13:56:08-13:56:15 local Europe/Kiev time.

Exact input:

- Role family: `Backend Developer`
- Technology: `Java`
- Stack: `Spring`, `Kafka`
- Location: `Ukraine`
- `LinkedIn profiles only`: on
- `Location filter`: on

Search counts:

- Queries succeeded: 10/10
- Raw Tavily results: 200
- Normalized results: 200
- Displayed occurrences: 102
- Unique candidates: 57
- Duplicates removed: 45
- Hidden by profile filter: 13
- Hidden by location filter: 85
- Hidden by foreign current location: 74

Quality summary:

- Role fit: 43 `target_or_close_role`, 11 `similar_role`, 3 `missing_role`
- Technology fit: 52 `exact`, 5 `missing`
- Stack fit: 13 `selected_stack_found`, 5 `stack_query_source_only`, 39 `missing_selected_stack`
- Seniority fit: 30 `found`, 26 `missing`, 1 `ambiguous`
- Quality score buckets: 2 candidates in `0-39`, 4 in `40-59`, 27 in `60-79`, 24 in `80-100`
- Quality score average: 76.3

Manual review conclusion:

- Phase 3 quality layer is useful: top quality-score candidates generally have stronger role, technology, stack, and seniority evidence.
- Review flags are useful and explain uncertainty, especially `selected_stack_missing`, `seniority_from_snippet_only`, `role_from_snippet_only`, and `stack_from_query_source_only`.
- Stack remains the weakest evidence area because Tavily public LinkedIn snippets often do not expose selected stack terms.
- No code changes were made inside `P3-010`.

Dedicated notes: `docs/phase-3-quality-baseline.md`.

---

## Task: P3-010.1 Review `missing_selected_stack` candidates from Java/Ukraine baseline

### Context

`P3-010` showed that stack evidence is the weakest part of the current Candidate Quality Layer.

For the baseline input `Backend Developer + Java + Spring/Kafka + Ukraine`:

- 57 unique candidates were found;
- 13 candidates had direct selected-stack evidence;
- 5 candidates had only weak query-source stack evidence;
- 39 candidates had `missing_selected_stack`.

For those 39 candidates, the frontend currently shows `Stack: n/a` and the review flag `selected_stack_missing`.

### Goal

Review the `missing_selected_stack` group before changing code, and decide what product behavior we actually want.

This is a review/analysis task, not a coding task.

### Questions to answer

1. Are these candidates mostly still useful Java candidates, or mostly weak/noisy results?
2. Is `Stack: n/a` clear enough for the recruiter, or does it look like a data bug?
3. Should `selected_stack_missing` lower ranking strongly, mildly, or only flag for review?
4. Should the UI show `Stack not visible in snippet` instead of plain `n/a` for this case?
5. Should stack be treated differently when it is selected by the user but not visible in public Tavily evidence?

### Proposed steps

1. Use the exact `P3-010` snapshot: `logs/search-runs/2026-05-15T10-56-15Z_structured-search_backend-developer-java-ukraine.json`.
2. Do not rerun Tavily for this task unless the snapshot is missing or unreadable.
3. Extract a balanced sample of at least 10 candidates with `stack_fit = missing_selected_stack`:
   - top quality-score candidates;
   - middle quality-score candidates;
   - low quality-score candidates;
   - candidates from different query sources.
4. For each sampled candidate, record:
   - name;
   - headline;
   - URL;
   - quality score;
   - role display;
   - technology display;
   - current stack display;
   - review flags;
   - query sources.
   - short public evidence text from Tavily title/snippet/content.
5. Compare the sampled candidates against top candidates with direct stack evidence.
6. Document whether the current `Stack: n/a` behavior is acceptable or should be changed.
7. Document the recommended scoring direction for `selected_stack_missing`.
8. Record the result in `Tasks.md`.
9. If the conclusion affects future product behavior, also update `docs/phase-3-quality-baseline.md`.

### Constraints

- Do not change backend code in this task.
- Do not change frontend code in this task.
- Do not open LinkedIn profiles.
- Do not scrape LinkedIn.
- Do not add AI model calls.
- Use only Tavily/public fields already returned by our search pipeline.

### Acceptance criteria

- At least 10 `missing_selected_stack` candidates are reviewed.
- The sample includes top, middle, low, and different query-source examples.
- The task answers whether these candidates are useful or mostly noisy.
- The task gives a clear recommendation for UI wording.
- The task gives a clear recommendation for quality-score penalty strength.
- The conclusion is recorded in `Tasks.md`.
- Any implementation changes are deferred to `P3-010.2`.

### Before implementation

Codex must restate the review scope, exact data source, and no-code constraint before running this analysis.

### Run result

Completed using exact snapshot `logs/search-runs/2026-05-15T10-56-15Z_structured-search_backend-developer-java-ukraine.json`.

No Tavily rerun was made. No backend or frontend code was changed. No LinkedIn profiles were opened.

#### Group summary

`missing_selected_stack` candidates are not mostly noise. They are mostly useful Java candidates with missing public stack evidence:

- Count: 39 of 57 unique candidates.
- Quality score: min 25, max 80, average 69.3.
- Role fit: 28 `target_or_close_role`, 8 `similar_role`, 3 `missing_role`.
- Technology fit: 34 `exact`, 5 `missing`.
- Seniority fit: 18 `found`, 20 `missing`, 1 `ambiguous`.
- Location status: 37 `target_location`, 2 `country_domain`.

Direct selected-stack candidates are clearly stronger:

- Count: 13 of 57 unique candidates.
- Quality score: min 86, max 100, average 96.2.
- Role fit: 12 `target_or_close_role`, 1 `similar_role`.
- Technology fit: 13 `exact`.
- Seniority fit: 9 `found`, 4 `missing`.

Query-source-only stack candidates sit in the middle:

- Count: 5 of 57 unique candidates.
- Quality score: min 69, max 86, average 79.2.
- All 5 had exact Java technology evidence, but stack was not directly confirmed.

#### Reviewed `missing_selected_stack` sample

| Candidate | Score | Headline | Role / Tech / Stack | Flags | Queries | Public evidence summary |
| --- | ---: | --- | --- | --- | --- | --- |
| [Kate Tyshko](https://ua.linkedin.com/in/kateryna-tyshko) | 80 | Senior Java Software Engineer | Senior Java Software Engineer / Java / n/a | `selected_stack_missing` | Q03 | Title/header confirms Senior Java Software Engineer in Ukraine, but does not show Spring or Kafka. |
| [Lyubomyr Shaydariv](https://ua.linkedin.com/in/lyubomyr-shaydariv) | 80 | Senior Java developer and tech lead | Senior Java developer / Java / n/a | `selected_stack_missing` | Q01, Q04, Q05 | Header confirms Senior Java developer and tech lead in Lviv, but selected stack is not visible. |
| [Oleksandr Nazarenko](https://ua.linkedin.com/in/oleksandr-nazarenko-7b9a573a) | 80 | Senior Software Java Engineer | Senior Software Java Engineer / Java / n/a | `selected_stack_missing` | Q04 | Snippet says Java developer with 15 years of backend experience, but no selected stack terms. |
| [Polina Serhiienko](https://ua.linkedin.com/in/polina-serhiienko-a050851b3) | 80 | Senior Java Backend Engineer - Levi9 Ukraine | Senior Java Backend Engineer / Java / n/a | `selected_stack_missing` | Q03, Q04 | Header confirms Java Backend Engineer in Kyiv, but Spring/Kafka are not visible. |
| [Artem Sobolenko](https://ua.linkedin.com/in/art-sobolenko) | 75 | Java Software Engineer \| Java Backend Developer \| Web Developer - DRAWER AI | Java Software Engineer / Java / n/a | `selected_stack_missing`, `seniority_missing` | Q02, Q03, Q06 | Header confirms Java Software Engineer and Java Backend Developer, but selected stack is not visible. |
| [Illia Sytnyk](https://ua.linkedin.com/in/illia-sytnyk-127b2b214) | 75 | Java Developer in B&B Solutions | Java Developer / Java / n/a | `selected_stack_missing`, `seniority_missing` | Q01 | Header confirms Java Developer in Kyiv; snippet says experienced Java developer, but no Spring/Kafka. |
| [Serhii Avakian](https://ua.linkedin.com/in/serhii-avakian-306980168/en) | 75 | Java Developer | Java Developer / Java / n/a | `selected_stack_missing`, `seniority_missing` | Q05 | Header confirms Java Developer in Dnipro, but selected stack is not visible. |
| [Tetiana Koval](https://ua.linkedin.com/in/hehetenya) | 75 | Java Software Engineer | Java Software Engineer / Java / n/a | `selected_stack_missing`, `seniority_missing` | Q04, Q05 | Header confirms Java Software Engineer in Lviv; snippet mentions Java Developer experience, but no selected stack. |
| [Alexander Stepanov](https://ua.linkedin.com/in/avstepanov) | 46 | Full Stack Web Developer. - DrugCards | Developer / n/a / n/a | `role_similar_only`, `technology_missing`, `selected_stack_missing`, `seniority_missing` | Q03 | Header points to Full Stack Web Developer; Java and selected stack are not confirmed. This is weak/noisy. |
| [Danish Mukhammad](https://ua.linkedin.com/in/danishm21) | 46 | Middle+ / Senior Backend Engineer \| Node.js \| Fintech - Superlogic | Senior Backend Engineer / n/a / n/a | `role_similar_only`, `technology_missing`, `selected_stack_missing`, `seniority_ambiguous` | Q03 | Header points to Node.js Backend Engineer in Odesa. This is not a good Java match. |
| [Roman Zherebetskyi](https://ua.linkedin.com/in/roman-zherebetskyi-80b774b9) | 25 | n/a | n/a / n/a / n/a | `role_missing`, `technology_missing`, `selected_stack_missing`, `seniority_missing` | Q03 | Header has person/company/location but no useful role, Java, or stack evidence. This is noise. |
| [Andriy Pavlyuk](https://ua.linkedin.com/in/andriy-pavlyuk-56890080) | 25 | n/a | n/a / n/a / n/a | `role_missing`, `technology_missing`, `selected_stack_missing`, `seniority_missing` | Q06 | Header has person/company/location but no useful role, Java, or stack evidence. This is noise. |

#### Comparison with direct stack evidence

Top direct-stack candidates look significantly stronger because the public evidence explicitly includes Spring/Kafka or related selected stack terms:

- [Andriy Paliychuk](https://ua.linkedin.com/in/andriy-paliychuk), score 100, `Stack: Spring`.
- [Vyacheslav Vasyanovich](https://ua.linkedin.com/in/viacheslav-vasianovych), score 100, `Stack: Spring, Kafka`.
- [Alexander Kuziv](https://ua.linkedin.com/in/alexander-kuziv), score 97, `Stack: Spring, Kafka`.
- [Andrii Didukh](https://ua.linkedin.com/in/andrii-didukh-b83029218), score 97, `Stack: Spring`.
- [Andrii Mykytyn](https://ua.linkedin.com/in/andriimykytyn), score 97, `Stack: Spring`.

#### Conclusion

- `missing_selected_stack` mostly means "selected stack is not visible in the public Tavily snippet", not "candidate does not know Spring/Kafka".
- The current backend behavior is honest because it does not display selected stack terms as facts unless direct evidence exists.
- The current frontend wording `Stack: n/a` is too blunt and can look like missing product data.
- Recommended UI wording for `P3-010.2`: show `Stack: Not visible` when selected stack was requested but not found in candidate public text.
- Recommended scoring direction: keep `selected_stack_missing` as a meaningful ranking penalty, but not a hard filter. The current score behavior is acceptable for now because strong Java candidates can still score 75-80, while direct stack candidates rise to 86-100.
- Keep `stack_query_source_only` as weak evidence and keep the visible review flag; query source should not be treated as direct stack proof.

---

## Task: P3-010.2 Improve stack evidence display and scoring semantics

### Context

`P3-010` and `P3-010.1` focus attention on a specific product issue: selected stack terms such as `Spring` and `Kafka` are important to the recruiter, but Tavily public LinkedIn snippets often do not expose stack evidence.

The current behavior is honest but may be too blunt:

- direct stack evidence shows as `Stack: Spring`, `Stack: Kafka`, or `Stack: Spring, Kafka`;
- query-source-only stack evidence is weak and flagged;
- missing selected stack shows as `Stack: n/a` with `selected_stack_missing`.

The product needs clearer semantics so the recruiter understands the difference between "not found in public snippet" and "candidate does not know this stack".

### Goal

Improve stack evidence semantics in the Candidate Quality Layer without pretending that query terms are confirmed candidate skills.

### Proposed behavior

Keep these principles:

1. Do not display selected stack terms as facts unless they were directly found in candidate text.
2. Keep `stack_query_source_only` as weak evidence, not as confirmed stack.
3. Keep `selected_stack_missing` visible as a review flag.
4. Replace recruiter-facing `Stack: n/a` with clearer wording when selected stack was requested but not visible.
5. Keep the current quality-score penalty unchanged in this task; `P3-010.1` showed the current penalty separates direct-stack candidates from missing-stack candidates without hiding useful Java candidates.

Final stack display states:

- Direct evidence: show actual matched stack terms, for example `Spring`, `Kafka`, or `Spring, Kafka`.
- Missing selected stack: show `Not visible`.
- Query-source-only stack signal: show `Not confirmed`.
- No stack requested, if this exists in a future flow: show `N/A`.

### Proposed steps

1. Review `P3-010.1` conclusions before changing code.
2. Define final stack display states:
   - direct selected stack found -> matched terms, for example `Spring`, `Kafka`, or `Spring, Kafka`;
   - related stack found -> matched related terms, if already supported by backend evidence;
   - query-source-only stack signal -> `Not confirmed`;
   - selected stack not visible in public snippet -> `Not visible`;
   - no stack requested -> `N/A`.
3. Update backend quality metadata only if needed to support clearer frontend semantics.
4. Update frontend stack display wording if approved.
5. Keep quality-score penalty unchanged and document why.
6. Keep review flags visible and normalized.
7. Add or update smoke checks for stack display and scoring.
8. Verify with a real or snapshot Java/Ukraine run.
9. Document the result in `Tasks.md`, `ProjectStatus.md`, and, if useful, `docs/phase-3-quality-baseline.md`.

### Constraints

- Do not treat query-source stack as direct candidate evidence.
- Do not hide candidates only because selected stack is missing from public snippet.
- Do not add hidden filters.
- Do not open LinkedIn profiles.
- Do not scrape LinkedIn.
- Do not add AI model calls.
- Do not change `QueryPlanner v1` unless separately approved.

### Acceptance criteria

- Recruiter-facing stack display is clearer than plain `n/a` for selected-but-not-visible stack.
- `missing_selected_stack` displays as `Not visible`.
- `stack_query_source_only` displays as `Not confirmed`.
- Direct stack evidence still displays actual matched terms such as `Spring`, `Kafka`, or `Spring, Kafka`.
- Future no-stack-requested state is reserved as `N/A`.
- Direct stack evidence remains clearly separated from query-source-only evidence.
- `selected_stack_missing` remains visible and explainable.
- Quality-score formula remains unchanged and this decision is documented.
- Existing Phase 3 quality fields remain backward-compatible unless a breaking change is explicitly approved.

### Before implementation

Codex must restate the proposed stack semantics, exact UI/backend changes, and scoring change before applying code.

### Implementation result

Implemented as a focused frontend display-semantics change.

Changed:

- `selected_stack_found` keeps showing direct evidence terms such as `Spring`, `Kafka`, or `Spring, Kafka`.
- `missing_selected_stack` now displays `Not visible`.
- `stack_query_source_only` now displays `Not confirmed`.
- future `missing` / no-stack-requested state displays `N/A`.

Not changed:

- backend search logic;
- `QueryPlanner v1`;
- filters;
- quality-score formula;
- review flag taxonomy.

Reasoning:

- `P3-010.1` showed that `missing_selected_stack` is usually missing public snippet evidence, not proof that the candidate lacks the selected stack.
- The previous frontend value `Stack: n/a` was too blunt.
- The current scoring already separates direct-stack candidates from missing-stack candidates without hiding useful Java candidates.

Verification:

- `node --check app/static/app.js`
- frontend stack mapping smoke passed;
- snapshot stack-state smoke passed for `selected_stack_found`, `missing_selected_stack`, and `stack_query_source_only`;
- render smoke passed for `Spring, Kafka`, `Not visible`, `Not confirmed`, and `N/A`;
- `python -m compileall app`

---

## Phase 4 - AI Agent Foundation

### Approved

- [ ] P4-001 Define AI Agent Foundation contract
- [ ] P4-002 Define Search Brief schema
- [ ] P4-008 Add approval before Tavily execution

### Backlog

- [ ] P4-009 Compare AI planner vs rule-based baseline
- [ ] P4-010 Close Phase 4 with decision

### In Progress

### Done

- [x] P4-003 Add Search Brief validation and adapter
- [x] P4-004 Define Agent tools contract
- [x] P4-005 Add AI Query Planner v0 behind explicit mode
- [x] P4-006 Add AI QueryPlan validation and fallback
- [x] P4-007 Add planner explanation UI

### Current Phase 4 strategy note

Phase 4 should move the product toward an AI Agent, but without throwing away the deterministic engine built in Phase 2 and Phase 3.

The current engine should become the agent's safe tool layer:

- structured search request;
- `QueryPlan`;
- rule-based planner fallback;
- search executor;
- multi-wave runner;
- URL normalization and dedupe;
- visible profile/location filters;
- Candidate Quality Layer;
- reports and snapshots.

AI should plan and explain, while backend validation, visible controls, and approval gates keep search behavior inspectable and safe.

Current Phase 4 implementation status:

- `P4-003` through `P4-007` are implemented in code.
- Backend supports `SearchBrief` validation/adapter endpoints, Agent Tools v0 metadata, explicit AI planner mode, deterministic AI QueryPlan validation/fallback, and non-executable planner responses.
- Frontend supports `Planner mode` and displays Search Brief summary, planner explanation, validation/fallback state, and approval-needed notices.
- `P4-008` is approved as the next execution-safety task: add a real backend approval gate before Tavily execution.
- Next task to review after `P4-008`: `P4-009 Compare AI planner vs rule-based baseline`.

Phase 4 should not immediately implement a fully autonomous agent loop. The goal is the foundation:

1. Turn recruiter intent into a structured `Search Brief`.
2. Let AI propose a validated `QueryPlan`.
3. Show explanations before execution.
4. Require approval before Tavily calls.
5. Run search through the existing engine.
6. Analyze results and suggest the next iteration.

Do not include in Phase 4 without separate approval:

- persistent memory or database;
- shortlist;
- export workflow;
- LinkedIn login;
- scraping or restriction bypass;
- fully autonomous tool-calling loop;
- multi-source search beyond Tavily.

---

## Task: P4-001 Define AI Agent Foundation contract

### Контекст

В проекте уже есть рабочий deterministic sourcing engine:

- `StructuredSearchRequest`;
- `QueryPlan`;
- rule-based planner;
- sequential Tavily runner;
- dedupe по normalized LinkedIn profile URL;
- видимые фильтры;
- Candidate Quality Layer;
- multi-wave runner;
- reports и local snapshots.

Следующее направление продукта - не просто AI-generated query list, а фундамент AI Agent поверх уже построенного engine.

### Цель

Зафиксировать первый контракт AI Agent Foundation до написания кода.

Контракт должен описать:

- как intent рекрутера превращается в structured brief;
- как AI предлагает план и действия;
- какие backend tools доступны агенту;
- где обязательно нужен approval пользователя.

### Основные понятия

#### Search Brief

Структурированная задача рекрутера, извлеченная из user intent.

Первичные поля:

- `role_family`;
- `technology`;
- `stack`;
- `location`;
- `seniority`;
- `must_have`;
- `nice_to_have`;
- `exclusions`;
- `search_depth`;
- `notes`.

#### Agent Plan

Читаемый человеком план, который создается до выполнения действий.

Он должен объяснять:

- что агент понял;
- кого и где он собирается искать;
- какой planner mode он предлагает использовать;
- рекомендует ли single-wave или multi-wave;
- ожидаемый tradeoff по cost/latency;
- какие действия требуют approval.

#### Agent Action

Предложенное действие агента. Оно может быть чисто аналитическим или может требовать backend tool call.

Примеры:

- построить query plan;
- запустить single-wave search;
- запустить multi-wave search;
- проанализировать кандидатов;
- предложить следующую итерацию поиска.

#### Tool Call

Валидированная backend operation, доступная агенту.

Агент не должен обходить существующие backend contracts. Tool calls должны переиспользовать текущие API и внутренние модели там, где это возможно.

#### Approval Gate

Любое дорогое или externally visible действие должно ждать approval пользователя.

Минимально approval нужен перед Tavily execution и multi-wave execution.

#### Agent Response

Объяснение агента для пользователя.

Оно должно быть читаемым и опираться на:

- Search Brief;
- QueryPlan;
- report metrics;
- candidate quality signals;
- known limitations.

### Шаги

1. Зафиксировать scope Phase 4 как `AI Agent Foundation`, а не только `AI Query Planner`.
2. Определить первый контракт `Search Brief`.
3. Определить сущности `Agent Plan`, `Agent Action`, `Tool Call`, `Approval Gate` и `Agent Response`.
4. Сопоставить текущие deterministic engine capabilities с agent tools.
5. Определить, какие действия требуют approval.
6. Определить, что AI не имеет права делать в Phase 4.
7. Определить, как должен валидироваться AI-generated `QueryPlan`.
8. Определить fallback behavior к `RuleBasedQueryPlanner`.
9. Определить baseline evaluation для Java Backend Ukraine.
10. Отделить то, что относится к следующим фазам: chat, memory, shortlist, autonomous loop, database.

### Утвержденные решения

- Step 1 approved: scope Phase 4 зафиксирован как `AI Agent Foundation`, а не только `AI Query Planner`.
- Phase 4 строит фундамент агента: `Search Brief`, AI-assisted planning, explanations, backend validation и approval gates.
- Existing deterministic engine остается safe execution layer: `QueryPlan`, planner fallback, search runner, multi-wave runner, dedupe, filters, Candidate Quality Layer, reports и snapshots.
- AI Query Planner остается отдельной задачей внутри Phase 4, но не является всей фазой.
- Fully autonomous agent loop, chat UI, persistent memory/database, shortlist/export, LinkedIn login/scraping и multi-source search остаются вне Phase 4 без отдельного approval.
- Step 2 approved: `Search Brief v0` является структурой диалога, а не копией текущей формы.
- `Search Brief v0` хранит recruiter intent, missing fields, clarifying questions, assumptions и явные ограничения пользователя.
- `target_titles` не хранятся в `Search Brief`; их генерирует planner.
- Если `stack` не указан, агент задает уточняющий вопрос, а не строит план на догадках.
- `seniority` входит в `Search Brief v0` как optional field.
- `must_have` и `nice_to_have` входят в `Search Brief v0`.
- `exclusions` заполняются только из явных слов рекрутера, например "не Android" или "исключить frontend"; по умолчанию они пустые.
- Location не обрабатывается через manual blacklist exclusions. Для location сохраняется current-location matching: если текущая локация явно не совпадает с target location, кандидат скрывается или помечается по существующим правилам.
- `search_depth` для v0 имеет значения `standard` и `deep`; `deep` может предложить deeper search или multi-wave, но только через approval.
- Если brief неполный, агент задает уточняющие вопросы до planner execution.
- Baseline для проверки `Search Brief v0`: `Backend Developer + Java + Spring/Kafka + Ukraine`.
- Step 3 approved: agent workflow строится как `Agent Plan -> Agent Action -> optional Approval Gate -> validated Tool Call -> Agent Response`.
- `Agent Plan` описывает, что агент понял, какой поиск предлагает, какой planner mode/depth хочет использовать, какие инструменты будут задействованы и что требует approval.
- `Agent Action` описывает следующий шаг агента: задать уточняющий вопрос, предложить query plan, запустить single-wave search, запустить multi-wave search, проанализировать результаты или предложить следующую итерацию.
- `Tool Call` является только валидированной backend operation из разрешенного списка; агент не вызывает произвольные backend действия и не обходит существующие contracts.
- `Approval Gate` обязателен перед Tavily execution, multi-wave execution, deep search и выполнением AI-generated QueryPlan.
- `Agent Response` должен быть читаемым и grounded в `Search Brief`, `QueryPlan`, report metrics, candidate quality signals и known limitations.
- Step 4 approved: current deterministic engine становится `Agent Tools v0`.
- Утвержденные `Agent Tools v0`: `validate_search_brief`, `adapt_brief_to_structured_request`, `build_query_plan`, `validate_query_plan`, `run_single_wave_search`, `run_multi_wave_search`, `analyze_candidate_quality`, `summarize_search_results`, `suggest_next_iteration`.
- Агент может предлагать `multi-wave`, но не запускать его без approval.
- `run_single_wave_search`, `run_multi_wave_search` и `deep search` всегда требуют approval.
- `build_query_plan` можно выполнять без approval, потому что он не запускает Tavily.
- `validate_search_brief`, `adapt_brief_to_structured_request`, `validate_query_plan`, `analyze_candidate_quality`, `summarize_search_results` и `suggest_next_iteration` можно выполнять без approval.
- Все agent tools работают только поверх текущего backend pipeline.
- Запрещены прямые web-search вызовы агентом, LinkedIn scraping, restriction bypass и произвольные HTTP-запросы.
- Step 5 approved: approval rules делятся на `без approval`, `approval required` и `запрещено вообще`.
- Без approval агент может понимать intent, собирать и валидировать `Search Brief`, задавать уточняющие вопросы, адаптировать brief в `StructuredSearchRequest`, строить/валидировать `QueryPlan`, объяснять план, анализировать уже полученные результаты и предлагать следующую итерацию.
- Approval required для `run_single_wave_search`, `run_multi_wave_search`, `deep search`, выполнения AI-generated `QueryPlan`, повторного запуска поиска, увеличения `max_results` и изменения depth с `standard` на `deep`.
- Перед approval агент должен показать `Search Brief`, execution mode, примерный query count, single-wave/multi-wave mode, включенные filters, cost/latency implications и понятный вопрос на запуск.
- Запрещено вообще: direct web-search агентом в обход backend, LinkedIn login, LinkedIn scraping, restriction bypass, автоматическая отправка сообщений кандидатам и любые действия с user или third-party accounts.
- Step 6 approved: Phase 4-specific AI boundaries зафиксированы отдельно от absolute product boundaries в `instructions`.
- В Phase 4 AI не может запускать поиск без approval.
- AI planner не становится default mode.
- AI не может обходить backend validation.
- AI не может изменять или отключать visible filters без явного решения пользователя.
- AI не может самостоятельно менять scoring, location или dedupe logic.
- AI не может скрывать кандидатов только по AI opinion без explainable deterministic reason.
- Phase 4 не добавляет persistent memory/database, shortlist/export workflow, fully autonomous agent loop, полноценный recruiter chat UI, multi-source search beyond Tavily, private/personal data sources или сохранение sensitive user/account data.
- Step 7 approved: AI-generated `QueryPlan` можно только предлагать; backend deterministic validator решает, можно ли его выполнять.
- AI-generated `QueryPlan` должен соответствовать тому же contract, что и rule-based `QueryPlan`: `planner_version`, `input_snapshot`, `queries`, `filters`, `execution`, `reporting`.
- Validator проверяет structure: non-empty queries, unique query IDs, non-empty query strings, required `category`, `purpose`, `query`, `max_results`, and max results within limit.
- Validator проверяет safety: only approved backend/search scope, LinkedIn public profiles scope, no LinkedIn login/scraping/bypass terms, no hidden filter bypass, no unsupported locations, no arbitrary web-search.
- Validator проверяет соответствие `Search Brief`: role, technology, stack/nice-to-have, location, search_depth и explicit exclusions не должны противоречить brief.
- `standard` не увеличивает query count beyond the current plan contract; `deep` может предложить multi-wave через тот же validated `QueryPlan`, но не произвольные extra queries.
- Даже valid AI-generated `QueryPlan` требует approval перед Tavily execution.
- Если validation fails, search не выполняется; response должен вернуть validation errors и предложить fallback к `RuleBasedQueryPlanner`.
- Step 8 approved: fallback к `RuleBasedQueryPlanner` является visible safe mode, а не скрытым откатом.
- Fallback включается, если AI model недоступна, AI call вернул error/timeout, AI вернул невалидную структуру, AI-generated `QueryPlan` не прошел validation, AI plan нарушает safety rules, пользователь выбрал rule-based mode, или supported brief можно надежно обработать deterministic planner.
- Fallback строит `QueryPlan` через текущий path: `Search Brief -> StructuredSearchRequest -> RuleBasedQueryPlanner -> QueryPlan`.
- Пользователь должен видеть `planner_mode = rule_based_fallback` и `fallback_reason`.
- Fallback plan не запускается автоматически; Tavily execution все равно требует approval.
- Если brief не поддерживается текущим `RuleBasedQueryPlanner`, fallback должен вернуть понятное сообщение, что deterministic fallback недоступен для этого brief.
- Agent Response должен объяснить, почему AI plan не использован, доступен ли fallback, что fallback сделает, какие ограничения у fallback, и что нужно approval перед запуском.
- Step 9 approved: Phase 4 baseline evaluation проверяет весь agent flow, а не только candidate count.
- Baseline scenario остается `Backend Developer + Java + Spring/Kafka + Ukraine`.
- Evaluation проверяет extraction живого recruiter text в корректный `Search Brief`.
- Если brief неполный, evaluation ожидает clarifying question, а не silent plan generation.
- `Agent Plan` должен быть понятен до запуска и объяснять target, location, depth, single-wave/multi-wave recommendation, tools и approval requirements.
- Tavily execution не должен происходить до approval.
- AI-generated `QueryPlan` должен либо пройти deterministic validation, либо быть отклонен с validation errors.
- Fallback к `RuleBasedQueryPlanner` должен быть видим пользователю и работать для supported brief.
- Approved search должен идти через текущий Phase 3 pipeline: visible filters, executor, dedupe, Candidate Quality Layer, reports и snapshots.
- Evaluation должна подтвердить no forbidden behavior: no direct web-search bypass, no LinkedIn login/scraping/bypass, no auto-messaging, no account actions.
- Step 10 approved: Phase 4 остается foundation phase, а chat/memory/shortlist/autonomous runtime выносятся в следующие фазы.
- В Phase 4 входят `Search Brief` contract, LLM-assisted brief/plan generation, agent tool boundaries, AI Query Planner mode, deterministic validation, rule-based fallback, approval gates, explanations и baseline evaluation.
- Полноценный recruiter chat UI относится к Phase 5.
- Tool-calling agent runtime относится к Phase 6.
- Candidate workspace, shortlist, notes/statuses и export workflow относятся к Phase 7.
- Persistent memory/database, saved searches, saved sessions/runs/candidates и long-term memory относятся к Phase 8.
- Multi-source search beyond Tavily, private/personal data sources, candidate outreach и account actions не входят в Phase 4; outreach/account actions запрещены absolute product boundaries.
- `P4-001` approved: все 10 шагов AI Agent Foundation contract согласованы как постановка задачи; кодинг требует отдельного явного approval.

### Ограничения

- Не реализовывать AI calls в этой задаче.
- Не менять current search runtime в этой задаче.
- Не удалять `RuleBasedQueryPlanner`.
- Не делать AI planner default.
- Не запускать Tavily.
- Не добавлять LinkedIn login, scraping или restriction bypass.
- Не добавлять database, shortlist, export или persistent memory.

### Критерии приемки

- Phase 4 задокументирована как `AI Agent Foundation`.
- Концепт `Search Brief` определен.
- Граница agent tools определена.
- Approval gates определены.
- Existing deterministic engine сохранен как safe execution layer.
- `QueryPlan` остается контрактом между planner и executor.
- Следующие P4-задачи можно ревьюить по одной перед кодингом.

### Перед реализацией

Codex должен пересказать scope задачи, предложить точные implementation steps и дождаться явного approval перед изменением кода.

---

## Task: P4-002 Define Search Brief schema

### Context

`P4-001` approved the AI Agent Foundation contract. The next step is to define the exact `Search Brief v0` schema before implementing any LLM calls, validation endpoints, or frontend chat behavior.

`Search Brief v0` is not just a copy of the current form. It is a dialogue state between recruiter intent and technical `QueryPlan` generation. It must support both complete and incomplete briefs.

### Goal

Define a concrete `Search Brief v0` schema that can store what the AI understood, what is missing, what questions should be asked, and what can later be adapted into `StructuredSearchRequest`.

### Approved principles

- `Search Brief v0` is a dialogue structure, not only a ready form.
- The schema must support incomplete briefs.
- `brief_status` is required:
  - `needs_clarification`;
  - `ready_for_planning`.
- `missing_fields` and `clarifying_questions` are part of the schema.
- `source_text` is kept so the product can show what recruiter text the brief came from.
- `assumptions` are explicit so AI guesses are not hidden.
- Canonical fields are more important than free-text `must_have` / `nice_to_have`.
- `target_titles` do not belong in `Search Brief`; planner generates them later.
- `exclusions` are only explicit user constraints such as "not Android" or "exclude frontend"; they are not a location blacklist.
- `search_depth` defaults to `standard`; `deep` can recommend deeper search or multi-wave but execution still requires approval.

### Proposed schema

```json
{
  "source_text": "Find Backend Developer with Java in Ukraine, ideally Spring and Kafka.",
  "brief_status": "ready_for_planning",
  "role_family": "Backend Developer",
  "technology": "Java",
  "stack": ["Spring", "Kafka"],
  "location": "Ukraine",
  "seniority": null,
  "must_have": ["Java"],
  "nice_to_have": ["Spring", "Kafka"],
  "exclusions": [],
  "search_depth": "standard",
  "profile_sources": ["linkedin_public"],
  "notes": null,
  "missing_fields": [],
  "clarifying_questions": [],
  "assumptions": []
}
```

Exact field names can be adjusted during implementation, but the schema must preserve this meaning.

### Field rules

- `source_text`: original recruiter text or latest user instruction that produced the brief.
- `brief_status`: `needs_clarification` or `ready_for_planning`.
- `role_family`: canonical role family. For v0, supported value is `Backend Developer`.
- `technology`: canonical main technology. For v0, supported value is `Java`.
- `stack`: selected stack signals. For current Java planning, stack is required before `ready_for_planning`.
- `location`: canonical target location. For v0, supported value is `Ukraine`.
- `seniority`: optional value such as `Junior`, `Middle`, `Senior`, `Lead`, or `null`.
- `must_have`: explicit hard requirements from the recruiter.
- `nice_to_have`: explicit preferred signals from the recruiter.
- `exclusions`: explicit exclusions from the recruiter only.
- `search_depth`: `standard` or `deep`; default is `standard`.
- `profile_sources`: for v0, only `linkedin_public`.
- `notes`: optional user notes.
- `missing_fields`: required-for-planning fields that are missing.
- `clarifying_questions`: questions the agent should ask before planning.
- `assumptions`: explicit assumptions made by AI or deterministic parsing.

### Ready-for-planning rules

For the current Java Backend baseline, `ready_for_planning` requires:

- `role_family`;
- `technology`;
- `stack`;
- `location`;
- `search_depth`;
- `profile_sources`.

`stack` is not required for the schema object to exist, but it is required for `ready_for_planning` in the current Java flow.

If any required-for-planning field is missing, status must be `needs_clarification`.

### Incomplete brief example

Input:

```text
Find Java backend developer in Ukraine.
```

Expected brief shape:

```json
{
  "source_text": "Find Java backend developer in Ukraine.",
  "brief_status": "needs_clarification",
  "role_family": "Backend Developer",
  "technology": "Java",
  "stack": [],
  "location": "Ukraine",
  "search_depth": "standard",
  "profile_sources": ["linkedin_public"],
  "missing_fields": ["stack"],
  "clarifying_questions": [
    "Which Java stack signals are important for this search: Spring, Kafka, AWS, Hibernate, or something else?"
  ],
  "assumptions": []
}
```

### Baseline brief example

Baseline scenario:

```text
Backend Developer + Java + Spring/Kafka + Ukraine
```

Expected status:

```json
{
  "brief_status": "ready_for_planning",
  "role_family": "Backend Developer",
  "technology": "Java",
  "stack": ["Spring", "Kafka"],
  "location": "Ukraine",
  "search_depth": "standard",
  "profile_sources": ["linkedin_public"],
  "missing_fields": [],
  "clarifying_questions": []
}
```

### Constraints

- Do not implement LLM calls in this task unless separately approved.
- Do not change search runtime in this task.
- Do not run Tavily.
- Do not build recruiter chat UI.
- Do not add database, memory, shortlist, export, or persistence.
- Do not add `target_titles` to `Search Brief`.
- Do not use `exclusions` as a location blacklist.

### Acceptance criteria

- `Search Brief v0` schema is documented.
- Schema supports both `needs_clarification` and `ready_for_planning`.
- Required-for-planning fields are documented for the Java Backend baseline.
- Incomplete brief behavior is documented.
- Baseline brief example is documented.
- `target_titles`, location blacklist exclusions, and execution behavior remain out of the schema.
- Follow-up task `P4-003` can implement validation and adapter from this contract.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

---

## Task: P4-003 Add Search Brief validation and adapter

### Context

`P4-002` defined `Search Brief v0` as a dialogue-state schema. The next step is to define backend validation and the adapter from `Search Brief` into the existing `StructuredSearchRequest`.

The adapter must not create a parallel search validation system. The current backend already has `StructuredSearchRequest` and `normalize_structured_search_request(...)`; `P4-003` should reuse that existing validation after mapping a ready brief into the structured request shape.

### Goal

Add a safe bridge from `Search Brief v0` to the current deterministic search engine:

```text
Search Brief
-> Search Brief validation/normalization
-> StructuredSearchRequest adapter
-> existing structured-search validation
```

This task prepares the backend for a future LLM/ChatGPT layer, but it does not add LLM calls.

### Proposed backend pieces

1. Add a `SearchBrief` backend model matching `P4-002`.
2. Add `validate_search_brief(...)`.
3. Add `adapt_search_brief_to_structured_request(...)`.
4. Add a validation endpoint:

```text
POST /api/search-brief/validate
```

The endpoint should return:

- `ok`;
- normalized brief;
- validation errors;
- clarifying questions when the brief is incomplete;
- adapted `StructuredSearchRequest` only when the brief is `ready_for_planning` and valid.

### Validation rules

Backend must not blindly trust `brief_status` from AI or client input.

- If `brief_status = ready_for_planning` but required-for-planning fields are missing, validation must fail or downgrade to `needs_clarification`.
- If `brief_status = needs_clarification`, adapter must not create `StructuredSearchRequest`.
- For the current Java flow, `stack` is required before planning.
- `target_titles` must be rejected if sent; planner owns target-title generation.
- `search_depth` allowed values are `standard` and `deep`.
- `profile_sources` v0 supports only `linkedin_public`.
- `exclusions` are accepted as explicit recruiter constraints only; they must not become Tavily negative terms or location blacklist logic.
- `source_text`, `missing_fields`, `clarifying_questions`, and `assumptions` remain part of normalized brief metadata.

### Adapter rules

Adapter maps only execution-ready canonical fields into `StructuredSearchRequest`:

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

Then the adapter must reuse existing `normalize_structured_search_request(...)` so the current rules remain authoritative for:

- supported role families;
- implemented technologies;
- Java stack canonicalization and max stack count;
- location filter availability;
- default `linkedin_profiles_only`;
- default `location_filter_enabled`.

### Search depth handling

`search_depth` does not belong in `StructuredSearchRequest`.

- `standard` maps to the normal single-wave path later.
- `deep` is kept as brief/agent metadata and may recommend multi-wave later.
- `deep` must not automatically trigger multi-wave in this task.

### Smoke checks

Use local backend checks without Tavily:

1. Complete baseline brief returns valid normalized brief and adapted structured request.
2. Missing stack returns `needs_clarification` and no adapted request.
3. Unsupported location returns validation error.
4. Unsupported profile source returns validation error.
5. `target_titles` in payload is rejected.
6. `exclusions` are preserved as metadata but not converted into query terms or location blacklist.
7. `deep` is accepted as metadata but does not change the adapted structured request.

### Constraints

- Do not add LLM/OpenAI calls in this task.
- Do not run Tavily.
- Do not build query plan in this endpoint.
- Do not execute search.
- Do not change `/api/structured-search` behavior.
- Do not change planner/search runner/dedupe/scoring/location filter behavior.
- Do not build recruiter chat UI.
- Do not add database, memory, shortlist, export, or persistence.

### Acceptance criteria

- `SearchBrief` validation is documented and ready for implementation.
- Adapter rules to `StructuredSearchRequest` are documented.
- Existing structured-search validation remains authoritative.
- Incomplete briefs do not produce adapted search requests.
- `search_depth` is preserved as metadata but not pushed into current search runtime.
- No Tavily or LLM calls are introduced.
- Follow-up `P4-004` can define the full agent tools contract on top of this bridge.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

Implemented in code as part of Phase 4 agent planner foundation:

- added `SearchBrief` backend model;
- added validation/normalization for Search Brief v0;
- added adapter from ready Search Brief into existing `StructuredSearchRequest`;
- reused existing structured-search validation as the authoritative backend layer;
- added `POST /api/search-brief/validate`;
- rejected extra fields such as `target_titles`;
- preserved `search_depth` as metadata and did not trigger Tavily or multi-wave execution.

Verification:

- backend compile passed;
- no-Tavily smoke covered complete brief, missing stack, stale `missing_fields`, unsupported/extra fields, and adapted structured request.

---

## Task: P4-004 Define Agent tools contract

### Context

`P4-001` approved the AI Agent Foundation contract, `P4-002` defined `Search Brief v0`, and `P4-003` defined the validation/adapter bridge from `Search Brief` to the existing deterministic backend pipeline.

The next step is to define the exact tools the future LLM/ChatGPT layer is allowed to use. This is a contract task, not a runtime implementation task.

### Goal

Define `Agent Tools v0`: names, inputs, outputs, approval requirements, error shape, and safety boundaries for the backend operations available to the agent.

The agent must only call allowlisted tools and must not bypass existing backend contracts.

### Approved Agent Tools v0

#### `validate_search_brief`

Validates and normalizes `Search Brief v0`.

Approval: not required.

Input:

```json
{
  "search_brief": {}
}
```

Output:

```json
{
  "ok": true,
  "normalized_brief": {},
  "missing_fields": [],
  "clarifying_questions": [],
  "errors": []
}
```

#### `adapt_brief_to_structured_request`

Maps a `ready_for_planning` brief into the existing `StructuredSearchRequest` shape and reuses existing structured-search validation.

Approval: not required.

Rule: incomplete briefs must not produce adapted requests.

#### `build_query_plan`

Builds a `QueryPlan` from an adapted structured request.

Approval: not required because it does not execute Tavily.

Phase 4 may later support planner modes, but the tool contract must keep execution separate from planning.

#### `validate_query_plan`

Validates AI-generated or rule-based `QueryPlan` before any execution.

Approval: not required.

Rule: validation must be deterministic backend validation, not "AI validates AI".

#### `run_single_wave_search`

Runs the existing single-wave structured-search pipeline through the approved backend path.

Approval: required.

Rule: this tool must not run before explicit user approval.

#### `run_multi_wave_search`

Runs the experimental multi-wave structured-search pipeline through the approved backend path.

Approval: required.

Rule: this tool must not run before explicit user approval and should remain explicit/deeper search behavior.

#### `analyze_candidate_quality`

Analyzes already returned candidates using existing Candidate Quality Layer signals, report metrics, evidence, and review flags.

Approval: not required.

Rule: this tool does not hide candidates or change scoring/filtering behavior.

#### `summarize_search_results`

Creates a human-readable summary of already available report/results data.

Approval: not required.

#### `suggest_next_iteration`

Suggests the next sourcing step, such as asking for stack clarification, trying `deep`, changing brief wording, or proposing multi-wave.

Approval: not required for the suggestion itself.

Rule: any suggested execution still requires the relevant approval gate.

### Tool call envelope

Every tool call should use a stable envelope:

```json
{
  "tool_name": "build_query_plan",
  "input": {},
  "requires_approval": false,
  "approval_status": "not_required",
  "idempotency_key": null,
  "reason": "Why the agent wants this tool."
}
```

### Tool result envelope

Every tool result should use a stable envelope:

```json
{
  "ok": true,
  "tool_name": "build_query_plan",
  "result": {},
  "errors": [],
  "requires_approval": false,
  "next_actions": []
}
```

### Approval statuses

Allowed approval statuses:

- `not_required`;
- `required`;
- `approved`;
- `rejected`.

### Safety rules

- Agent can call only allowlisted tools.
- Tools must not do more than their declared contract.
- Planning tools must not execute Tavily.
- `run_*` tools must not execute without approval.
- Tools must reuse existing backend functions/endpoints where possible.
- Tool errors must be structured.
- No direct web-search by the agent outside the approved backend pipeline.
- No LinkedIn login.
- No LinkedIn scraping or restriction bypass.
- No arbitrary HTTP requests.
- No automatic candidate messaging.
- No account actions.

### Constraints

- Do not implement LLM/tool runtime in this task unless separately approved.
- Do not add OpenAI calls in this task.
- Do not run Tavily.
- Do not change current search behavior.
- Do not build frontend chat UI.
- Do not add database, memory, shortlist, export, or persistence.

### Acceptance criteria

- `Agent Tools v0` list is documented.
- Each tool has a purpose and approval requirement.
- Tool call/result envelope is documented.
- Approval statuses are documented.
- Safety rules are documented.
- Follow-up `P4-005` can add AI Query Planner mode behind explicit controls using this tool boundary.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

Implemented in code as part of Phase 4 agent planner foundation:

- added Agent Tools v0 metadata endpoint;
- exposed allowlisted tools and approval requirements;
- preserved separation between planning/validation tools and search execution tools;
- encoded absolute boundaries: no direct web-search bypass, no LinkedIn login, no LinkedIn scraping/bypass, no automatic candidate messaging, and no account actions.

Verification:

- `/api/agent/tools` smoke passed;
- `build_query_plan` is marked `requires_approval = false`;
- `run_single_wave_search` and `run_multi_wave_search` are marked `requires_approval = true`.

---

## Task: P4-005 Add AI Query Planner v0 behind explicit mode

### Context

`P4-001` through `P4-004` approved the AI Agent Foundation, `Search Brief v0`, the Search Brief validation/adapter bridge, and the Agent Tools v0 contract.

This is the first Phase 4 task where a real LLM/ChatGPT layer may be introduced, but only for planning and explanation. The current deterministic search engine must remain the safe execution layer.

### Goal

Add an AI Query Planner v0 behind an explicit planner mode.

The AI planner may produce a draft `QueryPlan`, planner explanation, and metadata from a ready `Search Brief`, but it must not execute Tavily, change filters, change scoring, or become the default planner.

### Planner modes

Define explicit planner modes:

- `rule_based`: current default behavior.
- `ai`: use LLM/ChatGPT to propose a draft query plan.
- `ai_with_fallback`: optional mode that may try AI planning and fall back to rule-based planning when AI planning fails.

Default must remain `rule_based`.

### AI planner input

The AI planner should receive only controlled context:

- validated `Search Brief`;
- adapted/normalized `StructuredSearchRequest`;
- current `QueryPlan` contract;
- Agent Tools v0 boundary;
- safety rules and absolute product boundaries;
- allowed source: `linkedin_public`;
- max query count and max results limits;
- current supported baseline: `Backend Developer + Java + Spring/Kafka + Ukraine`.

### AI planner output

The output must be structured and treated as draft:

```json
{
  "planner_version": "ai_query_planner_v0",
  "planner_mode": "ai",
  "explanation": "Why these query slots were proposed.",
  "draft_query_plan": {},
  "warnings": [],
  "assumptions": []
}
```

Important rule: `draft_query_plan` is not executable until later deterministic validation and approval gates are applied.

### LLM/API configuration

- Use a real LLM/ChatGPT API only for planning and explanation.
- Do not hardcode the model name in business logic; read model/config from environment or central config.
- Do not hardcode API keys.
- Expected secret/config name: `OPENAI_API_KEY` or equivalent project-approved OpenAI API configuration.
- If no API key/config is available, AI mode should fail gracefully without breaking `rule_based` mode.

### Execution boundaries

- AI planner must not call Tavily.
- AI planner must not call `run_single_wave_search`.
- AI planner must not call `run_multi_wave_search`.
- AI planner must not perform direct web-search.
- AI planner must not scrape LinkedIn, log in to LinkedIn, bypass restrictions, send candidate messages, or act on accounts.
- AI planner must not change scoring, dedupe, location filter, or visible filter behavior.
- AI planner must not silently hide candidates by AI opinion.

### Relationship to P4-006 and P4-008

`P4-005` may return a `draft_query_plan`, but it must not treat it as executable.

- `P4-006` owns deterministic AI QueryPlan validation and fallback behavior.
- `P4-008` owns approval before Tavily execution.

Until those tasks are implemented, an AI-generated plan should remain a proposal only.

### Proposed steps

1. Add explicit planner mode contract: `rule_based`, `ai`, optional `ai_with_fallback`.
2. Define AI planner prompt/context using only validated brief, adapted request, QueryPlan contract, limits, and safety rules.
3. Add LLM/ChatGPT planning call behind explicit `ai` mode.
4. Return structured output with `explanation`, `draft_query_plan`, `warnings`, and `assumptions`.
5. Keep `rule_based` as the default planner.
6. Ensure AI planner never executes Tavily or search tools.
7. Add graceful error/fallback response when LLM config/API is unavailable.
8. Keep generated AI plan non-executable until P4-006 validation and P4-008 approval are in place.
9. Add local smoke checks that do not require Tavily execution.

### Smoke checks

- Default planner mode remains `rule_based`.
- AI mode requires explicit selection.
- Missing LLM/API config returns graceful error and does not break rule-based mode.
- AI planner output is structured as draft.
- AI planner does not run Tavily.
- AI planner does not call search execution tools.
- Draft AI plan is not accepted as executable in this task.

### Constraints

- Do not make AI planner default.
- Do not execute Tavily.
- Do not implement final AI QueryPlan validation in this task; that belongs to `P4-006`.
- Do not implement execution approval UI/flow in this task; that belongs to `P4-008`.
- Do not change existing search runtime behavior.
- Do not change scoring, dedupe, location filter, or Candidate Quality logic.
- Do not build full recruiter chat UI.
- Do not add database, memory, shortlist, export, or persistence.
- Do not violate absolute product boundaries in `instructions`.

### Acceptance criteria

- AI Query Planner v0 is documented as explicit mode only.
- `rule_based` remains default.
- AI planner is limited to planning and explanation.
- AI output is treated as `draft_query_plan`, not executable plan.
- Missing LLM/API config fails gracefully.
- Tavily/search execution is not triggered by AI planner.
- Follow-up `P4-006` can validate/fallback AI plans before any execution.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

Implemented in code as part of Phase 4 agent planner foundation:

- added explicit planner modes: `rule_based`, `ai`, and `ai_with_fallback`;
- kept `rule_based` as the default planner mode;
- added OpenAI/ChatGPT planning call behind explicit AI mode;
- used environment-based OpenAI configuration and did not hardcode secrets;
- returned AI planner explanation, warnings, assumptions, and draft QueryPlan data;
- kept AI output non-executable and did not trigger Tavily from AI planning.

Verification:

- no-Tavily smoke covered rule-based agent plan and mocked AI planner response;
- live OpenAI planner call succeeded through the backend and returned a validated-not-executable plan.

---

## Task: P4-006 Add AI QueryPlan validation and fallback

### Context

`P4-005` allows an explicit AI planner mode to produce a non-executable `draft_query_plan`. Before any AI-generated plan can get near execution, the backend must deterministically validate it and provide a visible fallback path.

This task is the safety gate between LLM planning and search execution.

### Goal

Validate AI-generated draft plans deterministically and produce one of these outcomes:

- validated AI plan, still not executable until approval;
- rejected AI plan with structured errors;
- visible fallback option or fallback plan from `RuleBasedQueryPlanner` when supported.

No Tavily execution happens in this task.

### Source of truth

Validator must check the AI draft against backend-normalized inputs:

```text
normalized_brief + normalized_structured_request
```

The AI output is not authoritative for filters, execution settings, or supported domain rules.

### Plan status

Validated AI plans should still be marked non-executable until the approval flow exists:

```json
{
  "plan_status": "validated_not_executable",
  "execution_allowed": false
}
```

### Structural validation

The AI-generated plan must include the existing `QueryPlan` contract:

- `planner_version`;
- `planner_mode`;
- `input_snapshot`;
- `queries`;
- `filters`;
- `execution`;
- `reporting`.

Each query slot must include:

- `id`;
- `category`;
- `purpose`;
- `role_phrase`;
- `query`;
- `uses_stack`;
- `max_results`.

Query IDs must be unique and query strings must be non-empty.

### Limit validation

- Standard mode must not exceed the current 10-query plan contract.
- `max_results` must not exceed `QUERY_PLAN_MAX_RESULTS`.
- `deep` does not allow arbitrary extra queries.
- `deep` may only support later multi-wave behavior through the same validated plan.

### Safety validation

The validator must reject plans that:

- omit `site:linkedin.com/in` for LinkedIn public profile search;
- include arbitrary domains or unsupported sources;
- include LinkedIn login, scraping, bypass, account-action, or messaging terms;
- try to bypass visible filters;
- try to change scoring, dedupe, location filter, or candidate quality behavior;
- include direct web-search behavior outside the approved backend pipeline.

### Brief alignment validation

The AI plan must align with the normalized brief/request:

- role signal aligns with `role_family`;
- technology signal aligns with `technology`;
- location appears in each executable query string;
- stack/nice-to-have terms do not contradict the brief;
- `profile_sources` remains `linkedin_public`;
- explicit `exclusions` are not turned into location blacklist logic.

AI may propose query wording within approved scope, but the validator must ensure the query still contains the target location and relevant role/technology signal from the brief.

### Authoritative filters

Filters should come from backend normalized request, not from AI output.

AI may propose filters in metadata, but backend must remain authoritative for:

- `linkedin_profiles_only`;
- `location_filter_enabled`;
- execution limits;
- report fields.

### Validation error shape

Validation errors must be structured:

```json
{
  "field": "queries[3].query",
  "code": "missing_target_location",
  "message": "Query does not include target location Ukraine."
}
```

### Fallback behavior

Fallback to `RuleBasedQueryPlanner` should be available when the normalized structured request is supported.

Fallback can be used when:

- AI output is missing or invalid;
- AI output is invalid JSON/shape;
- AI model is unavailable;
- AI call times out or errors;
- AI plan validation fails;
- AI plan violates safety rules;
- user selects fallback;
- planner mode is `ai_with_fallback`.

Fallback response should be visible:

```json
{
  "planner_mode": "rule_based_fallback",
  "fallback_reason": "AI plan failed validation.",
  "query_plan": {}
}
```

Fallback plan also remains non-executable until approval.

### Proposed backend pieces

- `validate_ai_query_plan(draft_plan, normalized_brief, normalized_structured_request)`.
- `build_rule_based_fallback_plan(normalized_structured_request, fallback_reason)`.
- Optional endpoint:

```text
POST /api/ai-query-plan/validate
```

Endpoint shape can be finalized during coding, but the contract must preserve the validation/fallback behavior above.

### Smoke checks

- Valid draft plan returns `validated_not_executable`.
- Missing `site:linkedin.com/in` is rejected.
- Missing target location is rejected.
- Too many queries are rejected.
- `max_results` above limit is rejected.
- Unsupported domain/source is rejected.
- Filter override attempt is ignored or rejected.
- Invalid AI output returns structured errors and fallback option when supported.
- Fallback plan uses `RuleBasedQueryPlanner`.
- No Tavily execution occurs.

### Constraints

- Do not run Tavily.
- Do not make AI plans executable in this task.
- Do not implement approval flow in this task; approval belongs to `P4-008`.
- Do not change default planner mode.
- Do not change current search runtime behavior.
- Do not change scoring, dedupe, location filter, or Candidate Quality logic.
- Do not build frontend chat UI.
- Do not add database, memory, shortlist, export, or persistence.

### Acceptance criteria

- AI QueryPlan deterministic validation is documented.
- Validation uses normalized brief/request as source of truth.
- Valid AI plan is marked `validated_not_executable`.
- Structured validation errors are defined.
- Rule-based fallback behavior is defined.
- No Tavily execution is introduced.
- Follow-up `P4-007` can display planner explanations and validation/fallback state.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

Implemented in code as part of Phase 4 agent planner foundation:

- added deterministic AI QueryPlan validation helper;
- added `POST /api/ai-query-plan/validate`;
- validated structure, query count, max results, LinkedIn public profile source scope, target location, role/technology signal, execution mode, and forbidden behavior terms;
- normalized authoritative filters/execution/reporting from backend state instead of trusting AI output;
- added visible rule-based fallback behavior for invalid AI plans and AI errors.

Verification:

- no-Tavily smoke covered valid AI plan, missing `site:linkedin.com/in`, fallback from invalid AI plan, and non-executable response state.

---

## Task: P4-007 Add planner explanation UI

### Context

`P4-005` defines AI Query Planner v0 behind explicit mode, and `P4-006` defines deterministic validation/fallback for AI-generated draft plans.

The frontend already has a `Generated QueryPlan` panel and `renderQueryPlan(...)`. `P4-007` should extend that existing preview with planner explanation and validation/fallback state. It should not become a broad UI rewrite or full recruiter chat.

### Goal

Show the user what the planner understood and proposed before execution:

- planner mode;
- Search Brief summary;
- planner explanation;
- query plan preview;
- validation status;
- validation errors/warnings;
- fallback state;
- approval-needed notice.

### UI direction

Extend the existing `Generated QueryPlan` preview instead of creating a new chat UI.

The UI should remain backward-compatible:

- if explanation/status fields are present, show them;
- if they are absent, current rule-based QueryPlan preview keeps working.

### Planner mode display

Show a clear planner mode badge or status:

- `rule_based`;
- `ai_draft`;
- `validated_not_executable`;
- `rejected`;
- `rule_based_fallback`.

Exact labels can be user-friendly, but the underlying state must remain visible enough for debugging.

### Search Brief summary

When available, show a compact brief summary near the plan:

- role;
- technology;
- stack;
- location;
- search depth;
- missing fields or clarifying questions when the brief is incomplete.

### Planner explanation

When available, show:

- AI planner explanation;
- assumptions;
- warnings;
- fallback explanation/reason.

For rule-based mode, show a simple explanation such as:

```text
Using tested Java Backend rule-based planner baseline.
```

### QueryPlan preview

Keep the current query plan list and enrich it when fields exist:

- query id;
- category;
- role phrase;
- purpose;
- query string;
- stack usage.

### Validation and fallback display

Show validation state:

- `draft_query_plan`;
- `validated_not_executable`;
- `rejected`;
- `rule_based_fallback`.

Show structured validation errors when present:

- `field`;
- `code`;
- `message`.

### Approval-needed notice

Until `P4-008` implements approval flow, show a clear notice when a plan is not executed:

```text
This plan is not executed yet. Search execution requires approval.
```

### Constraints

- Do not run Tavily.
- Do not implement approval execution flow; that belongs to `P4-008`.
- Do not build full recruiter chat UI; that belongs to Phase 5.
- Do not change planner/search runtime.
- Do not make AI plans executable.
- Do not hide validation errors.
- Do not rewrite the whole frontend candidate/results UI.
- Keep existing rule-based QueryPlan preview working.

### Acceptance criteria

- Existing QueryPlan preview remains functional.
- Planner mode/status can be displayed when present.
- Search Brief summary can be displayed when present.
- Planner explanation/warnings/assumptions can be displayed when present.
- Validation errors can be displayed in a readable way.
- Fallback reason can be displayed.
- UI clearly says execution requires approval before search.
- No Tavily/search execution is introduced.

### Before implementation

Codex must restate the task scope, propose exact UI changes, and wait for explicit approval before changing code.

### Implementation result

Implemented in code as part of Phase 4 agent planner foundation:

- added `Planner mode` frontend control;
- built Search Brief from the current form state;
- changed plan refresh to use `/api/agent/query-plan`;
- rendered planner mode/status, Search Brief summary, planner explanation, warnings, assumptions, validation errors, fallback reason, role phrase, and approval-needed notice;
- blocked direct search execution while AI planner preview mode is selected.

Verification:

- `node --check app/static/app.js`;
- browser smoke confirmed planner UI renders, AI mode blocks direct Search, and console has no errors.

---

## Task: P4-008 Add approval before Tavily execution

### Context

`P4-003` through `P4-007` added the Phase 4 planner foundation. Planner responses can now say `execution_approval_required = true`, but the execution endpoints still need a real backend approval gate.

The current risk is that `/api/structured-search` and `/api/structured-search/multi-wave` can still run Tavily when called directly. P4-008 closes that gap.

### Goal

Add a real backend approval gate before Tavily execution.

Approval must be explicit, tied to the concrete action, and tied to the current visible `QueryPlan` so a user cannot approve one plan and accidentally execute another after changing inputs.

### Approval payload

Execution requests should include approval metadata similar to:

```json
{
  "execution_approval": {
    "approval_status": "approved",
    "approved_action": "run_single_wave_search",
    "approved_planner_mode": "rule_based",
    "approved_query_count": 10,
    "approved_plan_fingerprint": "..."
  }
}
```

### Backend rules

- `/api/structured-search` requires approval for `run_single_wave_search`.
- `/api/structured-search/multi-wave` requires approval for `run_multi_wave_search`.
- Backend recalculates the current rule-based `QueryPlan` and computes the current fingerprint before Tavily execution.
- Missing approval is rejected before Tavily.
- Wrong action approval is rejected before Tavily.
- Stale plan fingerprint is rejected before Tavily.
- Wrong query count or planner mode is rejected before Tavily.
- Approval metadata is saved into structured-search snapshots/logs.

### Frontend rules

- The user must see the plan before execution.
- The Search button should communicate that the click approves Tavily execution, for example `Approve & Search`.
- Single-wave and multi-wave approvals must be distinct.
- Multi-wave remains explicit because it is deeper/costlier.

### AI plan boundary

AI-generated plans remain non-executable in this task.

P4-008 should enable approval-gated execution for current rule-based single-wave and multi-wave paths first. Executing AI-generated plans should remain a later separately reviewed task.

### Smoke checks

Use local/mocked checks where possible and avoid unnecessary Tavily calls:

1. Missing approval returns an error and does not call Tavily.
2. Wrong action approval returns an error and does not call Tavily.
3. Stale `approved_plan_fingerprint` returns an error and does not call Tavily.
4. Correct single-wave approval allows `/api/structured-search`.
5. Correct multi-wave approval allows `/api/structured-search/multi-wave`.
6. Snapshot includes approval metadata.
7. Frontend sends approval metadata only when the user clicks the explicit execution button.
8. AI planner preview remains non-executable.

### Constraints

- Do not make AI-generated QueryPlans executable in this task.
- Do not bypass existing structured-search validation.
- Do not change scoring, dedupe, Candidate Quality, or location filter behavior.
- Do not add recruiter chat UI.
- Do not add database, shortlist, export, or persistent memory.
- Do not perform direct web-search outside the approved backend pipeline.
- Do not add LinkedIn login, scraping, restriction bypass, candidate messaging, or account actions.

### Acceptance criteria

- Tavily execution cannot happen without explicit backend-validated approval.
- Approval is bound to action, planner mode, query count, and plan fingerprint.
- Single-wave and multi-wave approvals are separate.
- Stale or mismatched approvals fail safely before Tavily.
- Approval metadata is logged in snapshots.
- Frontend makes execution approval visible to the user.
- AI-generated plans remain non-executable.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

---

## Task: P3-011 Add experimental multi-wave API runner

### Context

Recent Tavily experiments showed that live result sets vary between runs. Repeating the same `QueryPlan` can return a slightly different candidate pool, but the incremental gain drops quickly.

Measured experiments for `Backend Developer + Java + Spring/Kafka + Ukraine`:

- 1 wave: `60` cumulative unique profiles;
- 3 waves: `64` cumulative unique profiles;
- 5 waves: `61` cumulative unique profiles in one fresh block;
- 10 waves: `60` cumulative unique profiles in one fresh block.

The conclusion is not to always run many waves. The useful product idea is an adaptive multi-wave runner that stops when extra waves stop adding enough new unique profiles.

### Goal

Add an experimental backend API runner for multi-wave execution so Candidate Quality Layer evaluation can use a larger candidate pool when explicitly requested.

The runner should repeat the same validated `QueryPlan`, dedupe across waves by normalized LinkedIn URL, and stop based on incremental unique gain.

This task should not add frontend controls yet.

### Proposed behavior

- Add a new experimental endpoint instead of changing the current stable single-wave `/api/structured-search` behavior:
  - `/api/structured-search/multi-wave`.
- Input uses the same structured search request and generated `QueryPlan` as the current pipeline.
- Extract or reuse an internal helper for one `QueryPlan` execution wave so the new endpoint does not duplicate Tavily execution logic from the single-wave endpoint.
- Additional explicit request fields:
  - `max_waves`;
  - `min_new_unique_per_wave`;
  - `patience`.
- Safety defaults:
  - default `max_waves = 5`;
  - maximum allowed `max_waves = 7`;
  - default `min_new_unique_per_wave = 3`;
  - default `patience = 2`.
- Validation:
  - `max_waves` minimum `1`, maximum `7`;
  - `min_new_unique_per_wave` minimum `0`;
  - `patience` minimum `1`;
  - invalid values return validation errors using the existing structured-search validation style.
- Each wave runs the same 10 query slots through Tavily.
- Keep the existing `query_sources` structure unchanged because Candidate Quality already uses it.
- Add a separate `wave_sources` array for multi-wave evidence:
  - `wave_id`;
  - `query_id`;
  - `query`;
  - `role_phrase`;
  - `uses_stack`.
- Results are deduped across waves by normalized LinkedIn profile URL.
- The report includes per-wave and cumulative metrics:
  - `waves_run`;
  - `planned_max_waves`;
  - `stop_reason`;
  - `queries_executed`;
  - `raw_total`;
  - `unique_profiles_per_wave`;
  - `new_unique_profiles_per_wave`;
  - `cumulative_unique_profiles`;
  - `duplicates_across_waves`;
  - `hidden_by_profile_filter`;
  - `hidden_by_location_filter`;
  - `hidden_by_foreign_current_location`.
- Stop condition:
  - compute new unique profiles after visible filters and normalized-url cross-wave dedupe;
  - stop after `patience` consecutive waves where new unique profiles are lower than `min_new_unique_per_wave`;
  - always stop at `max_waves`.

### Constraints

- Do not change `QueryPlanner v1` in this task.
- Do not add AI planner behavior in this task.
- Do not change Candidate Quality scoring in this task.
- Do not bypass visible filters.
- Do not change current single-wave `/api/structured-search` behavior.
- If shared internal code is extracted, it must preserve the current single-wave API response and snapshot behavior.
- Do not change the existing `query_sources` contract.
- Do not add frontend controls in this task.
- Do not open LinkedIn profiles.
- Do not scrape LinkedIn.
- Do not make multi-wave the default until cost/benefit is confirmed.

### Acceptance criteria

- A separate experimental API path can run the same `QueryPlan` for multiple waves.
- Deduping works across waves, not only inside one wave.
- Report shows per-wave new unique gain and cumulative unique profiles.
- Runner can stop early when incremental unique gain is low.
- Candidate metadata preserves enough evidence to explain which wave/query found the candidate.
- Local snapshots for this endpoint use `snapshot_type = "structured-search-multi-wave"` and include multi-wave report data.
- API clearly marks multi-wave mode as experimental/supporting, not the default Phase 2 search path.
- The stable single-wave search endpoint remains unchanged.
- Smoke checks cover validation, cross-wave dedupe, stop condition, snapshot shape, and unchanged single-wave endpoint behavior without requiring a real Tavily run.

### Before implementation

Codex must restate the task scope, propose exact implementation steps, and wait for explicit approval before changing code.

### Implementation result

Implemented as a backend-only experimental API runner.

Added:

- new endpoint: `/api/structured-search/multi-wave`;
- `MultiWaveStructuredSearchRequest` with:
  - `max_waves`;
  - `min_new_unique_per_wave`;
  - `patience`;
- safety defaults:
  - default `max_waves = 5`;
  - maximum allowed `max_waves = 7`;
  - default `min_new_unique_per_wave = 3`;
  - default `patience = 2`;
- validation for `max_waves`, `min_new_unique_per_wave`, and `patience`;
- shared internal `run_query_plan_wave(...)` helper used by both single-wave and multi-wave flows;
- cross-wave dedupe by normalized LinkedIn profile URL;
- separate `wave_sources` metadata while preserving existing `query_sources`;
- multi-wave report fields:
  - `experimental`;
  - `mode`;
  - `multi_wave_settings`;
  - `waves_run`;
  - `planned_max_waves`;
  - `stop_reason`;
  - `queries_executed`;
  - `unique_profiles_per_wave`;
  - `new_unique_profiles_per_wave`;
  - `cumulative_unique_profiles`;
  - `duplicates_across_waves`;
  - `wave_reports`;
- multi-wave snapshot support with `snapshot_type = "structured-search-multi-wave"`.

Not changed:

- `/api/structured-search` external response shape;
- `QueryPlanner v1`;
- Candidate Quality scoring;
- visible filters;
- frontend controls.

Verification:

- `python -m compileall app`;
- `node --check app/static/app.js`;
- `git diff --check`;
- no-Tavily multi-wave endpoint smoke:
  - validation rejects `max_waves = 8`;
  - endpoint stops early after `patience = 2` low-gain waves;
  - cross-wave dedupe produces expected cumulative unique counts;
  - `wave_sources` is present only in multi-wave results;
  - single-wave `/api/structured-search` remains non-experimental and does not include `wave_sources`;
  - multi-wave snapshot type is `structured-search-multi-wave`.

Real Tavily evaluation is intentionally deferred to `P3-012`.

---

## Task: P3-012 Evaluate adaptive multi-wave results

### Context

`P3-011` adds an experimental backend multi-wave API runner. Before exposing it in the frontend, we need to measure whether it actually improves candidate quality or only spends more Tavily requests.

### Goal

Run controlled multi-wave experiments and decide whether the adaptive runner is useful enough to expose to users.

This is a measurement/documentation task, not a feature task.

### Proposed steps

1. Use the same baseline input as `P3-010`:
   - Role family: `Backend Developer`;
   - Technology: `Java`;
   - Stack: `Spring`, `Kafka`;
   - Location: `Ukraine`;
   - `LinkedIn profiles only`: on;
   - `Location filter`: on.
2. Run one primary real request against the experimental multi-wave endpoint with the approved default settings:
   - `max_waves = 5`;
   - `min_new_unique_per_wave = 3`;
   - `patience = 2`.
3. Do not run a second Tavily experiment unless the first result is clearly contradictory or broken and the user separately approves another run.
4. Compare against:
   - the historical `P3-010` single-wave baseline;
   - wave 1 inside the same multi-wave run;
   - final cumulative multi-wave result.
5. Measure search/cost metrics:
   - unique candidates;
   - new unique candidates per wave;
   - `waves_run`;
   - `stop_reason`;
   - `queries_executed`;
   - hidden by filters.
6. Measure quality of the cumulative result and incremental candidates:
   - quality-score distribution;
   - new high-quality candidates with `quality_score >= 80`;
   - direct stack evidence count;
   - missing stack count;
   - seniority found/missing;
   - technology missing count;
   - low/noisy candidates.
7. Document whether multi-wave improves candidate quality enough to justify the extra Tavily cost.
8. Record the result in `Tasks.md`, `ProjectStatus.md`, and a dedicated doc if useful.
9. Provide a recommendation for `P3-013`, but do not implement or approve frontend behavior inside this task.

### Constraints

- Do not change code in this task unless a bug blocks the measurement and is separately approved.
- Do not open LinkedIn profiles.
- Do not scrape LinkedIn.
- Do not add AI model calls.
- Do not expose frontend controls in this task.
- Do not treat Tavily live counts as deterministic.
- Do not run repeated Tavily experiments without separate approval.
- Do not make a final frontend decision in this task; provide a recommendation for `P3-013`.

### Acceptance criteria

- At least one real adaptive multi-wave run is completed.
- Results are compared with the historical `P3-010` single-wave baseline.
- Results are compared with wave 1 from the same multi-wave run.
- Final cumulative multi-wave result is documented.
- Extra cost is described through `waves_run`, `stop_reason`, `new_unique_profiles_per_wave`, and `queries_executed`.
- Quality of incremental candidates is reviewed.
- Recommendation for `P3-013` is documented: expose, keep backend-only, tune, or drop.

### Before implementation

Codex must restate the measurement scope, exact input, run settings, and documentation updates before running the experiment.

### Run result

Completed one real adaptive multi-wave run on 2026-05-15, 16:37:00-16:37:53 local time.

Input:

- Role family: `Backend Developer`
- Technology: `Java`
- Stack: `Spring`, `Kafka`
- Location: `Ukraine`
- `LinkedIn profiles only`: on
- `Location filter`: on
- `max_waves = 5`
- `min_new_unique_per_wave = 3`
- `patience = 2`

Snapshot:

- `logs/search-runs/2026-05-15T13-37-53Z_structured-search-multi-wave_backend-developer-java-ukraine.json`

Run summary:

- Waves run: 4 of planned 5
- Stop reason: `low_incremental_gain`
- Queries executed: 40
- Queries succeeded: 40
- Queries failed: 0
- Raw Tavily results: 754
- Displayed occurrences: 457
- Final unique candidates: 67
- Duplicates removed: 390
- Duplicates across waves: 176
- Hidden by profile filter: 41
- Hidden by location filter: 256
- Hidden by foreign current location: 216

Per-wave unique gain:

| Wave | Raw | Displayed | Wave unique | New unique | Cumulative unique |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 176 | 109 | 60 | 60 | 60 |
| 2 | 179 | 109 | 60 | 6 | 66 |
| 3 | 199 | 119 | 62 | 1 | 67 |
| 4 | 200 | 120 | 61 | 0 | 67 |

Comparison:

- Historical `P3-010` single-wave baseline: 57 unique candidates from 200 raw Tavily results.
- Wave 1 inside this multi-wave run: 60 unique candidates from 176 raw Tavily results.
- Final cumulative multi-wave result: 67 unique candidates from 754 raw Tavily results.
- Incremental gain over same-run wave 1: +7 unique candidates for +30 extra Tavily queries.

Cumulative quality:

- Quality score average: 76.6
- Quality score buckets: 1 in `0-39`, 6 in `40-59`, 32 in `60-79`, 28 in `80-100`
- Role fit: 51 `target_or_close_role`, 15 `similar_role`, 1 `missing_role`
- Technology fit: 61 `exact`, 6 `missing`
- Stack fit: 13 `selected_stack_found`, 7 `stack_query_source_only`, 47 `missing_selected_stack`
- Seniority fit: 35 `found`, 31 `missing`, 1 `ambiguous`

Incremental candidates after wave 1:

- Total new incremental candidates: 7
- New high-quality candidates with `quality_score >= 80`: 3
- New direct-stack candidates: 1
- New query-source-only stack candidates: 1
- New missing-stack candidates: 5
- New technology-missing candidates: 3
- New low-score candidates under 60: 3

Conclusion:

- Multi-wave works technically and stops correctly.
- It added candidates, but the incremental gain was modest: +7 unique candidates after 30 additional Tavily queries.
- Quality did improve slightly in absolute candidate count: +3 high-quality candidates and +1 direct-stack candidate after wave 1.
- Cost/gain is mixed: 4x query cost compared with one wave for about +11.7% unique candidates over the same-run wave 1.
- Recommendation for `P3-013`: do not make multi-wave default. Keep it backend-only for now or consider a clearly labeled advanced/deeper-search control with cost/latency warning.

---

## Task: P3-013 Add visible Multi-wave frontend toggle

### Context

`P3-011` added the backend experimental runner. `P3-012` measured the cost/gain tradeoff: multi-wave can add candidates, but the incremental gain is modest and should not be default.

User decision: expose multi-wave as an explicit frontend toggle, off by default.

### Goal

Add a visible frontend `Multi-wave` toggle.

Default behavior remains single-wave search through `/api/structured-search`.

If the user enables `Multi-wave` and clicks Search, frontend should call `/api/structured-search/multi-wave`.

### Proposed behavior

- Add visible toggle label: `Multi-wave`.
- Toggle is off by default.
- If toggle is off:
  - call existing `/api/structured-search`;
  - current single-wave behavior remains unchanged.
- If toggle is on:
  - call `/api/structured-search/multi-wave`;
  - send default multi-wave settings:
    - `max_waves = 5`;
    - `min_new_unique_per_wave = 3`;
    - `patience = 2`.
- Show that multi-wave mode was used.
- Show multi-wave report fields when present:
  - `waves_run`;
  - `queries_executed`;
  - `stop_reason`;
  - `new_unique_profiles_per_wave`.
- Keep wave/source metadata inside existing details; do not redesign candidate cards in this task.

### Proposed steps

1. Add a checkbox/toggle input to the form.
2. Keep it unchecked by default.
3. Add frontend request builder logic:
   - single-wave payload unchanged when toggle is off;
   - multi-wave payload includes the approved default settings when toggle is on.
4. Update Search submit logic to choose endpoint based on the toggle.
5. Update loading/status copy so multi-wave feels slower/explicit.
6. Update report rendering to include multi-wave metrics only when response report has `mode = multi_wave` or `experimental = true`.
7. Add frontend smoke checks for:
   - default endpoint remains `/api/structured-search`;
   - toggle-on endpoint becomes `/api/structured-search/multi-wave`;
   - multi-wave settings are sent;
   - report renders multi-wave metrics.
8. Verify syntax and compile checks.
9. Update `Tasks.md`, `ProjectStatus.md`, and `Roadmap.md`.

### Constraints

- Multi-wave must remain off by default.
- Do not hide Tavily cost/latency implications.
- Do not change backend runner behavior in this task unless separately approved.
- Do not add AI planner behavior.
- Do not change Candidate Quality scoring.
- Do not change `QueryPlanner v1`.
- Do not run a new Tavily evaluation in this task unless separately approved.

### Acceptance criteria

- A visible `Multi-wave` toggle exists.
- Toggle is off by default.
- Search uses `/api/structured-search` when toggle is off.
- Search uses `/api/structured-search/multi-wave` when toggle is on.
- Multi-wave request sends approved default settings.
- UI shows key multi-wave metrics when available.
- Existing single-wave behavior remains unchanged.

### Before implementation

Approved by user after confirming the intended behavior.

### Implementation result

Implemented the approved frontend control.

Changed:

- Added visible `Multi-wave` toggle to the search form.
- Toggle is unchecked by default.
- When toggle is off, Search uses `/api/structured-search`.
- When toggle is on, Search uses `/api/structured-search/multi-wave`.
- Multi-wave request sends approved defaults:
  - `max_waves = 5`;
  - `min_new_unique_per_wave = 3`;
  - `patience = 2`.
- Report status now labels `Single-wave` or `Multi-wave`.
- Multi-wave report adds visible metrics when present:
  - `Waves`;
  - `Executed queries`;
  - `Stop reason`;
  - `New per wave`.

Not changed:

- backend runner behavior;
- `QueryPlanner v1`;
- Candidate Quality scoring;
- default single-wave behavior.

Verification:

- `node --check app/static/app.js`;
- `python -m compileall app`;
- frontend smoke confirmed:
  - default endpoint is `/api/structured-search`;
  - toggle-on endpoint is `/api/structured-search/multi-wave`;
  - toggle-on request includes multi-wave defaults;
  - multi-wave report metrics render.

---

## Task: P3-014 Close Phase 3 and prepare Phase 4 handoff

### Context

Phase 3 has delivered the first Candidate Quality Layer on top of the Phase 2 multi-query search engine.

Completed Phase 3 capabilities:

- candidate-facing name/headline extraction;
- role fit signals;
- technology and stack fit signals;
- seniority detection;
- normalized review flag taxonomy;
- explainable `quality_score`;
- hybrid frontend candidate quality view;
- Java/Ukraine quality baseline;
- review of `missing_selected_stack` behavior;
- clearer stack display semantics;
- experimental adaptive multi-wave runner;
- real multi-wave evaluation;
- visible `Multi-wave` frontend toggle, off by default.

### Goal

Close Phase 3 as a completed phase and prepare the handoff into Phase 4: `AI Agent Foundation`.

### Phase 3 final conclusion

Phase 3 is successful as a Candidate Quality Layer baseline.

It does not make Tavily/LinkedIn public snippets complete or deterministic, but it makes the current evidence visible, ranked, explainable, and reviewable.

Main conclusion: the application is ready to explore an AI Agent foundation because the downstream pipeline is now stable enough:

- structured search request;
- `QueryPlan` contract;
- sequential query execution;
- URL normalization and dedupe;
- visible profile/location filters;
- candidate quality fields;
- explainable score;
- query source metadata;
- optional multi-wave execution.

### Important limitations carried into Phase 4

- Tavily live results vary between runs.
- LinkedIn public snippets are incomplete.
- Selected stack evidence can be missing from snippets even for relevant candidates.
- `Location filter` remains heuristic and currently has only Ukraine config.
- Multi-wave search can add candidates, but should remain explicit and off by default.
- Candidate quality score is deterministic v1 ranking support, not final recruiting judgment.

### Phase 4 handoff rules

Phase 4 may add AI-assisted planning and agent-style orchestration, but it should preserve these contracts:

- AI planner must output a validated `QueryPlan`;
- executor, dedupe, report, filters, snapshots, and candidate quality layer should not be rewritten for P4-001;
- AI planner suggestions should be inspectable before execution;
- visible filters remain user-controlled;
- no LinkedIn login, scraping, restriction bypass, database, shortlist, or full agent runtime unless separately approved.

### Next recommended task

`P4-001 Define AI Agent Foundation contract`

Before coding Phase 4, review and approve the AI Agent foundation contract:

- `Search Brief`;
- `Agent Plan`;
- `Agent Action`;
- agent tool boundaries;
- approval gates;
- required `QueryPlan` output fields for AI planner actions;
- validation rules;
- fallback to `RuleBasedQueryPlanner`;
- approval/visibility behavior before Tavily execution;
- examples for Java Backend Ukraine baseline.

### Implementation result

Docs-only task completed:

- `Tasks.md` marks `P3-014` as done and records Phase 3 closeout.
- `Roadmap.md` marks Phase 3 completed and Phase 4 as the active next phase.
- `ProjectStatus.md` marks Phase 3 completed through `P3-014`; after `P4-001` contract approval, `P4-002` is the next task to review.

No code changes.

---

## Task: P2-012 Replace blacklist negative_terms with current location classification

### Context

`P2-009.1` added a configurable `Location filter` for Ukraine. It currently uses:

- `include_terms` for target-location terms such as `Ukraine`, `Kyiv`, `Lviv`;
- `negative_terms` for explicit foreign current-location terms such as `Prague`, `Czechia`;
- `ua.linkedin.com/in/...` as a country-domain signal.

The current `negative_terms` approach does not scale. It catches only the foreign locations explicitly listed in config, so candidates with clear current location such as `Warsaw, Mazowieckie, Poland` can still pass when their URL is `ua.linkedin.com/in/...`.

The better product rule is not to list every bad country or city. The filter should determine whether the candidate has an explicit current-location line in the public LinkedIn header. If that current location is clearly not the target location, it should hide the candidate.

### Goal

Replace the blacklist-style `negative_terms` logic with current-location classification:

- `target_location`;
- `foreign_current_location`;
- `unknown_current_location`.

The key rule: if the public header has an explicit current location and it does not match the target location, the candidate should be hidden even if the URL is `ua.linkedin.com/in/...`.

### Approval

Задача и предложенные шаги одобрены пользователем.

### Scope

This is an improvement to the existing `Location filter`, not a new search pipeline.

Keep the current planner, Tavily runner, dedupe, query source metadata, frontend flow, local snapshot logging, and overall report structure unless a small report-field addition is needed for the new location classification.

### Proposed steps

1. Зафиксировать проблему: `negative_terms` не масштабируется. `Prague/Czechia` ловит только частные случаи, но пропускает `Warsaw/Poland`, `Berlin/Germany`, etc.

2. Сохранить текущий общий pipeline:
   - `StructuredSearchRequest`;
   - `QueryPlanner v1`;
   - `QueryPlan`;
   - sequential Tavily runner;
   - LinkedIn profile filtering;
   - URL normalization and dedupe;
   - candidate `query_sources`;
   - local structured-search snapshot logging.

3. Replace config semantics:
   - keep target location terms for Ukraine;
   - stop treating foreign locations as a finite blacklist.

Example target terms:

```python
"target_location_terms": [
    "Ukraine",
    "Kyiv",
    "Kiev",
    "Lviv",
    "Kharkiv",
    "Odesa",
    "Odessa",
    "Dnipro",
    "Vinnytsia",
    "Zaporizhzhia",
    "Chernivtsi",
    "Ternopil",
    "Ivano-Frankivsk",
]
```

4. Add current-location line extraction from `header_location_text`.

Typical source:

```text
Name
Headline
Current location
connections/followers
```

Example:

```text
Ivan V.
Java Developer
Warsaw, Mazowieckie, Poland
500 connections
```

Expected current-location line:

```text
Warsaw, Mazowieckie, Poland
```

5. Add current-location classification:

```text
target_location
foreign_current_location
unknown_current_location
```

6. Target-location rule:

If the current-location line contains target Ukraine terms such as `Ukraine`, `Kyiv`, `Lviv`, etc., classify it as `target_location` and allow the candidate.

7. Foreign-current-location rule:

If the current-location line is explicit and looks like a geography line, but it does not contain target Ukraine terms, classify it as `foreign_current_location` and hide the candidate.

Examples that should hide:

```text
Warsaw, Mazowieckie, Poland
Berlin, Germany
Prague, Czechia
Amsterdam, Netherlands
```

This rule must beat `ua.linkedin.com/in/...`.

8. Unknown-current-location rule:

If no current-location line can be confidently extracted, fall back to existing softer signals:

- `ua.linkedin.com/in/...` can pass as `country_domain`;
- non-UA profile with target terms in header can pass as `rescued_header_location`;
- target terms only in history/education remain hidden as `weak_history_only`;
- no target terms remain hidden as `unknown_non_country_domain`.

9. Update final display priority:

```text
foreign_current_location -> hide
target_location -> show
country_domain -> show
rescued_header_location -> show
weak_history_only -> hide
unknown_non_country_domain -> hide
```

10. Update status/report naming.

Add or map a status such as:

```text
excluded_foreign_current_location
```

The report should make it clear how many candidates were hidden because their explicit current location did not match the target location.

11. Add smoke checks:

- `ua.linkedin.com` + `Warsaw, Poland` -> hidden;
- `ua.linkedin.com` + `Kyiv, Ukraine` -> shown;
- `www.linkedin.com` + `Ukraine` in current-location header -> shown/rescued;
- `www.linkedin.com` + Ukraine only in education/history -> hidden;
- no clear current-location line + `ua.linkedin.com` -> shown as `country_domain`;
- duplicate candidate where one occurrence has foreign current location -> hidden;
- `location_filter_enabled = false` -> filter skipped.

12. Run one real Java/Ukraine baseline after implementation.

Compare with the current latest snapshot:

- current snapshot displayed `75` unique candidates;
- at least the known Warsaw/Poland false positives should disappear;
- success criterion should remain above `20` unique candidates.

13. Update documents with implementation result and measured counts.

### Expected behavior

The location filter stops relying on a finite blacklist of foreign countries/cities. A displayed candidate should not pass just because the URL is `ua.linkedin.com/in/...` when the public header clearly says the current location is outside Ukraine.

### Constraints

- Do not implement LinkedIn login.
- Do not scrape LinkedIn.
- Do not open LinkedIn profiles automatically.
- Use only Tavily returned public `title`, `content`, `snippet`, and URL fields.
- Do not add a database.
- Do not change the query planner in this task.
- Do not change Tavily query generation in this task.
- Do not expand into Candidate Quality Layer scoring in this task.
- Do not introduce a new external geocoding/location API.

### Acceptance criteria

- `negative_terms` no longer drives the primary exclusion logic for current-location mismatch.
- The filter extracts or derives a current-location line from `header_location_text`.
- Explicit current-location line matching target Ukraine terms passes.
- Explicit current-location line that looks geographic but does not match Ukraine is hidden.
- Foreign current location beats `ua.linkedin.com/in/...`.
- Unknown current location can still fall back to `country_domain` or other existing signals.
- Candidate-level merge keeps the existing rule that a strong hide signal from any occurrence can hide the deduped candidate.
- Report exposes a clear count for candidates hidden by foreign current location.
- Local structured-search snapshots include the new location signal/status metadata.
- Smoke checks cover target, foreign, unknown, weak-history-only, duplicate-merge, and filter-off cases.
- One real baseline run is documented after implementation.

### Implementation result

Implemented in `app/main.py` and `app/static/app.js`.

- Runtime location config now uses `target_location_terms`; `negative_terms` no longer drives exclusion.
- Added current-location extraction from multiline LinkedIn headers and conservative one-line snippets.
- Added current-location classification: `target_location`, `foreign_current_location`, `unknown_current_location`.
- Added final location status `excluded_foreign_current_location`; this status hides the candidate before `country_domain` can allow it.
- Candidate metadata and local structured-search snapshots now include `current_location_line`, `current_location_lines`, and `current_location_classifications`.
- Frontend report label changed from `Negative location` to `Foreign location`.

### Verification result

- `python -m compileall app` passed.
- `node --check app/static/app.js` passed.
- Inline smoke check passed for:
  - `ua.linkedin.com` + `Warsaw, Poland` -> hidden;
  - `ua.linkedin.com` + `Kyiv, Ukraine` -> displayed as `target_location`;
  - `www.linkedin.com` + one-line `Kyiv, Ukraine` header -> displayed as `target_location`;
  - Ukraine only in education/history one-line text -> hidden as weak/ambiguous;
  - no clear current-location line + `ua.linkedin.com` -> displayed as `country_domain`;
  - duplicate candidate with one foreign current-location occurrence -> hidden;
  - `location_filter_enabled = false` -> filter skipped.
- Latest local snapshot replayed without a new Tavily request: `2026-05-14T17-12-12Z_structured-search_backend-developer-java-ukraine.json`.
- Snapshot replay result: `197` raw, `105` displayed occurrences, `73` unique displayed profiles.
- Displayed unique location statuses: `target_location = 71`, `country_domain = 2`.
- Known Warsaw/Poland false positives are hidden:
  - `ua.linkedin.com/in/ivan-vasylenko-java-dev` -> `excluded_foreign_current_location`;
  - `ua.linkedin.com/in/sviatoslav-konstantyniv-542744179` -> `excluded_foreign_current_location`.
- No new Tavily baseline was run in this coding pass; verification used the latest local structured-search snapshot to avoid spending extra API credits.

### Before implementation

Codex должен пересказать задачу `P2-012`, предложить точный implementation scope и дождаться явного подтверждения перед изменением кода.

---

## Task: P2-013 Improve one-line LinkedIn snippet current-location extraction

### Context

Во время no-code симуляции `P2-012` на последнем structured-search snapshot обнаружен отдельный parsing gap.

Tavily иногда возвращает LinkedIn public header не как multiline block:

```text
Name
Headline
Current location
connections/followers
```

а как compact one-line snippet:

```text
Serhii Ivanov. Java Software Developer. Kyiv, Kyiv City, Ukraine. 968 followers 500+ connections.
```

Текущий extraction лучше работает с multiline header. Для compact one-line snippets он может не выделить `current_location_line`, хотя location явно есть. В no-code симуляции это привело к `unknown_current_location = 4`.

### Goal

Улучшить extraction current-location line для compact one-line Tavily snippets, чтобы `Location filter` мог корректно классифицировать target/foreign/unknown location не только в multiline, но и в one-line формате.

Use the conservative parser variant approved after no-code testing:

- only extract one-line current location when the snippet contains social markers such as `followers`, `connections`, or `500+ connections`;
- do not extract dangling fragments such as `Kyiv,` without enough confidence;
- keep education/history/company-looking one-line snippets as `unknown_current_location` when current location cannot be isolated confidently.

### Approval

Задача и шаги одобрены пользователем.

### Proposed steps

1. Зафиксировать проблему: one-line snippets могут содержать явную current location, но текущий parser её не выделяет.

2. Собрать реальные примеры из последнего snapshot.

Examples:

```text
Serhii Ivanov. Java Software Developer. Kyiv, Kyiv City, Ukraine. 968 followers 500+ connections.
```

```text
Serhii Avakian. Java Developer. Zappysales. Dnipro, Dnipropetrovsk, Ukraine. 2K followers 500+ connections.
```

Ambiguous example:

```text
Volodymyr Maksymenko. Java Software Engineer. Finalto National Technical University of Ukraine 'Kyiv Polytechnic Institute'. Kyiv,
```

3. Define expected extraction:

```text
Kyiv, Kyiv City, Ukraine
Dnipro, Dnipropetrovsk, Ukraine
unknown / ambiguous when the location cannot be extracted confidently
```

4. Add a conservative parser path for compact one-line snippets.

If `header_location_text` is not multiline, the parser should first require a social marker such as:

```text
followers
connections
500+ connections
```

Then it should look for a location fragment before that marker.

If no social marker exists, do not extract one-line current location in this task.

5. Use target location terms as anchors.

For Ukraine, target terms include:

```text
Ukraine, Kyiv, Kiev, Lviv, Kharkiv, Odesa, Odessa, Dnipro, ...
```

6. Extract fragment boundaries carefully.

Example input:

```text
Name. Java Developer. Kyiv, Kyiv City, Ukraine. 968 followers 500+ connections.
```

Expected location fragment:

```text
Kyiv, Kyiv City, Ukraine
```

7. Stay conservative with education/history ambiguity.

Example:

```text
Finalto National Technical University of Ukraine 'Kyiv Polytechnic Institute'. Kyiv,
```

Should not be aggressively treated as current location if the parser cannot isolate a clear location fragment.

Also do not classify dangling fragments such as:

```text
Kyiv,
```

when they appear after an education/history/company-looking phrase and no social marker confirms the header shape.

8. Preserve multiline behavior.

This must continue to work:

```text
Name
Headline
Kyiv, Ukraine
500 connections
```

9. Add smoke checks:

- one-line `Kyiv, Ukraine` -> extracts `Kyiv, Ukraine`;
- one-line `Dnipro, Ukraine` -> extracts `Dnipro, Ukraine`;
- one-line `Warsaw, Poland` -> extracts `Warsaw, Poland`;
- university/history one-line with Ukraine -> stays unknown/ambiguous;
- multiline header still works;
- no location text -> unknown.

10. Test on the latest local snapshot.

Current no-code simulation before this task:

```text
unknown_current_location = 4
```

Approved conservative no-code simulation:

```text
before:
target_location = 69
unknown_current_location = 4
foreign_current_location = 2

after conservative parser:
target_location = 71
unknown_current_location = 2
foreign_current_location = 2
```

The conservative parser safely moved these two candidates from `unknown_current_location` to `target_location`:

- `Serhii Ivanov`: `Kyiv, Kyiv City, Ukraine`
- `Serhii Avakian`: `Dnipro, Dnipropetrovsk, Ukraine`

The parser intentionally kept the ambiguous `Volodymyr Maksymenko` one-line snippet unknown because `Kyiv` appears near university/history text and cannot be isolated confidently as current location.

11. Update `Tasks.md` with implementation result and measured before/after.

12. Do not change search logic:

- no Tavily query changes;
- no planner changes;
- no dedupe changes;
- no scoring changes;
- no frontend changes unless explicitly approved.

### Expected behavior

Compact one-line snippets with clear current location are classified more accurately, while ambiguous one-line snippets remain conservative.

### Constraints

- Do not log in to LinkedIn.
- Do not scrape LinkedIn.
- Do not open LinkedIn profiles automatically.
- Use only Tavily returned public fields already present in structured-search response/snapshot.
- Do not add external geocoding/location APIs.
- Do not broaden this task into Candidate Quality Layer.
- Do not change query generation or search execution.

### Acceptance criteria

- One-line snippets with clear Ukraine current location can be extracted as target location.
- One-line snippets with clear foreign current location can be extracted for `P2-012` classification.
- Ambiguous one-line snippets stay unknown/ambiguous.
- One-line extraction requires a social marker such as `followers`, `connections`, or `500+ connections`.
- Dangling fragments such as `Kyiv,` are not enough for current-location classification.
- Existing multiline header parsing still works.
- Smoke checks cover target, foreign, ambiguous education/history, multiline, and no-location cases.
- Latest snapshot simulation should match the approved conservative expectation: `unknown_current_location` decreases from `4` to `2` without classifying the ambiguous university/history example as target location.

### Implementation result

Implemented in `app/main.py`.

- Added one-line current-location extraction only when a compact snippet contains a social marker such as `followers` or `connections`.
- The parser chooses the last plausible location fragment before the social marker.
- Dangling fragments such as `Kyiv,` are rejected.
- Education/history/company-looking fragments are not treated as current location.
- Existing multiline header extraction remains supported.

### Verification result

- Inline smoke check passed for:
  - `Serhii Ivanov. Java Software Developer. Kyiv, Kyiv City, Ukraine. 968 followers 500+ connections.` -> `Kyiv, Kyiv City, Ukraine`;
  - `Serhii Avakian. Java Developer. Zappysales. Dnipro, Dnipropetrovsk, Ukraine. 2K followers 500+ connections.` -> `Dnipro, Dnipropetrovsk, Ukraine`;
  - `Ivan V. Java Developer. Warsaw, Mazowieckie, Poland. 500 connections.` -> `foreign_current_location`;
  - multiline `Warsaw, Mazowieckie, Poland` header -> `foreign_current_location`;
  - `Volodymyr Maksymenko... National Technical University of Ukraine... Kyiv,` -> `unknown_current_location` with empty `current_location_line`.
- Latest local snapshot replay produced displayed unique statuses: `target_location = 71`, `country_domain = 2`.
- The ambiguous university/history one-line example remained unknown for current-location extraction.

### Before implementation

Codex должен пересказать задачу `P2-013`, предложить точный implementation scope и дождаться явного подтверждения перед изменением кода.

---

## Task: P2-011 Добавить локальное логирование structured-search результатов для анализа

### Context

После запуска `POST /api/structured-search` результаты сейчас доступны в response и frontend, но не сохраняются локально как audit/debug snapshot.

Из-за этого нельзя надежно вернуться к последнему поиску и проверить:

- все ли показанные кандидаты действительно имеют Ukraine location signal;
- какие кандидаты прошли по `country_domain`;
- какие были rescued by header/location;
- какие были hidden by foreign current-location;
- какие query sources нашли конкретного кандидата;
- какие counts/report были у конкретного прогона.

Повторять Tavily-запрос только ради анализа нежелательно, потому что это тратит credits и может вернуть немного другую выдачу.

### Goal

Добавить локальное логирование результатов structured-search запусков, чтобы Codex и пользователь могли анализировать последний или выбранный search run без повторного Tavily-запроса.

### Approval

Задача одобрена пользователем.

### Scope

Это локальное debug/audit логирование для POC и разработки, не production logging.

Логи должны сохраняться только локально и не коммититься в git.

### Proposed behavior

После каждого успешного или частично успешного `POST /api/structured-search` backend сохраняет JSON snapshot локально.

Snapshot должен включать:

- timestamp;
- normalized request summary;
- `query_plan`;
- `report`;
- `location_filter_report`;
- `deduped_results`;
- candidate-level `query_sources`;
- candidate-level location signal metadata;
- per-query status summary;
- enough raw/public Tavily fields to audit title, snippet/content, URL, score, and source.

Snapshot не должен включать:

- API keys;
- `.env` values;
- secrets;
- unrelated machine/user data.

### Proposed local storage

Preferred directory:

```text
logs/search-runs/
```

Example filename:

```text
2026-05-14T12-30-15_structured-search_backend-developer-java-ukraine.json
```

Add the log directory to `.gitignore`.

### Expected behavior

После выполнения задачи можно открыть последний локальный run и проверить выдачу без нового Tavily-запроса.

Минимальный удобный анализ:

- найти latest snapshot;
- посмотреть summary counts;
- увидеть список displayed/deduped candidates;
- увидеть URL, title, snippet/content;
- увидеть `location_signal_status`;
- увидеть `location_signal_terms`;
- увидеть `query_sources`;
- понять, почему кандидат был показан или скрыт location filter.

### Constraints

- Не отправлять логи во внешние сервисы.
- Не сохранять secrets.
- Не коммитить generated logs.
- Не менять логику поиска, planner, scoring или фильтров в рамках этой задачи.
- Не добавлять базу данных.
- Не добавлять production observability stack.
- Не открывать LinkedIn profiles.
- Не логиниться в LinkedIn.
- Не скрейпить LinkedIn.

### Acceptance criteria

- В проекте есть локальная директория/механизм для structured-search snapshots.
- Generated logs игнорируются git.
- Каждый `POST /api/structured-search` может сохранить JSON snapshot результата.
- Snapshot содержит request summary, query plan, report, location filter report, deduped candidates, location signal metadata, and query sources.
- Snapshot не содержит API keys или secrets.
- Есть понятный способ найти последний search run.
- Логирование не меняет поисковую выдачу.
- Если запись snapshot не удалась, сам search response не должен падать только из-за logging failure; ошибка логирования должна быть безопасной и диагностируемой.

### Before implementation

Codex должен пересказать задачу `P2-011`, предложить точный implementation scope и дождаться явного подтверждения перед изменением кода.

### Implementation result

`P2-011` выполнена.

Добавлено:

- локальная директория snapshots: `logs/search-runs/`;
- `.gitignore` правило для generated structured-search logs;
- backend helper `write_structured_search_snapshot(...)`;
- JSON snapshot после `POST /api/structured-search`;
- snapshot fields: timestamp, normalized request, `query_plan`, `report`, `location_filter_report`, `deduped_results`, `query_results_summary`, and `query_results`;
- safe logging behavior: failure to write a snapshot does not fail the search response.

Не добавлено в рамках `P2-011`:

- production logging;
- external log shipping;
- database storage;
- frontend changes;
- search, planner, filter, or scoring changes.

Checks passed:

- `.venv\Scripts\python.exe -m compileall app`;
- `node --check app/static/app.js`;
- mocked structured-search smoke created a local snapshot without Tavily credits;
- snapshot did not contain the test API key value;
- generated snapshot is ignored by git.

---

## Task: P2-010 Зафиксировать выводы Phase 2 и подготовить место под AI Planner

### Context

Phase 2 довела продукт от одного ручного запроса до planner-based multi-query pipeline:

- structured inputs;
- `QueryPlanner v1`;
- 10 focused Tavily queries;
- sequential executor;
- normalization and dedupe by normalized LinkedIn profile URL;
- query source metadata;
- report/counts;
- frontend diagnostic panel;
- configurable `Location filter`.

### Goal

Закрыть Phase 2 как завершенную фазу и зафиксировать, что следующий шаг должен быть выбран осознанно: либо идти в AI Query Planner, либо сначала улучшать качество кандидатов.

### Final Phase 2 result

Baseline input:

```json
{
  "role_family": "Backend Developer",
  "technology": "Java",
  "stack": ["Spring", "Kafka", "AWS"],
  "location": "Ukraine",
  "linkedin_profiles_only": true,
  "location_filter_enabled": true
}
```

Final measured result:

- `200` raw Tavily results;
- `58` unique candidates after filters and dedupe;
- `9` unique non-UA profiles rescued by header/location signal;
- historical `P2-009.1`: `2` unique profiles excluded by explicit negative header/location signal;
- Phase 2 success criterion passed: `58` unique vs target `20`.

Current note after `P2-012`/`P2-013`: the old explicit negative term logic is superseded by current-location classification. The current hide status is `excluded_foreign_current_location`, and the current report field is `hidden_by_foreign_current_location`.

### Conclusions

- Multi-query search is better than one broad universal query for the tested Java/Ukraine scenario.
- `QueryPlan` is the right architectural contract: it lets us replace `RuleBasedQueryPlanner` with `AIQueryPlanner` later without rewriting executor, dedupe, report, or frontend.
- `Location filter` should stay visible and configurable, not hidden backend behavior.
- Country-domain LinkedIn URL is useful, but only one signal.
- Explicit foreign current location must beat country-domain signals.
- Tavily snippets are enough for a working baseline, but not enough for high-confidence final candidate qualification.
- Tavily live result sets vary between runs; use local snapshots for deterministic analysis.
- Phase 2 should not be expanded further before choosing the next product direction.

### Known limitations carried forward

- `name` extraction remains weak and often returns `unknown`.
- Location confidence is heuristic and based only on Tavily public snippets/content.
- Stack fit is not yet scored deeply.
- Seniority is not modeled.
- No database, shortlist, export, CRM workflow, auth, or saved searches.
- No AI planner yet.
- No LinkedIn login, scraping, bypass, or direct profile automation.

### Next phase order

Phase 3: `Candidate Quality Layer`

- Improve name extraction.
- Improve location confidence.
- Add stack/seniority scoring.
- Improve ranking and candidate diagnostics.
- Add adaptive multi-wave runner for quality evaluation.
- Keep query generation rule-based for now.

Phase 4: `AI Agent Foundation`

- Keep the existing `QueryPlan` contract.
- Add an AI planner that proposes query slots from structured inputs as one agent tool.
- Add a `Search Brief` and approval flow before Tavily execution.
- Require explanation/debug metadata for generated queries.
- Compare AI-generated plans against `RuleBasedQueryPlanner v1`.

### Decision

Phase 2 is closed. Phase 3 is selected as Candidate Quality Layer. AI Agent Foundation is deferred to Phase 4.

### Implementation result

`P2-010` выполнена как документационное закрытие Phase 2.

Updated documents:

- `Tasks.md`: `P2-010` moved to Done and documented.
- `Roadmap.md`: Phase 2 marked as completed, final result and next phase order added.
- `ProjectStatus.md`: current phase updated to Phase 2 completed, with Phase 3 selected and AI Query Planner deferred to Phase 4.

No code changes were made for `P2-010`.

---

## Task: P2-001 Зафиксировать QueryPlan и baseline planner v1

### Context

Phase 1.1 показала, что один широкий универсальный Boolean-запрос не является лучшей стратегией для покрытия кандидатов.

Для Java/Ukraine сценария несколько focused queries дали больше уникальных `ua.linkedin.com/in/...` профилей, чем один общий запрос. Дополнительные эксперименты показали, что полезнее фиксировать не конкретный хардкод `Java + Ukraine`, а понятный `QueryPlan`, который генерируется из клиентских вводных.

Конечная цель продукта - AI агент для поиска. Но в Phase 2 не нужно сразу отдавать формирование запросов свободной AI-логике. Более надежный шаг: сделать `QueryPlanner v1` как rule-based baseline planner, который строит план из полей клиента. Позже его можно заменить на `AIQueryPlanner`, не переписывая executor, dedupe, counts и frontend reporting.

### Goal

Зафиксировать структуру `QueryPlan` и правила `baseline planner v1`, чтобы Phase 2 строила 10 focused Tavily queries из клиентских вводных, а не из ручного одноразового списка.

### Constraints

- Не писать backend runner в рамках `P2-001`.
- Не менять frontend в рамках `P2-001`.
- Не менять существующую Phase 1.1 search behavior.
- Не реализовывать AI planner в рамках `P2-001`.
- Не хардкодить `Java + Ukraine` как финальную бизнес-логику.
- Не добавлять LinkedIn login, scraping, bypass, database, shortlist, AI agent или multi-source search beyond Tavily.
- Не считать задачу завершенной, пока стратегия не просмотрена и явно не принята.

### Proposed steps

1. Зафиксировать смысл Phase 2: planner-based multi-query search, где `QueryPlanner v1` генерирует `QueryPlan`, а не пользователь вручную ведет один Boolean query.

2. Зафиксировать первую структуру клиентского запроса:

- `Role Family`: обязательный single-select.
- Первый поддерживаемый `Role Family`: `Backend Developer`.
- `Technology`: обязательный single-select, который показывается после выбора `Backend Developer`.
- Поддерживаемые технологии для `Backend Developer`:
  - `Java`
  - `Python`
  - `Node.js`
  - `C#`
  - `Go`
  - `PHP`
- После выбора `Technology = Java` показывается Java-related stack multi-select.
- Клиент обязан выбрать минимум 1 и максимум 3 значения из Java-related stack.
- Поддерживаемые значения Java-related stack:
  - `Spring`
  - `Spring Boot`
  - `Hibernate`
  - `Kafka`
  - `PostgreSQL`
  - `AWS`
  - `Docker`
  - `Kubernetes`
  - `Microservices`
  - `REST`

3. Зафиксировать conceptual contract `QueryPlan`:

- `planner_version`: например `rule_based_v1`.
- `input_snapshot`: исходные поля клиента.
- `queries`: список query slots.
- `filters`: явно выбранные фильтры, например `LinkedIn profiles only`, `Ukraine LinkedIn domain only`.
- `execution`: sequential execution, `max_results` на каждый query.
- `reporting`: какие counts и query source metadata нужно вернуть.

4. Зафиксировать conceptual contract одного query slot:

- `id`: стабильный ID, например `Q01`.
- `query`: Tavily Boolean query.
- `category`: например `role_based`, `backend_role`, `stack_focused`, `fallback`.
- `purpose`: короткое объяснение, зачем этот query нужен.
- `uses_stack`: какие выбранные stack items участвуют в query.
- `max_results`: на первом этапе `20`.

5. Зафиксировать правила `QueryPlanner v1` для `Backend Developer + Java`:

- План строит 10 query slots.
- Каждый query содержит `site:linkedin.com/in`.
- Каждый query содержит выбранную локацию; location не выкидывается ни из одного query.
- Основу плана дают короткие role-based phrases.
- Stack используется в отдельных stack-focused query slots.
- Все выбранные клиентом stack-технологии должны участвовать в stack-focused slots.
- Если Java-related stack не выбран, planner не запускается и возвращается validation error.
- Не добавлять seniority вроде `Senior`, `Middle`, `Lead`, если клиент явно не выбрал seniority.
- Не строить один большой OR-query как основной способ поиска.

6. Зафиксировать baseline role phrases для Java Backend:

- `Java Developer`
- `Java Software Engineer`
- `Java Backend Engineer`
- `Java Engineer`
- `Java Programmer`
- `Java Application Developer`

7. Зафиксировать baseline 10-query pattern для Java Backend:

```text
Q01: site:linkedin.com/in AND "Java Developer" AND "{location}"
Q02: site:linkedin.com/in AND "Java Software Engineer" AND "{location}"
Q03: site:linkedin.com/in AND "Java Backend Engineer" AND "{location}"
Q04: site:linkedin.com/in AND "Java Engineer" AND "{location}"
Q05: site:linkedin.com/in AND "Java Programmer" AND "{location}"
Q06: site:linkedin.com/in AND "Java Application Developer" AND "{location}"
Q07: site:linkedin.com/in AND "Java Developer" AND {stack_or} AND "{location}"
Q08: site:linkedin.com/in AND "Java Engineer" AND {stack_or} AND "{location}"
Q09: site:linkedin.com/in AND "Java Backend Engineer" AND {stack_or} AND "{location}"
Q10: site:linkedin.com/in AND "Java Application Developer" AND {stack_or} AND "{location}"
```

8. Зафиксировать stack selection rule:

- Java-related stack обязателен: минимум 1, максимум 3 значения.
- Если выбран 1 stack item, `{stack_or}` равен одному quoted value, например `"Spring"`.
- Если выбрано 2 stack items, `{stack_or}` строится через OR, например `("Spring" OR "Kafka")`.
- Если выбрано 3 stack items, `{stack_or}` строится через OR по всем трем значениям, например `("Spring" OR "AWS" OR "Kafka")`.
- Если stack не выбран, planner не строит `QueryPlan` и возвращает validation error.

9. Зафиксировать location rule v1: `{location}` берется из клиентского поля как обязательный query anchor и вставляется в каждый query как quoted phrase. `Location aliases` и country-specific domain filters считаются отдельными механизмами и не смешиваются с базовым rule-based planner без отдельного решения.

10. Зафиксировать режим выполнения: sequential Tavily requests, `max_results=20` на каждый query, без parallel execution на первом этапе. Ошибка одного query не должна валить весь поиск: успешные query объединяются, а ошибка конкретного query попадает в report.

11. Зафиксировать baseline-фильтры для проверки Java/Ukraine: `LinkedIn profiles only = on`, `Ukraine LinkedIn domain only = on`. Planner только строит queries; visible filters применяются после Tavily и не включаются скрыто.

12. Зафиксировать правило dedupe: главным ключом является normalized LinkedIn profile URL. Нормализация: lowercase host, убрать `www.`, убрать trailing slash, убрать query params и fragments, сохранить country subdomain. Если один профиль найден несколькими query, оставить одного кандидата и объединить metadata.

13. Зафиксировать query source metadata: у каждого кандидата сохраняются query sources, из которых он пришел. Минимум: query `id`, `category`, `matched_query`. В UI v1 можно показывать коротко `Found by: Q02, Q07`, а полный query держать в details/debug.

14. Зафиксировать counts/report для Phase 2 baseline: `queries_total`, `queries_succeeded`, `queries_failed`, `raw_total`, `normalized_total`, `unique_profiles`, `duplicates_removed`, `displayed`, `hidden_by_profile_filter`, `hidden_by_location_domain_filter`, `query_contribution`. В `query_contribution` фиксировать минимум query `id`, `raw`, `displayed_before_dedupe`, `new_unique_profiles`, `duplicates`, `error`.

15. Зафиксировать экспериментальный ориентир: исправленный 10-query шаблон для `Java + Ukraine + Spring/AWS/Kafka` дал 60 уникальных `ua.linkedin.com/in/...` профилей после dedupe.

16. Зафиксировать критерий успеха: для baseline Java/Ukraine `QueryPlanner v1` генерирует 10 queries из клиентских вводных, runner выполняет их sequentially, после фильтров и dedupe получается минимум 20 уникальных `ua.linkedin.com/in/...` профилей, а UI/report показывает generated queries, counts, query contribution и deduped candidates.

17. Зафиксировать границы Phase 2: без LinkedIn login, scraping, database, shortlist, AI agent, AI query planner implementation и multi-source search beyond Tavily.

18. Сохранить стратегию прямо в блоке `P2-001` в `Tasks.md` и использовать его как рабочий draft до финального утверждения.

### Expected behavior

После выполнения `P2-001` в проекте есть понятная и согласованная стратегия Phase 2:

- как выглядит клиентский search request;
- как выглядит `QueryPlan`;
- как выглядит один query slot;
- как `QueryPlanner v1` строит 10 queries для Java Backend;
- почему это baseline planner, а не финальный AI agent;
- как объединяются результаты;
- как считается уникальность кандидатов;
- какие фильтры используются в baseline-прогоне;
- какие counts/report должен вернуть backend;
- по какому критерию Phase 2 считается успешной;
- как позже заменить rule-based planner на AI planner без переписывания остального pipeline.

### Acceptance criteria

- Создан или обновлен подробный блок `P2-001` в `Tasks.md`.
- В стратегии явно указано, что Phase 2 строится вокруг `QueryPlan` и `QueryPlanner v1`.
- В стратегии явно указана первая структура клиентского запроса: `Role Family -> Technology -> Related stack`.
- В стратегии явно указано, что `Role Family` является обязательным single-select.
- В стратегии явно указано, что первый поддерживаемый `Role Family`: `Backend Developer`.
- В стратегии явно указано, что `Technology` является обязательным single-select.
- В стратегии перечислены поддерживаемые технологии для `Backend Developer`: `Java`, `Python`, `Node.js`, `C#`, `Go`, `PHP`.
- В стратегии явно указано, что для `Technology = Java` показывается Java-related stack multi-select.
- В стратегии явно указано, что клиент обязан выбрать минимум 1 и максимум 3 значения из Java-related stack.
- В стратегии перечислены значения Java-related stack: `Spring`, `Spring Boot`, `Hibernate`, `Kafka`, `PostgreSQL`, `AWS`, `Docker`, `Kubernetes`, `Microservices`, `REST`.
- В стратегии описан conceptual contract `QueryPlan`.
- В стратегии описан conceptual contract одного query slot.
- В стратегии явно указаны правила `QueryPlanner v1` для `Backend Developer + Java`.
- В стратегии явно указан baseline 10-query pattern для Java Backend.
- В стратегии явно указано, как selected stack участвует в stack-focused query slots.
- В стратегии явно указано, что если Java-related stack не выбран, planner возвращает validation error.
- В стратегии явно указано, что location является обязательным query anchor и остается в каждом query.
- В стратегии явно указано, что seniority не добавляется без явного выбора клиента.
- В стратегии явно указано, что `QueryPlanner v1` не является AI planner.
- В стратегии явно указано, что первый runner выполняет queries sequentially через Tavily.
- В стратегии явно указано, что ошибка одного query не валит весь поиск и попадает в report.
- В стратегии явно указано, что `max_results=20` применяется к каждому query.
- В стратегии описано правило normalized LinkedIn URL для dedupe.
- В стратегии описана query source metadata для кандидатов.
- В стратегии перечислены counts/report для multi-query выдачи.
- В стратегии зафиксирован критерий успеха: не менее 20 уникальных украинских LinkedIn-профилей после dedupe.
- В стратегии явно перечислены out-of-scope пункты Phase 2.

### Before implementation

Codex должен пересказать стратегию `P2-001`, показать draft пользователю и дождаться явного подтверждения перед тем, как считать задачу выполненной или переходить к `P2-002`.

### Decision result

`P2-001` выполнена как документационная задача. Согласованы и записаны:

- Phase 2 строится вокруг `QueryPlan` и `QueryPlanner v1`.
- `QueryPlanner v1` является rule-based baseline planner, а не AI planner.
- Первый supported flow: `Backend Developer -> Java -> Java-related stack -> Location`.
- Java-related stack обязателен: минимум 1, максимум 3 значения.
- Location является обязательным query anchor и остается в каждом query.
- Утвержден baseline 10-query pattern для Java Backend.
- Утверждены `QueryPlan`, query slot contract, execution mode, visible filters, dedupe, query source metadata, counts/report, success criteria и out-of-scope границы.

---

## Task: P2-002 Добавить входную модель поиска: Role Family, Technology, Stack, Location

### Context

`P2-001` зафиксировала, что Phase 2 строится вокруг `QueryPlan` и `QueryPlanner v1`. Перед реализацией planner нужно добавить структурированную входную модель поиска, которую frontend будет отправлять в backend.

Phase 1.1 single-query POC считается завершенным прототипом. Phase 2 заменяет этот flow planner-based structured search. Single-query search не нужно сохранять как отдельный поддерживаемый пользовательский режим, если он мешает новой архитектуре. Полезные части Phase 1.1 можно переиспользовать, менять или удалять по мере необходимости.

### Goal

Добавить входную модель `StructuredSearchRequest` и endpoint валидации, чтобы backend мог принимать, нормализовать и проверять structured search input до построения `QueryPlan`.

### Constraints

- Не строить `QueryPlan` в рамках `P2-002`.
- Не реализовывать `QueryPlanner v1` в рамках `P2-002`.
- Не запускать Tavily в рамках `P2-002`.
- Не реализовывать multi-query runner в рамках `P2-002`.
- Не менять frontend в рамках `P2-002`, если отдельно не согласовано.
- Не добавлять AI planner, LinkedIn login, scraping, bypass, database, shortlist или multi-source search beyond Tavily.
- `max_results_per_query` не должен входить в `StructuredSearchRequest`; Tavily execution v1 всегда использует `max_results = 20` per query.

### Proposed steps

1. Зафиксировать replacement scope: Phase 2 заменяет Phase 1.1 single-query POC flow. Single-query search не обязан оставаться поддерживаемым пользовательским режимом.

2. Добавить backend model `StructuredSearchRequest` со следующими полями:

- `role_family`
- `technology`
- `stack`
- `location`
- `linkedin_profiles_only`
- `location_domain_only`

3. Зафиксировать смысл pipeline:

```text
StructuredSearchRequest -> QueryPlanner v1 -> QueryPlan
```

4. Добавить validation rules:

- `role_family` required.
- `role_family` v1 поддерживает только `Backend Developer`.
- `technology` required.
- Для `Backend Developer` известны технологии: `Java`, `Python`, `Node.js`, `C#`, `Go`, `PHP`.
- В Phase 2 planner реально поддерживает только `Backend Developer + Java`.
- Если выбрана известная, но еще не реализованная технология, например `Python`, backend возвращает понятную ошибку: `Technology is known but planner is not implemented yet.`
- `location` required.
- `location` не может быть пустой строкой.
- Для `technology = Java` поле `stack` required.
- Java stack: min 1, max 3, only from allowed Java stack list.
- Если `stack` не выбран, backend возвращает validation error: `At least one Java stack item is required.`
- Если `stack` содержит больше 3 значений, backend возвращает validation error: `Java stack supports up to 3 selected items.`
- Если `stack` содержит значение не из allowed list, backend возвращает validation error: `Unsupported Java stack item.`
- `linkedin_profiles_only` boolean.
- `location_domain_only` boolean.

5. Зафиксировать allowed Java stack values:

- `Spring`
- `Spring Boot`
- `Hibernate`
- `Kafka`
- `PostgreSQL`
- `AWS`
- `Docker`
- `Kubernetes`
- `Microservices`
- `REST`

6. Зафиксировать filter defaults:

- `linkedin_profiles_only = true` by default.
- `location_domain_only = true` by default for Ukraine baseline.
- Для не-Ukraine location `location_domain_only = false` до расширения country-domain mapping.
- Future requirement: для будущих стран отдельно расширить country-domain mapping, например `Ukraine -> ua.linkedin.com`, `Poland -> pl.linkedin.com`, `Germany -> de.linkedin.com`.

7. Добавить endpoint:

```text
POST /api/structured-search/validate
```

Endpoint должен:

- принимать `StructuredSearchRequest`;
- валидировать поля;
- возвращать `normalized_request`;
- не строить `QueryPlan`;
- не запускать Tavily;
- не менять текущие результаты поиска.

8. Зафиксировать пример успешного ответа:

```json
{
  "ok": true,
  "normalized_request": {
    "role_family": "Backend Developer",
    "technology": "Java",
    "stack": ["Spring", "AWS", "Kafka"],
    "location": "Ukraine",
    "linkedin_profiles_only": true,
    "location_domain_only": true
  }
}
```

9. Зафиксировать пример ошибки:

```json
{
  "ok": false,
  "errors": [
    {
      "field": "stack",
      "message": "At least one Java stack item is required."
    }
  ]
}
```

10. Добавить normalization rules:

- `role_family`: trim whitespace, match against allowed values, return canonical value.
- `technology`: trim whitespace, case-insensitive match, return canonical value.
- `stack`: trim each item, case-insensitive match, remove duplicates, preserve client input order, return canonical values.
- `location`: trim whitespace only; do not translate, resolve aliases, or change meaning in `P2-002`.
- `linkedin_profiles_only`: default `true` if omitted.
- `location_domain_only`: default `true` only when location is `Ukraine`; otherwise `false` until country-domain mapping is expanded.

11. Add backend smoke checks for:

- valid Java request;
- trim/case normalization;
- missing stack;
- too many stack items;
- unsupported stack item;
- known but not implemented technology;
- unsupported role family;
- missing/empty location;
- non-Ukraine filter defaults.

12. Обновить `Tasks.md` после реализации:

- перенести `P2-002` из Backlog в Done;
- добавить `Implementation result`;
- записать smoke-check results;
- явно указать, что `QueryPlan` еще не строится и Tavily еще не вызывается.

### Expected behavior

После выполнения `P2-002` backend умеет принимать structured search input, возвращать normalized request или понятные validation errors. Это подготавливает `P2-003`, где `StructuredSearchRequest` будет превращаться в `QueryPlan`.

### Acceptance criteria

- Добавлена модель `StructuredSearchRequest`.
- `StructuredSearchRequest` содержит только согласованные поля: `role_family`, `technology`, `stack`, `location`, `linkedin_profiles_only`, `location_domain_only`.
- `max_results_per_query` не входит во входную модель клиента.
- Реализована validation для required fields.
- Реализована validation для supported `Role Family`.
- Реализована validation для known technologies и not implemented technologies.
- Реализована validation для Java stack min 1 / max 3.
- Реализована validation allowed Java stack values.
- Реализована normalization с trim, case-insensitive enum matching и stack dedupe.
- `location` только trim, без aliases/translation.
- Defaults фильтров соответствуют согласованным правилам.
- Добавлен endpoint `POST /api/structured-search/validate`.
- Endpoint не строит `QueryPlan`.
- Endpoint не запускает Tavily.
- Добавлены или выполнены backend smoke checks по согласованным сценариям.

### Before implementation

Codex должен пересказать задачу `P2-002`, показать точный implementation scope пользователю и дождаться явного подтверждения перед изменением кода.

### Implementation result

`P2-002` выполнена.

Добавлено:

- backend model `StructuredSearchRequest`;
- endpoint `POST /api/structured-search/validate`;
- validation для `role_family`, `technology`, `stack`, `location`;
- normalization с trim, case-insensitive enum matching и stack dedupe;
- default filters:
  - `linkedin_profiles_only = true`;
  - `location_domain_only = true` only for `Ukraine`;
  - `location_domain_only = false` for non-Ukraine locations until country-domain mapping is expanded;
- validation response shape with `ok`, `normalized_request` or `errors`.

Не добавлено в рамках `P2-002`:

- `QueryPlan` generation;
- `QueryPlanner v1`;
- Tavily calls;
- multi-query runner;
- frontend changes.

Smoke checks passed:

- valid Java request;
- trim/case normalization;
- missing stack;
- too many stack items;
- unsupported stack item;
- known but not implemented technology;
- unsupported role family;
- missing/empty location;
- non-Ukraine filter defaults.

---

## Task: P2-003 Реализовать Rule-based Query Planner v1 для Java Backend

### Context

`P2-002` добавила `StructuredSearchRequest` и endpoint валидации. Следующий шаг - превратить валидный structured input в `QueryPlan`, но пока без Tavily и без multi-query runner.

`P2-003` реализует только rule-based planner v1 для согласованного flow:

```text
Backend Developer + Java + Java-related stack + Location
```

### Goal

Добавить явный backend planner-компонент `RuleBasedQueryPlannerV1`, который принимает normalized `StructuredSearchRequest` и строит `QueryPlan` из 10 query slots по утвержденному Java Backend шаблону.

Важно: planner должен быть оформлен как отдельная заменяемая часть pipeline, а не как скрытая ad hoc функция. Это нужно, чтобы позже можно было заменить `RuleBasedQueryPlannerV1` на `AIQueryPlanner` без переписывания validation, endpoint, runner, dedupe и reporting.

### Constraints

- Не запускать Tavily в рамках `P2-003`.
- Не реализовывать multi-query runner в рамках `P2-003`.
- Не делать dedupe/merge результатов в рамках `P2-003`.
- Не менять frontend в рамках `P2-003`, если отдельно не согласовано.
- Не реализовывать AI planner.
- Planner v1 поддерживает только `Backend Developer + Java`.
- Каждый query должен содержать `site:linkedin.com/in`.
- Каждый query должен содержать выбранную location.
- `max_results` каждого query slot равен `20`.

### Proposed steps

1. Добавить явный planner-компонент `RuleBasedQueryPlannerV1`, который принимает normalized structured request и строит `QueryPlan`.

2. Зафиксировать `planner_version`:

```text
rule_based_v1
```

3. QueryPlan response должен содержать:

- `planner_version`
- `input_snapshot`
- `queries`
- `filters`
- `execution`
- `reporting`

4. Каждый query slot должен содержать:

- `id`
- `category`
- `purpose`
- `query`
- `uses_stack`
- `max_results`

5. Реализовать 10 query slots:

```text
Q01: site:linkedin.com/in AND "Java Developer" AND "{location}"
Q02: site:linkedin.com/in AND "Java Software Engineer" AND "{location}"
Q03: site:linkedin.com/in AND "Java Backend Engineer" AND "{location}"
Q04: site:linkedin.com/in AND "Java Engineer" AND "{location}"
Q05: site:linkedin.com/in AND "Java Programmer" AND "{location}"
Q06: site:linkedin.com/in AND "Java Application Developer" AND "{location}"
Q07: site:linkedin.com/in AND "Java Developer" AND {stack_or} AND "{location}"
Q08: site:linkedin.com/in AND "Java Engineer" AND {stack_or} AND "{location}"
Q09: site:linkedin.com/in AND "Java Backend Engineer" AND {stack_or} AND "{location}"
Q10: site:linkedin.com/in AND "Java Application Developer" AND {stack_or} AND "{location}"
```

6. Реализовать `stack_or`:

- 1 stack: `"Spring"`
- 2 stack: `("Spring" OR "Kafka")`
- 3 stack: `("Spring" OR "AWS" OR "Kafka")`

7. Добавить endpoint:

```text
POST /api/query-plan
```

Endpoint должен:

- принимать `StructuredSearchRequest`;
- использовать validation/normalization из `P2-002`;
- возвращать validation errors, если input невалидный;
- строить `QueryPlan` через `RuleBasedQueryPlannerV1`, если input валидный;
- не запускать Tavily.

8. Зафиксировать `execution`:

```json
{
  "mode": "sequential",
  "max_results_per_query": 20
}
```

9. Зафиксировать `filters` из normalized request:

- `linkedin_profiles_only`
- `location_domain_only`

10. Зафиксировать `reporting` как список ожидаемых report fields для будущего runner:

- `queries_total`
- `queries_succeeded`
- `queries_failed`
- `raw_total`
- `normalized_total`
- `unique_profiles`
- `duplicates_removed`
- `displayed`
- `hidden_by_profile_filter`
- `hidden_by_location_domain_filter`
- `query_contribution`

11. Добавить smoke checks:

- valid 1-stack request;
- valid 2-stack request;
- valid 3-stack request;
- location remains in every query;
- no stack returns validation error;
- Python returns not implemented validation error;
- query count is 10;
- every query has `site:linkedin.com/in`;
- every query has `max_results=20`.

12. Обновить `Tasks.md` после реализации:

- перенести `P2-003` из Backlog в Done;
- добавить `Implementation result`;
- записать smoke-check results;
- явно указать, что Tavily еще не вызывается и multi-query runner еще не реализован.

### Expected behavior

После выполнения `P2-003` backend умеет строить прозрачный `QueryPlan` для Java Backend поиска. Пользователь или frontend/debug tooling может увидеть, какие 10 Tavily queries будут выполнены позже, но реальный поиск еще не запускается.

### Acceptance criteria

- Добавлен явный planner-компонент `RuleBasedQueryPlannerV1`.
- Endpoint `/api/query-plan` строит plan через `RuleBasedQueryPlannerV1`, а не через скрытую ad hoc функцию.
- Planner-компонент отделен так, чтобы позже его можно было заменить на `AIQueryPlanner` без переписывания validation/runner/dedupe/report.
- Добавлен endpoint `POST /api/query-plan`.
- Endpoint принимает `StructuredSearchRequest`.
- Endpoint переиспользует validation/normalization из `P2-002`.
- Endpoint возвращает validation errors для невалидного input.
- Endpoint возвращает `QueryPlan` для валидного `Backend Developer + Java` input.
- QueryPlan содержит `planner_version`, `input_snapshot`, `queries`, `filters`, `execution`, `reporting`.
- QueryPlan содержит ровно 10 query slots.
- Каждый query slot содержит `id`, `category`, `purpose`, `query`, `uses_stack`, `max_results`.
- Каждый query содержит `site:linkedin.com/in`.
- Каждый query содержит выбранную location.
- Stack-focused queries используют корректный `stack_or`.
- Tavily не вызывается.
- Multi-query runner не реализуется.
- Smoke checks passed.

### Before implementation

Codex должен пересказать задачу `P2-003`, показать точный implementation scope пользователю и дождаться явного подтверждения перед изменением кода.

### Implementation result

`P2-003` выполнена.

Добавлено:

- explicit `RuleBasedQueryPlannerV1` planner component for Java Backend;
- `/api/query-plan` builds plan through `RuleBasedQueryPlannerV1`;
- endpoint `POST /api/query-plan`;
- `planner_version = rule_based_v1`;
- `QueryPlan` response with `input_snapshot`, `queries`, `filters`, `execution`, `reporting`;
- 10 query slots `Q01` through `Q10`;
- stack-focused query slots using `{stack_or}`;
- `execution.mode = sequential`;
- `execution.max_results_per_query = 20`;
- report field list for the future runner.

Не добавлено в рамках `P2-003`:

- Tavily calls;
- multi-query runner;
- merge/dedupe over real Tavily results;
- frontend changes;
- AI planner.

Smoke checks passed:

- valid 1-stack request;
- valid 2-stack request;
- valid 3-stack request;
- location remains in every query;
- no stack returns validation error;
- Python returns not implemented validation error;
- query count is 10;
- every query has `site:linkedin.com/in`;
- every query has `max_results=20`;
- `P2-002` validation endpoint still passes key smoke checks.

---

## Task: P2-004 Добавить backend multi-query runner для QueryPlan

### Context

`P2-003` добавила `RuleBasedQueryPlannerV1` и endpoint `/api/query-plan`, который строит `QueryPlan`, но не запускает Tavily. Следующий шаг - добавить backend runner, который выполняет queries из `QueryPlan`.

`P2-004` должен запускать query slots и возвращать результаты, сгруппированные по `query_id`. Он еще не создает deduped candidate objects и не добавляет `query_sources` на уровне кандидата.

### Goal

Добавить backend endpoint, который принимает `StructuredSearchRequest`, строит `QueryPlan`, последовательно запускает 10 Tavily queries и возвращает `query_plan` вместе с per-query raw results.

### Constraints

- Делать только runner.
- Не делать dedupe.
- Не делать merge в единый candidate list.
- Не делать query source metadata на уровне кандидата.
- Не делать финальный counts/report.
- Не менять frontend в рамках `P2-004`, если отдельно не согласовано.
- Не добавлять AI planner.
- Не удалять `/api/search` специально в рамках `P2-004`.

### Proposed steps

1. Добавить endpoint:

```text
POST /api/structured-search
```

2. Endpoint принимает `StructuredSearchRequest`.

3. Flow endpoint:

```text
validate/normalize StructuredSearchRequest
-> RuleBasedQueryPlannerV1.build(...)
-> QueryPlan
-> sequential Tavily calls for each query slot
-> return query_plan + per-query results
```

4. Tavily execution для каждого query slot:

- `search_depth = basic`
- `topic = general`
- `max_results = query_slot.max_results`, то есть `20`
- `include_answer = false`
- `include_raw_content = false`
- `include_images = false`
- `include_favicon = false`
- `include_domains = ["linkedin.com"]`
- `include_usage = true`

5. Ошибка одного query не валит весь search:

- если один query упал, runner продолжает следующие queries;
- failed query получает `ok: false` и `error`;
- успешные query возвращают свои results;
- общий response `ok: true`, если хотя бы один query успешно выполнен;
- если все queries упали, общий response `ok: false`.

6. Response shape:

```json
{
  "ok": true,
  "query_plan": {},
  "query_results": [
    {
      "query_id": "Q01",
      "category": "role_based",
      "query": "site:linkedin.com/in AND \"Java Developer\" AND \"Ukraine\"",
      "ok": true,
      "raw_results": [],
      "raw_count": 20,
      "response_time": 1.23,
      "usage": {},
      "request_id": "...",
      "error": null
    }
  ]
}
```

7. Для validation errors возвращать:

```json
{
  "ok": false,
  "errors": [...]
}
```

и Tavily не вызывать.

8. Если `TAVILY_API_KEY` отсутствует:

- не запускать runner;
- возвращать понятную ошибку.

9. Переиспользовать существующий Tavily call pattern из `/api/search`, но вынести в helper:

```text
run_tavily_query(query_slot)
```

10. Smoke checks:

- validation error не вызывает Tavily;
- missing API key возвращает понятную ошибку;
- valid request строит `QueryPlan`;
- valid request запускает 10 query slots;
- каждый result связан с `query_id`;
- если один mocked query падает, остальные продолжаются;
- если все mocked queries падают, общий response `ok: false`;
- `max_results=20` у каждого Tavily payload.

11. Обновить `Tasks.md` после реализации:

- перенести `P2-004` из Backlog в Done;
- добавить `Implementation result`;
- записать проверки;
- явно указать, что dedupe, merge, candidate-level query source metadata и финальный counts/report еще не реализованы.

### Expected behavior

После выполнения `P2-004` backend умеет выполнять весь `QueryPlan` через Tavily sequentially и возвращать per-query results. Это подготавливает `P2-005`, где результаты будут нормализованы и deduped.

### Acceptance criteria

- Добавлен endpoint `POST /api/structured-search`.
- Endpoint принимает `StructuredSearchRequest`.
- Endpoint переиспользует validation/normalization из `P2-002`.
- Endpoint строит `QueryPlan` через `RuleBasedQueryPlannerV1`.
- Endpoint sequentially запускает Tavily для каждого query slot.
- Каждый per-query result содержит `query_id`, `category`, `query`, `ok`, `raw_results`, `raw_count`, `response_time`, `usage`, `request_id`, `error`.
- Ошибка одного query не валит весь runner.
- Если все queries упали, общий response `ok: false`.
- Если хотя бы один query успешен, общий response `ok: true`.
- Validation errors не вызывают Tavily.
- Missing API key возвращает понятную ошибку.
- Dedupe не реализован в рамках `P2-004`.
- Candidate-level query source metadata не реализована в рамках `P2-004`.
- Финальный counts/report не реализован в рамках `P2-004`.
- Smoke checks passed.

### Before implementation

Codex должен пересказать задачу `P2-004`, показать точный implementation scope пользователю и дождаться явного подтверждения перед изменением кода.

### Implementation result

`P2-004` выполнена.

Добавлено:

- endpoint `POST /api/structured-search`;
- shared Tavily helper for single-query and structured runner flows;
- sequential runner over all query slots from `QueryPlan`;
- per-query result blocks with `query_id`, `category`, `query`, `ok`, `raw_results`, `raw_count`, `response_time`, `usage`, `request_id`, `error`;
- query-level error handling that continues running following query slots;
- overall `ok = true` when at least one query succeeds;
- overall `ok = false` when all query slots fail;
- missing API key validation before runner execution.

Не добавлено в рамках `P2-004`:

- dedupe;
- merge into one candidate list;
- candidate-level query source metadata;
- final counts/report;
- frontend changes;
- AI planner.

Smoke checks passed:

- validation error does not call Tavily;
- missing API key returns a clear error;
- valid request builds `QueryPlan`;
- valid request runs 10 query slots;
- each result is linked to `query_id`;
- one mocked query failure does not stop remaining queries;
- all mocked queries failed returns `ok: false`;
- each Tavily payload uses `max_results=20`.

---

## Task: P2-005 Добавить нормализацию LinkedIn URL и dedupe

### Context

`P2-004` добавила runner, который возвращает результаты по каждому query slot отдельно. Один и тот же LinkedIn profile может быть найден несколькими query, поэтому следующий шаг - нормализовать LinkedIn profile URLs и убрать дубли.

`P2-005` добавляет технический dedupe, но еще не делает полноценную candidate-level query source metadata. Красивые `query_sources` на уровне кандидата будут задачей `P2-006`.

### Goal

Добавить normalized LinkedIn profile URL key и dedupe внутри `POST /api/structured-search`, чтобы response содержал общий deduped список результатов.

### Constraints

- Не удалять `query_results`; per-query raw results остаются в response.
- Не делать полноценные `query_sources` на уровне кандидата в рамках `P2-005`.
- Не делать финальный counts/report в рамках `P2-005`.
- Не менять frontend, если отдельно не согласовано.
- Не добавлять AI planner, database, shortlist, scraping или LinkedIn automation.

### Proposed steps

1. Добавить helper для normalized LinkedIn profile URL.

2. Dedupe key: normalized LinkedIn profile URL.

3. URL normalization rules:

- lowercase host;
- убрать `www.`;
- убрать trailing slash;
- убрать query params;
- убрать fragment;
- сохранить country subdomain, например `ua.linkedin.com`;
- path должен быть `/in/...`.

4. Если URL не является LinkedIn profile-like URL, он не получает normalized LinkedIn profile URL key.

5. В `POST /api/structured-search` после получения всех per-query results:

```text
raw per-query results
-> normalize Tavily results
-> apply visible filters
-> dedupe by normalized LinkedIn profile URL
```

6. Visible filters:

- если `linkedin_profiles_only = true`, оставить только profile-like LinkedIn URLs;
- если `location_domain_only = true`, оставить только `ua.linkedin.com/in/...` for Ukraine baseline;
- фильтры применяются до dedupe.

7. Добавить в response поле:

```json
"deduped_results": []
```

8. Shape одного deduped result:

```json
{
  "normalized_url": "ua.linkedin.com/in/example",
  "result": {}
}
```

9. Если один профиль пришел из нескольких query, оставить один объект.

10. Если данные отличаются между дублями, выбрать более полный вариант:

- предпочесть result с более длинным непустым `title`;
- предпочесть result с более длинным непустым `snippet`;
- если разницы нет, оставить первый найденный.

11. Не добавлять красивый `query_sources` в `P2-005`; это будет `P2-006`.

12. Smoke checks:

- duplicate URL with query params/fragments dedupes into one result;
- `www.linkedin.com/in/...` and `linkedin.com/in/...` normalize consistently;
- `ua.linkedin.com/in/...` preserves country subdomain;
- non-profile LinkedIn URLs are filtered when `linkedin_profiles_only = true`;
- non-UA LinkedIn profile URLs are filtered when `location_domain_only = true`;
- `query_results` остаются в response;
- `deduped_results` появляется в response.

13. Обновить `Tasks.md` после реализации:

- перенести `P2-005` из Backlog в Done;
- добавить `Implementation result`;
- записать smoke-check results;
- явно указать, что candidate-level `query_sources` и final counts/report еще не реализованы.

### Expected behavior

После выполнения `P2-005` `/api/structured-search` возвращает per-query raw results и общий deduped list. Это подготавливает `P2-006`, где deduped candidates получат query source metadata.

### Acceptance criteria

- Добавлен helper для normalized LinkedIn profile URL.
- Dedupe использует normalized LinkedIn profile URL.
- Query params/fragments/trailing slash не создают разные дубли.
- Country subdomain сохраняется.
- Visible filters применяются до dedupe.
- `deduped_results` добавлен в `POST /api/structured-search` response.
- `query_results` остается в response.
- Полноценные candidate-level `query_sources` не реализуются в `P2-005`.
- Финальный counts/report не реализуется в `P2-005`.
- Smoke checks passed.

### Before implementation

Codex должен пересказать задачу `P2-005`, показать точный implementation scope пользователю и дождаться явного подтверждения перед изменением кода.

### Implementation result

`P2-005` выполнена.

Добавлено:

- helper `normalize_linkedin_profile_url`;
- technical dedupe by normalized LinkedIn profile URL;
- visible filter application before dedupe;
- `deduped_results` in `POST /api/structured-search` response;
- result selection that prefers a more complete duplicate by title/snippet length.

Не добавлено в рамках `P2-005`:

- candidate-level `query_sources`;
- final counts/report;
- frontend changes;
- AI planner.

Smoke checks passed:

- duplicate URL with query params/fragments dedupes into one result;
- `www.linkedin.com/in/...` and `linkedin.com/in/...` normalize consistently;
- `ua.linkedin.com/in/...` preserves country subdomain;
- non-profile LinkedIn URLs are filtered when `linkedin_profiles_only = true`;
- non-UA LinkedIn profile URLs are filtered when `location_domain_only = true`;
- non-UA LinkedIn profile URLs remain when `location_domain_only = false`;
- `query_results` remains in response;
- `deduped_results` appears in response.

---

## Task: P2-006 Добавить query source metadata для кандидатов

### Context

`P2-005` добавила technical dedupe и `deduped_results`, но deduped candidate еще не показывает, из каких query он был найден. Для анализа качества planner и будущего reporting нужно сохранять query source metadata на уровне deduped candidate.

### Goal

Добавить `query_sources` в каждый item внутри `deduped_results`.

### Constraints

- Не менять planner в рамках `P2-006`.
- Не менять runner flow в рамках `P2-006`.
- Не делать финальный counts/report в рамках `P2-006`.
- Не менять frontend, если отдельно не согласовано.
- Не добавлять scoring bonus за multiple query sources.

### Proposed steps

1. Расширить `build_deduped_results`, чтобы при обработке raw result он сохранял metadata текущего query:

- `query_id`
- `category`
- `query`

2. Добавить shape `query_sources`:

```json
"query_sources": [
  {
    "id": "Q01",
    "category": "role_based",
    "query": "site:linkedin.com/in AND \"Java Developer\" AND \"Ukraine\""
  }
]
```

3. Обновить shape одного deduped result:

```json
{
  "normalized_url": "ua.linkedin.com/in/example",
  "result": {},
  "query_sources": []
}
```

4. Если candidate найден в одном query, `query_sources` содержит один source.

5. Если candidate найден в нескольких query:

- candidate остается один;
- `query_sources` содержит все unique query sources;
- порядок query sources соответствует порядку обнаружения.

6. Если один и тот же query вернул один и тот же URL дважды, не добавлять duplicate query source.

7. Сохранить существующее поведение выбора более полного result при duplicate URL.

8. Не добавлять scoring bonus за multiple query sources.

9. Не добавлять final counts/report.

10. Smoke checks:

- same profile from Q01 and Q07 has one deduped result;
- `query_sources` contains Q01 and Q07;
- duplicate same URL inside one query does not duplicate source;
- order of query_sources preserved;
- result still chooses more complete duplicate;
- single-source candidate has one query_source.

11. Обновить `Tasks.md` после реализации:

- перенести `P2-006` из Backlog в Done;
- добавить `Implementation result`;
- записать smoke-check results;
- явно указать, что final counts/report и scoring bonus еще не реализованы.

### Expected behavior

После выполнения `P2-006` каждый deduped candidate показывает, какими query он был найден. Это подготавливает `P2-007`, где можно будет считать query contribution и общий report.

### Acceptance criteria

- Каждый `deduped_results` item содержит `query_sources`.
- `query_sources` содержит query `id`, `category`, `query`.
- Candidate, найденный несколькими query, содержит несколько unique query sources.
- Duplicate URL внутри одного query не добавляет duplicate source.
- Порядок query_sources сохраняет порядок обнаружения.
- Выбор более полного duplicate result сохраняется.
- Финальный counts/report не реализуется в рамках `P2-006`.
- Scoring bonus за multiple query sources не реализуется в рамках `P2-006`.
- Smoke checks passed.

### Before implementation

Codex должен пересказать задачу `P2-006`, показать точный implementation scope пользователю и дождаться явного подтверждения перед изменением кода.

### Implementation result

`P2-006` выполнена.

Добавлено:

- `query_sources` for each item in `deduped_results`;
- query source metadata shape with `id`, `category`, `query`;
- unique query source append by query ID;
- preservation of query source discovery order;
- existing more-complete duplicate selection preserved.

Не добавлено в рамках `P2-006`:

- final counts/report;
- scoring bonus for multiple query sources;
- frontend changes;
- AI planner.

Smoke checks passed:

- same profile from Q01 and Q07 has one deduped result;
- `query_sources` contains Q01 and Q07;
- duplicate same URL inside one query does not duplicate source;
- order of query_sources is preserved;
- more complete duplicate result is still selected;
- single-source candidate has one query_source.

---

## Task: P2-007 Обновить counts/report для multi-query pipeline

### Context

`P2-006` добавила `query_sources` для deduped candidates. Теперь backend умеет вернуть `query_plan`, `query_results`, `deduped_results`, но еще не возвращает общий report по multi-query pipeline.

Нужен report, который показывает общий объем raw results, фильтрацию, dedupe, ошибки query и вклад каждого query.

### Goal

Добавить поле `report` в `POST /api/structured-search` response.

### Constraints

- Не менять planner в рамках `P2-007`.
- Не менять Tavily runner flow в рамках `P2-007`.
- Не менять frontend в рамках `P2-007`.
- Не менять scoring в рамках `P2-007`.
- Не добавлять AI planner.

### Proposed steps

1. Добавить поле response:

```json
"report": {}
```

2. Report top-level fields:

```json
{
  "queries_total": 10,
  "queries_succeeded": 10,
  "queries_failed": 0,
  "raw_total": 200,
  "normalized_total": 180,
  "displayed": 60,
  "unique_profiles": 60,
  "duplicates_removed": 120,
  "hidden_by_profile_filter": 10,
  "hidden_by_location_domain_filter": 30,
  "query_contribution": []
}
```

3. Definitions:

- `queries_total`: count of query slots in `QueryPlan`.
- `queries_succeeded`: count of query results with `ok=true`.
- `queries_failed`: count of query results with `ok=false`.
- `raw_total`: sum of all raw results from successful query results before filters.
- `normalized_total`: count of raw results normalized into the current result shape.
- `hidden_by_profile_filter`: count hidden by `linkedin_profiles_only`.
- `hidden_by_location_domain_filter`: count hidden by `location_domain_only`.
- `displayed`: count after visible filters but before dedupe.
- `unique_profiles`: count of `deduped_results`.
- `duplicates_removed`: `displayed - unique_profiles`.

4. Avoid duplicating filter logic:

- use shared logic for filtered/deduped processing and report;
- do not maintain separate inconsistent filter paths.

5. Add `query_contribution`:

```json
{
  "id": "Q01",
  "category": "role_based",
  "raw": 20,
  "filtered": 13,
  "new_unique_profiles": 8,
  "duplicates": 5,
  "ok": true,
  "error": null
}
```

6. `new_unique_profiles` logic:

- iterate query_results in Q01-Q10 order;
- apply visible filters;
- normalize LinkedIn profile URL;
- if normalized URL was not seen before, count as `new_unique_profiles`;
- otherwise count as duplicate.

7. Failed query contribution:

- `raw = 0`;
- `filtered = 0`;
- `new_unique_profiles = 0`;
- `duplicates = 0`;
- `ok = false`;
- `error = ...`.

8. Response after `P2-007`:

```json
{
  "ok": true,
  "query_plan": {},
  "query_results": [],
  "deduped_results": [],
  "report": {}
}
```

9. Smoke checks:

- `raw_total` counts correctly;
- `hidden_by_profile_filter` counts correctly;
- `hidden_by_location_domain_filter` counts correctly;
- `displayed` counts results after filters before dedupe;
- `unique_profiles` equals `len(deduped_results)`;
- `duplicates_removed = displayed - unique_profiles`;
- `query_contribution` counts new/duplicate profiles in query order;
- failed query appears in report;
- all failed queries produce `ok=false` and report still exists.

10. Обновить `Tasks.md` после реализации:

- перенести `P2-007` из Backlog в Done;
- добавить `Implementation result`;
- записать smoke-check results;
- явно указать, что frontend еще не обновлен.

### Expected behavior

После выполнения `P2-007` backend response содержит достаточно информации, чтобы понять, сколько результатов пришло, сколько скрыли фильтры, сколько дублей убрано и какие query реально добавили новых кандидатов.

### Acceptance criteria

- `POST /api/structured-search` response содержит `report`.
- Report содержит согласованные top-level fields.
- `raw_total`, `normalized_total`, `displayed`, `unique_profiles`, `duplicates_removed` считаются корректно.
- `hidden_by_profile_filter` и `hidden_by_location_domain_filter` считаются корректно.
- `query_contribution` показывает вклад каждого query.
- Failed query отображается в `query_contribution`.
- All-failed run возвращает `ok=false` и содержит report.
- Frontend не меняется в рамках `P2-007`.
- Smoke checks passed.

### Before implementation

Codex должен пересказать задачу `P2-007`, показать точный implementation scope пользователю и дождаться явного подтверждения перед изменением кода.

### Implementation result

`P2-007` выполнена.

Добавлено:

- `report` в response `POST /api/structured-search`;
- top-level counts: `queries_total`, `queries_succeeded`, `queries_failed`, `raw_total`, `normalized_total`, `displayed`, `unique_profiles`, `duplicates_removed`, `hidden_by_profile_filter`, `hidden_by_location_domain_filter`;
- `query_contribution` по каждому query slot с `id`, `category`, `raw`, `filtered`, `new_unique_profiles`, `duplicates`, `ok`, `error`;
- подсчет failed query в общем report без падения всего поиска, если остальные query успешны;
- all-failed сценарий возвращает `ok=false`, пустой `deduped_results` и заполненный `report`.

Не добавлено в рамках `P2-007`:

- frontend changes;
- scoring changes;
- planner changes;
- AI planner.

Smoke checks passed:

- `raw_total` counts raw results from successful queries;
- `hidden_by_profile_filter` and `hidden_by_location_domain_filter` count visible filters;
- `displayed` counts results after visible filters before dedupe;
- `unique_profiles` equals `len(deduped_results)`;
- `duplicates_removed = displayed - unique_profiles`;
- `query_contribution` counts new and duplicate profiles in query order;
- failed query appears in `query_contribution`;
- all-failed run returns `ok=false` and still contains `report`;
- `.venv\Scripts\python.exe -m compileall app` passed.

---

## Task: P2-008 Обновить frontend под planner-based search

### Context

После `P2-007` backend уже умеет принимать structured request, строить `QueryPlan`, выполнять 10 query slots, делать dedupe и возвращать `report`. Frontend все еще был построен вокруг Phase 1.1 single-query flow: editable Boolean query и endpoint `/api/search`.

### Goal

Заменить основной frontend flow на planner-based search: пользователь выбирает структурированные поля, видит generated `QueryPlan`, запускает `POST /api/structured-search` и получает deduped candidates вместе с report.

### Constraints

- Не возвращать ручное редактирование Boolean query как основной сценарий.
- Не менять backend planner logic в рамках `P2-008`.
- Не менять scoring в рамках `P2-008`.
- Не добавлять AI planner.
- Не запускать реальный Tavily smoke из frontend без отдельной необходимости.

### Approved steps

1. Заменить старую форму на structured form: `Role Family`, `Technology`, `Stack`, `Location`.
2. Для `Role Family` оставить активным `Backend Developer`.
3. Для `Technology` показать список `Java`, `Python`, `Node.js`, `C#`, `Go`, `PHP`, но активной оставить только `Java`.
4. Для `Java` показать Java stack multi-select: `Spring`, `Spring Boot`, `Hibernate`, `Kafka`, `PostgreSQL`, `AWS`, `Docker`, `Kubernetes`, `Microservices`, `REST`.
5. Enforce UI rule: минимум 1 и максимум 3 stack items.
6. Оставить обязательную editable `Location`, default `Ukraine`.
7. Показать visible filters: `LinkedIn profiles only`, `Ukraine LinkedIn domain only`.
8. Показывать read-only generated `QueryPlan` preview через `/api/query-plan`.
9. Search отправляет structured request в `POST /api/structured-search`.
10. Results показывают `deduped_results`, а не старый single-query список.
11. Report показывает backend `report` и `query_contribution`.
12. Добавить validation/error states.
13. После реализации обновить `Tasks.md`.

### Expected behavior

Пользователь работает с Phase 2 frontend как с рабочей диагностической панелью planner-а: видит structured inputs, generated queries, report по multi-query pipeline и deduped candidates.

### Acceptance criteria

- Старый editable Boolean query больше не является основным frontend flow.
- Frontend вызывает `/api/query-plan` для preview.
- Frontend вызывает `/api/structured-search` для поиска.
- Stack selection ограничен минимум 1 и максимум 3 значениями.
- Unsupported technologies видны, но disabled.
- `Ukraine LinkedIn domain only` является видимым filter toggle и отключается для не-Ukraine location.
- Results показывают `deduped_results` и query source IDs.
- Report показывает top-level counts и `query_contribution`.
- Browser smoke checks passed.

### Implementation result

`P2-008` выполнена.

Добавлено:

- Phase 2 structured search form;
- active `Backend Developer` role family select;
- technology select with only `Java` enabled;
- Java stack chip multi-select with min 1 / max 3 behavior;
- editable `Location`;
- visible `LinkedIn profiles only` and `Ukraine LinkedIn domain only` toggles;
- read-only generated `QueryPlan` preview from `/api/query-plan`;
- search via `POST /api/structured-search`;
- rendering of `deduped_results`;
- rendering of `report` top-level counts;
- rendering of `query_contribution`;
- candidate query source badges and details.

Не добавлено в рамках `P2-008`:

- backend planner changes;
- scoring changes;
- AI planner;
- real Tavily frontend smoke run.

Smoke checks passed:

- `.venv\Scripts\python.exe -m compileall app` passed;
- `node --check app/static/app.js` passed;
- `/api/query-plan` smoke returned 10 queries;
- Browser loaded `http://127.0.0.1:8000/`;
- QueryPlan preview rendered Q01-Q10;
- max 3 stack behavior disables additional unchecked stack items;
- empty stack shows validation and no query plan;
- non-Ukraine location disables `Ukraine LinkedIn domain only`;
- browser console has no errors.

---

## Task: P2-009 Прогнать Java/Ukraine baseline и сравнить результаты

### Context

После `P2-008` Phase 2 pipeline готов end-to-end: frontend отправляет structured request, backend строит `QueryPlan`, выполняет 10 Tavily queries, объединяет результаты, делает dedupe и возвращает report.

### Goal

Проверить baseline Java/Ukraine сценарий одним реальным multi-query прогоном и сравнить результат с критерием успеха Phase 2.

### Constraints

- Сделать один честный baseline run, а не серию оптимизационных экспериментов.
- Не менять planner в рамках `P2-009`.
- Не менять frontend/backend код в рамках `P2-009`.
- Не логиниться в LinkedIn.
- Не скрейпить LinkedIn и не открывать профили автоматически.

### Approved baseline input

```json
{
  "role_family": "Backend Developer",
  "technology": "Java",
  "stack": ["Spring", "Kafka", "AWS"],
  "location": "Ukraine",
  "linkedin_profiles_only": true,
  "location_domain_only": true
}
```

### Approved steps

1. Проверить `/api/query-plan`.
2. Убедиться, что generated plan содержит 10 queries Q01-Q10.
3. Убедиться, что Q07-Q10 используют selected stack через OR: `("Spring" OR "Kafka" OR "AWS")`.
4. Запустить один `POST /api/structured-search`.
5. Снять backend `report`.
6. Посмотреть `query_contribution`.
7. Сравнить `unique_profiles` с Phase 2 success criterion: минимум 20 unique `ua.linkedin.com/in/...` profiles.
8. Качественно просмотреть top results по title/snippet/url без LinkedIn login/scraping.
9. Обновить документы.

### Implementation result

`P2-009` выполнена.

QueryPlan preview:

- `Q01-Q10` generated successfully.
- Q07-Q10 include stack OR group: `("Spring" OR "Kafka" OR "AWS")`.
- Location `Ukraine` remains in every generated query.

Baseline report:

```json
{
  "queries_total": 10,
  "queries_succeeded": 10,
  "queries_failed": 0,
  "raw_total": 190,
  "normalized_total": 190,
  "displayed": 75,
  "unique_profiles": 51,
  "duplicates_removed": 24,
  "hidden_by_profile_filter": 40,
  "hidden_by_location_domain_filter": 75
}
```

Query contribution:

| Query | Category | Raw | Filtered | New unique | Duplicates |
| --- | --- | ---: | ---: | ---: | ---: |
| Q01 | role_based | 19 | 5 | 5 | 0 |
| Q02 | role_based | 20 | 13 | 13 | 0 |
| Q03 | backend_role | 20 | 10 | 8 | 2 |
| Q04 | role_based | 19 | 7 | 4 | 3 |
| Q05 | role_based | 19 | 10 | 5 | 5 |
| Q06 | role_based | 20 | 13 | 7 | 6 |
| Q07 | stack_focused | 19 | 5 | 3 | 2 |
| Q08 | stack_focused | 17 | 3 | 2 | 1 |
| Q09 | stack_focused | 18 | 3 | 1 | 2 |
| Q10 | stack_focused | 19 | 6 | 3 | 3 |

Result:

- Phase 2 baseline success criterion passed: `51` unique profiles vs target `20`.
- Q02 was the strongest single contributor with `13` new unique profiles.
- Role-based queries contributed most of the new unique candidates.
- Stack-focused queries added `9` new unique candidates and also confirmed overlap/duplicates with role-based queries.
- Tavily returned `190` raw results instead of the theoretical `200`, because some query slots returned fewer than 20.
- Top results mostly look like Java / Java Software Engineer / Java Backend candidates based on public snippets.

Important limitation:

- `ua.linkedin.com/in/...` is useful as a Ukraine-domain signal, but it is not a guaranteed current-location signal. One top result had a `ua.linkedin.com/in/...` URL while the snippet showed `Prague, Czechia`.
- Future location quality should not rely only on LinkedIn country subdomain. It likely needs explicit location scoring/validation from title/snippet/content, or a later richer profile enrichment step.

Checks passed:

- `/api/query-plan` returned 10 queries.
- `/api/structured-search` returned `ok=true`.
- `queries_succeeded = 10`, `queries_failed = 0`.
- `unique_profiles = 51`.
- `duplicates_removed = 24`.
- Phase 2 baseline success criterion passed.

---

## Task: P2-009.1 Add configurable header/location location filter

### Context

`P2-009` показала, что `Ukraine LinkedIn domain only` полезен, но слишком груб:

- `ua.linkedin.com/in/...` не гарантирует текущую локацию кандидата;
- часть non-UA LinkedIn profiles имеет `Ukraine` прямо в header/location части Tavily snippet и зря скрывается;
- часть non-UA profiles содержит `Ukraine/Kyiv/etc.` только в education/company/history, и это слабый location signal;
- часть `ua.linkedin.com/in/...` profiles может иметь явную текущую foreign location в header/location, например `Prague, Czechia`.

После ручного анализа вариантов выбран вариант C: фильтрующий паттерн для выдачи + диагностический report.

Важно: старая внутренняя логика и имя поля `location_domain_only` больше не соответствуют смыслу фильтра. В рамках этой задачи нужно заменить API/frontend contract на `location_filter_enabled` без legacy alias и без поддержки двух полей.

### Goal

Улучшить location filtering без LinkedIn login/scraping: использовать только уже полученные Tavily `title/content/snippet`, выделять header/location zone и применять configurable pattern-based include/exclude rules.

Первая реализация использует конфиг для `Ukraine`, но механизм должен быть общим: будущие страны добавляются через location config, а не через переписывание filtering logic.

### Chosen approach: Variant C

Display rule for enabled location filter:

- keep country-domain LinkedIn profiles, например `ua.linkedin.com/in/...` для Ukraine, если header/location не содержит explicit negative location;
- rescue non-UA LinkedIn profiles, если header/location содержит Ukraine location terms;
- exclude profiles, если header/location содержит explicit negative location terms;
- do not rescue non-UA profiles, если Ukraine/Kyiv/etc. найдены только ниже header/location, например в `Education`, `Experience`, `Company`.

Report rule:

- показывать counts для strong/rescued/excluded/weak/unknown групп;
- не терять диагностику weak candidates, даже если они не попали в display list.

### API/frontend contract

Replace old field:

```json
"location_domain_only": true
```

with new field:

```json
"location_filter_enabled": true
```

Rules:

- do not support both fields;
- do not add a legacy alias for `location_domain_only`;
- frontend sends only `location_filter_enabled`;
- backend `StructuredSearchRequest` accepts only `location_filter_enabled`;
- `QueryPlan.filters` contains `location_filter_enabled`;
- frontend toggle label should become `Location filter`;
- internal implementation should be configurable for future locations.
- when `location_filter_enabled = false`, no location filter is applied; only other enabled filters such as `linkedin_profiles_only` remain active.
- when `location_filter_enabled = true` but no config exists for selected `location`, backend returns validation error and frontend should prevent/disable this state when possible.

### Location filter config pattern

Initial structure idea:

```python
LOCATION_FILTER_CONFIG = {
    "Ukraine": {
        "linkedin_domains": ["ua.linkedin.com"],
        "include_terms": [...],
        "negative_terms": [...],
    }
}
```

Future countries should be added by extending config:

- country-specific LinkedIn domains;
- city/country include terms;
- explicit negative terms relevant for the target location.

### Initial include terms

Ukraine header/location terms:

- `Ukraine`
- `Kyiv`
- `Kiev`
- `Lviv`
- `Kharkiv`
- `Odesa`
- `Odessa`
- `Dnipro`
- `Vinnytsia`
- `Zaporizhzhia`
- `Chernivtsi`
- `Ternopil`
- `Ivano-Frankivsk`

### Initial negative terms

Negative current-location terms discovered during P2-009:

- `Prague`
- `Praha`
- `Czechia`
- `Czech Republic`

These terms should only exclude a candidate when found in header/location zone, not when found lower in education/company/history.

### Header/location zone draft

Use the top public snippet lines that usually represent:

```text
Name
Headline
Current location
connections/followers
```

Stop header parsing before lower profile sections such as:

- `About`
- `Experience`
- `Education`
- `Licenses`
- `Certifications`
- `Skills`
- `Projects`

### Approved experimental result

One no-code simulation of variant C on a repeated Java/Ukraine baseline run produced:

- `96` unique LinkedIn profiles before location-domain filtering;
- current `ua.linkedin.com/in/...` filter kept `49` unique profiles;
- variant C displayed `53` strong candidates;
- `5` non-UA profiles were rescued by header/location `Ukraine`;
- `1` `ua.linkedin.com/in/...` profile was excluded because header/location contained `Prague, Czechia`;
- `22` non-UA profiles had Ukraine/Kyiv/etc. only below header, usually education/history/company;
- `20` non-UA profiles had no Ukraine terms in Tavily snippet.

Conclusion: variant C improves quality and adds useful candidates without pulling weak education/history matches into the main display list.

### Proposed implementation steps

1. Rename request contract:
   - frontend sends `location_filter_enabled`;
   - backend `StructuredSearchRequest` uses `location_filter_enabled`;
   - `QueryPlan.filters` uses `location_filter_enabled`;
   - remove usage of `location_domain_only`;
   - no legacy alias.
2. Rename frontend toggle label from `Ukraine LinkedIn domain only` to `Location filter`.
3. Add configurable location filter config with first supported config for `Ukraine`.
4. Add validation for unsupported location filter config:
   - `Ukraine` is supported first;
   - if `location_filter_enabled = true` and selected location has no config, return validation error;
   - frontend should disable/prevent enabled location filter for unsupported locations when possible.
5. Define filter order explicitly:
   - apply `linkedin_profiles_only` first;
   - apply location filter variant C only to LinkedIn profile-like results;
   - normalize LinkedIn profile URL;
   - dedupe by normalized LinkedIn profile URL.
6. Add helper to extract `header_location_text` from Tavily public fields:
   - prefer `content`;
   - fallback to `snippet`;
   - fallback to `raw_content` if available;
   - handle both multiline snippets and compact one-line snippets.
7. Add pattern matcher for include terms and negative terms.
8. Extend normalized result or dedupe item with location signal metadata:
   - `location_signal_status`: `country_domain`, `rescued_header_location`, `excluded_negative_header_location`, `weak_history_only`, `unknown_non_country_domain`;
   - `location_signal_terms`;
   - `header_location_text`.
9. Collect location signals per normalized LinkedIn profile URL before final display decision:
   - normalize LinkedIn profile URL after profile filter;
   - extract location signals for every occurrence from every query;
   - merge all location signals by normalized profile URL;
   - do not make final location pass/hide decision only from a single occurrence.
10. Apply candidate-level location decision after merging signals:
   - `excluded_negative_header_location` wins and hides the candidate if any occurrence has this signal;
   - if no negative signal exists, `country_domain` passes;
   - if no negative or country-domain signal exists, `rescued_header_location` passes;
   - otherwise `weak_history_only` and `unknown_non_country_domain` stay hidden.
11. Replace current hard `location_domain_only` behavior with configurable variant C behavior when `location_filter_enabled` is enabled:
   - target country-domain candidates can pass unless negative header/location match exists;
   - non-UA candidates can pass only if rescued by header/location match;
   - weak/unknown non-UA candidates stay hidden.
12. Rename report field:
   - replace `hidden_by_location_domain_filter` with `hidden_by_location_filter`;
   - no legacy duplicate report field unless separately approved.
13. Extend report with a grouped `location_filter_report` object plus top-level compatibility for agreed report fields only if needed:
   - `hidden_by_location_filter`;
   - `rescued_by_header_location`;
   - `hidden_by_negative_header_location`;
   - `weak_location_history_only`;
   - `unknown_non_country_domain_location`;
   - count semantics must be explicit.
14. Count semantics:
   - pipeline filter counts such as `hidden_by_location_filter` are occurrence-level before dedupe, matching existing report behavior;
   - add unique breakdown inside `location_filter_report`, so the report can show real candidate-level impact after normalized URL merge.
15. Show these counts in frontend report.
16. Add smoke checks with mocked Tavily results:
   - non-UA + header `Ukraine` is rescued;
   - non-UA + Ukraine only in education is not rescued;
   - ua-domain + header `Prague, Czechia` is excluded;
   - negative terms below header do not exclude;
   - `location_filter_enabled = false` skips location filtering;
   - unsupported location config with enabled filter returns validation error;
   - multiline and one-line snippets are parsed deterministically;
   - duplicate profile URL with negative signal in one occurrence is hidden after candidate-level merge;
   - duplicate profile URL with country-domain in one occurrence and rescued-header in another still appears once;
   - frontend/backend use `location_filter_enabled`;
   - old `location_domain_only` is not used;
   - report counts are correct.
17. Run one real Java/Ukraine baseline after implementation and compare to current P2-009 baseline.
18. Update `Tasks.md`, `ProjectStatus.md`, and `Roadmap.md` with measured result, including that `ua.linkedin.com` is no longer the only location signal.

### Constraints

- Do not open LinkedIn profiles.
- Do not log in to LinkedIn.
- Do not scrape LinkedIn.
- Do not add browser automation against LinkedIn.
- Use only Tavily returned public `title/content/snippet`.
- Do not implement AI planner in this task.
- Do not expand negative/include term lists broadly without review; keep terms explicit and explainable.

### Acceptance criteria

- Variant C behavior is implemented behind the visible `Location filter` toggle.
- Request/response contract uses `location_filter_enabled`, not `location_domain_only`.
- No legacy support for `location_domain_only` remains.
- Location filtering uses a config pattern with first supported config for `Ukraine`.
- `location_filter_enabled = false` skips location filtering.
- Unsupported location config with enabled location filter returns validation error.
- Filter order is explicit: profile filter, then location filter, then URL normalization, then dedupe.
- Location signals are collected and merged by normalized LinkedIn profile URL before final candidate display decision.
- Negative header/location signal wins over country-domain or rescued-header signals for the same normalized URL.
- Header/location extraction is deterministic and covered by smoke checks.
- Header/location extraction handles multiline and compact one-line snippets.
- Non-UA profile with `Ukraine` in header/location can be displayed.
- Non-UA profile with Ukraine only in education/history remains hidden.
- Profile with negative current location in header/location is hidden.
- Report shows rescued, negative-hidden, weak-history-only, and unknown non-country-domain counts.
- Report count semantics are explicit: occurrence-level pipeline counts and unique candidate-level breakdown after normalized URL merge.
- Frontend report shows the new counts.
- Real baseline comparison is documented.

### Before implementation

Codex must restate the task scope and wait for explicit approval before changing code.

### Implementation result

`P2-009.1` выполнена.

Code changes:

- backend structured request contract renamed to `location_filter_enabled`;
- old structured field `location_domain_only` is not supported as a legacy alias;
- `QueryPlan.filters` now contains `location_filter_enabled`;
- frontend toggle label changed to `Location filter`;
- first configurable location filter config added for `Ukraine`;
- unsupported location with enabled location filter returns validation error;
- frontend disables/prevents enabled location filter for unsupported locations in the current UI;
- location signals are collected per occurrence and merged by normalized LinkedIn profile URL before final display decision;
- candidate-level explicit foreign current-location signal wins over country-domain and rescued-header signals after `P2-012`;
- report now exposes `hidden_by_location_filter`, `rescued_by_header_location`, `hidden_by_foreign_current_location`, `weak_location_history_only`, `unknown_non_country_domain_location`, and `location_filter_report`;
- frontend report shows the new location filter counts.

Historical real baseline after initial `P2-009.1` implementation:

```json
{
  "queries_total": 10,
  "queries_succeeded": 10,
  "queries_failed": 0,
  "raw_total": 200,
  "normalized_total": 200,
  "displayed": 85,
  "unique_profiles": 58,
  "duplicates_removed": 27,
  "hidden_by_profile_filter": 53,
  "hidden_by_location_filter": 62,
  "rescued_by_header_location": 13,
  "hidden_by_negative_header_location": 3,
  "weak_location_history_only": 26,
  "unknown_non_country_domain_location": 33
}
```

Unique `location_filter_report` breakdown:

```json
{
  "country_domain": 49,
  "rescued_header_location": 9,
  "excluded_negative_header_location": 2,
  "weak_history_only": 18,
  "unknown_non_country_domain": 21
}
```

Conclusion:

- Phase 2 still passes the success criterion: `58` unique profiles vs target `20`.
- The new filter keeps `ua.linkedin.com/in/...` as a strong signal but no longer relies on it as the only location signal.
- `9` unique non-UA LinkedIn profiles were rescued because header/location contained Ukraine terms.
- `2` unique profiles were excluded because header/location contained explicit negative current-location terms.
- Weak history-only Ukraine matches remain hidden from the main display list but visible in diagnostics.

Current note after `P2-012`/`P2-013`:

- `negative_terms` no longer drives runtime exclusion.
- Runtime config uses `target_location_terms`.
- Explicit foreign current location is classified as `foreign_current_location` and hidden as `excluded_foreign_current_location`.
- The frontend report label is `Foreign location`.
- Saved snapshot replay after the current-location classifier produced `73` unique displayed profiles with `target_location = 71` and `country_domain = 2`.
- Recent live Tavily one-wave runs for `Backend Developer + Java + Spring/Kafka + Ukraine` produce roughly `55-60` unique profiles; counts vary because Tavily returns different result pools.

Checks passed:

- `.venv\Scripts\python.exe -m compileall app`;
- `node --check app/static/app.js`;
- backend smoke for `location_filter_enabled` contract;
- backend smoke for rejecting old `location_domain_only`;
- backend smoke for unsupported location validation;
- backend smoke for rescued, weak, negative, filter-off, and candidate-level negative-wins cases;
- browser smoke for `Location filter`, generated `QueryPlan`, frontend report metrics, and no console errors;
- real `POST /api/structured-search` baseline run.

---

## Task: P1-001 Определить границы POC

### Context

Фаза 1 должна проверить минимальную ценность продукта: можно ли через один поисковый источник находить релевантных IT специалистов для рекрутера или менеджера.

### Goal

Определить и зафиксировать узкий сценарий POC: рекрутер ищет публичные LinkedIn-профили IT специалистов через Tavily по одному X-ray Boolean-запросу.

### Constraints

- Не писать код.
- Не подключать интеграции.
- Не расширять POC до нескольких источников поиска.
- Не переходить к архитектуре до согласования границ.
- Не делать прямую автоматизацию LinkedIn.
- Не использовать логин в LinkedIn.
- Не делать scraping или обход ограничений LinkedIn.
- Не добавлять базу данных, shortlist, авторизацию или AI agent в рамках P1-001.

### Expected behavior

После выполнения задачи должно быть понятно, какой один пользовательский сценарий проверяет POC.

### Acceptance criteria

- Целевой пользователь POC: рекрутер.
- Поисковый движок POC: Tavily.
- Целевой источник профилей: публичные LinkedIn-профили, доступные через web search/cache/snippets.
- POC работает с одним согласованным тестовым запросом.
- UI форма содержит поля: основной якорь-позиция, дополнительные якоря через запятую, стек через запятую, одна локация, preview итогового X-ray Boolean-запроса.
- Поля формы заполняются латиницей.
- Поиск идет по title и доступному body/snippet профиля.
- Если условия в Boolean-запросе соединены через AND, все обязательные условия должны совпасть, чтобы кандидат считался релевантным.
- Обязательные поля результата: имя, роль, стек, локация, ссылка на источник, snippet/описание, источник данных, причина релевантности.
- Критерий успеха POC: для одного согласованного тестового запроса найдено 20 кандидатов, которые выглядят релевантными по заданным условиям.

### Before implementation

Codex должен пересказать задачу, предложить границы POC и дождаться подтверждения пользователя.

---

## Task: P1-002 Выбрать минимальный стек

### Context

Для POC нужен простой технический стек, который позволит быстро проверить поиск через Tavily и показать результаты в веб интерфейсе.

### Goal

Выбрать и зафиксировать минимальный frontend/backend стек для первой версии без лишней инфраструктуры.

### Constraints

- Не усложнять стек без необходимости.
- Не добавлять базу данных, авторизацию или фоновые очереди без отдельного согласования.
- Учитывать, что POC должен быть простым для запуска локально.
- Не использовать React, Next.js, Node.js/Express, Docker, базу данных, авторизацию, shortlist или AI agent в рамках минимального POC.

### Expected behavior

После выполнения задачи должен быть согласован минимальный набор технологий для POC.

### Acceptance criteria

- Frontend подход: plain HTML/CSS/JS.
- Backend подход: Python + FastAPI.
- Backend endpoint для поиска: `POST /api/search`.
- Health endpoint: `GET /api/health`.
- Tavily API key хранится локально в `.env` и читается из переменной `TAVILY_API_KEY`.
- `.env` не коммитится в git; в репозиторий добавляется только `.env.example`.
- Tavily API key не попадает во frontend.
- Python окружение: `.venv` внутри проекта.
- Локальный запуск: создать `.venv`, установить `requirements.txt`, запустить `uvicorn app.main:app --reload`, открыть `http://localhost:8000`.
- Один FastAPI backend отдает frontend static files и API.
- Не входит в первую версию: база данных, авторизация, React, Next.js, Node.js/Express, Docker, AI agent, shortlist.

### Before implementation

Codex должен пересказать задачу, предложить Python + FastAPI подход и дождаться подтверждения пользователя.

---

## Task: P1-003 Зафиксировать тестовый сценарий POC

### Context

Чтобы честно оценить POC, нужен заранее согласованный тестовый сценарий и seed query. Без этого невозможно объективно понять, достигнут ли критерий успеха в 20 релевантных кандидатов.

### Goal

Зафиксировать один тестовый сценарий POC, на котором будет проверяться поиск, фильтрация, нормализация и scoring.

### Constraints

- Не выбирать слишком широкий сценарий.
- Не менять критерий успеха во время финального тестового прогона.
- Не подгонять запрос после получения результатов без отдельной фиксации.
- Не считать POC успешным без проверки фактических результатов.

### Expected behavior

Перед финальным прогоном POC есть один согласованный сценарий: кто ищется, где ищется, какие технологии важны, какая локация и какой итоговый Boolean-запрос используется.

### Acceptance criteria

- Определена целевая роль: `Java`.
- Определены дополнительные якоря: `Developer`, `Engineer`.
- Определен стек: `Java`, `Spring`.
- Определена одна локация: `Ukraine`.
- Зафиксирован итоговый Boolean-запрос.
- Зафиксирован критерий успеха: 20 релевантных кандидатов.
- UI language для POC: English.
- Тестовый сценарий используется в `P1-010` для отчета по POC.

### Before implementation

Codex должен пересказать задачу, предложить один узкий тестовый сценарий и дождаться подтверждения пользователя.

---

## Task: P1-004 Создать каркас проекта

### Context

После согласования стека нужно создать минимальную Python + FastAPI структуру приложения, на которую можно будет добавлять поиск, frontend и обработку результатов.

### Goal

Создать базовый каркас проекта с понятной структурой файлов и минимальным запуском.

### Constraints

- Не добавлять бизнес-логику поиска.
- Не подключать Tavily.
- Не делать полноценный дизайн.
- Не создавать лишние директории и абстракции.

### Expected behavior

Проект должен запускаться локально через FastAPI, показывать минимальную стартовую страницу и отвечать на health endpoint.

### Acceptance criteria

- Создана минимальная структура проекта: `app/`, `app/main.py`, `app/static/`, `requirements.txt`, `.env.example`.
- FastAPI отдает static frontend из `app/static/`.
- Добавлен `GET /api/health`.
- Добавлены инструкции локального запуска через virtual environment и `uvicorn app.main:app --reload`.
- Проверено, что проект стартует локально, если Python dependencies доступны.

### Before implementation

Codex должен пересказать задачу, показать план создаваемых Python/FastAPI файлов и дождаться подтверждения пользователя.

---

## Task: P1-005 Собрать X-ray Boolean-запрос из формы

### Context

POC использует форму поиска, где рекрутер вводит позицию, дополнительные якоря, стек и локацию. Из этих полей нужно собрать итоговый X-ray Boolean-запрос для поиска публичных LinkedIn профилей через Tavily.

### Goal

Определить и реализовать простую логику сборки editable X-ray Boolean-запроса из полей формы.

### Constraints

- Не добавлять AI генерацию запроса.
- Не добавлять несколько поисковых источников.
- Не делать сложный query language builder.
- Не делать прямую автоматизацию LinkedIn.
- Не использовать логин, scraping или обход ограничений LinkedIn.

### Expected behavior

Пользователь заполняет поля формы, система собирает preview Boolean-запроса, пользователь может вручную отредактировать итоговый запрос перед запуском поиска.

### Acceptance criteria

- Итоговый запрос содержит ограничение на публичные LinkedIn профили, например `site:linkedin.com/in`.
- Основной якорь-позиция добавляется как обязательное условие.
- Дополнительные якоря через запятую преобразуются в условия запроса.
- Стек через запятую преобразуется в OR условия запроса.
- Локация добавляется как обязательное условие.
- Итоговый Boolean-запрос доступен пользователю для ручного редактирования перед поиском.
- Frontend отправляет на backend именно итоговый отредактированный Boolean-запрос.
- Логика сборки запроса простая, предсказуемая и видимая пользователю.

### Before implementation

Codex должен пересказать задачу, предложить шаблон Boolean-запроса и дождаться подтверждения пользователя.

---

## Task: P1-006 Подключить поиск через Tavily

### Context

POC использует Tavily как первый поисковый источник для проверки возможности находить IT специалистов через web search.

### Goal

Добавить FastAPI backend логику, которая принимает поисковый запрос и возвращает результаты Tavily.

### Constraints

- Не добавлять дополнительные поисковые источники.
- Не хранить API ключ в коде.
- Не делать сложную нормализацию результатов.
- Не добавлять AI агента.

### Expected behavior

Пользовательский запрос отправляется на FastAPI backend, backend обращается к Tavily и возвращает raw результаты поиска.

### Acceptance criteria

- Есть FastAPI endpoint `POST /api/search`.
- Tavily API key читается из переменной окружения.
- Ошибки Tavily обрабатываются понятным ответом.
- Есть простой способ проверить запрос локально.

### Before implementation

Codex должен пересказать задачу, описать схему запроса/ответа и дождаться подтверждения пользователя.

---

## Task: P1-007 Показать raw результаты Tavily во фронте

### Context

После подключения Tavily нужно показать первые результаты во frontend без сложной обработки, чтобы быстро проверить полезность поиска.

### Goal

Добавить простой frontend экран поиска: форма из согласованных POC полей, preview X-ray Boolean-запроса, кнопка поиска и список raw результатов Tavily.

### Constraints

- Не делать сложный UI.
- Не добавлять scoring.
- Не нормализовать данные глубже, чем нужно для отображения.
- Не добавлять сохранение результатов.
- Не добавлять shortlist, базу данных или AI обработку.
- Не парсить LinkedIn профили на этом этапе.

### Expected behavior

Пользователь заполняет форму поиска, видит preview итогового Boolean-запроса, нажимает кнопку поиска и получает список raw результатов Tavily.

### Acceptance criteria

- Есть форма с полями: основной якорь-позиция, дополнительные якоря через запятую, стек через запятую, одна локация.
- Поля формы заполняются латиницей.
- UI текст и labels на английском языке.
- Есть editable preview итогового X-ray Boolean-запроса.
- Есть кнопка запуска поиска.
- Frontend отправляет итоговый поисковый запрос на backend endpoint `POST /api/search`.
- Показываются raw результаты Tavily.
- Для каждого raw результата показываются минимум: name, title, url, content/snippet, score если Tavily его возвращает.
- Показываются состояния loading, empty и error.

### Before implementation

Codex должен пересказать задачу, предложить минимальный UI формы и дождаться подтверждения пользователя.

---

## Task: P1-008 Нормализовать результаты поиска

### Context

Raw результаты Tavily нужно привести к единому формату, чтобы дальше можно было сортировать, оценивать и показывать их как кандидатоподобные результаты.

### Goal

Определить и реализовать минимальную структуру нормализованного результата, чтобы raw ответы Tavily приводились к единому кандидатоподобному формату.

### Constraints

- Не пытаться гарантированно извлекать все данные кандидата из любого сайта.
- Не добавлять сложный scraping.
- Не добавлять AI обработку без отдельного согласования.
- Не менять источник поиска.
- Не открывать страницы LinkedIn профилей.
- Не добавлять scoring, shortlist или базу данных.

### Expected behavior

Каждый raw результат Tavily преобразуется в единый формат с понятными полями. Если поле не удалось определить из title/snippet/url, оно остается `unknown`, `null` или пустым массивом.

### Acceptance criteria

- Определена структура нормализованного результата.
- Raw результат преобразуется в эту структуру.
- Сохраняется ссылка на источник.
- При нехватке данных поля остаются пустыми или помечаются как unknown.
- Если `name` нельзя надежно извлечь из raw Tavily title/snippet/url, значение `name` устанавливается в `unknown`.
- Сохраняются исходные raw поля Tavily, чтобы не терять данные.
- Источник определяется по URL, например `linkedin`, если URL относится к LinkedIn.
- Минимальная структура результата:
  - `name`
  - `title`
  - `url`
  - `source`
  - `location`
  - `stack`
  - `snippet`
  - `raw_title`
  - `raw_content`
  - `tavily_score`
  - `matched_fields`
  - `relevance_reason`

### Before implementation

Codex должен пересказать задачу, предложить поля нормализованного результата и дождаться подтверждения пользователя.

---

## Task: P1-009 Добавить базовую оценку релевантности

### Context

Для POC нужна простая оценка релевантности, чтобы показывать более подходящие результаты выше и понимать, есть ли ценность в ранжировании.

### Goal

Добавить базовый scoring результатов по совпадению с запросом и ключевыми словами, а также фильтрацию результатов по обязательным условиям.

### Constraints

- Не добавлять сложную ML модель.
- Не добавлять AI агента.
- Не делать scoring непрозрачным.
- Не скрывать причину оценки от пользователя.
- Не использовать embeddings, LLM scoring или сложную семантическую оценку.
- Не добавлять shortlist, базу данных или автоматическое исправление запроса.

### Expected behavior

Результаты проходят проверку обязательных условий, затем получают простой score и краткое объяснение, почему они релевантны. Если обязательное условие не совпало, результат не показывается пользователю вообще.

### Acceptance criteria

- У каждого результата есть score.
- Результаты можно отсортировать по score.
- Есть краткое объяснение score.
- Scoring работает локально и предсказуемо.
- Максимальный score: `100`.
- Примерная структура score: position match до `35`, additional anchors match до `20`, stack match до `25`, location match до `10`, LinkedIn source до `5`, data completeness до `5`.
- Добавлены поля результата: `score`, `is_relevant`, `matched_fields`, `missing_required_fields`, `relevance_reason`.
- Если обязательные условия из Boolean-запроса не совпали, результат получает `is_relevant: false` и не отображается в списке результатов.
- Для stack достаточно совпадения хотя бы одного значения из списка, так как stack в Boolean-запросе соединяется через OR.
- Пользователю показываются только результаты с `is_relevant: true`.
- Причина релевантности должна быть понятной и строиться из совпавших полей.

### Before implementation

Codex должен пересказать задачу, предложить простую формулу scoring и правило фильтрации по обязательным условиям, затем дождаться подтверждения пользователя.

---

## Task: P1-010 Описать выводы POC

### Context

После реализации первой версии нужно зафиксировать, что POC показал, какие есть ограничения и стоит ли двигаться к следующей фазе.

### Goal

Подготовить краткий документ с результатами реального POC прогона, выводами и рекомендациями по следующей фазе.

### Constraints

- Не придумывать результаты без проверки.
- Не маскировать ограничения.
- Не переходить к реализации следующей фазы без отдельного согласования.
- Не писать финальные выводы до реального тестового прогона POC.
- Не менять scoring, логику поиска или реализацию в рамках этой задачи.
- Не добавлять AI agent, презентацию или новый функционал.

### Expected behavior

После выполнения задачи понятно, работает ли идея POC, был ли достигнут критерий успеха в 20 релевантных кандидатов, что нужно улучшить и какие риски есть дальше.

### Acceptance criteria

- Описано, что было проверено.
- Описано, что получилось.
- Описаны ограничения и проблемы.
- Предложены следующие шаги.
- Указан тестовый сценарий.
- Указаны search input и итоговый Boolean query.
- Указано количество raw результатов Tavily.
- Указано количество результатов после фильтрации обязательных условий.
- Указано, достигнут ли критерий успеха: 20 релевантных кандидатов.
- Приведены 3-5 примеров хороших результатов.
- Приведены примеры плохих или шумных результатов, если они есть.
- Описано, какие поля не удалось извлекать стабильно: name, title, location, stack или другие.
- Зафиксирована рекомендация: переходить к следующей фазе, изменить подход или уточнить запрос.
- Предлагаемая структура отчета:
  - `Test scenario`
  - `Search input`
  - `Boolean query`
  - `Results summary`
  - `Relevant candidates`
  - `What worked`
  - `What did not work`
  - `Limitations`
  - `Risks`
  - `Recommendation`
  - `Next steps`

### Before implementation

Codex должен пересказать задачу, предложить структуру отчета, убедиться что POC был реально протестирован, и дождаться подтверждения пользователя.

---

## Task: P1.1-001 Сделать editable Boolean query единственным источником поиска

### Context

В Phase 1 поля формы одновременно собирали Boolean query и скрыто влияли на backend-фильтрацию. Это создает неочевидное поведение: пользователь может вручную изменить query, но backend продолжит учитывать старые значения полей.

### Goal

Сделать так, чтобы итоговый editable Boolean query был единственным источником поискового намерения при нажатии `Search`.

### Constraints

- Не менять поисковый движок Tavily.
- Не добавлять AI генерацию запроса.
- Не добавлять скрытые фильтры.
- Не менять смысл кнопки `Rebuild query`: она только пересобирает query из полей формы.

### Expected behavior

Поля формы помогают пользователю собрать query. После ручного редактирования textarea именно текст из textarea отправляется на backend и используется для Tavily search.

### Acceptance criteria

- Frontend при `Search` отправляет итоговый `query`.
- `main_anchor`, `additional_anchors`, `stack`, `location` не отправляются как backend-фильтры.
- Ручное изменение textarea влияет на фактический поисковый запрос.
- `Rebuild query` обновляет textarea из полей формы.
- Пользовательская логика поиска видна в textarea.

### Before implementation

Codex должен пересказать задачу, показать какие frontend payload поля будут изменены, и дождаться подтверждения пользователя.

---

## Task: P1.1-002 Убрать скрытую backend-фильтрацию по полям формы

### Context

Backend Phase 1 проверяет результаты Tavily по `main_anchor`, `additional_anchors`, `stack`, `location` и скрывает результаты, если обязательные условия не найдены в коротких returned fields. Это может ошибочно исключать кандидатов, потому что Tavily ищет по своему индексу, а backend видит только `title`, `url` и обрезанный `content/snippet`.

### Goal

Убрать скрытое исключение результатов по значениям полей формы после Tavily search.

### Constraints

- Не удалять нормализацию результатов.
- Не скрывать результаты из-за отсутствия слов из формы в snippet/title/content.
- Не считать поля формы обязательными условиями backend-фильтрации.
- Не добавлять новые скрытые правила вместо старых.

### Expected behavior

Backend отправляет editable query в Tavily, получает raw results, нормализует их и возвращает результаты без скрытого required-condition filtering по полям формы.

### Acceptance criteria

- `SearchRequest` не требует `main_anchor`, `additional_anchors`, `stack`, `location` для фильтрации.
- Backend не формирует `missing_required_fields` на основе полей формы.
- Результаты не исключаются из UI только потому, что `Ukraine`, `Java`, `Spring`, `Developer` или похожие слова не найдены в коротком snippet/title/content.
- Counts отражают raw/normalized/displayed results без неявного поля `relevant_results` как основной выдачи.
- Поведение backend соответствует принципу: query is source of truth.

### Before implementation

Codex должен пересказать задачу, показать какие backend проверки будут удалены или отключены, и дождаться подтверждения пользователя.

---

## Task: P1.1-003 Заменить `Relevant results` на `Search results`

### Context

После удаления скрытой фильтрации UI не должен называть основной список `Relevant results`, потому что backend больше не принимает скрытое решение о релевантности.

### Goal

Сделать wording UI честным: основной список показывает search results, полученные по editable query.

### Constraints

- Не менять дизайн радикально.
- Не добавлять новые фильтры.
- Не обещать пользователю релевантность, если результат просто пришел из Tavily.

### Expected behavior

UI показывает заголовок `Search results` и счетчик результатов без misleading формулировки про relevant results.

### Acceptance criteria

- Заголовок блока результатов: `Search results`.
- Счетчик показывает displayed results и raw Tavily results.
- Текст не говорит, что результаты прошли скрытую проверку релевантности.
- Empty/error/loading states остаются понятными.

### Before implementation

Codex должен пересказать задачу, показать новый UI wording и дождаться подтверждения пользователя.

---

## Task: P1.1-004 Сделать scoring нейтральным и не фильтрующим

### Context

Scoring Phase 1 смешивает ранжирование с обязательной фильтрацией. После изменения логики score должен помогать сортировать и понимать качество результата, но не скрывать результаты.

### Goal

Оставить простой нейтральный score без required-condition filtering.

### Constraints

- Не использовать score для скрытого исключения результатов.
- Не штрафовать результат как нерелевантный только из-за отсутствия слов из формы в snippet.
- Не добавлять ML, embeddings или LLM scoring.
- Не делать score непрозрачным.

### Expected behavior

Каждый нормализованный результат может получить score на основе технических сигналов: Tavily score, похожесть URL на LinkedIn profile, полнота данных. Score помогает ранжировать, но не является фильтром.

### Acceptance criteria

- Score не устанавливает `is_relevant: false` из-за полей формы.
- Score не скрывает результат из списка.
- В score можно учитывать Tavily score.
- В score можно учитывать profile-like URL как положительный сигнал.
- В score можно учитывать data completeness.
- `relevance_reason` заменен или переосмыслен как нейтральное объяснение score.

### Before implementation

Codex должен пересказать задачу, предложить простую формулу neutral score и дождаться подтверждения пользователя.

---

## Task: P1.1-005 Добавить явный toggle `LinkedIn profiles only`

### Context

Даже при query `site:linkedin.com/in` Tavily может вернуть непрофильные страницы: jobs, company, posts, search pages или другой шум. Такой фильтр нужен, но он должен быть видимым пользовательским выбором, а не скрытой backend-логикой.

### Goal

Добавить на frontend выключенный по умолчанию toggle `LinkedIn profiles only`, который явно включает фильтрацию по profile-like LinkedIn URLs.

### Constraints

- Toggle выключен по умолчанию.
- Не включать URL/profile filtering скрыто.
- Не считать URL filter частью Boolean query.
- Не открывать и не парсить LinkedIn страницы.

### Expected behavior

Если toggle выключен, UI показывает все нормализованные результаты Tavily. Если toggle включен, backend показывает только URL, похожие на личные LinkedIn профили, и честно сообщает сколько результатов скрыто как non-profile.

### Acceptance criteria

- На frontend есть toggle `LinkedIn profiles only`.
- По умолчанию toggle выключен.
- При выключенном toggle результаты не фильтруются по profile-like URL.
- При включенном toggle остаются URL вида `linkedin.com/in/...` и country-subdomain варианты вроде `ua.linkedin.com/in/...`.
- При включенном toggle исключаются очевидные non-profile URL: `/jobs/`, `/company/`, `/posts/`, `/search/` и похожий шум.
- UI показывает сколько результатов отображено и сколько скрыто URL/profile filter.

### Before implementation

Codex должен пересказать задачу, показать правило profile-like URL, показать frontend toggle behavior и дождаться подтверждения пользователя.

---

## Task: P1.1-006 Зафиксировать результаты Phase 1.1 в документах

### Context

После реализации Phase 1.1 нужно обновить документы, чтобы они отражали новую архитектурную договоренность: editable query является source of truth, а скрытая field-based фильтрация больше не используется.

### Goal

Обновить Roadmap, Tasks, ProjectStatus и при необходимости findings document после проверки Phase 1.1.

### Constraints

- Не фиксировать задачу как done до реальной проверки.
- Не переписывать историю Phase 1 так, будто ошибки дизайна не было.
- Не менять код в рамках этой документационной задачи.

### Expected behavior

Документы ясно показывают, что Phase 1 POC был успешен как доказательство концепции, а Phase 1.1 исправляет поведение POC перед Phase 2.

### Acceptance criteria

- `Roadmap.md` отражает статус Phase 1.1.
- `Tasks.md` отражает выполненные задачи Phase 1.1.
- `ProjectStatus.md` содержит актуальный статус, текущие ограничения и следующий шаг.
- При необходимости обновлен `docs/phase-1-poc-findings.md`.
- Документы не противоречат фактическому поведению приложения.

### Before implementation

Codex должен пересказать задачу, перечислить документы для обновления и дождаться подтверждения пользователя.

---

## Task: P1.1-007 Добавить видимый фильтр по украинскому LinkedIn-домену

### Контекст

Текущая проверка локации через поисковый запрос недостаточно надежна. Если в Boolean query есть `"Ukraine"`, Tavily может вернуть профиль, где Украина упоминается где-то в опыте, образовании, компании или snippet, но текущая видимая локация человека в LinkedIn может быть не Украина.

Для POC более понятный первый location-сигнал - это украинский LinkedIn subdomain:

- `ua.linkedin.com/in/...`

Это не идеальная гарантия текущей локации, но это более прозрачный и проверяемый технический сигнал, чем скрытая проверка слова `Ukraine` в snippet.

### Цель

Добавить на фронте видимый выключатель, который позволяет пользователю оставить только LinkedIn-профили с украинского LinkedIn-домена.

### UI

Добавить checkbox/toggle:

`[ ] Ukraine LinkedIn domain only`

Состояние по умолчанию: выключен.

### Поведение backend

Если toggle выключен:

- не фильтровать результаты по LinkedIn country subdomain;
- показывать все нормализованные/displayed результаты, кроме других явно включенных пользователем фильтров.

Если toggle включен:

- оставлять только profile-like URL, где:
  - domain ровно `ua.linkedin.com`;
  - path начинается с `/in/`;
- исключать:
  - `www.linkedin.com/in/...`;
  - `linkedin.com/in/...`;
  - другие country subdomains, например `de.linkedin.com/in/...`, `pl.linkedin.com/in/...`;
  - не-профильные URL: `/jobs/`, `/company/`, `/posts/`, `/search/`.

### Counts / feedback в UI

Когда toggle включен, UI должен явно показывать, сколько результатов скрыто этим фильтром, например:

`Showing 12 search results from 20 raw Tavily results. 8 non-UA-domain results hidden.`

### Ограничения

- Не делать это скрытым backend-фильтром.
- Не включать фильтр по умолчанию без отдельного согласования.
- Не парсить LinkedIn-страницы.
- Не логиниться в LinkedIn.
- Не делать scraping LinkedIn.
- Не считать `ua.linkedin.com/in/...` идеальной гарантией текущей локации.
- Не удалять существующий toggle `LinkedIn profiles only`.
- Новый фильтр должен работать вместе с `LinkedIn profiles only`.

### Ожидаемое поведение

Пользователь может явно решить, хочет ли он сузить выдачу до профилей `ua.linkedin.com/in/...`. Это дает более управляемое первое приближение к локации Украина, чем relying только на слово `Ukraine` в Tavily query или snippet.

### Acceptance criteria

- На frontend есть видимый toggle `Ukraine LinkedIn domain only`.
- Toggle выключен по умолчанию.
- Frontend отправляет boolean-флаг на backend только как явно выбранный пользователем фильтр.
- Backend применяет фильтр только если флаг `true`.
- Если фильтр включен, backend оставляет только URL вида `https://ua.linkedin.com/in/...`.
- UI показывает количество результатов, скрытых как non-UA-domain.
- Логика `editable Boolean query = source of truth` остается без изменений.
- Существующий toggle `LinkedIn profiles only` остается без изменений.
- Фильтр проверен простым smoke-check/manual test.

### Before implementation

Codex должен пересказать задачу, показать точное frontend/backend поведение и дождаться подтверждения пользователя перед изменением кода.

### Implementation result

- Добавлен frontend toggle `Ukraine LinkedIn domain only`.
- Toggle выключен по умолчанию.
- Frontend отправляет `ukraine_linkedin_domain_only`.
- Backend применяет фильтр только если флаг включен.
- Фильтр оставляет только `ua.linkedin.com/in/...`.
- UI показывает счетчик `non-UA-domain results hidden`.
- Фильтр работает вместе с `LinkedIn profiles only`.
- Проверено через `python -m compileall app`, `node --check app/static/app.js`, URL-rule smoke-check, backend counts smoke-check и UI check.

### Test notes

- Для запроса `site:linkedin.com/in AND "Java Software Engineer" AND "Ukraine"` с включенными `LinkedIn profiles only` и `Ukraine LinkedIn domain only` получено 16 украинских LinkedIn-профилей из 20 raw Tavily results.
- За 10 тестовых запросов найдено 53 уникальных `ua.linkedin.com/in/...` профиля.
- Широкий запрос `site:linkedin.com/in AND "Java" AND ("Developer" OR "Engineer") AND ("Java" OR "Spring") AND "Ukraine"` дал 0 украинских LinkedIn-профилей после включения обоих фильтров.
