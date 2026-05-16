### Roadmap



Цель продукта создать веб приложение для поиска IT специалистов по всему миру.

Через какие системы надо искать - LinkedIn, etc.

Пользователи - рекрутеры, менеджеры.

Конечная цель - AI агент на базе протестированного движка и веб приложения.



Все разбиваем на фазы.

Фаза 1

POC прототип с легким фронтом и одним поисковиком Тавили.

Статус Phase 1: POC успешно завершен и принят как рабочее доказательство концепции. После изменения stack matching с AND на OR найдено 10 релевантных кандидатов из 20 raw результатов. Цель 20 релевантных кандидатов остается ориентиром для следующей итерации настройки. Детали см. `ProjectStatus.md` и `docs/phase-1-poc-findings.md`.



Фаза 1.1 - POC behavior tuning

Настройка поведения Phase 1 POC после проверки реального сценария поиска.

Главная цель: сделать editable Boolean query единственным источником поисковой логики. Поля формы нужны только для удобной сборки запроса, а backend не должен скрыто фильтровать результаты по этим полям после ответа Tavily.

Согласованные направления:

- Frontend: поля формы только собирают editable Boolean query; Search отправляет итоговый query.
- Backend: убрать скрытую фильтрацию по `main_anchor`, `additional_anchors`, `stack`, `location`.
- UI: заменить `Relevant results` на `Search results`.
- Scoring: оставить только нейтральный score для ранжирования/подсказки, без скрытого исключения результатов.
- URL/profile filter: добавить явный toggle `LinkedIn profiles only`, выключенный по умолчанию.
- Ukraine domain filter: добавить явный toggle `Ukraine LinkedIn domain only`, выключенный по умолчанию.

Статус Phase 1.1: завершена. Editable Boolean query стал единственным источником поиска, скрытая backend-фильтрация по полям формы убрана, UI показывает `Search results`, score стал нейтральным и не фильтрующим, URL/profile filtering вынесен в явный toggle `LinkedIn profiles only`, а фильтр Украины вынесен в явный toggle `Ukraine LinkedIn domain only`. Оба фильтра выключены по умолчанию.

Результат проверки Phase 1.1: для поиска Java-программиста в Украине лучше всего сработал точный запрос `site:linkedin.com/in AND "Java Software Engineer" AND "Ukraine"` с включенными фильтрами `LinkedIn profiles only` и `Ukraine LinkedIn domain only`: 16 украинских LinkedIn-профилей из 20 raw Tavily results. За 10 разных запросов найдено 53 уникальных `ua.linkedin.com/in/...` профиля. Вывод: Phase 1.1 улучшила управляемость и качество фильтрации, а следующий сильный шаг - последовательный multi-query search с dedupe.



Фаза 2 - Multi-query Search + Baseline Query Planner

Статус Phase 2: завершена. Phase 2 закрыта как рабочий baseline search engine: structured inputs -> QueryPlanner v1 -> 10 focused Tavily queries -> dedupe -> report -> frontend diagnostic UI -> configurable Location filter -> local structured-search snapshots.

Цель Phase 2: построить multi-query pipeline, где поисковые запросы не вводятся как один ручной Boolean query и не хардкодятся как один Java/Ukraine список, а генерируются через `QueryPlanner v1` из клиентских вводных.

Главная гипотеза: для поиска кандидатов лучше работает набор коротких focused queries, сгенерированных по понятному плану, чем один широкий универсальный query. При этом Phase 2 должна готовить архитектуру к будущему AI planner, но сама еще не реализует AI agent.

Базовый сценарий Phase 2: рекрутер ищет `Backend Developer`, выбирает `Technology = Java`, от 1 до 3 Java-related stack технологий и локацию. Для проверки baseline используем Java-программиста в Украине.

Ключевые понятия Phase 2:

- `SearchRequest`: клиентские вводные, например `Role Family`, `Technology`, `Stack`, `Location`.
- `QueryPlan`: список Tavily queries с IDs, purpose/category, исходными вводными, фильтрами и параметрами выполнения.
- `QueryPlanner v1`: rule-based baseline planner, который строит 10 focused queries по правилам для Java Backend.
- `Search Executor`: последовательно запускает queries из `QueryPlan`.
- `Result Merger`: нормализует результаты, объединяет их и делает dedupe по normalized LinkedIn profile URL.
- `Search Report`: показывает counts, query source metadata и вклад каждого query.

Смысл baseline planner v1:

- Не хранить финальный хардкод `Java + Ukraine`.
- Генерировать queries из выбранных клиентом полей.
- Всегда использовать `site:linkedin.com/in`.
- Всегда учитывать выбранную локацию в query.
- Для Java Backend использовать несколько role-based query slots.
- Java-related stack является обязательным сигналом: клиент выбирает минимум 1 и максимум 3 значения.
- Выбранные stack-технологии использовать в отдельных stack-focused query slots и далее в scoring/reporting.
- Не добавлять seniority вроде `Senior`, `Middle`, `Lead`, если клиент явно не выбрал seniority.

Текущий экспериментальный ориентир: 10-query шаблон для `Backend Developer + Java + Ukraine` стабильно проходит критерий успеха, но Tavily выдача не детерминирована. Последние live single-wave прогоны для `Spring/Kafka` дают примерно `55-60` unique profiles, replay сохраненного snapshot после `P2-012/P2-013` дал `73` unique profiles, а multi-wave эксперименты дали ограниченный дополнительный прирост.

Фактический Phase 2 baseline run для `Backend Developer + Java + Spring/Kafka/AWS + Ukraine` дал 51 уникальный `ua.linkedin.com/in/...` профиль из 190 raw Tavily results. Критерий успеха Phase 2 пройден: 51 unique против целевых 20. Важное ограничение: `ua.linkedin.com/in/...` является сигналом домена/страны профиля, но не гарантирует текущую физическую локацию кандидата.

Дополнительная настройка `P2-009.1`: strict `Ukraine LinkedIn domain only` в structured pipeline заменен на общий `Location filter`. Изначально фильтр использовал pattern с country-domain signal, rescue non-UA профилей по Ukraine/Kyiv/Lviv/etc. в header/location Tavily snippet, explicit negative terms и скрытие weak history-only matches. Реальный baseline для `Backend Developer + Java + Spring/Kafka/AWS + Ukraine` дал 58 unique profiles из 200 raw Tavily results.

Уточнение `P2-012`/`P2-013`: blacklist-style `negative_terms` заменены на current-location classification. Для Ukraine runtime config хранит `target_location_terms`; фильтр извлекает `current_location_line` из public LinkedIn header/snippet и классифицирует `target_location`, `foreign_current_location` или `unknown_current_location`. Explicit foreign current location скрывается как `excluded_foreign_current_location` даже для `ua.linkedin.com/in/...`; unknown current location может fallback-иться на `country_domain`, `rescued_header_location`, `weak_history_only` или `unknown_non_country_domain`.

Итог Phase 2: критерий успеха пройден с запасом (`55-73` observed unique candidates в последних проверках против цели `20`). Главное архитектурное достижение - `QueryPlan` contract: теперь можно менять planner logic, не переписывая executor, dedupe, report и frontend.

Ограничения, которые переносим дальше из Phase 2: Tavily snippets неполные, Tavily live выдача меняется между запусками, `name` extraction слабый, location confidence эвристический, stack/seniority fit пока не является полноценным ranking layer. В Phase 4 уже появился explicit AI draft planner и backend approval gate для rule-based Tavily execution, но AI-generated plans остаются non-executable до отдельной задачи.

Порядок реализации:

- Сначала зафиксировать контракт `QueryPlan` и правила `QueryPlanner v1`.
- Потом добавить входную модель поиска: `Role Family`, `Technology`, `Stack`, `Location`.
- Потом реализовать rule-based query planner v1 для Java Backend.
- Потом backend multi-query runner: последовательно выполнить queries из `QueryPlan`.
- Потом нормализация, объединение и dedupe по normalized LinkedIn URL.
- Потом query source metadata: сохранить, из каких query найден кандидат.
- Потом counts/report: raw total, unique profiles, duplicates removed, displayed, hidden by filters, query contribution.
- Потом frontend режим planner-based search: показать generated queries и общий deduped список.
- Потом scoring для multi-query результатов.
- Потом pattern-based `Location filter` вместо жесткого country-domain-only фильтра.
- Потом локальное snapshot-логирование structured-search результатов.
- Потом current-location classification вместо blacklist-style `negative_terms`.
- Потом итоговый Phase 2 baseline прогон и документирование результатов.

Критерий успеха Phase 2:

- По базовому Java/Ukraine сценарию получить не менее 20 уникальных украинских LinkedIn-профилей за один planner-based multi-query проход.
- Пользователь должен видеть, какие queries были сгенерированы.
- Пользователь должен видеть, какие фильтры включены и сколько результатов они скрыли.
- Пользователь должен видеть итоговый deduped список, а не разрозненные результаты по каждому query.
- Архитектура должна позволять позже заменить `RuleBasedQueryPlanner` на `AIQueryPlanner` без переписывания executor/dedupe/report.

Не входит в Phase 2 без отдельного согласования:

- LinkedIn login.
- Scraping или обход ограничений LinkedIn.
- База данных.
- Shortlist.
- AI agent или AI query planner implementation.
- Multi-source search beyond Tavily.
- Автоматическое открытие и парсинг LinkedIn-профилей.

Следующий порядок после Phase 2:

- Phase 3 - `Candidate Quality Layer`: оставить rule-based planner, но улучшить name extraction, location confidence, stack/seniority scoring и ranking. В Phase 3 также добавить adaptive multi-wave runner как supporting capability для quality evaluation: несколько волн одного `QueryPlan`, dedupe across waves, stop по incremental unique gain.
- Phase 4 - `AI Agent Foundation`: сохранить текущий deterministic engine как безопасный tool layer, добавить `Search Brief`, AI-assisted planning, agent action/tool boundaries, explanation и approval перед Tavily execution.
- Phase 5 - `Recruiter Chat UX + Search Brief conversation`: добавить внутренний чат, где рекрутер живым диалогом описывает задачу, AI уточняет brief, задает вопросы и готовит действия через Phase 4 agent foundation.
- Phase 6 - `Tool-Calling Agent Runtime`: превратить чат в agent loop: AI получает цель, планирует шаги, вызывает доступные инструменты (`AI Query Planner`, search runner, multi-wave runner, quality layer), смотрит на результаты и предлагает следующий шаг с approval для дорогих или важных действий.
- Phase 7 - `Candidate Workspace/Table + Shortlist`: сделать таблицу кандидатов главным рабочим artifact после чата: score, evidence, role/tech/location fit, review flags, query/wave source, filters, сортировка, объяснения, shortlist и экспорт.
- Phase 8 - `Persistent Memory + Saved Searches`: добавить хранение chat sessions, search briefs, runs, candidates, scores, shortlists и saved searches, чтобы агент мог продолжать работу между сессиями и не терять контекст.

Phase 3 завершена как baseline `Candidate Quality Layer`. Следующий этап - Phase 4 `AI Agent Foundation`.

Фаза 4 - AI Agent Foundation

Цель Phase 4: двигаться к настоящему AI Agent на базе уже построенного search engine, не выбрасывая deterministic pipeline. Текущий движок становится безопасным набором инструментов: `QueryPlan`, rule-based planner fallback, search executor, multi-wave runner, dedupe, visible filters, Candidate Quality Layer, reports и snapshots.

AI в Phase 4 должен планировать и объяснять, а backend должен валидировать, ограничивать и требовать approval для дорогих действий.

