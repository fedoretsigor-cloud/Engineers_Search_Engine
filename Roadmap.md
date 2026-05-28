### Roadmap



Цель продукта создать веб приложение для поиска IT специалистов по всему миру.

Через какие системы надо искать - LinkedIn, etc.

Пользователи - рекрутеры, менеджеры.

Конечная цель - AI агент на базе протестированного движка и веб приложения.

Принцип движения: каждая фаза и каждая задача должны приближать продукт к реальному AI Agent experience: живой диалог с рекрутером, понимание intent, планирование, approved backend tools, безопасное execution, анализ результатов и последующий уточняющий цикл. Deterministic planners допустимы, когда они являются безопасными executable tools для агента, а не заменой AI Agent направления. Агент не должен быть автономным исполнителем: он предлагает, объясняет, валидирует и анализирует, а execution требует явного approval.



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

- База данных.
- Shortlist.
- AI agent или AI query planner implementation.
- Multi-source search beyond Tavily.

Запрещено в рамках продукта, не является будущим approval item:

- LinkedIn login.
- Scraping или обход ограничений LinkedIn.
- Автоматическое или прямое открытие/парсинг LinkedIn-профилей.
- Автоматическая отправка сообщений кандидатам.
- Любые действия с user или third-party accounts.

Следующий порядок после Phase 2:

