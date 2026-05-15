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

Ограничения, которые переносим дальше: Tavily snippets неполные, Tavily live выдача меняется между запусками, `name` extraction слабый, location confidence эвристический, stack/seniority fit пока не является полноценным ranking layer, AI planner еще не реализован.

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
- Phase 4 - `AI Query Planner v0`: сохранить `QueryPlan` contract, но заменить rule-based planner на AI planner, который предлагает query slots и объясняет логику.
- Phase 5 - `Recruiter Chat + Search Brief`: добавить внутренний чат, где рекрутер живым диалогом описывает задачу, AI собирает structured `Search Brief`, задает уточняющие вопросы и просит подтверждение перед запуском поиска.
- Phase 6 - `Tool-Calling Agent Runtime`: превратить чат в agent loop: AI получает цель, планирует шаги, вызывает доступные инструменты (`AI Query Planner`, search runner, multi-wave runner, quality layer), смотрит на результаты и предлагает следующий шаг с approval для дорогих или важных действий.
- Phase 7 - `Candidate Workspace/Table + Shortlist`: сделать таблицу кандидатов главным рабочим artifact после чата: score, evidence, role/tech/location fit, review flags, query/wave source, filters, сортировка, объяснения, shortlist и экспорт.
- Phase 8 - `Persistent Memory + Saved Searches`: добавить хранение chat sessions, search briefs, runs, candidates, scores, shortlists и saved searches, чтобы агент мог продолжать работу между сессиями и не терять контекст.

Phase 3 выбрана как следующий этап. AI Query Planner перенесен в Phase 4.

Фазы 5-8 описывают путь к настоящему AI Agent внутри приложения. Agent здесь означает не просто чат, а AI-модель с целью, контекстом, инструментами, approval flow и циклом действий: понять задачу, собрать brief, запустить инструменты, оценить результат, уточнить план и вернуть кандидатов в виде таблицы.

### Ideas

- Backend URL/profile filter should be visible to the user as a frontend toggle, not hidden backend behavior.
- Location rule: treat country-specific LinkedIn profile domains such as `ua.linkedin.com/in/...` as a location signal for Ukraine.
- Future country support must extend the location config with country domains and `target_location_terms`, then reuse current-location classification instead of building finite negative-location blacklists.
- Sequential multi-query search: run several focused Tavily queries, merge results, dedupe by normalized LinkedIn URL, then apply visible filters.
- Phase 3 multi-wave search should stop based on incremental unique gain. Recent experiments: 1 wave gave 60 unique, 3 waves gave 64 cumulative unique, one 5-wave block gave 61 cumulative unique, and one 10-wave block gave 60 cumulative unique.
- Phase 3 quality baseline confirms the quality layer is useful for ranking/review, but selected stack evidence is still weak in public Tavily/LinkedIn snippets.
- For selected stack terms that are not visible in Tavily public snippets, the UI now says `Not visible`; query-source-only stack evidence says `Not confirmed`.

### Planned

- Phase 4: `AI Query Planner v0`.
- Phase 5: `Recruiter Chat + Search Brief`.
- Phase 6: `Tool-Calling Agent Runtime`.
- Phase 7: `Candidate Workspace/Table + Shortlist`.
- Phase 8: `Persistent Memory + Saved Searches`.

### In Progress

- Phase 3: `Candidate Quality Layer` - completed through `P3-010.2`; next task is `P3-011 Add adaptive multi-wave runner for quality evaluation`.

### Done

- Phase 2 - Multi-query Search + Baseline Query Planner.