Важное решение Phase 4: продукт должен использовать LLM/ChatGPT layer для живого общения с рекрутером, понимания intent, сборки `Search Brief`, уточняющих вопросов, планирования и объяснений. Это не заменяет backend engine. AI думает и общается; backend валидирует, ограничивает и выполняет через проверенный pipeline.

Порядок задач Phase 4:

- `P4-001 Define AI Agent Foundation contract`
- `P4-002 Define Search Brief schema`
- `P4-003 Add Search Brief validation and adapter`
- `P4-004 Define Agent tools contract`
- `P4-005 Add AI Query Planner v0 behind explicit mode`
- `P4-006 Add AI QueryPlan validation and fallback`
- `P4-007 Add planner explanation UI`
- `P4-008 Add approval before Tavily execution`
- `P4-009 Compare AI planner vs rule-based baseline`
- `P4-010 Close Phase 4 with decision`

Статус `P4-001`: approved as contract. Утверждено:

- Phase 4 = `AI Agent Foundation`, а не только `AI Query Planner`.
- `Search Brief v0` является структурой диалога: recruiter intent, missing fields, clarifying questions, assumptions, explicit user constraints.
- `target_titles` остаются в planner, а не в `Search Brief`.
- Если brief неполный, AI задает уточняющие вопросы, а не строит план на догадках.
- `search_depth` v0: `standard` и `deep`; `deep` может предложить multi-wave, но только через approval.
- Agent workflow: `Search Brief -> Agent Plan -> Agent Action -> optional Approval Gate -> validated Tool Call -> Agent Response`.
- Agent tools v0: `validate_search_brief`, `adapt_brief_to_structured_request`, `build_query_plan`, `validate_query_plan`, `run_single_wave_search`, `run_multi_wave_search`, `analyze_candidate_quality`, `summarize_search_results`, `suggest_next_iteration`.
- Без approval AI может понимать intent, собирать/валидировать brief, задавать вопросы, строить/валидировать plan, объяснять, анализировать уже полученные результаты и предлагать next iteration.
- Approval обязателен для `run_single_wave_search`, `run_multi_wave_search`, `deep search`, выполнения AI-generated `QueryPlan`, повторного запуска поиска, увеличения `max_results` и изменения depth с `standard` на `deep`.
- AI-generated `QueryPlan` проходит deterministic backend validation; если validation fails, search не выполняется и предлагается visible fallback к `RuleBasedQueryPlanner`.
- Baseline evaluation Phase 4 проверяет весь agent flow на сценарии `Backend Developer + Java + Spring/Kafka + Ukraine`, а не только candidate count.

Статус `P4-002`: approved as `Search Brief v0` schema contract. Утверждено:

- `Search Brief v0` является dialogue state, а не копией формы.
- Schema поддерживает `needs_clarification` и `ready_for_planning`.
- `source_text`, `missing_fields`, `clarifying_questions` и `assumptions` входят в contract.
- `stack` не обязателен для существования brief object, но обязателен для `ready_for_planning` в текущем Java flow.
- `target_titles` не входят в brief; их генерирует planner.
- `exclusions` заполняются только из explicit recruiter constraints и не используются как location blacklist.
- Baseline brief: `Backend Developer + Java + Spring/Kafka + Ukraine`.

Статус `P4-003`: approved as Search Brief validation/adapter contract. Утверждено:

- Bridge flow: `Search Brief -> Search Brief validation/normalization -> StructuredSearchRequest adapter -> existing structured-search validation`.
- Backend не доверяет blindly `brief_status` от AI/client.
- Incomplete brief не адаптируется в `StructuredSearchRequest`.
- Adapter переиспользует `normalize_structured_search_request(...)` как authoritative validation для role/technology/stack/location/filter defaults.
- `search_depth` остается metadata; `deep` не запускает multi-wave automatically.
- `target_titles` rejected if sent; planner owns target-title generation.
- No LLM calls, no Tavily calls, no query-plan generation, no search execution in this task.

Статус `P4-004`: approved as Agent Tools v0 contract. Утверждено:

- Allowlisted tools: `validate_search_brief`, `adapt_brief_to_structured_request`, `build_query_plan`, `validate_query_plan`, `run_single_wave_search`, `run_multi_wave_search`, `analyze_candidate_quality`, `summarize_search_results`, `suggest_next_iteration`.
- Planning/validation/analysis/suggestion tools do not require approval.
- `run_single_wave_search` and `run_multi_wave_search` require explicit approval.
- Tool calls/results use stable envelopes with `tool_name`, `input`, `requires_approval`, `approval_status`, `reason`, `result`, `errors`, and `next_actions`.
- Agent can call only allowlisted tools and cannot bypass backend contracts.

Статус `P4-005`: approved as AI Query Planner v0 behind explicit mode. Утверждено:

- Это первая Phase 4 задача, где может появиться реальный LLM/ChatGPT call.
- LLM используется только для planning и explanation.
- Default planner остается `rule_based`.
- AI planner включается только через explicit planner mode.
- AI output является `draft_query_plan`, не executable plan.
- AI planner не запускает Tavily, не вызывает search execution tools и не меняет filters/scoring/dedupe/location logic.
- Missing LLM/API config должен давать graceful error без поломки rule-based mode.
- `P4-006` отвечает за deterministic validation/fallback, а `P4-008` за approval before execution.

Статус `P4-006`: approved as deterministic AI QueryPlan validation/fallback contract. Утверждено:

- Validator uses `normalized_brief + normalized_structured_request` as source of truth.
- AI output is not authoritative for filters, execution settings, or supported domain rules.
- Valid AI plans are marked `validated_not_executable` with `execution_allowed = false`.
- Validation checks structure, limits, safety, brief alignment, source scope, target location, role/technology signal, and forbidden behavior.
- Validation errors are structured with `field`, `code`, and `message`.
- Fallback to `RuleBasedQueryPlanner` is visible with `planner_mode = rule_based_fallback` and `fallback_reason`.
- Fallback also remains non-executable until approval.
- No Tavily execution in this task.

Статус `P4-007`: approved as planner explanation UI contract. Утверждено:

- Extend existing `Generated QueryPlan` preview instead of building full recruiter chat UI.
- Show planner mode/status, Search Brief summary, planner explanation, warnings, assumptions, validation state, validation errors, fallback reason, and approval-needed notice when fields are present.
- Keep existing rule-based QueryPlan preview backward-compatible when those fields are absent.
- Do not run Tavily, do not implement approval execution flow, and do not make AI plans executable in this task.

Статус `P4-008`: implemented as backend approval gate before Tavily execution. Утверждено и реализовано:

- Planner preview говорит `execution_approval_required = true`, а `/api/structured-search` и `/api/structured-search/multi-wave` теперь проверяют approval на backend перед Tavily execution.
- P4-008 добавил реальную проверку approval непосредственно перед Tavily execution.
- Approval должен быть привязан к конкретному действию: `run_single_wave_search` или `run_multi_wave_search`.
- Approval должен быть привязан к текущему плану через `approved_plan_fingerprint`, чтобы нельзя было одобрить один `QueryPlan`, изменить форму и выполнить другой.
- Backend пересчитывает/проверяет текущий `QueryPlan` перед execution и reject'ит missing/stale/wrong-action approval.
- Frontend делает смысл клика явным через `Approve & Search`: пользователь одобряет запуск Tavily по видимому плану, а не просто нажимает абстрактный `Search`.
- Multi-wave требует отдельного approval, потому что это более дорогой/deep execution mode.
- Approval metadata сохраняется в structured-search snapshot/log.
- AI-generated plans остаются non-executable в P4-008; запуск AI plan в Tavily не входит в эту задачу.

Absolute product boundaries: запрещены direct web-search агентом в обход approved backend pipeline, LinkedIn login, LinkedIn scraping, restriction bypass, автоматическая отправка сообщений кандидатам и любые действия с user или third-party accounts.

