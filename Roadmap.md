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



Фаза 2

Multi-query search engine.

Цель Phase 2: перейти от одного ручного Boolean-запроса к поисковому движку, который по одному сценарию запускает несколько точных Tavily-запросов, объединяет результаты, убирает дубли и показывает один список кандидатов.

Главная гипотеза: несколько focused queries дают лучшее покрытие кандидатов, чем один широкий универсальный query.

Базовый сценарий Phase 2: Java programmer in Ukraine.

Рекомендуемый первый набор запросов:

- U02: `site:linkedin.com/in AND "Java Software Engineer" AND "Ukraine"`
- U10: `site:linkedin.com/in AND "Java Programmer" AND "Ukraine"`
- U08: `site:linkedin.com/in AND ("Java Developer" OR "Java Engineer" OR "Backend Java") AND ("Ukraine" OR "Kyiv" OR "Lviv")`

Ожидаемый результат по текущим тестам: примерно 24-30 уникальных украинских LinkedIn-профилей за один multi-query проход после dedupe. Простая сумма U02 + U10 + U08 равна 38, но часть кандидатов повторяется между запросами.

Порядок реализации:

- Сначала backend multi-query runner: последовательно выполнить несколько Tavily queries.
- Потом нормализация и объединение результатов.
- Потом dedupe по normalized LinkedIn URL.
- Потом применение видимых фильтров `LinkedIn profiles only` и `Ukraine LinkedIn domain only`.
- Потом вывод одного общего списка кандидатов во frontend.
- Потом counts: raw total, displayed, unique profiles, duplicates removed, hidden by profile filter, hidden by Ukraine domain filter.
- Потом query source metadata: показывать, из какого query найден кандидат; если кандидат найден несколькими query, сохранить все query sources.
- Потом scoring для multi-query: бонус за совпадение в нескольких query sources.
- Потом итоговый Phase 2 прогон и документирование результатов.

Критерий успеха Phase 2:

- По базовому Java/Ukraine сценарию получить не менее 20 уникальных украинских LinkedIn-профилей за один multi-query проход.
- Пользователь должен видеть, какие фильтры включены и сколько результатов они скрыли.
- Пользователь должен видеть итоговый deduped список, а не разрозненные результаты по каждому query.

Не входит в Phase 2 без отдельного согласования:

- LinkedIn login.
- Scraping или обход ограничений LinkedIn.
- База данных.
- Shortlist.
- AI agent.
- Multi-source search beyond Tavily.
- Автоматическое открытие и парсинг LinkedIn-профилей.

### Ideas

- Backend URL/profile filter should be visible to the user as a frontend toggle, not hidden backend behavior.
- Location rule: treat country-specific LinkedIn profile domains such as `ua.linkedin.com/in/...` as a location signal for Ukraine.
- Sequential multi-query search: run several focused Tavily queries, merge results, dedupe by normalized LinkedIn URL, then apply visible filters.

### Planned

### In Progress

### Done