- Phase 3 - `Candidate Quality Layer`: оставить rule-based planner, но улучшить name extraction, location confidence, stack/seniority scoring и ranking. В Phase 3 также добавить adaptive multi-wave runner как supporting capability для quality evaluation: несколько волн одного `QueryPlan`, dedupe across waves, stop по incremental unique gain.
- Phase 4 - `AI Agent Foundation`: сохранить текущий deterministic engine как безопасный tool layer, добавить `Search Brief`, AI-assisted planning, agent action/tool boundaries, explanation и approval перед Tavily execution.
- Phase 5 - `Recruiter Chat UX + Search Brief conversation`: довести один узкий Java/Ukraine flow до качества: чат собирает и уточняет `Search Brief`, умеет менять brief через follow-up, показывает Agent Plan, запускает поиск только после approval и после результатов ведет к следующей итерации.
- Phase 5.5 - `Technical modularization before Agent Runtime`: без изменения поведения разделить большой backend в `app/main.py` на модули перед настоящим tool-calling runtime.
- Phase 6 - `Tool-Calling Agent Runtime`: превратить чат в bounded human-approved tool loop: AI получает цель, планирует шаги, готовит вызовы доступных инструментов (`AI Query Planner`, search runner, multi-wave runner, quality layer), смотрит на результаты и предлагает следующий шаг; execution не автономный и требует approval.
- Phase 7 - `Agent Conversation Wording Layer`: после Phase 6 runtime добавить controlled wording layer для agent conversation messages: taxonomy/lifecycle, facts contract, style policy, deterministic source messages, LLM routing/gating, bounded payload/prompt contract, validation/fallback/provenance, typed frontend rendering и golden scenario regression. Lightweight wording provenance/version metadata входит в P7-007/P7-009, но не как отдельная product analytics/telemetry задача.
- Phase 7.5 - `Recruiter Simulation QA & Flow Hardening`: перед Phase 8 проведена глубокая симуляция живого рекрутера в локальном браузере на текущем Java/Ukraine Agent flow. OpenAI live calls были разрешены для существующих chat/planning/wording paths. Tavily-backed execution был разрешен только через существующий approved backend pipeline и явный `Approve & Search`. Покрытие RU + EN завершено, approved fixes реализованы, closeout decision: `ready after approved fixes completed`.
- Phase 8 - `Candidate Workspace/Table + Shortlist`: сделать таблицу кандидатов главным рабочим artifact после чата: score, evidence, role/tech/location fit, review flags, query/wave source, filters, сортировка, объяснения, shortlist и экспорт. `P8-001` зафиксировал Candidate Workspace v0 contract; `P8-002`, `P8-003`, `P8-004`, `P8-005`, and `P8-006.1` implemented консервативные candidate-workspace slices: mapper/workspace run state/table/read-only details, workspace view sorting/filtering поверх `workspaceCandidates`, local review state/derived shortlist/escaped notes/statuses, deterministic candidate-level explanations на базе returned workspace facts без влияния recruiter review state, затем explicit-action selected-candidate wording overlay через `POST /api/candidate-workspace/explanation-wording`. LLM может только переформулировать уже построенное deterministic explanation без изменения фактов, stable `reason_key`, reason codes, source/version, scoring, filters, review state или execution behavior; opening/selecting candidate must not call OpenAI. Implementation separates versioned frontend-to-backend request payload from versioned backend-to-OpenAI model payload, uses opaque non-URL `wording_target_key` in the request instead of URL-derived current `candidate_id`, rejects frontend-supplied prompt rules/hard boundaries/allowed numbers/OpenAI execution controls, treats candidate/user-derived summary/labels/facts/stack-location-query values as data rather than instructions, keeps backend-owned policy/schema instructions structurally separate from bounded data in the model payload, recomputes allowed numbers from user-visible wording fields only, recomputes request-level explanation fingerprint from sanitized request-bounded fields using UTF-8 canonical JSON/sha256 parity for request integrity/UI correlation only, validates wording-safe allowlisted bounded facts through an explicit facts mapper, keeps request correlation/cache/internal fields out of the OpenAI payload, rejects model-returned `warnings` in v1, uses Phase 7-aligned backend-owned provenance/fallback/no-call metadata, prevents duplicate in-flight requests through a separate `frontend_pending_key`, and reuses validated overlays through frontend current-run memory only. Wording is a separate non-mutating current-run overlay, uses explicit request/model payload contract versions plus reason semantics/canonicalizer provenance and exact candidate provenance values, enforces strict plain-text output caps with conservative v1 English validation that tolerates technology/location/query tokens, no-calls unsupported languages before OpenAI, validates backend-only model payload version internally before OpenAI, avoids backend session storage/backend candidate workspace memory, and avoids persistent storage/logging or backend-error/frontend-status exposure of raw wording payloads, backend-to-OpenAI model payloads, or raw model responses. This validation is not candidate-fact proof or latest-run proof; backend-owned candidate facts need a later backend producer or persistence task. `P8-007` завершен как локальный frontend-only export workflow: Excel-on-Windows-friendly CSV, deterministic Markdown, default `visible` scope, явные `visible`/`shortlisted`/`all` scopes, stable allowlisted fields, grouped export UI, current-run export state, click-time visible recomputation, local `Blob` download, bounded inline statuses, no raw candidate payload dump, no persistence/backend/API/search/runtime/Tavily/LinkedIn/outreach/account behavior. Shortlist/notes/statuses в Phase 8 являются browser in-memory session/local UI state до Phase 10, `workspace_run_id` имеет per-run компонент, а profile links остаются manual user-click только после safe LinkedIn URL validation. Узкие chat-flow улучшения вроде chat-confirmed `Build Plan` можно держать в Phase 8 backlog, если они не меняют execution boundary и сохраняют отдельный `Approve & Search` перед Tavily.
- Update after Bundles B/C: the earlier Phase 8 backlog idea of chat-confirmed technical planning is superseded by implemented `P8-024`; the current normal path can start search from a clean state-bound chat confirmation, and `P8-022` makes multi-wave the default selected execution mode.
- `P8-006` latest contract details: every current candidate-explanation reason code has explicit allowed wording meaning, forbidden wording meaning, and allowed wording-safe fact keys. Wording-safe facts must use controlled/normalized values, strip raw-ish `role` text from `role_or_technology_visible`, keep `stack_confirmed.terms` to normalized selected/recognized stack terms, allow nested `components`/`penalties` only through explicit top-level and nested allowlists, and fail a drift check if `EXPLANATION_REASON_CODES` changes without a reviewed wording contract/mapper/prompt/validator/test update. `P8-006.1` now implements structured/JSON-object preferred output and applies frontend response binding before rendering an LLM wording overlay: same `workspace_run_id`, same `wording_target_key`, same `request_explanation_fingerprint`, same language, and no stale workspace/candidate identity reset; mismatched late responses are discarded and deterministic `P8-005` wording remains visible.
- `P8-006` prompt/data separation detail: candidate/user-derived summary, labels, facts, stack/location terms, query-source ids/categories, and any instruction-like text inside bounded data fields are data, not instructions. `P8-006.1` backend-to-OpenAI payload construction keeps backend-owned policy/schema instructions separate from bounded data fields and prevents data-contained instructions from changing policy, output shape, reason keys/codes, facts, scores, provenance, or execution behavior.
- `P8-008` through `P8-016` are completed as bounded current-flow chat-quality hardening: optional bounded LLM onboarding wording with deterministic fallback, deterministic off-topic/noise routing before Search Brief extraction, conservative classification policy coverage, Russian pending-stack clarification answers, RU/EN next-iteration option localization, frontend/session-only chat-confirmed `Build Plan`, Enter-to-send, normalized visible `AI Assistant` speaker titles, and hardened pending clarification answer routing. `P8-032A` then completed the first recruiter-facing presentation cleanup slice: visible normal-flow labels now use `Prepare search`, `Run search`, `Search details`, `Search summary`, `Candidate workspace`, and `Search steps`; aggregate report metrics are collapsed by default; visible `Frontend ready` was removed; and backend/API/runtime contracts, approval payloads, fingerprints, Tavily execution path, query generation, scoring, filtering, dedupe, location logic, candidate facts, and export behavior remain unchanged. Follow-up review confirmed `P8-028` and `P8-029` are covered by `P8-032A`; `P8-027` is completed as Bundle D, removing query contribution details from recruiter UI while preserving backend report data. `P8-020` and `P8-021` are completed as a separate narrow frontend-only cleanup slice: default Recruiter Chat status is empty/hidden while preserving the dynamic status target, and the initial empty-chat helper uses warmer recruiter-facing wording. `P8-032B` completed the second conversation cleanup slice: harmless standalone small talk now receives deterministic friendly handling instead of generic off-topic redirect, draft/ready search-summary state is preserved with no stale clearing, greeting/near-empty onboarding still uses the approved bounded onboarding overlay, and EN/RU greeting plus unclear/noise fallbacks are more polite. `P8-032C` completed the third post-search chat cleanup slice: recruiter chat now shows only compact completion counts after search, Agent Response LLM wording is bounded to visible-message candidate/quality counts, and next-iteration option blocks are hidden from recruiter chat while backend non-executable option data remains available for future reviewed surfaces. `P8-032` is closed as the parent umbrella for these recruiter-facing conversation and workspace presentation improvements. This work preserves explicit human confirmation before Tavily and does not add autonomous execution, direct web-search bypass, direct LinkedIn access/login/scraping, candidate messaging, account actions, persistence, memory, new search sources, or country/technology expansion.
- Bundle A (`P8-031` + `P8-030`) is implemented and later refined by Phase 8.8 primary-workspace cleanup: `Candidate Results` is now the primary post-search surface before `Search summary`, desktop layout gives the candidate workspace more width, and candidate rows focus on score/identity/role/location/stack/source. After `P8.8-019` through `P8.8-024`, visible sort/filter/export controls, agentic guidance blocks, row-level review controls, and diagnostic details are hidden from the primary recruiter view while backend/runtime/search behavior remains unchanged.
- Bundle B (`P8-024`) is implemented: recruiter chat now treats a clean state-bound confirmation as explicit approval intent, then internally uses the existing safe `agent query-plan -> runtime prepare -> runtime execute` path without direct structured-search bypass.
- Bundle C (`P8-022`) is implemented: `Multi-wave` is now the default approved search mode in the primary UI/runtime path, while the visible toggle remains as an opt-out to single-wave and backend single/multi compatibility endpoints remain unchanged.
- Current recruiter-facing execution boundary after Bundle B/C: search can start from clean chat confirmation, but only through the existing backend runtime approval path; multi-wave is the default selected mode, and single-wave remains an explicit opt-out.

