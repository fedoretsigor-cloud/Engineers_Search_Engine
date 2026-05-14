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
- `2` unique profiles excluded by explicit negative header/location signal;
- Phase 2 success criterion passed: `58` unique vs target `20`.

### Conclusions

- Multi-query search is better than one broad universal query for the tested Java/Ukraine scenario.
- `QueryPlan` is the right architectural contract: it lets us replace `RuleBasedQueryPlanner` with `AIQueryPlanner` later without rewriting executor, dedupe, report, or frontend.
- `Location filter` should stay visible and configurable, not hidden backend behavior.
- Country-domain LinkedIn URL is useful, but only one signal.
- Tavily snippets are enough for a working baseline, but not enough for high-confidence final candidate qualification.
- Phase 2 should not be expanded further before choosing the next product direction.

### Known limitations carried forward

- `name` extraction remains weak and often returns `unknown`.
- Location confidence is heuristic and based only on Tavily public snippets/content.
- Stack fit is not yet scored deeply.
- Seniority is not modeled.
- No database, shortlist, export, CRM workflow, auth, or saved searches.
- No AI planner yet.
- No LinkedIn login, scraping, bypass, or direct profile automation.

### Next phase options

Option A: `Phase 3A - AI Query Planner v0`

- Keep the existing `QueryPlan` contract.
- Add an AI planner that proposes query slots from structured inputs.
- Require explanation/debug metadata for generated queries.
- Compare AI-generated plans against `RuleBasedQueryPlanner v1`.

Option B: `Phase 3B - Candidate Quality Layer`

- Improve name extraction.
- Improve location confidence.
- Add stack/seniority scoring.
- Improve ranking and candidate diagnostics.
- Keep query generation rule-based for now.

### Decision

Phase 2 is closed. The next implementation phase is not selected yet.

### Implementation result

`P2-010` выполнена как документационное закрытие Phase 2.

Updated documents:

- `Tasks.md`: `P2-010` moved to Done and documented.
- `Roadmap.md`: Phase 2 marked as completed, final result and Phase 3 options added.
- `ProjectStatus.md`: current phase updated to Phase 2 completed, with final conclusions and next decision point.

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
- candidate-level negative header/location signal wins over country-domain and rescued-header signals;
- report now exposes `hidden_by_location_filter`, `rescued_by_header_location`, `hidden_by_negative_header_location`, `weak_location_history_only`, `unknown_non_country_domain_location`, and `location_filter_report`;
- frontend report shows the new location filter counts.

Real baseline after implementation:

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