Не входит в Phase 4: persistent memory/database, shortlist, export, fully autonomous tool-calling loop, полноценный recruiter chat UI, multi-source search beyond Tavily, private/personal data sources. Chat UI относится к Phase 5, tool-calling runtime к Phase 6, candidate workspace/shortlist/export к Phase 7, persistence/memory/saved searches к Phase 8.

Фазы 5-8 описывают путь к настоящему AI Agent внутри приложения. Agent здесь означает не просто чат, а AI-модель с целью, контекстом, инструментами, approval flow и циклом действий: понять задачу, собрать brief, запустить инструменты, оценить результат, уточнить план и вернуть кандидатов в виде таблицы.

Ориентир по пути к AI Agent:

- Минимум до AI Agent v0: Phase 4 + Phase 5 + Phase 6.
- Phase 4 дает foundation: `Search Brief`, LLM-assisted planning, AI planner mode, agent tools contract, deterministic validation, approval gates, fallback и объяснения.
- Phase 5 делает агентный UX через recruiter chat и согласованный `Search Brief`.
- Phase 6 добавляет настоящий tool loop: агент планирует следующий шаг, вызывает доступные инструменты после approval, анализирует результат и предлагает итерацию.
- Для реально удобного recruiter workflow нужна еще Phase 7: candidate workspace, shortlist, notes/statuses и рабочая таблица кандидатов.
- Phase 8 добавляет persistence/memory, чтобы агент мог продолжать работу между сессиями.

Вывод: через 3 фазы после Phase 3 можно получить AI Agent v0; через 4 фазы - agent-based sourcing workflow, которым уже можно пользоваться как рабочим продуктом.

### Ideas

- Backend URL/profile filter should be visible to the user as a frontend toggle, not hidden backend behavior.
- Location rule: treat country-specific LinkedIn profile domains such as `ua.linkedin.com/in/...` as a location signal for Ukraine.
- Future country support must extend the location config with country domains and `target_location_terms`, then reuse current-location classification instead of building finite negative-location blacklists.
- Sequential multi-query search: run several focused Tavily queries, merge results, dedupe by normalized LinkedIn URL, then apply visible filters.
- Phase 3 multi-wave search should stop based on incremental unique gain. Recent experiments: 1 wave gave 60 unique, 3 waves gave 64 cumulative unique, one 5-wave block gave 61 cumulative unique, and one 10-wave block gave 60 cumulative unique.
- Phase 3 quality baseline confirms the quality layer is useful for ranking/review, but selected stack evidence is still weak in public Tavily/LinkedIn snippets.
- For selected stack terms that are not visible in Tavily public snippets, the UI now says `Not visible`; query-source-only stack evidence says `Not confirmed`.
- Real `P3-012` multi-wave evaluation produced 67 unique candidates after 4 waves and 40 Tavily queries; incremental gain over wave 1 was +7 unique candidates, so multi-wave should not become default yet.
- `P3-013` keeps single-wave as default and exposes multi-wave only through an explicit frontend toggle that is off by default.
- `P3-014` closes Phase 3 and prepares the handoff to Phase 4. Phase 4 is now `AI Agent Foundation`: it should preserve the `QueryPlan` contract, visible filters, existing executor/dedupe/report pipeline, Candidate Quality Layer, and add `Search Brief`, agent tool boundaries, AI planner mode, explanations, and approval gates.

### Planned

- Phase 5: `Recruiter Chat + Search Brief`.
- Phase 6: `Tool-Calling Agent Runtime`.
- Phase 7: `Candidate Workspace/Table + Shortlist`.
- Phase 8: `Persistent Memory + Saved Searches`.

### In Progress

- Phase 4: `AI Agent Foundation` - `P4-001` through `P4-008` are approved as contracts; `P4-003` through `P4-008` are implemented; next task to review is `P4-009 Compare AI planner vs rule-based baseline`.

### Done

- Phase 2 - Multi-query Search + Baseline Query Planner.
- Phase 3 - Candidate Quality Layer.