- Future direction after Phase 9 closeout: Phase 8 presentation, Phase 8.5 agentic candidate review, Phase 8.75 acceptance gates, Phase 8.8 recruiter-facing hardening, Phase 8.9 UI polish, Phase 9 multi-provider search expansion, Phase 9.5 final POC hardening/deploy, Phase 9.6 UX polish, Phase 9.7 semantic pending-answer interpretation, Phase 9.8 role anchoring, and Phase 9.9 AI Agent semantic-understanding hardening are completed. The POC is live on Render at `https://engineers-search-engine-poc.onrender.com/`. Phase 10+ persistence, manual evidence intake, and resume analysis are parked future tracks.
- Phase 8.5 - `Agentic Candidate Review & Iteration`: make the post-search workspace feel more agentic by letting the agent rank returned candidates, compare selected candidates, explain fit/gaps, and guide the next refinement from already returned workspace facts. `P8.5-001` completed the docs-only Agentic Candidate Review v0 contract and guardrail smoke; `P8.5-002` completed deterministic frontend-only top-candidate recommendation from current visible workspace facts; `P8.5-003` completed deterministic frontend-only selected-candidate comparison over current visible shortlisted candidates; `P8.5-004` completed deterministic frontend-only fit/gap explanation over visible shortlisted candidates; `P8.5-005` completed deterministic frontend-only non-executable review/refinement guidance from current visible workspace facts. This phase must not add autonomous execution, direct LinkedIn access, scraping, messaging, persistence, or new search providers.
- Phase 8.75 - `Recruiter UAT & Acceptance Gate`: completed green before Phase 9 multi-provider expansion and Phase 10 persistence. `P8.75-001` covered backend/runtime/workspace acceptance with deterministic no-live checks plus limited local live runtime execution; `P8.75.1-001` covered real frontend simulated-user conversation UX with Playwright and deterministic OpenAI/Tavily doubles, passing `116/116` scenarios. These gates must stay non-persistent and must not add autonomous execution, direct LinkedIn access/login/scraping, candidate messaging, account actions, or unreviewed providers.
- Phase 8.8 - `Recruiter Concern Backlog before Persistence`: completed as a bounded recruiter-facing conversation hardening slice before Phase 9 multi-provider search and Phase 10 persistence. Completed tasks: `P8.8-001` through `P8.8-024`. The result is bounded conversation intent recognition and wording hardening, bounded restart/update/refine routing, immediate user-message echo with assistant thinking state, suppression of redundant technical update bubbles, and a simplified recruiter-facing candidate workspace with compact chat, dominant Candidate Results, fixed-height pagination, and hidden primary sort/filter/export/review/diagnostic controls. The slice preserved the same no-autonomy/no-LinkedIn/no-scraping/no-messaging/no-account-actions/no-persistence boundaries.
- Phase 8.9 - `Recruiter UI Polish Backlog before Persistence`: completed as a small recruiter-facing UI polish slice. It removes stale assistant `Thinking...` bubbles after real responses, renders Candidate Results as a compact score-sorted table, keeps 5-10 rows visible through bounded pagination/scroll, and aligns the desktop Candidate Results panel height with Recruiter Chat.
- Phase 9 - `Multi-Provider Search Expansion`: completed as approved backend-provider search through Tavily, Serper, SerpApi Google 5-page review, and SerpApi Bing 5-page review in one approved search run. The backend normalizes provider results, preserves provider/query provenance, merges results, dedupes by normalized LinkedIn URL, and shows one unified Candidate Results set. This stays inside the approved runtime/search boundary and preserves approval, cost/latency limits, failure handling, no-secret logging, and no LinkedIn login/scraping/messaging/account actions.
- Phase 9.5 - `Final POC Hardening And Render Deployment`: completed final POC phase. See `docs/phase-9-5-final-poc-plan.md`. `P9.5-001` through `P9.5-007` are implemented and verified: Phase 10+ is parked, Phase 9 providers are unchanged, input is English-only, search supports any English IT role with role/main technology/stack/location, Candidate Results has polished empty/loading states, duplicate ready/search wording and visible `Workspace Ready` are removed, final regression is wired into `scripts/check_all.ps1`, and the POC is deployed to Render at `https://engineers-search-engine-poc.onrender.com/`.
- Phase 9.6 - `Post-Deploy Recruiter UX Polish`: completed narrow post-deploy UI/conversation polish through `P9.6-008`. Completed work shows manual safe LinkedIn profile links under candidate identity, removes low-value `Location` and `Stack` columns from the primary table, tightens the initial chat helper, increases the message input height, reduces chat action button height, replaces hardcoded stack-signal-only acceptance with bounded LLM IT/software relevance validation where deterministic recognition is insufficient, fixes the exact empty-chat default layout target, and removes old Ukraine-only behavior from pending location clarification. Safe English pending-location answers such as `Spain`, `Remote`, and `Madrid` are accepted, while technology/role/noise answers are rejected. The observed `Java only` pending-stack issue is intentionally moved to Phase 9.7 instead of being handled as another phrase-specific patch. This preserves manual user-click-only LinkedIn behavior and keeps backend/runtime search approval authoritative.
- Phase 9.7 - `Recruiter Chat Semantic Interpreter`: completed architectural correction for recruiter-chat understanding before any future persistence work. The phase introduced `PendingAnswerInterpreter v1`, a bounded LLM semantic interpreter contract, strict backend validator, incremental rollout for natural pending stack/location/update-refinement answers, shared pending clarification handling, and semantic conversation UAT. The implemented path is `message -> deterministic safety precheck -> bounded LLM semantic interpreter -> strict backend validator -> deterministic patch/action`, preserving human approval, no autonomous execution, no direct web-search bypass, no LinkedIn automation/scraping/messaging/account actions, and no persistence.
- Phase 9.8 - `Role-Anchored Query Planning And Scoring Guardrail`: completed post-deploy correction for global role drift. `P9.8-001` adds deterministic `RoleAliasPlan` metadata to rule-based query plans, rejects generic technology-only role phrases such as `Java Developer` for arbitrary target roles such as `QA Automation`, preserves explicitly configured domain plans such as `Backend Developer + Java`, and makes candidate scoring use approved role aliases as the strong role evidence set. Future bounded LLM role-alias expansion can be added behind the same backend validator, but this slice does not add a live LLM call inside the planner/runtime approval path.
- Phase 9.9 - `AI Agent Semantic Understanding Hardening`: completed through `P9.9-007`. This is the final POC AI Agent chat-understanding correction after Phase 9.8. `P9.9-001` added the isolated bounded `SearchBriefExtractor v2` foundation. `P9.9-002` added strict backend validation for extractor output, including domain-vs-technology guardrails and normalized Search Brief draft output. `P9.9-003` routes clean-state recruiter-chat requests through the validated extractor and blocks legacy clean-state fallback on extractor/validator failure. `P9.9-004` removed/guarded legacy clean-state role-only/role-label branches so they no longer compete with the extractor. `P9.9-005` added deterministic no-network semantic recruiter UAT and wired it into the full local regression baseline. `P9.9-006` added bounded Search Brief refinement interpretation for existing drafts, including backend-owned must-have/domain patch operations and no-legacy-fallback behavior when interpreter output is rejected. `P9.9-007` records the closeout decision in `docs/phase-9-9-closeout.md`. The phase replaces fragile clean-state initial message parsing and later brittle refinement parsing with bounded LLM extraction/interpretation plus strict backend validation. It did not change planner/scoring, providers, runtime approval, LinkedIn/account boundaries, or persistence.
- Phase 9.10 - `Global LocationGuard v1`: completed through `P9.10-001`. This post-POC hardening turns location validation into a global backend pattern instead of the old Ukraine-only filter availability. Every non-empty target location now receives a deterministic LocationGuard config: seeded country/city/domain aliases for common POC locations and exact-term fallback for unseeded locations. The backend hides explicit foreign-current-location, weak history-only, and unknown non-country-domain candidates when the guard is active, and the primary UI does not call a candidate `Strong match` when location is not confirmed.
- Phase 10 - `Persistent Memory + Saved Searches`: parked future phase; add storage for chat sessions, search briefs, runs, candidates, scores, shortlists, notes/statuses, and saved searches only if the POC is explicitly reopened.
- Phase 11 - `Manual Candidate Evidence Intake`: allow a recruiter to manually open a public profile, copy visible profile text, paste it into the app, and ask the agent to compare that user-provided evidence against the current Search Brief and candidate workspace. The app must not open LinkedIn, log in, scrape, automate browsing, bypass restrictions, message candidates, or act on any account.
- Phase 12 - `Resume Upload & Fit Analysis`: allow a recruiter to upload a resume/CV and receive a structured fit analysis against the current Search Brief, target stack, location expectations, and candidate criteria. Resume data is sensitive; storage, retention, masking, logging, and deletion rules must be explicit and should align with Phase 10 persistence/privacy decisions.

- Phase 10 - `Persistent Memory + Saved Searches`: добавить хранение chat sessions, search briefs, runs, candidates, scores, shortlists и saved searches, чтобы агент мог продолжать работу между сессиями и не терять контекст.

Phase 4 завершена как `AI Agent Foundation`. Phase 5 завершена как narrow Java/Ukraine Agent UX foundation. Phase 5.5 завершена как `Technical modularization before Agent Runtime`. Phase 6 завершена как `AI Agent Runtime v0 baseline`. Phase 7 завершена как `Agent Conversation Wording Layer v0 baseline`. Phase 7.5 завершена как `Recruiter Simulation QA & Flow Hardening` с решением `ready after approved fixes completed`. Phase 8.5 завершена через `P8.5-005`. Phase 8.75 `Recruiter UAT & Acceptance Gate` завершена green, включая `P8.75.1` real frontend simulated-user conversation UX. Phase 8.8 завершена как bounded recruiter-facing conversation hardening перед provider expansion / persistence. Phase 8.9 завершена как recruiter-facing UI polish. Phase 9 завершена как approved multi-provider backend search expansion. Phase 9.5, Phase 9.6, Phase 9.7, Phase 9.8, Phase 9.9, and Phase 9.10 are completed as final POC hardening, post-deploy polish, semantic chat interpretation, role anchoring, semantic Search Brief understanding, and global LocationGuard hardening; Phase 10+ remains parked unless the POC is explicitly reopened.

Критическое решение по дальнейшему пути: сначала доводим до качества один узкий flow `Backend Developer + Java + Ukraine`, а не расширяем страны/технологии. Phase 5 закрыла агентный UX на этом flow: onboarding, clarification, brief refinement, approved search, result-to-next-iteration loop и единый AI Agent visual style. Phase 5.5 модульно подготовила backend. Phase 6 добавила human-approved runtime baseline. Phase 7 закрыла controlled agent conversation wording layer без изменения state, tools, approval, Search Brief, QueryPlan, candidates, counts или execution actions. Phase 7.5 проверила текущий flow глазами рекрутера в RU/EN, нашла blockers, провела approved fixes и закрылась решением `ready after approved fixes completed`. Phase 8 превратила результаты поиска в рабочий recruiter artifact: candidate workspace/table, shortlist, notes/statuses и export workflow. `P8-001 Define candidate workspace contract`, `P8-002 Build recruiter-facing candidate table`, `P8-003 Add sorting and filtering by quality signals`, `P8-004 Add shortlist, notes, and statuses`, `P8-005 Add candidate-level agent explanations`, `P8-006.1 Implement explicit selected-candidate wording overlay`, `P8-007 Prepare export workflow`, `P8-008` through `P8-016`, `P8-020`, `P8-021`, `P8-032A`, `P8-032B`, `P8-032C`, and the `P8-032` parent umbrella are completed. Phase 8.5 completed `P8.5-001 Define agentic candidate review contract`, `P8.5-002 Add top-candidate recommendation from returned workspace facts`, `P8.5-003 Add selected-candidate comparison`, `P8.5-004 Add fit/gap explanation across selected candidates`, and `P8.5-005 Add guided next-refinement suggestions from workspace results`, so the agent can analyze already returned workspace facts without persistence or external actions. Phase 8.75 then passed backend/runtime/workspace and real frontend simulated-user conversation UX gates before Phase 9.

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
- `P4-010 Diagnose and improve AI planner coverage`
- `P4-011 Close Phase 4 with decision`

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

Статус `P4-009`: completed as no-Tavily AI planner baseline evaluation.

- Baseline: `Backend Developer + Java + Spring/Kafka + Ukraine`.
- Rule-based planner produced the expected 10-query baseline coverage.
- Live AI planner produced a formally valid but too narrow 1-query plan.
- Live `ai_with_fallback` produced a 3-query AI plan and did not fall back, because current validation checks structure/safety/alignment but not baseline coverage quality.
- Decision: keep `RuleBasedQueryPlanner v1` as default and only executable planner for now.
- Follow-up: before AI-generated plans can be executable, add a planner quality gate for coverage, role phrase diversity, and stack-focused slots.

Статус `P4-010`: implemented.

- Goal: diagnose why AI planner did not return the expected 10-query plan, improve planner coverage, and fallback when AI plan remains structurally valid but under-covered.
- AI planner should be prompted to produce the tested 10-query standard baseline rather than a minimal 1-query/3-query plan.
- Expected standard structure: role-based coverage plus stack-focused coverage.
- Standard baseline should not accept a 1-query or 3-query AI plan as good enough for Java Backend Ukraine.
- Quality gate should check coverage, role phrase diversity, and stack-focused slots.
- Implement this as a minimal `AIPlannerCoveragePolicy v0` with one strict supported policy for the current baseline, not as scattered Java/Ukraine checks in the validator.
- Implementation result: live no-Tavily OpenAI planner evaluation returned the expected 10-query plan for both `ai` and `ai_with_fallback`; mocked smoke covered one repair attempt and fallback after failed repair.
- AI remains useful for planning/explanation, but backend decides whether the plan is strong enough.
- Follow-up `P4-011` completed the docs-only closeout and moved the active product focus to Phase 5.

Статус `P4-011`: implemented as docs-only closeout.

- Close Phase 4 as `AI Agent Foundation`, not as a complete autonomous sourcing agent.
- Decision to capture: backend foundation is ready for Phase 5 because Search Brief, AI-assisted planning, deterministic validation/fallback, coverage policy, explanations, and approval-gated execution boundaries exist.
- Transition criterion to Phase 5: build recruiter chat/Search Brief conversation on top of the Phase 4 foundation.
- Keep explicit non-goals in the closeout: no full autonomous loop, no database/persistence, no shortlist/workspace, and no multi-source search beyond Tavily.
- Preserve absolute product boundaries as prohibited behavior: no direct LinkedIn access/automation, no LinkedIn login, no LinkedIn scraping or restriction bypass, no candidate messaging/automatic outreach, no autonomous execution, and no user or third-party account actions.
- Phase 5 is completed and closed; `P5-001 Define recruiter chat and Search Brief conversation contract` through `P5-012 Close Phase 5 with narrow Java/Ukraine agent UX decision` are completed.
- Phase 5.5 is completed and closed; `P5.5-001` through `P5.5-009` are completed.
- Phase 6 is completed and closed; `P6-001` through `P6-006` are completed, and `docs/phase-6-closeout.md` records Phase 6 as `AI Agent Runtime v0 baseline`.

Absolute product boundaries: запрещены direct web-search агентом в обход approved backend pipeline, direct LinkedIn access/automation, LinkedIn login, LinkedIn scraping, restriction bypass, автоматическая отправка сообщений кандидатам, автономное execution и любые действия с user или third-party accounts.

Не входит в Phase 4: persistent memory/database, shortlist, export, autonomous execution, fully autonomous tool-calling loop, полноценный recruiter chat UI, multi-source search beyond Tavily, private/personal data sources. Autonomous execution и fully autonomous loop запрещены; human-approved tool runtime относится к Phase 6, ordinary agent conversation wording к Phase 7, candidate workspace/shortlist/export к Phase 8, persistence/memory/saved searches к Phase 10.

Фазы 5-8 описывают путь к настоящему AI Agent внутри приложения. Agent здесь означает не просто чат, а AI-модель с целью, контекстом, инструментами, approval flow и циклом действий: понять задачу, собрать brief, запустить инструменты, оценить результат, уточнить план и вернуть кандидатов в виде таблицы.

Ориентир по пути к AI Agent:

- Минимум до надежного AI Agent v0: Phase 4 + Phase 5 + Phase 5.5 + Phase 6.
- Phase 4 дает foundation: `Search Brief`, LLM-assisted planning, AI planner mode, agent tools contract, deterministic validation, approval gates, fallback и объяснения.
- Phase 5 делает агентный UX через recruiter chat, согласованный `Search Brief`, refinement через follow-up и result-to-next-iteration loop на узком Java/Ukraine flow.
- Phase 5.5 технически готовит код к runtime: разделяет `app/main.py` на модули без изменения поведения.
- Phase 6 добавляет настоящий human-approved tool loop: агент планирует следующий шаг, готовит вызов доступных инструментов, выполняет execution только после approval, анализирует результат и предлагает итерацию.
- Phase 7 добавляет LLM-assisted Agent Conversation Wording Layer поверх стабильного runtime/message taxonomy, без права менять state, tools, approval, Search Brief, QueryPlan, candidates, counts или actions.
- Phase 7.5 добавила recruiter simulation QA gate: текущий Java/Ukraine flow проверен как живой рекрутер в RU/EN, с OpenAI для существующих путей и approved Tavily-backed execution через существующий UI/backend flow, когда сценарий этого требовал.
- Phase 8 теперь должна добавить реально удобный recruiter workflow: candidate workspace, shortlist, notes/statuses и рабочую таблицу кандидатов.
- Phase 10 добавляет persistence/memory, чтобы агент мог продолжать работу между сессиями.

Вывод: через Phase 5 + Phase 5.5 + Phase 6 получен надежный AI Agent v0 baseline для узкого Java/Ukraine flow. Phase 7 улучшила обычную речь агента после стабилизации runtime. Phase 7.5 проверила этот flow глазами рекрутера, закрыла approved fixes и дала Phase 8 readiness decision. Phase 8, Phase 9 и Phase 10 должны превратить этот foundation в полноценный recruiter workflow с рабочей таблицей, расширенным backend provider search и памятью между сессиями.

### Ideas

- Backend URL/profile filter should be visible to the user as a frontend toggle, not hidden backend behavior.
- Location rule: treat country-specific LinkedIn profile domains such as `ua.linkedin.com/in/...` as a location signal for Ukraine.
- Future country support must extend the location config with country domains and `target_location_terms`, then reuse current-location classification instead of building finite negative-location blacklists.
- Sequential multi-query search: run several focused Tavily queries, merge results, dedupe by normalized LinkedIn URL, then apply visible filters.
- Phase 3 multi-wave search should stop based on incremental unique gain. Recent experiments: 1 wave gave 60 unique, 3 waves gave 64 cumulative unique, one 5-wave block gave 61 cumulative unique, and one 10-wave block gave 60 cumulative unique.
- Phase 3 quality baseline confirms the quality layer is useful for ranking/review, but selected stack evidence is still weak in public Tavily/LinkedIn snippets.
- For selected stack terms that are not visible in Tavily public snippets, the UI now says `Not visible`; query-source-only stack evidence says `Not confirmed`.
- Real `P3-012` multi-wave evaluation produced 67 unique candidates after 4 waves and 40 Tavily queries; incremental gain over wave 1 was +7 unique candidates. Historical Phase 3 recommendation was to keep multi-wave explicit, but this was intentionally superseded by Phase 8 `P8-022`.
- `P3-013` historically kept single-wave as default and exposed multi-wave through a visible toggle. Current Phase 8 behavior after `P8-022`: the same visible toggle remains, but it is checked by default and acts as an opt-out to single-wave.
- `P3-014` closed Phase 3 and prepared the handoff to Phase 4. Phase 4 later completed as `AI Agent Foundation`: it preserved the `QueryPlan` contract, visible filters, existing executor/dedupe/report pipeline, Candidate Quality Layer, and added `Search Brief`, agent tool boundaries, AI planner mode, explanations, approval gates, and AI planner coverage validation.

### Planned

- Phase 9.9: `AI Agent Semantic Understanding Hardening` completed through `P9.9-007`. Includes bounded clean-state Search Brief extraction, strict validator, clean-state integration, legacy semantic-branch retirement, automated semantic recruiter UAT, bounded refinement interpreter v2, and closeout.
- Phase 10+ future tracks remain parked unless the POC is reopened.
- Phase 10: `Persistent Memory + Saved Searches` parked.

### In Progress

### Completed

- Phase 8.9: `Recruiter UI Polish Backlog before Persistence`.
- Phase 9: `Multi-Provider Search Expansion`.
- Phase 9.5: `Final POC Hardening And Render Deployment` through `P9.5-007`, deployed to Render.
- Phase 9.6: `Post-Deploy Recruiter UX Polish` through `P9.6-008`.
- Phase 9.7: `Recruiter Chat Semantic Interpreter` through `P9.7-008`.

- Phase 5: `Recruiter Chat UX + Search Brief conversation` - `P5-001` through `P5-012` are completed. Phase 5 is closed as a narrow Java/Ukraine Agent UX foundation.
- Phase 5.5: `Technical modularization before Agent Runtime` - `P5.5-001` through `P5.5-009` are completed. Phase 5.5 is closed as no-behavior-change backend modularization before Phase 6.
- Phase 6: `Tool-Calling Agent Runtime` - `P6-001` through `P6-006` are completed. Phase 6 is closed as `AI Agent Runtime v0 baseline`, not as a complete autonomous recruiter agent.
- Phase 7: `Agent Conversation Wording Layer` - `P7-001` through `P7-010` are completed. Phase 7 is closed as `Agent Conversation Wording Layer v0 baseline`.
- Phase 7.5: `Recruiter Simulation QA & Flow Hardening` - `P7.5-001` through `P7.5-011` are completed. Phase 7.5 is closed with the decision `ready after approved fixes completed`; see `docs/phase-7-5-closeout.md`.

### Phase 5 Approved Contract

`P5-001` defined the recruiter chat and `Search Brief` conversation contract before coding.

Approved decisions:

- Support both Russian and English recruiter messages.
- Ask one clarifying question at a time.
- Make recruiter chat the primary UX over time, replacing the current structured form.
- Show a normalized brief summary before `Build Plan`.
- Treat `Build Plan` as planner preview only, not Tavily execution.
- Use `rule_based` as the primary executable planner mode for chat `Build Plan` after `P5-004`, so supported briefs produce an approvable Search Plan. This is a safe agent-tool bridge, not a rollback from AI planning; preserve AI planner modes for the next reviewed step toward AI-assisted executable planning.
- Keep Tavily execution behind explicit backend approval.
- Preserve prohibited behavior as hard boundaries: no direct web-search bypass, no direct LinkedIn access/automation, no LinkedIn login, no LinkedIn scraping/restriction bypass, no candidate messaging/automatic outreach, no autonomous execution, and no user or third-party account actions.

Recommended implementation order after the contract:

- `P5-002 Add backend chat-to-brief adapter` - implemented.
- `P5-003 Replace structured form with recruiter chat UI` - implemented.
- `P5-004 Make Build Plan produce an approvable Search Plan` - implemented.
- `P5-005 Instantiate human-approved Agent v0 for Java/Ukraine baseline` - implemented.
- `P5-006 Add post-results Agent Response in chat` - implemented.
- `P5-007 Add LLM-assisted Agent Plan/Response with deterministic fallback` - implemented.
- `P5-007.1 Sync Phase 5 docs and tighten Agent Plan guardrail` - implemented.
- `P5-008 Chat onboarding and clarification quality` - implemented.
- `P5-009 Search Brief refinement through chat` - implemented.
- `P5-010 Result-to-next-iteration loop` - implemented.
- `P5-011 Apply AI Agent visual direction / dark workspace refresh` - implemented.
- `P5-012 Close Phase 5 with narrow Java/Ukraine agent UX decision` - implemented.

Phase 5 closeout result:

- keep the product focused on `Backend Developer + Java + Ukraine`;
- make chat capable of collecting and refining the `Search Brief`;
- keep `Agent Plan` and `Build Plan` separate from Tavily execution;
- require explicit approval for search and multi-wave search;
- after results, let the agent guide the recruiter toward the next iteration without executing it automatically.
- apply a coherent dark AI Agent workspace style inspired by the first MVP visual direction, without copying its layout.
- keep broader communication scenarios and ordinary LLM-assisted recruiter chat wording for Phase 7 after the Phase 6 runtime/message taxonomy is stable.

After Phase 5, Phase 5.5 should modularize the backend before Phase 6. Do not start Phase 6 tool runtime directly on the current monolithic `app/main.py`.

Phase 5.5 progress:

- `P5.5-001` completed the docs-only module-boundary and migration-order decision.
- `P5.5-002` extracted shared schemas, domain config, text helpers, structured search validation, and Search Brief validation/adapter/fingerprinting into focused modules while preserving behavior and `main.*` compatibility.
- `P5.5-003` extracted rule-based planner, QueryPlan fingerprint helpers, planner explanation, deterministic AI QueryPlan prompt/validation/coverage helpers, and related shared planner config while preserving behavior and `main.*` compatibility.
- `P5.5-004` extracted Tavily/query-wave execution and structured-search snapshot helpers while preserving behavior and `main.*` compatibility.
- `P5.5-005` extracted Candidate Quality producer logic into `app/candidate_quality.py`, moved Candidate Quality constants to `app/domain_config.py`, moved shared profile text/ordering helpers to `app/text_utils.py`, and preserved `main.*` compatibility without behavior changes.
- `P5.5-006` extracted Agent Tools v0 contract/approval helpers into `app/agent_tools.py` and deterministic Agent Plan helpers into `app/agent_plan.py`, while preserving `main.*` compatibility and current validation/wording wrapper behavior.
- `P5.5-006.1` added `scripts/check_all.ps1` and GitHub Actions CI so local and remote regression checks run the same compile/frontend/smoke baseline before the riskier Agent Response extraction.
- `P5.5-007` extracted shared brief patch helpers into `app/brief_patch.py`, deterministic Agent Response logic into `app/agent_response.py`, and bounded Agent Plan/Response wording logic into `app/agent_wording.py`, while preserving `main.*` compatibility and wording monkeypatch behavior.
- `P5.5-008` split FastAPI path decorators and thin route wrappers into `app/routes.py` behind `RouteDependencies`, while preserving `app/main.py` route-facing service functions, route path/method set, endpoint names, `main.*` compatibility, and smoke-test monkeypatch behavior.
- `P5.5-009` added route/import/no-network HTTP smoke coverage to the regression baseline and closed Phase 5.5.
- `P6-001 Define human-approved Agent Runtime contract` is completed as the docs-only runtime contract.
- `P6-002 Implement typed tool registry and tool-call envelopes` is completed as backend-only typed registry/envelope foundation code: typed Agent Tool definitions, internal Agent Runtime envelopes, deterministic fingerprints/idempotency keys, deny-by-default proposal validation, and no-network smoke coverage. It did not add runtime endpoints, frontend action queue, Tavily/OpenAI calls, tool execution, or structured-search approval behavior changes.
- `P6-003 Add frontend agent action review queue` is completed as frontend-only/status-only UI work: the queue shows `Build Search Plan` and `Run Search` action state, approval requirement, source, fingerprint context, query count, and single-wave vs multi-wave mode while preserving existing `Build Plan` and `Approve & Search` controls. It did not add backend routes, runtime endpoints, Tavily/OpenAI calls, API contract changes, new execution handlers, or autonomous execution.
- `P6-004 Implement first approved tool loop for Java/Ukraine baseline` is completed as the first real approved runtime execution slice: `POST /api/agent/runtime/turn` supports stateless `prepare` and `execute_approved` for execution tools only, validates backend-owned fingerprints/context, bridges valid runtime approval into existing `ExecutionApproval`, and routes frontend `Approve & Search` through the Agent Runtime path without direct structured-search fallback.
- `P6-005 Add runtime guardrail and stale-approval regression tests` is completed as no-network runtime hardening: stale/mutated approval, runtime context mismatch, unsafe frontend-owned fields, frontend runtime-only path, valid mocked execution, and missing-key guardrails are covered in `scripts/check_all.ps1`.
- `P6-005.1 Fix runtime execution wrapper recursion and add unmocked runtime execution smoke` is completed: real single/multi runtime execution wrappers now call the existing approved pipelines instead of recursing, and no-network unmocked-wrapper smoke coverage is part of `scripts/check_all.ps1`.
- `P6-006 Close Phase 6 with AI Agent v0 decision` is completed: Phase 6 is closed as `AI Agent Runtime v0 baseline`, the closeout decision is recorded in `docs/phase-6-closeout.md`, and Phase 7 became the active direction at that point.
- `P7-001 Define agent message taxonomy and lifecycle mapping` is completed. `P7-002 Define message facts and source-of-truth contract` is completed with `docs/phase-7-message-facts-contract.md`. `P7-003 Define agent wording style and language policy` is completed with `docs/phase-7-agent-wording-style-policy.md`. `P7-004 Build deterministic source messages for approved message types` is completed with the backend-first deterministic source-message helper layer and smoke coverage.

`P5-002` implementation result: added `POST /api/recruiter-chat/turn`, strict OpenAI/ChatGPT JSON extraction, deterministic refusal for prohibited requests, deterministic supported-signal hints, Ukraine alias normalization, conservative draft merge, existing Search Brief validation, one next clarification question, default `recommended_planner_mode = rule_based` after `P5-004`, and no-Tavily smoke coverage. Guardrail preserved: `chat messages -> draft Search Brief -> validation -> one assistant response`; it does not grow into an agent loop.

`P5-003` implementation result: the primary frontend input is now recruiter chat. Search execution uses `adapted_structured_request` from the planner response, not stale structured-form DOM fields. The implemented path is `chat -> normalizedBrief -> Build Plan -> adapted_structured_request/query_plan -> Approve & Search`. AI draft plans remain visible but non-executable; rule-based and rule-based fallback plans remain the executable paths behind approval.

`P5-004` implementation result: the recruiter-facing flow is now `Chat -> Search Brief -> Build Plan -> Review Search Plan -> Approve & Search -> Results`. The primary `Build Plan` action produces an approvable deterministic backend plan for supported briefs by using `planner_mode = rule_based`. This gives the AI Agent path a working executable tool and approval gate now; the existing AI planner capability is preserved for the next reviewed step toward validated AI-assisted executable planning, explanation, comparison, diagnostics, and iterative agent work.

`P5-005` implementation result: after a ready supported Java/Ukraine Search Brief, the UI calls `POST /api/agent/plan`, shows an Agent Plan in chat, and enables `Build Plan` only from the supported `agent_plan.proposed_action`. The action points to `/api/agent/query-plan` with `planner_mode = rule_based`; the backend validates the Search Brief fingerprint and rejects stale or mismatched actions. This instantiates Agent v0 without adding autonomous execution, Tavily calls before approval, direct LinkedIn access, persistence, generic tool loops, or new LLM behavior.

`P5-006` implementation result: approved search responses now return deterministic backend-generated `agent_response` grounded only in executed QueryPlan/request/report/results/quality data. The frontend passes minimal `agent_language`, shows the response as a local-only `AI Agent` chat message after results, and keeps suggested next actions inert text. No extra Tavily/LLM/web/LinkedIn calls, broad agent context, autonomous execution, persistence, or executable next-action buttons were added.

Implemented `P5-007` result:

- Agent Plan and Agent Response wording can be LLM-assisted when OpenAI is configured.
- Deterministic fallback remains available without OpenAI configuration or when LLM output is unsafe/invalid.
- LLM wording is backend-only, bounded to text overlay fields, and has no execution authority.

Implemented `P5-007.1` stabilization result:

- Phase 5 docs are synchronized after work from another computer.
- `README.md` and `AGENTS.md` now agree that `P5-007` is implemented.
- Current recruiter chat / AI planner paths explicitly require `OPENAI_API_KEY` and `OPENAI_MODEL`; LLM-assisted wording still has deterministic fallback.
- `/api/agent/query-plan` now requires the current Agent Plan action and Search Brief fingerprint so backend behavior matches the approved Agent v0 flow.
- Handoff details for another workstation are summarized in `docs/phase-5-agent-stabilization.md`.

Implemented `P5-008` result:

- Recruiter chat handles greeting-only RU/EN messages deterministically before OpenAI extraction.
- Greeting-only and near-empty turns do not call OpenAI and do not create a ready `Search Brief`.
- Existing draft briefs are preserved when the recruiter sends a greeting/near-empty message.
- Safety refusal remains first before onboarding/LLM extraction.
- Planner, Tavily execution, scoring, filters, dedupe, location logic, Agent Plan, Agent Response, and Search Brief refinement were not changed.

Implemented `P5-009` result:

- Recruiter chat can refine an existing `Search Brief` through deterministic `brief_patch.operations`.
- Supported baseline operations include Java stack add/remove/replace, seniority, and search depth.
- Patches are atomic; unsupported mixed patches do not apply partial valid changes.
- Removing the last stack item is blocked unless a valid replacement is in the same patch.
- Backend returns `brief_changed` and `stale_state_should_clear`.
- Frontend clears stale Agent Plan, Build Plan, QueryPlan, approval/results UI, and Agent Response only when `stale_state_should_clear = true`.
- Chat refinement still does not call Tavily, build QueryPlan, execute search, or expand beyond Java/Ukraine.

Implemented `P5-010` result:

- Approved search responses now include deterministic `agent_response.next_iteration_options`.
- Each option has `id`, `label`, `reason`, `proposed_brief_patch`, `requires_approval_before_execution = true`, and `is_executable_now = false`.
- Options are grounded only in returned QueryPlan/report/results/quality data and are not generated or selected by LLM wording.
- Frontend displays options as readable Agent Response text and adds no Apply/action buttons.
- `search_depth` is preserved as metadata in the adapted structured request and QueryPlan input snapshot, so `search_depth = deep` suggestions are grounded.
- Option generation does not call Tavily, LinkedIn, web search, Build Plan, `/api/agent/query-plan`, multi-wave, or any autonomous execution.

Implemented `P5-011` result:

- Applied a CSS-first/UI-only dark AI Agent visual refresh.
- Added dark workspace tokens, layered navy/charcoal surfaces, teal/cyan action/status accents, darker controls, compact panels/cards, report metrics, candidate cards, review flags, and score details.
- No backend code, `index.html`, `app.js`, API contracts, request payloads, state semantics, event flow, search behavior, or product logic changed.
- The old MVP layout was not copied and no new product features were added.

### Done

- Phase 2 - Multi-query Search + Baseline Query Planner.
- Phase 3 - Candidate Quality Layer.
- Phase 4 - AI Agent Foundation.
