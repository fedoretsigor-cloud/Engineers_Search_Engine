# Project Status

## Current phase

Phase 1 POC completed successfully and was accepted as a proof of concept.

Phase 1.1 - POC behavior tuning is completed.

Phase 2 - Multi-query Search + Baseline Query Planner is completed.

Completed through `P2-013`: Phase 2 conclusions are documented, local structured-search snapshots are available, and the Ukraine `Location filter` now uses current-location classification instead of a finite foreign-location blacklist.

Phase 3 - Candidate Quality Layer is completed.

Phase 4 - AI Agent Foundation is completed.

Current phase: `Phase 8.5 - Agentic Candidate Review & Iteration`.

Completed Phase 8 implementation slices include `P8-002` through `P8-006.1` and completed `P8-007` / `P8-007B`: Phase 4 is closed as an AI Agent Foundation, Phase 5 is closed as a narrow Java/Ukraine Agent UX foundation, Phase 5.5 is closed as technical modularization before Agent Runtime, Phase 6 is closed as `AI Agent Runtime v0 baseline`, Phase 7 is closed as `Agent Conversation Wording Layer v0 baseline` in `docs/phase-7-closeout.md`, Phase 7.5 is closed as `Recruiter Simulation QA & Flow Hardening` in `docs/phase-7-5-closeout.md` with the decision `ready after approved fixes completed`, and Phase 8 now has the docs-only Candidate Workspace v0 contract in `docs/phase-8-candidate-workspace-contract.md`. `P8-002 Build recruiter-facing candidate table`, `P8-003 Add sorting and filtering by quality signals`, `P8-004 Add shortlist, notes, and statuses`, `P8-005 Add candidate-level agent explanations`, `P8-006.1 Implement explicit selected-candidate wording overlay`, `P8-007A Implement export model and serializers`, and `P8-007B Add export UI and download workflow` are implemented as conservative candidate-workspace slices: approved search results map into explicit workspace state, sorting/filtering operate only over already returned candidates, review status/shortlist/notes remain browser in-memory only, deterministic candidate explanations are grounded only in returned workspace facts, selected-candidate explanation wording is an explicit backend-owned validated LLM overlay with deterministic fallback, and export is a local frontend-only workflow with allowlisted model/CSV/Markdown helpers plus explicit UI/download glue and no backend/runtime behavior. Phase 7 delivered the docs-only `Agent Message Taxonomy V0` contract in `docs/phase-7-agent-message-taxonomy.md`, the docs-only `Agent Message Facts Contract V0` in `docs/phase-7-message-facts-contract.md`, the docs-only `Agent Wording Style and Language Policy V0` in `docs/phase-7-agent-wording-style-policy.md`, the backend-first deterministic source-message helper layer in `app/agent_messages.py`, the docs-only `LLM Routing and Gating Policy V0` in `docs/phase-7-llm-routing-gating-policy.md`, the docs-only `Bounded LLM Wording Payload and Prompt Contract V0` in `docs/phase-7-bounded-llm-payload-prompt-contract.md`, code-level wording validation/fallback/provenance metadata in `app/agent_wording.py`, frontend typed rendering for current agent chat messages in `app/static/app.js`, and no-network golden conversation regression coverage in `scripts/smoke_p7_golden_conversations.py`. Phase 6 delivered the human-approved runtime contract, typed backend registry/envelope helpers, frontend Agent Action Review Queue, first approved runtime execution loop for the Java/Ukraine baseline, runtime guardrail regression coverage, repaired real runtime wrapper execution, and a dedicated closeout decision. The backend has Search Brief validation/adapter, extracted rule-based planner and deterministic AI QueryPlan validation modules, extracted Tavily/query-wave execution and snapshot modules, extracted Candidate Quality module, extracted Agent Tools/Agent Plan modules, extracted Agent Response/brief patch/Agent wording modules, extracted deterministic Agent Messages, extracted FastAPI route wrappers, typed Agent Runtime registry/envelope helpers, `POST /api/agent/runtime/turn`, route/import/runtime guardrail/unmocked-wrapper no-network HTTP smoke coverage in the regression baseline, local regression check script, GitHub Actions CI, Agent Tools v0 metadata, explicit AI planner mode, deterministic AI QueryPlan validation/fallback, planner explanation UI, backend approval before Tavily execution, AI planner baseline evaluation, AI planner coverage policy/repair behavior, `POST /api/recruiter-chat/turn`, `POST /api/agent/plan`, `agent_response`, and `agent_response.next_iteration_options` on approved search responses. The frontend starts from recruiter chat, shows typed current agent messages and current agent actions as a review/status queue, and `Approve & Search` uses the Agent Runtime path instead of direct structured-search execution. This is still not a complete autonomous recruiter agent.

Completed Phase 5 tasks: `P5-001 Define recruiter chat and Search Brief conversation contract`, `P5-002 Add backend chat-to-brief adapter`, `P5-003 Replace structured form with recruiter chat UI`, `P5-004 Make Build Plan produce an approvable Search Plan`, `P5-005 Instantiate human-approved Agent v0 for Java/Ukraine baseline`, `P5-006 Add post-results Agent Response in chat`, `P5-007 Add LLM-assisted Agent Plan/Response with deterministic fallback`, `P5-007.1 Sync Phase 5 docs and tighten Agent Plan guardrail`, `P5-008 Chat onboarding and clarification quality`, `P5-009 Search Brief refinement through chat`, `P5-010 Result-to-next-iteration loop`, `P5-011 Apply AI Agent visual direction / dark workspace refresh`, `P5-012 Close Phase 5 with narrow Java/Ukraine agent UX decision`.

Completed Phase 5.5 tasks: `P5.5-001 Define backend module boundaries and migration order`, `P5.5-002 Extract shared schemas, domain config, and Search Brief validation/adapter`, `P5.5-003 Extract rule-based planner and deterministic AI QueryPlan validation modules`, `P5.5-004 Extract search executor, Tavily, snapshots, and multi-wave modules`, `P5.5-005 Extract Candidate Quality module`, `P5.5-006 Extract Agent Tools and Agent Plan modules`, `P5.5-006.1 Add local regression check script and GitHub Actions CI`, `P5.5-007 Extract Agent Response and bounded wording/OpenAI modules`, `P5.5-008 Split FastAPI routes from domain logic`, `P5.5-009 Run no-behavior-change regression checks and close Phase 5.5`.

Completed Phase 6 tasks: `P6-001 Define human-approved Agent Runtime contract`, `P6-002 Implement typed tool registry and tool-call envelopes`, `P6-003 Add frontend agent action review queue`, `P6-004 Implement first approved tool loop for Java/Ukraine baseline`, `P6-005 Add runtime guardrail and stale-approval regression tests`, `P6-005.1 Fix runtime execution wrapper recursion and add unmocked runtime execution smoke`, `P6-006 Close Phase 6 with AI Agent v0 decision`.

Completed Phase 7 tasks: `P7-001 Define agent message taxonomy and lifecycle mapping`, `P7-002 Define message facts and source-of-truth contract`, `P7-003 Define agent wording style and language policy`, `P7-004 Build deterministic source messages for approved message types`, `P7-005 Define LLM routing and gating policy for conversation wording`, `P7-006 Add bounded LLM wording payloads and prompt contract`, `P7-007 Add wording validation, fallback, and provenance metadata`, `P7-008 Add frontend rendering for typed agent messages`, `P7-009 Add golden conversation scenario regression tests`, `P7-010 Close Phase 7 with wording quality and guardrail evaluation`.

Completed Phase 7.5 tasks: `P7.5-001 Define Phase 7.5 QA gate and pause Phase 8 implementation`, `P7.5-002 Define RU/EN recruiter simulation scenarios`, `P7.5-003 Prepare safe browser QA checklist with approved Tavily execution when needed`, `P7.5-004 Run RU browser QA with approved Tavily execution when needed`, `P7.5-005 Run EN browser QA with approved Tavily execution when needed`, `P7.5-006 Create recruiter simulation QA findings report`, `P7.5-007 Review and approve current-flow fixes`, `P7.5-008 Implement approved critical current-flow fixes`, `P7.5-009 Add regression coverage for fixed issues`, `P7.5-011 Implement immediate EN/mixed hardening fixes`, `P7.5-010 Close Phase 7.5 with Phase 8 readiness decision`, `P7.5-012 Backfill RU regression hardening for chat control signals`.

Completed Phase 8 tasks: `P8-001 Define candidate workspace contract`, `P8-002 Build recruiter-facing candidate table`, `P8-003 Add sorting and filtering by quality signals`, `P8-004 Add shortlist, notes, and statuses`, `P8-005 Add candidate-level agent explanations`, `P8-006 Define bounded candidate explanation wording contract`, `P8-006.1 Implement explicit selected-candidate wording overlay`, `P8-007 Prepare export workflow`, `P8-007A Implement export model and serializers`, `P8-007B Add export UI and download workflow`, `P8-008 Add bounded LLM onboarding wording overlay`, `P8-009 Add off-topic and unclear input guardrails before Search Brief extraction`, `P8-010 Define conservative off-topic and unclear/noise classification policy`, `P8-011 Apply Russian answers to pending clarification fields`, `P8-012 Localize next iteration options in Agent Response`, `P8-013 Add chat-confirmed Build Plan action`, `P8-014 Add Enter-to-send chat input behavior`, `P8-015 Normalize chat assistant speaker title`, `P8-016 Harden pending clarification answer routing`, `P8-020 Remove redundant Recruiter Chat helper subtitle`, `P8-021 Make initial chat helper prompt warmer`, `P8-024 Replace technical plan UX with conversational search confirmation`, `P8-022 Make multi-wave the default approved search mode`, `P8-027 Hide query contribution diagnostics from recruiter UI`, `P8-028 Collapse report metrics behind unique-candidate summary`, `P8-029 Remove frontend-ready status badge from recruiter UI`, `P8-030 Rebalance desktop layout toward candidate workspace`, `P8-031 Make candidate table the primary post-search surface`, `P8-032A Recruiter-facing language policy and visible-term cleanup`, `P8-032B Chat tone and harmless small-talk cleanup`, `P8-032C Post-search chat cleanup`, and `P8-032 Define recruiter-facing AI conversation and workspace presentation policy`.

Completed Phase 8.5 tasks: `P8.5-001 Define agentic candidate review contract`, `P8.5-002 Add top-candidate recommendation from returned workspace facts`, `P8.5-003 Add selected-candidate comparison`.

After Phase 7 closeout, Phase 7.5 was inserted as the QA gate before Phase 8. Phase 7.5 is now closed with the readiness decision `ready after approved fixes completed`. Phase 8 is closed through `P8-032`, and Phase 8.5 is active with `P8.5-001`, `P8.5-002`, and `P8.5-003` completed. `P8-001` is completed as the Candidate Workspace v0 contract and `P8-002 Build recruiter-facing candidate table`, `P8-003 Add sorting and filtering by quality signals`, `P8-004 Add shortlist, notes, and statuses`, `P8-005 Add candidate-level agent explanations`, `P8-006 Define bounded candidate explanation wording contract`, `P8-006.1 Implement explicit selected-candidate wording overlay`, `P8-007 Prepare export workflow`, `P8-007A Implement export model and serializers`, and `P8-007B Add export UI and download workflow` are implemented/completed. The current workspace is frontend-only except for the bounded wording endpoint: `P8-002` created the mapper, workspace run state, recruiter-facing table/list, and read-only candidate details; `P8-003` added workspace view sorting/filtering over `workspaceCandidates`; `P8-004` added frontend review state, derived shortlist, escaped plain-text notes, and review-status/shortlist view filters; `P8-005` added deterministic structured candidate explanations in candidate details; `P8-006` completed the docs-only bounded candidate explanation wording contract without code behavior changes; `P8-006.1` implemented explicit selected-candidate wording through `POST /api/candidate-workspace/explanation-wording`; `P8-007A` added DOM-free export model/CSV/Markdown serializers, filename/MIME helpers, text/URL sanitization, and helper smoke coverage; `P8-007B` added grouped export controls, current-run export state, export-specific event delegation, click-time visible recomputation, explicit local Blob/object URL download glue, bounded statuses, CSS, and no-network wiring smoke coverage without backend/runtime behavior. `P8-006.1` has no Agent Runtime/search/export/account action behavior, no auto-call on candidate open/select, no default local/CI live OpenAI, no backend session storage or backend candidate workspace memory, frontend current-run overlay reuse only, v1 `en` only, request construction from structured deterministic explanation data rather than DOM text, and escaped/plain-text rendering only. `P8-006` is the approved contract-first bounded candidate explanation wording task with stable `reason_key`, locked deterministic source/version, separate versioned frontend-to-backend request payload and backend-to-OpenAI model payload, bounded request validation, backend-recomputed allowed numbers from user-visible wording fields, request-level explanation fingerprint with UTF-8 canonical JSON/sha256 parity for request integrity/UI correlation only, separate frontend pending key and backend cache key, wording-safe allowlisted bounded facts mapper, explicit-action routing, wording-target and contract validation, semantic guardrails for all reason codes, Phase 7-aligned backend-owned provenance/fallback/no-call metadata, duplicate-call protection expectations, and deterministic fallback requirements. The contract explicitly says backend wording validation is contract/integrity validation, not candidate-fact verification or latest-run proof; candidate fact truth remains the frontend deterministic `P8-005` explanation until a later backend explanation producer or workspace-run persistence task is reviewed. It also forbids sending current workspace `candidate_id` to the wording payload when it can contain `normalized_url`; request correlation uses an opaque non-URL `wording_target_key` that is stable only within the current workspace run, frontend in-flight duplicate prevention uses a separate `frontend_pending_key`, validated overlay reuse uses frontend current-run memory plus backend-owned `backend_wording_cache_key` metadata, and request correlation/cache/internal fields are not sent to OpenAI. Frontend-supplied prompt rules/hard boundaries/allowed numbers/OpenAI execution controls are not trusted, and model-returned `warnings` are not part of the first candidate-explanation output shape. Prompt/data separation is explicit: candidate/user-derived summary, labels, facts, stack/location terms, and query-source values are data, not instructions, and backend-to-OpenAI payload construction keeps backend-owned policy/schema instructions separate from bounded data fields. Wording is a separate non-mutating current-run overlay, uses explicit request/model payload contract versions plus reason semantics/canonicalizer provenance and exact candidate provenance values, enforces strict plain-text output caps with conservative v1 English validation that tolerates technology/location/query tokens, no-calls unsupported languages before OpenAI, validates backend-only model payload version internally before OpenAI, and avoids persistent storage/logging or backend-error/frontend-status exposure of raw wording payloads, backend-to-OpenAI model payloads, or raw model responses. `P8-007` is now a completed local frontend-only export workflow with no backend/API/search/runtime/Tavily/OpenAI/LinkedIn calls, no persistence/browser storage, no outreach, no account actions, and no autonomous execution. Historical Phase 7.5 QA used Tavily only when a scenario required it, and only through the existing approved backend pipeline and explicit `Approve & Search` flow: recruiter chat -> Search Brief -> Agent Plan -> Build Plan -> visible QueryPlan -> explicit approval -> approved Tavily-backed results.

`P8-006` latest contract details: every current explanation reason code now has an explicit allowed wording meaning, forbidden wording meaning, and allowed wording-safe fact keys. Wording-safe facts must use controlled/normalized values, strip raw-ish `role` text from `role_or_technology_visible`, keep `stack_confirmed.terms` to normalized selected/recognized stack terms, allow nested `components`/`penalties` only through explicit top-level and nested allowlists, and fail a drift check if `EXPLANATION_REASON_CODES` changes without a reviewed wording contract/mapper/prompt/validator/test update. `P8-006.1` prefers JSON-object/structured output when available and applies frontend response binding before rendering an LLM wording overlay: same `workspace_run_id`, same `wording_target_key`, same `request_explanation_fingerprint`, same language, and no stale workspace/candidate identity reset. Mismatched late responses are discarded and deterministic `P8-005` wording remains visible.

`P8-006` prompt/data separation detail: candidate/user-derived summary, labels, facts, stack/location terms, query-source ids/categories, and any instruction-like text inside bounded data fields are data, not instructions. `P8-006.1` backend-to-OpenAI payload construction keeps backend-owned policy/schema instructions separate from bounded data fields and prevents data-contained instructions from changing policy, output shape, reason keys/codes, facts, scores, provenance, or execution behavior.

`P8-007` latest implementation status: implemented and completed. `P8-007A` is completed as the DOM-free export model/CSV/Markdown serializer/helper-smoke slice. `P8-007B` is completed as the explicit UI/download task with grouped controls, current-run export state, local Blob/object URL download glue, bounded status, CSS, and no-network export UI wiring smoke coverage.

`P8-008` through `P8-016` are implemented as bounded current-flow chat-quality hardening. The batch adds optional bounded LLM onboarding wording with deterministic fallback, deterministic pre-extraction off-topic/noise guardrails, the approved conservative classification policy in code, Russian pending-stack clarification answers, RU/EN next-iteration option localization, frontend/session-only chat-confirmed `Build Plan`, Enter-to-send, unified visible `AI Assistant` speaker titles, and deterministic pending clarification answer routing. `P8-016` keeps pending location/stack acceptance field-specific, preserves drafts on unrelated answers, treats unsupported pending-location answers such as Poland as unsupported for the current Java/Ukraine baseline, and asks the next missing clarification after valid different-field refinements while a brief remains incomplete. This batch preserved the explicit approval boundary then in place; after `P8-024`, current search execution can also start from clean state-bound recruiter chat confirmation, but still only through the backend runtime approval path. It does not add autonomous execution, direct web-search bypass, direct LinkedIn access/login/scraping, candidate messaging, account actions, persistence, memory, new sources, or country/technology expansion.

`P8-032A` is implemented as the first recruiter-facing presentation cleanup slice. The normal UI now uses recruiter-readable labels such as `Prepare search`, `Run search`, `Search details`, `Search summary`, `Candidate workspace`, and `Search steps`; aggregate report metrics are collapsed by default; and no-network assertions guard against returning visible internal terms such as `Generated QueryPlan`, `Agent Actions`, `Approve & Search`, `Frontend ready`, and `deduped candidates`. Follow-up review of `P8-027`/`P8-028`/`P8-029` confirmed that `P8-028` and `P8-029` are covered by `P8-032A`; `P8-027` is implemented as Bundle D, removing the remaining recruiter-facing query contribution details while preserving backend report data. `P8-020` and `P8-021` are implemented as a separate narrow frontend-only cleanup slice: the default Recruiter Chat status is empty/hidden while preserving the dynamic status target, and the initial empty-chat helper now uses warmer recruiter-facing wording. Backend/API/runtime contracts, approval payloads, fingerprints, Tavily execution path, query generation, scoring, filtering, dedupe, location logic, candidate facts, export behavior, and execution boundaries were not changed.

`P8-032B` is implemented as the second recruiter-facing conversation cleanup slice. Standalone harmless small-talk turns such as `how are you?`, `thanks`, `are you there?`, `как дела?`, and `спасибо` now route through deterministic small-talk handling instead of the generic off-topic redirect. Existing draft/ready search-summary state is preserved with `brief_changed = false`, `stale_state_should_clear = false`, and `clear_brief = false`; no recruiter-chat LLM extraction, new OpenAI wording call, planner/runtime/Tavily execution, LinkedIn behavior, export, persistence, or candidate workspace mutation is triggered by small talk. Greeting/near-empty turns still use the existing deterministic onboarding route and approved `P8-008` bounded onboarding overlay, while EN/RU greeting and unclear/noise deterministic fallbacks are more polite.

`P8-032C` is implemented as the third recruiter-facing post-search chat cleanup slice. Approved search responses now show a compact recruiter-chat completion sentence with only unique candidate count plus strong/review/weak quality distribution. The Agent Response LLM wording payload is reduced to visible-message facts only, and validation rejects limitations, raw/query counts, next-step/internal wording, URLs/LinkedIn inspection claims, markdown/list/multi-paragraph output, and multi-sentence completion messages for this surface. Backend `agent_response.summary_facts`, `quality_notes`, `limitations`, `suggested_next_actions`, and non-executable `next_iteration_options` remain available for existing contracts/future reviewed surfaces, but recruiter chat no longer renders `Follow-up ideas`, `Suggestions only`, or `next_iteration_options` payload blocks.

`P8-032` is closed as the parent recruiter-facing AI conversation and workspace presentation umbrella. Its observed child issues are either directly implemented or demonstrably covered by the reviewed slices and bundles: `P8-017` through `P8-021`, `P8-023` through `P8-031`, and separate `P8-022` multi-wave default behavior. The next reviewed direction is Phase 8.5 agentic candidate review and iteration from already returned workspace facts, without autonomous execution, direct LinkedIn access, scraping, messaging, account actions, persistence, or new providers.

`P8.5-001` is completed as the docs-only Agentic Candidate Review v0 contract in `docs/phase-8-5-agentic-candidate-review-contract.md`, with guardrail coverage in `scripts/smoke_p85_agentic_candidate_review_contract.py`. Phase 8.5 may analyze already returned current-run workspace facts, compare selected candidates, summarize fit/gaps, and propose non-executable refinements. It must not run Tavily, bypass backend search, open/scrape/login to LinkedIn, message candidates, perform account actions, persist workspace state, add providers, or add autonomous execution.

`P8.5-002` is implemented as a deterministic frontend-only top-candidate recommendation over current visible workspace candidates. It adds `candidateWorkspace.buildTopCandidateRecommendation()`, a compact `workspace-agent-review` UI block, and `scripts/smoke_p85_top_candidate_recommendation.py`. The recommendation excludes candidates marked `not_a_fit` and explicit foreign-location candidates, strips internal ranking before rendering, returns no URL-derived `candidate_id`, no profile URLs/normalized URLs, no raw snippets/content, no recruiter notes, and no account identifiers. It does not add backend/LLM/Tavily/LinkedIn/profile-opening/storage behavior and does not change candidate facts, scoring, filters, dedupe, export, Search Brief, QueryPlan, runtime approval, or search execution.

`P8.5-003` is implemented as deterministic frontend-only selected-candidate comparison over current visible shortlisted workspace candidates. It adds `candidateWorkspace.buildSelectedCandidateComparison()`, renders a compact selected comparison block, and is covered by `scripts/smoke_p85_selected_candidate_comparison.py`. The comparison reuses existing shortlist status as the only selection source, shows a minimal hint for one selected candidate, renders comparison for two or more, keeps explicit foreign-location selections as cautions, and returns no URL-derived `candidate_id`, profile URLs/normalized URLs, raw snippets/content, recruiter notes, or account identifiers. It does not add backend/LLM/Tavily/LinkedIn/profile-opening/storage behavior and does not change candidate facts, scoring, filters, dedupe, export, Search Brief, QueryPlan, runtime approval, or search execution.

Bundle A (`P8-031 Make candidate table the primary post-search surface` + `P8-030 Rebalance desktop layout toward candidate workspace`) is implemented. Candidate Results now render before Search summary, the desktop shell gives the right-side candidate workspace more width, candidate rows are denser and expose score/identity/role/location/stack/source/status/shortlist in the main row, notes are still available in candidate details, and review state/export/explanation controls remain wired.

Bundle B (`P8-024 Replace technical plan UX with conversational search confirmation`) is implemented. Supported ready searches now create a state-bound pending `start_search` confirmation identity. Clean recruiter confirmations trigger the existing safe internal chain (`/api/agent/query-plan` -> runtime `prepare` -> runtime `execute_approved`) and do not call direct structured-search endpoints. Confirmation identity binds the current Search Brief fingerprint, Agent action, run action, execution mode, and multi-wave toggle state. Ambiguous replies ask for clarification, refinement replies do not run search, and mixed/new-constraint replies are not treated as clean confirmation.

Bundle C (`P8-022 Make multi-wave the default approved search mode`) is implemented. The primary UI now defaults to `Multi-wave` checked, reset/new chat restores that default, and runtime action/context/tool input continue to bind to the current visible toggle. The toggle remains an opt-out to single-wave. Backend compatibility endpoints and runtime guardrails remain unchanged.

`P7.5-002` created `docs/phase-7-5-recruiter-simulation-scenarios.md` with 104 in-scope recruiter simulation scenarios across RU/EN happy paths, incomplete requests, refinement, noisy input, contradictions, unsupported scope, other languages, off-topic dialogue, safety/prohibited requests, and state/flow stress. The scenario bank records QA result fields, severity, evidence, and the rule that Tavily should run only for `required_for_scenario` or deliberately selected `allowed_if_approved` scenarios through the visible approved UI flow.

`P7.5-003` created `docs/phase-7-5-browser-qa-checklist.md`. The checklist maps all 104 scenarios with no missing/extra/duplicate IDs, assigns P7.5-004 47 RU scenarios and P7.5-005 57 EN/mixed/other scenarios, limits live Tavily to two approved single-wave searches (`CORE-RU-001`, `CORE-EN-001`), reuses those results for post-results scenarios, and defines result metadata, evidence fields, status/severity rules, OpenAI/LLM wording evaluation, and UI-only execution boundaries.

`P7.5-003` verification passed: the checklist matrix was reconciled against all 104 scenario IDs, owner/mode/search-mode totals matched the intended QA split, and `powershell -ExecutionPolicy Bypass -File .\scripts\check_all.ps1` passed after the document updates.

`P7.5-004` completed the RU browser QA pass in `docs/phase-7-5-ru-browser-qa-results.md`: 47/47 RU scenarios were run, with 39 pass, 7 fail, 1 blocked, 0 not-run, and 0 live Tavily executions. The pass found that the browser flow can build a Search Brief and visible Search Plan, but the runtime approval preparation can remain blocked after Build Plan, leaving `Approve & Search` disabled and preventing approved Tavily execution.

`P7.5-006` consolidated the initial RU findings in `docs/phase-7-5-qa-findings-report.md`. The original grouped RU blockers were: runtime approval not prepared after Build Plan, clean RU initial requests sometimes misclassified as blocked refinements, and several RU prohibited requests treated as normal search clarifications. `P7.5-007` reviewed those fixes, `P7.5-008` implemented them, and `P7.5-009` added no-network regression coverage.

`P7.5-005` then completed the EN/mixed browser QA pass in `docs/phase-7-5-en-browser-qa-results.md`: 57/57 scenarios run, 37 pass, 20 fail, 0 blocked, 0 not-run, and 1 live Tavily execution through the visible approved UI flow for `CORE-EN-001`. The EN happy-path approved search works end to end, but new findings `P75-QA-008` through `P75-QA-014` showed the flow was not ready to close as fully ready without a Phase 7.5 readiness decision.

`P7.5-011` is implemented as an immediate hardening pass for `P75-QA-008` through `P75-QA-014`: EN safety coverage now includes LinkedIn login phrasing, automatic candidate messaging, and autonomous execution; off-topic/meta/reset/ambiguity/contradiction turns route deterministically without mutating Search Brief incorrectly; typo handling covers `ukrane`/`sping`/`kafak`; LLM draft fields are sanitized to avoid schema-error leaks; and frontend post-results follow-up stays grounded in the latest visible Agent Response without rerunning or calling chat extraction. A targeted retest after P7.5-011 found and fixed stack fact contamination for Docker/Kubernetes and stale ready-flow status after stack explanation; commit `6e3df0c` passed local checks, targeted browser retest, and CI.

`P7.5-010` is completed as a docs-only closeout. `docs/phase-7-5-closeout.md` records the Phase 7.5 readiness decision `ready after approved fixes completed`, the closure status for `P75-QA-001` through `P75-QA-014`, the final Docker/Kubernetes/no-stack/ready-status hotfix evidence from commit `6e3df0c`, residual limitations, absolute product boundaries, and the Phase 8 handoff.

The first Phase 8 implementation batch is now completed: `P8-002 Build recruiter-facing candidate table`, `P8-003 Add sorting and filtering by quality signals`, and `P8-004 Add shortlist, notes, and statuses`. The implementation follows the frontend-only scopes defined in `Tasks.md` and `docs/phase-8-candidate-workspace-contract.md`: `review_status` is the source of truth, shortlist is derived, notes are escaped plain text, there is no persistence, and no backend/API/search/runtime behavior changed.

`P8-005` is implemented as a frontend-only deterministic candidate explanation layer. The helper is structured before rendering, exported through `CandidateWorkspace`, uses stable allowlisted reason codes with bounded facts, derives summary wording from selected reasons, avoids Java/Ukraine/backend hardcode, treats query-source stack evidence as unconfirmed, keeps foreign/mismatched location distinct from unknown/weak location, follows existing `qualityBucket` semantics, represents score breakdown through capped `quality_component` evidence, and ignores recruiter review state (`review_status`, derived shortlist, notes). The explanation wording path is now split: `P8-006 Define bounded candidate explanation wording contract` completed the payload/output/validation/fallback/routing contract before code, and `P8-006.1 Implement explicit selected-candidate wording overlay` implemented the selected-candidate backend-owned LLM overlay only after an explicit user action. The frontend sends only a bounded deterministic explanation wording request payload, not raw candidate/search data; the backend validates payload contract/source/version/reason keys/reason codes, rejects frontend-supplied prompt rules/hard boundaries/allowed numbers/OpenAI execution controls, recomputes allowed numbers from user-visible wording fields only, recomputes the request-level explanation fingerprint from sanitized request-bounded fields using UTF-8 canonical JSON/sha256 parity before any OpenAI call, validates wording-safe allowlisted bounded facts through an explicit facts mapper, and owns all provenance/fallback/no-call metadata. The backend-to-OpenAI model payload is separate, versioned, backend-built, keeps backend-owned policy/schema instructions separate from candidate/user-derived data fields, and excludes request correlation/cache/internal fields such as `workspace_run_id`, `wording_target_key`, `frontend_pending_key`, request-level fingerprints, backend cache keys, candidate ids, URL-derived identifiers, runtime identifiers, and provenance metadata. Candidate/user-derived summary, labels, facts, stack/location terms, and query-source values are data, not instructions, and instruction-like text inside those values must not change model policy, schema, reason keys/codes, facts, scores, provenance, or execution behavior. That backend validation is not proof of candidate fact truth or latest successful workspace run in this slice; the request-level fingerprint only protects request integrity/UI correlation, while `frontend_pending_key` prevents duplicate in-flight submissions before backend response and `backend_wording_cache_key` protects validated overlay reuse/cache behavior. Because current workspace `candidate_id` may be `normalized_url`, the wording request payload uses an opaque non-URL `wording_target_key` that is stable only within the current workspace run instead of `candidate_id`. The LLM may only rewrite the already-built deterministic explanation wording, with stable `reason_key` validation and deterministic fallback, and must not change candidate facts, reason codes, source/version, score, ranking, filters, search behavior, review state, or persistence. Accepted wording lives as a separate current-run overlay and does not mutate the deterministic explanation. Model-returned `warnings` are not allowed in the first candidate-explanation output shape; strict output validation caps summary/labels, rejects extra fields and unsafe formatting, no-calls unsupported languages before OpenAI, validates backend-only model payload version internally before OpenAI, and forbids persistent storage/logging or backend-error/frontend-status exposure of raw wording payloads, backend-to-OpenAI model payloads, or raw model responses. Opening candidate details or selecting a candidate does not call OpenAI by itself.

`P7.5-007` is completed as a docs-only decision task. It approved the exact fix scope for `P7.5-008` and regression scope for `P7.5-009`: prepare runtime approval only after Build Plan settles, refuse RU/EN prohibited intents on the latest user turn without mutating or visually clearing the current Search Brief while clearing/disabling stale executable downstream state, and route clean-state initial recruiter requests through initial Search Brief extraction instead of refinement blocking.

`P7.5-008` is implemented. Frontend runtime approval preparation now runs after `Build Plan` settles, so `Approve & Search` is enabled only after backend-owned pending runtime approval exists. Recruiter chat safety detection now checks the latest recruiter/user turn before LLM extraction/refinement and covers RU/EN profile opening/reading, private contact harvesting, and direct Google/web-search bypass. Clean-state recruiter messages now route through initial Search Brief extraction instead of deterministic refinement blocking. Refusals preserve the visible current Search Brief while clearing stale executable downstream state.

`P7.5-009` is implemented. Added `scripts/smoke_p75_current_flow_regressions.py` and wired it into `scripts/check_all.ps1`. The smoke is no-network and covers the fixed Phase 7.5 QA findings: runtime approval prepare after Build Plan, latest-turn prohibited-intent refusal before LLM extraction, clean-state initial request routing, frontend refusal-state preservation, and frontend Agent Runtime-only approved-search guardrails.

`P7.5-011` is implemented. `scripts/smoke_p75_current_flow_regressions.py` now maps and covers `P75-QA-001` through `P75-QA-014`. Local regression baseline and browser sanity QA passed after the immediate EN/mixed hardening fixes. The follow-up stack-grounding hotfix in `6e3df0c` also passed `scripts/check_all.ps1`, targeted browser retest, and GitHub Actions CI.

Current agreed strategy:

- keep the completed narrow high-quality flow first: `Backend Developer + Java + Ukraine`;
- do not expand countries or technologies yet;
- Phase 5 is closed as the narrow Java/Ukraine Agent UX foundation;
- Phase 5.5 technical modularization is complete;
- `P6-001` is approved as the docs-only runtime contract: backend-owned tool-call envelopes, runtime states/transitions, approval/fingerprint rules, deny-by-default registry behavior, idempotency expectations, error taxonomy, and Phase 7 wording boundary are defined;
- `P6-002` is implemented as backend-only typed registry/envelope foundation: no runtime endpoint, Tavily/OpenAI call, autonomous execution, or structured-search approval behavior change was added;
- `P6-003` is implemented as frontend-only/status-only Agent Action Review Queue: it displays `Build Search Plan` and `Run Search` action state/context while preserving existing execution controls and backend approval boundaries;
- `P6-004` is implemented as the first real approved runtime execution slice: `Approve & Search` now uses `POST /api/agent/runtime/turn` with stateless `prepare` and `execute_approved`, backend-owned fingerprints, strict Java/Ukraine supported-flow validation, and existing safe single/multi-wave execution after approval;
- `P6-005` is implemented as no-network runtime hardening: stale/mutated approvals, runtime context mismatches, unsafe frontend-owned fields, frontend direct-fallback regressions, missing Tavily key during approved execution, and valid mocked single/multi-wave execution are covered in `scripts/check_all.ps1`;
- `P6-005.1` is implemented as the repair before closeout: the real runtime execution wrappers no longer recurse, and an unmocked-wrapper no-network smoke verifies single/multi runtime `prepare -> execute_approved -> observed`;
- `P6-006` closed Phase 6 as `AI Agent Runtime v0 baseline`, not as a complete autonomous recruiter agent;
- Phase 7 is completed and closed as `Agent Conversation Wording Layer v0 baseline`: `P7-001` through `P7-010` are completed, and `docs/phase-7-closeout.md` records the closeout decision;
- Phase 7.5 is completed and closed by `P7.5-010` with the decision `ready after approved fixes completed`;
- Phase 7.5 covered both Russian and English recruiter simulation and preserved the approved UI-only Tavily boundary;
- Phase 8.5 is now the active reviewed direction; `P8.5-001 Define agentic candidate review contract`, `P8.5-002 Add top-candidate recommendation from returned workspace facts`, and `P8.5-003 Add selected-candidate comparison` are completed;
- Phase 8 candidate workspace implementation should follow the completed `P8-001` contract and still require separate task review before coding;
- keep ordinary LLM-assisted agent conversation wording inside Phase 7 guardrails, after the runtime message taxonomy is stable;
- Phase 7 task order is contract-first: message taxonomy/lifecycle, facts contract, style policy, deterministic source messages, LLM routing/gating, bounded prompt payloads, validation/fallback/provenance, frontend rendering, golden scenario tests, then closeout;
- lightweight wording provenance/version metadata is carried inside `P7-007` and golden scenario assertions inside `P7-009`, not as a separate observability/product analytics task;
- keep candidate workspace/shortlist for Phase 8 and database/persistent memory for Phase 9.

Planned current and later phases:

- Phase 7.5: `Recruiter Simulation QA & Flow Hardening`, completed and closed.
- Phase 8: `Candidate Workspace/Table + Shortlist`, completed current baseline for returned candidate workspace.
- Phase 9: `Persistent Memory + Saved Searches`.
- Phase 8.5: `Agentic Candidate Review & Iteration`, current active direction for top-candidate analysis, selected-candidate comparison, fit/gap explanation, and guided refinement from already returned workspace facts only.
- Phase 10: `Manual Candidate Evidence Intake`, future track where the recruiter manually pastes public profile text copied outside the app, and the agent compares that user-provided evidence against the current Search Brief and workspace context.
- Phase 11: `Resume Upload & Fit Analysis`, future track for structured resume/CV analysis against the current Search Brief, with explicit privacy, retention, masking, logging, and deletion rules.
- Phase 12: `Multi-Provider Search`, future provider-expansion track for Serper, SerpApi Google, and SerpApi Bing through the same approval-gated backend runtime boundary.

Future-track boundaries: manual LinkedIn/profile evidence and resume uploads are user-provided inputs only. The app must not open LinkedIn, log in, scrape, automate browsing, bypass restrictions, message candidates, perform account actions, or run new providers outside an approved backend pipeline. Provider expansion should stay separate from candidate evidence and resume-analysis phases.

`P5-001` is completed as a docs-only contract task. The approved recruiter chat contract supports Russian and English input, asks one clarifying question at a time, replaces the structured form as the primary UX over time, shows a normalized brief summary before `Build Plan`, and keeps `Build Plan` separate from Tavily execution. After `P5-004`, primary chat `Build Plan` defaults to `rule_based` so supported briefs produce an approvable Search Plan. Tavily execution remains behind explicit backend approval. Direct web-search bypass, direct LinkedIn access/automation, LinkedIn login, LinkedIn scraping/restriction bypass, candidate messaging/automatic outreach, autonomous execution, and user or third-party account actions remain prohibited behavior.

`P5-002` is implemented as a backend chat-to-brief adapter. The guardrail is preserved: `chat messages -> draft Search Brief -> validation -> one assistant response`. It adds `POST /api/recruiter-chat/turn`, strict OpenAI/ChatGPT JSON extraction, deterministic prohibited-request refusal, deterministic supported-signal hints, Ukraine alias normalization, conservative draft merge, existing Search Brief validation, one next clarification question, default `recommended_planner_mode = rule_based`, and a no-Tavily smoke script. It does not build `QueryPlan`, call `/api/agent/query-plan`, call Tavily, execute search, or change frontend UI.

`P5-003` is implemented. The primary frontend input is now recruiter chat. The implemented path is `chat -> normalizedBrief -> Build Plan -> adapted_structured_request/query_plan -> Approve & Search`, and search execution uses `adapted_structured_request` from the planner response, not old structured-form DOM fields. AI draft `validated_not_executable` plans remain visible but non-executable; rule-based and rule-based fallback plans remain the only executable frontend path.

`P5-004` is implemented. The primary recruiter-chat flow is now `Chat -> Search Brief -> Build Plan -> Review Search Plan -> Approve & Search -> Results`. `Build Plan` produces an approvable deterministic backend plan for supported briefs by using `planner_mode = rule_based`; `Approve & Search` is enabled only after a visible fingerprinted Search Plan exists. This is not a retreat from AI planning: it gives the future AI Agent a safe executable bridge through the existing backend planner and approval gate, while the existing AI planner capability remains available for the next reviewed step toward AI-assisted executable planning.

`P5-005` is implemented. After a ready supported Java/Ukraine Search Brief, the frontend calls `POST /api/agent/plan`, shows an Agent Plan as a chat message, and enables `Build Plan` only when a supported `agent_plan.proposed_action` exists. `Build Plan` now sends the action and Search Brief fingerprint to `/api/agent/query-plan`; the backend rejects stale or mismatched Agent Plan actions instead of falling back to a non-agent path. No Tavily execution, post-results Agent Response, new LLM behavior, generic tool loop, persistent backend state, direct LinkedIn access/automation, or role/country expansion was added.

`P5-006` is implemented. Approved search responses now include deterministic backend-generated `agent_response` grounded only in already returned search data: executed `QueryPlan` input snapshot, normalized structured request, report counts, deduped candidates, quality signals, review flags, and known limitations. The frontend passes minimal `agent_language` and renders the response as a local-only `AI Agent` chat message after results. Suggested next actions stay inert text. No broad `agent_context`, full chat history, extra Tavily/LLM/web/LinkedIn calls, executable next-action buttons, persistence, or autonomous behavior was added.

`P5-007` is implemented. Agent Plan and Agent Response now support LLM-assisted wording as an optional backend overlay after deterministic objects are built. The LLM receives bounded payloads only, with no raw candidate URLs or full candidate records. Backend validation rejects unsafe, wrong-language, fact-changing, action-changing, or number-inventing output and falls back to deterministic wording with provenance metadata. The LLM has no execution authority and cannot change `QueryPlan`, approval, Tavily execution, filters, scoring, dedupe, location logic, fingerprints, suggested next actions, or candidate ordering.

`P5-007.1` is implemented as a stabilization task. `README.md`, `AGENTS.md`, `ProjectStatus.md`, `Roadmap.md`, and `Tasks.md` now agree that `P5-007` is implemented. The docs clarify that `OPENAI_API_KEY` and `OPENAI_MODEL` are required for the current primary recruiter chat / AI planner paths, while LLM-assisted Agent Plan/Response wording has deterministic fallback. OpenAI Chat Completions requests use `max_completion_tokens`, not legacy `max_tokens`, for `gpt-5.4-mini` compatibility. Backend `/api/agent/query-plan` now requires the current Agent Plan action and Search Brief fingerprint instead of allowing a direct Build Plan call without Agent Plan context.

`P5-008` is implemented. Recruiter chat now handles greeting-only and near-empty messages deterministically before OpenAI extraction: RU/EN greetings get warm onboarding wording, near-empty backend turns ask for role/main technology/location/stack, greeting-only turns do not call OpenAI, and existing draft briefs are preserved instead of being wiped. The existing safety refusal still runs before onboarding/LLM extraction. No planner, Tavily, search execution, scoring, filters, dedupe, location, Agent Plan, Agent Response, or Search Brief refinement behavior changed.

`P5-009` is implemented. Recruiter chat can now refine an existing Search Brief through deterministic `brief_patch.operations` for add/remove/replace Java stack, seniority, and search depth. Patches are atomic, unsupported mixed patches do not apply partial valid changes, removing the last stack item without replacement is blocked, and no-op changes do not clear downstream state. The backend returns `brief_changed` and `stale_state_should_clear`; the frontend clears Agent Plan, Build Plan, QueryPlan, approval/results UI, and Agent Response only when that flag is true. No Tavily/search/planner execution was added to chat refinement.

`P5-010` is implemented. Approved search responses now include deterministic `agent_response.next_iteration_options` grounded only in returned QueryPlan/report/results/quality data. Options are structured with `proposed_brief_patch` operations, require approval before any execution, and are not executable now. After `P8-032C`, these options remain backend/internal future-surface data and are no longer rendered in recruiter chat. `search_depth` is preserved as metadata through the adapted structured request and QueryPlan input snapshot so `deep` suggestions are grounded. LLM wording does not generate, select, or mutate the options, and option generation does not call Tavily, LinkedIn, web search, Build Plan, `/api/agent/query-plan`, or multi-wave.

`P5-011` is implemented as a CSS-first/UI-only visual refresh. The current Phase 5 UI now uses a dark intelligence workspace direction: layered navy/charcoal surfaces, teal/cyan action/status accents, darker controls, compact panels/cards, report metrics, candidate cards, review flags, and score details. No backend code, `index.html`, `app.js`, API contracts, request payloads, state semantics, event flow, search behavior, or product logic changed. The old MVP layout was not copied and no new product features were added.

`P5-012` is completed as a docs-only closeout. Phase 5 is closed as a narrow Java/Ukraine Agent UX foundation, not as a complete autonomous recruiter agent. The closeout decision: the supported flow is ready for Phase 5.5 technical modularization and later Phase 6 human-approved tool runtime. Broader communication scenarios and ordinary LLM-assisted recruiter chat wording are intentionally moved to Phase 7 after Phase 6 runtime/message taxonomy is stable. See `docs/phase-5-closeout.md`.

`P5.5-001` is completed as a docs-only architecture task. It defines the Phase 5.5 module map, import direction, schema/config strategy, migration order, no-behavior-change baseline, and verification baseline before extracting code from the `app/main.py` monolith.

`P5.5-002` is implemented as the first behavior-preserving extraction task. Shared Pydantic schemas now live in `app/schemas.py`, shared domain constants/config in `app/domain_config.py`, text helpers in `app/text_utils.py`, structured search validation in `app/search_validation.py`, and Search Brief validation/adapter/fingerprinting in `app/search_brief.py`. `app/main.py` imports those names and preserves existing `main.*` compatibility for smoke scripts and internal callers. No endpoint paths, API contracts, validation messages, defaults, fingerprints, QueryPlan output, planner behavior, Tavily execution, scoring, filters, dedupe, location logic, approval logic, snapshots, frontend behavior, or Phase 6 runtime behavior changed.

`P5.5-003` is implemented as a behavior-preserving planner extraction task. Rule-based QueryPlan construction, QueryPlan fingerprint helpers, planner explanation, and shared plan-validation error helper now live in `app/planning.py`. Deterministic AI QueryPlan prompt helpers, structural validation, coverage policy lookup/prompting, coverage validation, and AI plan warning/assumption helpers now live in `app/ai_planning.py`. Planner config/constants and AI coverage policy config live in `app/domain_config.py`, while shared term matching lives in `app/text_utils.py`. `app/main.py` preserves existing `main.*` compatibility, including `main.RuleBasedQueryPlannerV1`, fingerprint helpers, AI validation helpers, planner mode constants, and `main.run_openai_json_planner` monkeypatching. Java/Ukraine 10-query baseline and fingerprint stayed unchanged.

`P5.5-004` is implemented as a behavior-preserving search execution extraction task. Tavily HTTP execution, query-slot execution, query-plan wave execution, and dependency-injected multi-wave core execution now live in `app/search_execution.py`. Structured-search snapshot helpers now live in `app/search_snapshots.py`. `app/main.py` preserves existing `main.*` compatibility, including `main.run_query_plan_wave`, `main.run_multi_wave_query_plan`, `main.TAVILY_SEARCH_URL`, and `main.SEARCH_RUN_LOG_DIR`; the multi-wave wrapper reads the current `main.run_query_plan_wave` at call time so smoke-test monkeypatching still works. `build_deduped_results_and_report`, location filtering, Candidate Quality, Agent Response, route handlers, and approval logic remain in `app/main.py` for later reviewed extraction tasks.

`P5.5-005` is implemented as a behavior-preserving Candidate Quality extraction task. Candidate Quality producer logic now lives in `app/candidate_quality.py`, Candidate Quality constants live in `app/domain_config.py`, and shared profile text/ordering helpers live in `app/text_utils.py`. `app/main.py` preserves existing `main.*` compatibility for Candidate Quality helpers/config while keeping dedupe/report building, location filtering, Agent Response, LLM wording, approval validation, and route handlers in place. Pre/post exact Candidate Quality parity checks passed for direct-stack, query-source-only stack, missing-stack, ambiguous technology, seniority-missing, and foreign-location-status fixtures.

`P5.5-006` is implemented as a behavior-preserving Agent Tools and Agent Plan extraction task. Agent Tools v0 constants, tool contract, execution approval metadata, and execution approval validation now live in `app/agent_tools.py`. Deterministic Agent Plan status constants, language/action/message helpers, Agent Plan response building, wording-wrapper dependency injection, and Agent Plan action validation now live in `app/agent_plan.py`. `app/main.py` preserves existing `main.*` compatibility and keeps wrappers for current validation-error wording and LLM wording monkeypatch behavior. Agent Response, bounded wording/OpenAI logic, route handlers, Tavily execution, dedupe/report building, location filtering, and Candidate Quality remain outside this task.

`P5.5-006.1` is implemented as a technical guardrail before `P5.5-007`. `scripts/check_all.ps1` now runs compileall, frontend JavaScript syntax check, and the Phase 5 smoke scripts in one local command. `.github/workflows/ci.yml` runs the same regression script on `push` and `pull_request` to `main`. This does not change product behavior and does not require Tavily or OpenAI secrets.

`P5.5-007` is implemented as a behavior-preserving Agent Response and bounded wording extraction task. Shared `BRIEF_PATCH_*` constants and `build_brief_patch` now live in `app/brief_patch.py`; deterministic Agent Response summaries, limitations, suggested actions, next-iteration options, and `build_agent_response` now live in `app/agent_response.py`; bounded Agent Plan/Agent Response wording prompts, OpenAI wording request helper, validators, metadata helpers, payload builders, and apply functions now live in `app/agent_wording.py`. `app/main.py` preserves existing `main.*` compatibility and keeps wrapper paths so monkeypatching `main.run_openai_json_agent_wording` still affects Agent Plan/Response wording behavior. Recruiter chat OpenAI orchestration and AI planner OpenAI orchestration stayed in `app/main.py`, and no product behavior changed.

`P5.5-008` is implemented as a behavior-preserving FastAPI route split. FastAPI path decorators and thin route wrappers now live in `app/routes.py` behind `RouteDependencies` and `create_router(deps, static_dir)`. `app/main.py` still owns the FastAPI app creation, static mount, router inclusion, and current route-facing service/orchestration functions. Existing `main.*` callable names and smoke-test monkeypatch paths are preserved, `app.routes` does not import `app.main`, and the API route path/method set plus endpoint names stayed unchanged.

`P5.5-009` is implemented as a no-behavior-change Phase 5.5 closeout. `scripts/smoke_p55_routes.py` now verifies route import direction, route path/method parity, endpoint names, `main.*` compatibility names, monkeypatch target names, and no-network HTTP behavior for root, health, Agent Tools, structured-search validation, QueryPlan preview, and legacy disabled search. `scripts/check_all.ps1` now runs that smoke-check locally and in GitHub Actions CI. Phase 5.5 is closed; Phase 6 became the next active phase at that point and is now also completed.

`P6-002` is implemented as the first Phase 6 runtime foundation code task. `app/agent_tools.py` now has typed tool definitions, registry metadata helpers, risk/category constants, approval status constants, and runtime error constants while preserving `AGENT_TOOLS_V0` and `agent_tool_contract()` compatibility. New `app/agent_runtime.py` contains internal runtime states, untrusted proposal normalization, backend-owned tool-call/result/turn-response envelopes, deterministic fingerprints, deterministic execution idempotency keys, and deny-by-default proposal validation. `scripts/smoke_p6_agent_runtime.py` is now part of `scripts/check_all.ps1`. No runtime endpoint, frontend action queue, Tavily/OpenAI call, tool execution, `ExecutionApproval` replacement, or current structured-search approval behavior change was added.

`P6-003` is implemented as a frontend-only/status-only Agent Action Review Queue. The UI now shows an `Agent Actions` surface with derived `Build Search Plan` and `Run Search` states, approval requirement, action source, brief/query-plan fingerprint context, query count, and single-wave vs multi-wave mode. Minimal frontend-local display state is used only for `running`, `completed`, and `failed` rendering and is cleared or recomputed when context changes. Existing `Build Plan` and `Approve & Search` buttons remain the only execution controls. No backend route, runtime endpoint, Tavily/OpenAI call, API contract change, new execution handler, autonomous execution, or structured-search approval behavior change was added.

`P6-004` is implemented as the first narrow human-approved Agent Runtime execution loop for the Java/Ukraine baseline. Added `POST /api/agent/runtime/turn` with strict `prepare` and `execute_approved` modes, execution-tools-only support for `run_single_wave_search` and `run_multi_wave_search`, allowlisted tool input, backend QueryPlan rebuild/fingerprint validation, Search Brief fingerprint context binding, backend-owned pending approval, runtime approval validation, and an internal bridge into the existing `ExecutionApproval` before Tavily execution. Frontend `Approve & Search` now uses the runtime endpoint and reads the search response from `tool_results[0].result`; it does not fallback to the old direct structured-search path on runtime failure. Old structured-search endpoints remain available for compatibility and backend checks.

`P6-005` is implemented as a no-network runtime guardrail regression task. Added `scripts/smoke_p6_runtime_guardrails.py` and wired it into `scripts/check_all.ps1`. The smoke covers stale normalized tool input, changed Search Brief / plan / query-count context, single-wave vs multi-wave approval mismatch, multi-wave setting mismatch, mutated runtime approval fields, schema extra-field rejection, unsafe frontend-owned runtime fields, prepare-without-execution, missing Tavily key during `execute_approved`, valid mocked single/multi-wave execution, and frontend runtime-only execution guardrails. No product behavior, Tavily query generation, scoring, filtering, dedupe, location logic, Candidate Quality, snapshots, Agent Response, LLM wording, new tools, AI executable QueryPlans, persistence, or broader runtime architecture changed.

`P6-005.1` is implemented as the required repair before `P6-006` closeout. A no-network review reproduction showed that runtime `prepare` succeeded, but real `execute_approved` without monkeypatching `main.execute_single_wave_structured_search_response` returned `execution_failed` because the runtime execution helper recursively called itself. The single/multi runtime wrapper bodies now use the existing approved pipeline functions instead of recursing. Added `scripts/smoke_p6_runtime_unmocked_execution.py` and wired it into `scripts/check_all.ps1`; the smoke exercises the real wrappers, monkeypatches only the lower `main.run_query_plan_wave` level, uses Tavily-like Java/Ukraine LinkedIn raw data, removes OpenAI env values during the run, no-ops snapshot writing, restores env/functions, and verifies `report.unique_profiles >= 1` for both single-wave and multi-wave runtime execution.

`P6-006` is completed as a docs-only closeout. Phase 6 is closed as `AI Agent Runtime v0 baseline`: a narrow, human-approved runtime for the supported Java/Ukraine flow with typed runtime turns, backend-owned approvals, frontend action review, guarded single/multi-wave execution, result observation, and regression coverage. This is not a complete autonomous recruiter agent. Phase 7 `Agent Conversation Wording Layer` is now the active direction. See `docs/phase-6-closeout.md`.

`P7-004` is implemented. It adds `app/agent_messages.py` as the backend-first deterministic source-message helper layer with an explicit coverage matrix for the implemented slice. Recruiter chat source messages, Agent Plan source/fallback messages, QueryPlan approval notices, runtime/tool unavailable and execution-failed messages, and deterministic Agent Response source messages/options now route through this helper while preserving existing API fields and object shapes. `scripts/smoke_p7_agent_messages.py` covers the matrix, import boundary, RU/EN source messages, public response fields, and inert next-iteration options. No LLM routing, prompts, provenance fields, typed frontend rendering, Tavily/OpenAI calls, approval/fingerprint changes, candidate/result changes, or autonomous behavior were added.

Latest Phase 3 quality baseline used `Backend Developer + Java + Spring/Kafka + Ukraine` with visible profile/location filters enabled:

- Queries succeeded: 10/10
- Raw Tavily results: 200
- Displayed occurrences: 102
- Unique candidates: 57
- Duplicates removed: 45
- Hidden by profile filter: 13
- Hidden by location filter: 85
- Quality score average: 76.3

Main Phase 3 baseline conclusion: the Candidate Quality Layer is useful for ranking and review, but selected stack evidence remains weak in public Tavily/LinkedIn snippets. See `docs/phase-3-quality-baseline.md`.

`P3-010.1` conclusion: `missing_selected_stack` mostly means the selected stack is not visible in Tavily public snippets, not that the candidate lacks the stack. The current backend behavior is honest, but the frontend wording `Stack: n/a` was too blunt. The agreed display label is now `Not visible` for selected-but-unconfirmed stack while keeping `selected_stack_missing` as a ranking penalty, not a hard filter.

`P3-010.2` implemented the agreed frontend display semantics: direct evidence shows actual stack terms, `missing_selected_stack` shows `Not visible`, `stack_query_source_only` shows `Not confirmed`, and future no-stack-requested state is reserved as `N/A`. Quality scoring and backend search/filter logic were not changed.

`P3-011` added `/api/structured-search/multi-wave` as an experimental backend endpoint. It repeats the same validated `QueryPlan`, dedupes across waves, preserves existing `query_sources`, adds separate `wave_sources`, stops on low incremental unique gain, and writes `structured-search-multi-wave` snapshots. The normal `/api/structured-search` endpoint remains the stable single-wave path.

`P3-012` evaluated the multi-wave runner with one real Tavily run. It ran 4 waves, executed 40 queries, stopped on `low_incremental_gain`, and produced 67 final unique candidates. Compared with wave 1 inside the same run, multi-wave added 7 unique candidates, including 3 high-quality candidates and 1 direct-stack candidate, after 30 extra Tavily queries. Historical recommendation was not to make multi-wave default at that time; this was intentionally superseded by Phase 8 `P8-022`.

`P3-013` added the explicit frontend control: historically default Search remained single-wave and enabling the `Multi-wave` toggle called the multi-wave path with approved defaults. Current Phase 8 behavior after `P8-022`: the same visible toggle remains, but it is checked by default and acts as an opt-out to single-wave.

`P3-014` closed Phase 3 as a docs-only handoff. Phase 4 should preserve the `QueryPlan` contract, structured request, visible filters, executor/dedupe/report pipeline, snapshots, and Candidate Quality Layer while adding the AI Agent Foundation: `Search Brief`, agent tool boundaries, AI-assisted planning, explanations, and approval gates before Tavily execution.

`P4-001` is approved as the AI Agent Foundation contract. Phase 4 should use an LLM/ChatGPT layer for recruiter intent understanding, Search Brief creation, planning, clarification, and explanations, while keeping execution inside the existing validated backend pipeline. The approved flow is `Search Brief -> Agent Plan -> Agent Action -> optional Approval Gate -> validated Tool Call -> Agent Response`.

`P4-002` is approved as the `Search Brief v0` schema contract. The brief is a dialogue state, not just a form copy. It supports `needs_clarification` and `ready_for_planning`, keeps `source_text`, `missing_fields`, `clarifying_questions`, and `assumptions`, leaves `target_titles` to the planner, and uses `exclusions` only for explicit recruiter constraints, not location blacklists.

`P4-003` is approved as the Search Brief validation/adapter contract. It should bridge `Search Brief -> Search Brief validation/normalization -> StructuredSearchRequest adapter -> existing structured-search validation`, reuse `normalize_structured_search_request(...)` as the authoritative search validation layer, reject `target_titles`, preserve `search_depth` as metadata, and avoid LLM calls, Tavily calls, query-plan generation, or search execution.

`P4-004` is approved as the Agent Tools v0 contract. The approved tools are `validate_search_brief`, `adapt_brief_to_structured_request`, `build_query_plan`, `validate_query_plan`, `run_single_wave_search`, `run_multi_wave_search`, `analyze_candidate_quality`, `summarize_search_results`, and `suggest_next_iteration`. Planning/analysis tools do not require approval; search execution tools require explicit approval.

`P4-005` is approved as the AI Query Planner v0 contract behind explicit mode. A real LLM/ChatGPT call is used for planning/explanation only, with `rule_based` remaining default. AI output is a non-executable `draft_query_plan`; deterministic validation exists in `P4-006`, and AI-generated plan execution remains out of scope until a later task.

`P4-006` is approved as the deterministic AI QueryPlan validation/fallback contract. Validation uses `normalized_brief + normalized_structured_request` as source of truth, marks valid AI plans as `validated_not_executable`, returns structured errors for rejected plans, and provides visible fallback to `RuleBasedQueryPlanner` when supported. No Tavily execution is introduced.

`P4-007` is approved as the planner explanation UI contract. It should extend the existing `Generated QueryPlan` preview with planner mode, Search Brief summary, planner explanation, validation/fallback state, structured errors/warnings, and an approval-needed notice, while remaining backward-compatible with the current rule-based QueryPlan preview.

`P4-003` through `P4-007` are implemented in code. The backend now supports `SearchBrief` validation/adapter endpoints, Agent Tools v0 metadata, explicit AI planner mode through OpenAI/ChatGPT for planning only, deterministic AI QueryPlan validation/fallback, and non-executable planner responses. The frontend now has a `Planner mode` control and renders Search Brief summary, planner explanation, validation/fallback state, and approval-needed notices.

`P4-008` is implemented as the real backend approval gate before Tavily execution. `/api/structured-search` and `/api/structured-search/multi-wave` now require explicit execution approval, bind approval to the concrete action and current QueryPlan fingerprint, reject missing/stale/wrong-action approval before Tavily, log approval metadata in search snapshots, and keep AI-generated plans non-executable. The legacy raw `/api/search` Tavily path is disabled so execution cannot bypass the approval-gated structured pipeline. Rule-based single-wave and multi-wave are the supported execution targets.

`P4-009` is completed as a no-Tavily planner evaluation. For the baseline `Backend Developer + Java + Spring/Kafka + Ukraine`, the rule-based planner produced the expected 10-query coverage. A live AI planner run produced a formally valid but too narrow 1-query plan, and `ai_with_fallback` produced a 3-query AI plan without triggering fallback. Conclusion: AI is useful for intent understanding and explanation, but current validation does not yet enforce baseline coverage quality. `RuleBasedQueryPlanner v1` remains the default and only executable planner. See `docs/phase-4-ai-planner-baseline.md`.

`P4-010` is implemented. The root cause was confirmed: the old AI planner prompt said `max_queries = 10`, showed a one-query output example, and the validator accepted `1..10` queries. The AI planner prompt now requests the tested 10-query standard baseline shape, `AIPlannerCoveragePolicy v0` applies strict coverage checks for the current Java/Ukraine baseline, `ai_with_fallback` can make one bounded repair attempt, and under-covered plans fall back visibly to `RuleBasedQueryPlanner`. AI-generated plans remain non-executable and Tavily is not called by this flow.

`P4-011` is completed as a docs-only closeout. Phase 4 is closed as an AI Agent Foundation, not as a complete autonomous recruiter agent. The closeout decision: the backend foundation is ready for Phase 5 because Search Brief, AI planning, deterministic validation/fallback, coverage policy, explanations, and approval-gated execution boundaries exist. Full recruiter chat, human-approved tool runtime, candidate workspace, and persistence remain later phases. Autonomous execution is prohibited: the agent may suggest, prepare, explain, validate, and analyze, but externally meaningful execution must require explicit approval. Direct LinkedIn access/automation, LinkedIn login, LinkedIn scraping/restriction bypass, candidate messaging/automatic outreach, and user or third-party account actions remain absolute prohibited behavior.

## What was built in Phase 1

- FastAPI backend.
- Static HTML/CSS/JS frontend.
- Editable X-ray Boolean query builder.
- Tavily search endpoint.
- Raw Tavily result display.
- Normalized result format.
- Initial relevance scoring.
- Initial required-condition filtering.
- Phase 1 findings document.

## Phase 1 POC result

- Raw Tavily results: 20
- Normalized results: 20
- Relevant results after required filters: 10
- Original target: 20 relevant candidates
- Status: successful POC accepted for Phase 1

## What Phase 1.1 changed

Phase 1.1 corrected the product behavior discovered during real frontend testing.

Implemented:

- Frontend sends only the final editable Boolean query and `max_results` when the user clicks `Search`.
- Form fields are only helpers for building the editable Boolean query.
- Backend no longer uses `main_anchor`, `additional_anchors`, `stack`, or `location` as hidden filters.
- UI shows `Search results` instead of `Relevant results`.
- Scoring is neutral and non-filtering.
- Results are sorted by neutral score but are not hidden by score.
- `LinkedIn profiles only` is an explicit frontend toggle and is off by default.
- `Ukraine LinkedIn domain only` is an explicit frontend toggle and is off by default.
- URL/profile filtering is applied only when the user enables the relevant visible toggle.

## Current product rule

- Current frontend search starts from recruiter chat that produces a validated `Search Brief`.
- Backend execution is still driven by the adapted structured request fields: `Role Family`, `Technology`, `Stack`, and `Location`.
- `QueryPlanner v1` builds a visible 10-query `QueryPlan` from the adapted structured request.
- Tavily receives only the generated queries from the visible `QueryPlan`.
- `LinkedIn profiles only` is an explicit visible filter.
- `Location filter` is an explicit visible filter and currently has the first config for `Ukraine`.
- `ua.linkedin.com/in/...` is treated as a country-domain signal, not a guaranteed current physical-location signal.
- The Ukraine `Location filter` uses `target_location_terms` and extracts a conservative `current_location_line` from Tavily public LinkedIn header/snippet text.
- Current-location classification is `target_location`, `foreign_current_location`, or `unknown_current_location`.
- Explicit foreign current location, for example `Warsaw, Mazowieckie, Poland`, hides the candidate even if the URL is `ua.linkedin.com/in/...`.
- Unknown current location can still fall back to softer signals: `country_domain`, `rescued_header_location`, `weak_history_only`, or `unknown_non_country_domain`.
- Non-UA LinkedIn profiles can be rescued only when the Tavily public header/current-location signal contains supported Ukraine target-location terms.

## Phase 1.1 test results

Target profile: Java programmer in Ukraine.

Test setup:

- `max_results`: 20
- `LinkedIn profiles only`: on
- `Ukraine LinkedIn domain only`: on
- Final displayed result shape: only `ua.linkedin.com/in/...` profile-like URLs.

10 tested query variants produced 53 unique `ua.linkedin.com/in/...` profiles in total.

Best single-query result:

```text
site:linkedin.com/in AND "Java Software Engineer" AND "Ukraine"
```

Result: 16 Ukrainian LinkedIn profiles from 20 raw Tavily results.

Other useful variants:

- `site:linkedin.com/in AND "Java Programmer" AND "Ukraine"`: 12 Ukrainian LinkedIn profiles from 20 raw results.
- `site:linkedin.com/in AND ("Java Developer" OR "Java Engineer" OR "Backend Java") AND ("Ukraine" OR "Kyiv" OR "Lviv")`: 10 Ukrainian LinkedIn profiles from 20 raw results.
- `site:linkedin.com/in AND ("Senior Java Developer" OR "Middle Java Developer") AND "Ukraine"`: 9 Ukrainian LinkedIn profiles from 20 raw results.

Weak result:

```text
site:linkedin.com/in AND "Java" AND ("Developer" OR "Engineer") AND ("Java" OR "Spring") AND "Ukraine"
```

Result: 0 Ukrainian LinkedIn profiles after both visible filters were enabled. The query can return role-like profiles, but too many results are outside `ua.linkedin.com/in/...` or are not usable after the Ukraine-domain filter.

## Main conclusion

Phase 1.1 improved the product substantially, but mainly by making the search behavior honest, visible, and controllable.

It did not prove that one broad universal query is the best strategy. The tests suggest the opposite: several focused queries produce better candidate coverage than one broad query.

## Phase 2 recommendation

Start Phase 2 with sequential multi-query search:

1. Run several focused Tavily queries.
2. Merge all returned results.
3. Normalize LinkedIn URLs.
4. Dedupe by normalized URL.
5. Apply visible filters such as `LinkedIn profiles only` and `Ukraine LinkedIn domain only`.
6. Show one combined candidate list.

Recommended first multi-query set:

- U02: `site:linkedin.com/in AND "Java Software Engineer" AND "Ukraine"`
- U10: `site:linkedin.com/in AND "Java Programmer" AND "Ukraine"`
- U08: `site:linkedin.com/in AND ("Java Developer" OR "Java Engineer" OR "Backend Java") AND ("Ukraine" OR "Kyiv" OR "Lviv")`

Expected result based on current tests: approximately 24-30 unique Ukrainian LinkedIn profiles in one pass. The simple sum is 38, but duplicates are expected across queries.

## Phase 2 baseline result

Baseline input:

- Role Family: `Backend Developer`
- Technology: `Java`
- Stack: `Spring`, `Kafka`, `AWS`
- Location: `Ukraine`
- `LinkedIn profiles only`: on
- `Ukraine LinkedIn domain only`: on

Measured result from one `POST /api/structured-search` run:

- Queries total: 10
- Queries succeeded: 10
- Queries failed: 0
- Raw Tavily results: 190
- Normalized results: 190
- Displayed before dedupe: 75
- Unique profiles after dedupe: 51
- Duplicates removed: 24
- Hidden by profile filter: 40
- Hidden by location-domain filter: 75

Phase 2 baseline criterion passed: 51 unique `ua.linkedin.com/in/...` profiles vs target 20.

Best query contributor:

- Q02 `site:linkedin.com/in AND "Java Software Engineer" AND "Ukraine"` added 13 new unique profiles.

Important limitation:

- `ua.linkedin.com/in/...` remains a useful Ukraine-domain signal, not a guaranteed current-location signal. At least one top result had a Ukraine-domain URL while the public snippet showed `Prague, Czechia`.
- Future work should add explicit location quality logic instead of relying only on country-specific LinkedIn subdomains.

## Phase 2 location filter result

`P2-009.1` replaced the hard `Ukraine LinkedIn domain only` structured contract with `location_filter_enabled`.

`P2-012` and `P2-013` then superseded the initial blacklist-style `negative_terms` logic. The current runtime behavior is:

- config stores Ukraine `target_location_terms`, not a finite list of bad countries/cities;
- the filter extracts a conservative `current_location_line` from multiline and one-line Tavily snippets;
- `target_location` is displayed;
- `foreign_current_location` becomes `excluded_foreign_current_location` and is hidden before `country_domain` can allow it;
- `unknown_current_location` falls back to country-domain/header/weak/unknown signals;
- frontend report shows `Foreign location` via `hidden_by_foreign_current_location`.

Current baseline input:

- Role Family: `Backend Developer`
- Technology: `Java`
- Stack: `Spring`, `Kafka`, `AWS`
- Location: `Ukraine`
- `LinkedIn profiles only`: on
- `Location filter`: on

Historical `P2-009.1` measured result from one `POST /api/structured-search` run before `P2-012`:

- Queries total: 10
- Queries succeeded: 10
- Queries failed: 0
- Raw Tavily results: 200
- Normalized results: 200
- Displayed before dedupe: 85
- Unique profiles after dedupe: 58
- Duplicates removed: 27
- Hidden by profile filter: 53
- Hidden by location filter: 62
- Rescued by header/location: 13 occurrences, 9 unique profiles
- Hidden by negative header/location: 3 occurrences, 2 unique profiles
- Weak history-only location signal: 26 occurrences, 18 unique profiles
- Unknown non-country-domain location: 33 occurrences, 21 unique profiles

Location filter unique breakdown:

- `country_domain`: 49
- `rescued_header_location`: 9
- `excluded_negative_header_location`: 2
- `weak_history_only`: 18
- `unknown_non_country_domain`: 21

Conclusion from `P2-009.1`: the first `Location filter` improved Phase 2 quality compared with strict domain-only filtering because it kept the Ukraine-domain signal, rescued strong non-UA profiles with Ukraine in header/location, and excluded some explicit foreign-current-location matches.

Current `P2-012`/`P2-013` replay on local snapshot `2026-05-14T17-12-12Z_structured-search_backend-developer-java-ukraine.json`:

- Raw Tavily results: 197
- Displayed occurrences: 105
- Unique profiles after dedupe: 73
- Displayed unique status breakdown: `target_location = 71`, `country_domain = 2`
- Known `ua.linkedin.com` false positives with `Warsaw, Mazowieckie, Poland` are hidden as `excluded_foreign_current_location`

Live Tavily runs are not stable. Recent runs for `Backend Developer + Java + Spring/Kafka + Ukraine` produced roughly `55-60` unique profiles in a single wave. Multi-wave experiments showed limited incremental gain:

- 1 wave: 60 cumulative unique profiles
- 3 waves: 64 cumulative unique profiles
- 5 waves: 61 cumulative unique profiles in one fresh block
- 10 waves: 60 cumulative unique profiles in one fresh block

Conclusion: multi-wave can add candidates, but returns diminish quickly. A future implementation should stop based on incremental unique gain rather than always running a fixed high number of waves.

## Phase 2 final conclusion

Phase 2 is completed successfully.

What Phase 2 proved:

- Multi-query search gives stronger coverage than one broad query for the tested Java/Ukraine scenario.
- `QueryPlan` is the right architectural contract for the next product steps.
- The executor, dedupe, report, and frontend can stay stable while planner logic evolves.
- Visible filters are the right product behavior; hidden backend filtering caused confusion earlier.
- Location should be treated as a confidence signal, not a single hard URL-domain rule.

Final baseline numbers remain above the Phase 2 success criterion:

- Historical `P2-009.1` single run: 58 unique candidates vs target 20
- Current `P2-012`/`P2-013` local replay: 73 unique candidates vs target 20
- Recent live single-wave runs: roughly 55-60 unique candidates vs target 20
- The exact Tavily count is not stable and should not be treated as a deterministic product guarantee

Recommended next steps:

- Phase 5: `Recruiter Chat UX + Search Brief conversation`, focused on one narrow Java/Ukraine flow where chat collects and refines a validated `Search Brief`, uses Phase 4 planner/approval contracts, guides a next iteration after results, and gets a coherent AI Agent visual style. `P5-001` through `P5-012` are completed and Phase 5 is closed.
- Phase 5.5: `Technical modularization before Agent Runtime`, completed as no-behavior-change backend modularization before the tool-calling runtime.
- Phase 6: `Tool-Calling Agent Runtime`, completed as a bounded, human-approved Agent Runtime v0 baseline that can prepare approved backend tool calls, execute only after approval, inspect results, and suggest next iterations without autonomous execution.
- Phase 7: `Agent Conversation Wording Layer`, completed and closed as `Agent Conversation Wording Layer v0 baseline`.
- Phase 7.5: `Recruiter Simulation QA & Flow Hardening`, completed and closed.
- Phase 8: `Candidate Workspace/Table + Shortlist`, completed and closed through `P8-032`.
- Phase 8.5: `Agentic Candidate Review & Iteration`, current active direction after `P8-032`; `P8.5-001 Define agentic candidate review contract`, `P8.5-002 Add top-candidate recommendation from returned workspace facts`, and `P8.5-003 Add selected-candidate comparison` are completed.
- Phase 9: `Persistent Memory + Saved Searches`.

Phase 4 is completed as AI Agent Foundation. Phase 5 is completed as the narrow Java/Ukraine Agent UX foundation. Phase 5.5 is completed as technical preparation before runtime. Phase 6 is completed as `AI Agent Runtime v0 baseline`. Phase 7 is completed as `Agent Conversation Wording Layer v0 baseline`. Phase 7.5 is completed as a recruiter simulation QA gate with the decision `ready after approved fixes completed`. Phase 8 is completed and closed through `P8-032` as the Candidate Workspace/Table + Shortlist phase. Phase 8.5 is now active, and `P8.5-001 Define agentic candidate review contract`, `P8.5-002 Add top-candidate recommendation from returned workspace facts`, and `P8.5-003 Add selected-candidate comparison` are completed as deterministic current-run review slices. Every following task should intentionally move the product toward a real AI Agent experience while preserving backend tool boundaries and explicit approval before execution.

## Verification

- `powershell -ExecutionPolicy Bypass -File .\scripts\check_all.ps1`
- `python -m compileall app`
- `node --check app/static/app.js`
- Backend smoke-check for query-only request behavior.
- Backend smoke-check for neutral scoring.
- Backend smoke-check for LinkedIn profile URL detection and toggle request field.
- Backend smoke-check for Ukraine LinkedIn domain URL detection and counts.
- UI check: `Search results`, `LinkedIn profiles only`, and `Ukraine LinkedIn domain only` are visible; both toggles are off by default.
- Phase 2 `/api/query-plan` smoke: 10 generated queries.
- Phase 2 `/api/structured-search` baseline run: 51 unique profiles.
- Phase 2 `P2-009.1` backend smoke: `location_filter_enabled` contract, no legacy `location_domain_only`, rescue/weak/negative signals, and candidate-level URL merge.
- Phase 2 `P2-009.1` browser smoke: `Location filter` toggle, generated `QueryPlan`, frontend report metrics, and no console errors.
- Phase 2 `P2-009.1` real baseline run: 58 unique profiles with the new location filter.
- Phase 2 `P2-010` documentation closeout completed.
- Phase 2 `P2-011` local structured-search snapshots added under `logs/search-runs/`.
- Phase 2 `P2-012` current-location classification smoke passed: target, foreign, unknown, weak-history-only, duplicate-merge, and filter-off cases.
- Phase 2 `P2-013` conservative one-line current-location extraction smoke passed.
- Phase 2 multi-wave Tavily experiments completed for 1, 3, 5, and 10 waves.
- Phase 3 local smoke checks passed for seniority detection, review flag taxonomy, and quality score.
- Phase 3 browser verification passed for the hybrid candidate quality view on desktop and mobile viewport.
- Phase 3 `P3-010` real Java/Ukraine quality baseline completed: 57 unique candidates from 200 raw Tavily results.
- Phase 3 `P3-010.1` no-code review completed for `missing_selected_stack` candidates from the exact baseline snapshot.
- Phase 3 `P3-010.2` frontend stack display semantics passed syntax, mapping, snapshot-state, render, and compile checks.
- Phase 3 `P3-011` no-Tavily smoke passed for multi-wave validation, early stop, cross-wave dedupe, `wave_sources`, snapshot type, and unchanged single-wave endpoint behavior.
- Phase 3 `P3-012` real adaptive multi-wave evaluation completed: 4 waves, 40 queries, 67 unique candidates, stopped by low incremental gain.
- Phase 3 `P3-013` frontend smoke passed for default single-wave endpoint, toggle-on multi-wave endpoint, multi-wave defaults payload, and report metric rendering.
- Phase 3 `P3-014` docs-only closeout completed and Phase 4 handoff prepared.
- Phase 4 `P4-003`-`P4-007` implementation checks passed: backend compile, frontend syntax, no-Tavily smoke for SearchBrief/tools/rule-based plan/AI validation/mocked AI fallback, browser smoke for planner UI, live OpenAI planner call, and live Tavily single-wave run through the backend.
- Phase 4 `P4-008` implementation checks passed: backend compile, frontend syntax, no-Tavily smoke for missing/wrong/stale approval rejection, approved single-wave, approved multi-wave, and snapshot approval metadata.
- Phase 4 `P4-009` no-Tavily planner evaluation completed: rule-based planner returned 10 baseline queries, live AI planner returned 1 query, and live `ai_with_fallback` returned 3 queries without fallback because the current validator does not yet enforce coverage quality.
- Phase 4 `P4-010` implementation checks passed: backend compile, no-Tavily mocked smoke for coverage gate, one repair attempt, fallback after failed repair, validation endpoint coverage errors, and live no-Tavily OpenAI planner evaluation returning 10 queries for both `ai` and `ai_with_fallback`.
- Phase 4 `P4-011` docs-only closeout completed: Phase 4 is completed as AI Agent Foundation and Phase 5 is the next active phase.
- Phase 5 `P5-004` implementation checks passed: backend compile, frontend syntax, chat adapter smoke, git whitespace check, and browser smoke for RU chat -> Search Brief -> `Build Plan` -> `Search Plan` / `Ready for approval` with 10 rule-based queries and enabled `Approve & Search`. Tavily execution was not triggered.
- Phase 5 `P5-005`-`P5-007` implementation checks passed: backend compile, frontend syntax, no-Tavily Agent Plan smoke, no-Tavily Agent Response smoke, and LLM wording smoke for assisted wording, deterministic fallback, disallowed-number fallback, provenance metadata, and no raw LinkedIn URL/full candidate payload.
- Phase 5 `P5-007.1` stabilization checks passed: backend compile, frontend syntax, Phase 5 smoke scripts, and missing Agent Plan action/fingerprint rejection in `/api/agent/query-plan`.
- Phase 5 `P5-008` onboarding checks passed: backend compile, frontend syntax, chat adapter smoke for RU/EN greetings without OpenAI, near-empty backend input, partial/complete intent, prohibited refusal, and draft preservation.
- Phase 5 `P5-009` refinement checks passed: backend compile, frontend syntax, chat adapter smoke for deterministic add/remove/replace stack, seniority, search depth, unsupported atomic patch, refinement without draft, duplicate add, missing remove, and last-stack removal block.
- Phase 5 `P5-010` next-iteration checks passed: backend compile, frontend syntax, Agent Response smoke for non-executable options/deep patch, LLM wording smoke proving options are preserved and not sent as mutable wording output, and git diff whitespace check.
- Phase 5 `P5-011` visual refresh checks passed: frontend syntax check and git diff whitespace check. No desktop/mobile visual QA was required for this task by scope.
- Phase 5 `P5-012` docs-only closeout completed: Phase 5 is closed as the narrow Java/Ukraine Agent UX foundation, Phase 5.5 became the next active phase at that point, and broader conversation scenarios/ordinary chat wording were carried forward to Phase 7.
- Phase 5.5 `P5.5-009` closeout completed: Phase 5.5 is closed as no-behavior-change backend modularization, route/import/no-network HTTP smoke coverage is part of the regression baseline, and Phase 6 became the next active phase at that point.
- Phase 6 `P6-005` runtime guardrail checks passed: no-network runtime smoke covers stale/mutated approval rejection, runtime context mismatch, frontend runtime-only execution path, mocked approved single/multi-wave execution, prepare-without-execution, and missing Tavily key during approved execution.
- Phase 6 `P6-005.1` unmocked runtime execution smoke passed: real single/multi runtime wrappers execute through the existing backend pipeline with lower-level Tavily wave monkeypatching only, no OpenAI calls, no snapshot writes, and `report.unique_profiles >= 1`.
- Phase 6 `P6-006` docs-only closeout completed: Phase 6 is closed as `AI Agent Runtime v0 baseline`, `docs/phase-6-closeout.md` records the decision, Phase 7 became the active direction at that point, and the local regression baseline passed.
- Phase 7 `P7-007` wording validation checks passed: code-level nested `wording_provenance`, deterministic fallback/no-call metadata, attempted-call fallback semantics, Agent Plan limitation rejection, Agent Response limitation-kind guardrail, unsafe wording fallback, and `main.run_openai_json_agent_wording` monkeypatch compatibility are covered by `scripts/smoke_p7_wording_validation.py` and the full local regression baseline.
- Phase 7 `P7-008` frontend typed rendering completed: current recruiter chat, Agent Plan, Agent Response, tool-unavailable, safety, validation, refinement, clarification, and system-error messages now use frontend-local typed rendering metadata without changing backend/API/runtime/search behavior. Historical typed rendering supported inert `next_iteration_options`; after `P8-032C`, recruiter chat no longer renders those option blocks, while backend/internal option data remains non-executable.
- Phase 7 `P7-009` golden conversation regression completed: `scripts/smoke_p7_golden_conversations.py` covers no-network recruiter chat, Search Brief refinement, Agent Plan, Build Plan, runtime prepare, Agent Response, wording fallback/provenance, and frontend typed-message contract scenarios, and it is included in `scripts/check_all.ps1`.
- Phase 7 `P7-010` docs-only closeout completed: Phase 7 is closed as `Agent Conversation Wording Layer v0 baseline`, `docs/phase-7-closeout.md` records wording quality evaluation, guardrail evaluation, residual gaps, verification evidence, and the original Phase 8 handoff; Phase 7.5 was later inserted as the QA gate before Phase 8, and the local regression baseline passed after document updates.
- Phase 7.5 `P7.5-003` browser QA checklist completed: all 104 scenario IDs are mapped with no missing/extra/duplicates, the QA split is 47 RU scenarios and 57 EN/mixed/other scenarios, live Tavily is limited to two approved single-wave UI searches, and the local regression baseline passed after document updates.
- Phase 7.5 `P7.5-004` RU browser QA completed: 47/47 RU scenarios were recorded in `docs/phase-7-5-ru-browser-qa-results.md`, with 39 pass, 7 fail, 1 blocked, and 0 live Tavily executions because approved runtime preparation did not complete.
- Phase 7.5 `P7.5-006` initial QA findings report completed: `docs/phase-7-5-qa-findings-report.md` groups the RU blockers and sets `P7.5-007 Review and approve current-flow fixes` as the next task.
- Phase 7.5 `P7.5-007` docs-only decision completed: the approved P7.5-008 fix scope is runtime approval after Build Plan settles, latest-turn prohibited-intent refusal with current Search Brief preservation and stale executable-state clearing, and clean-state initial request routing away from refinement blocking.
- Phase 7.5 `P7.5-008` implementation completed: frontend runtime approval preparation moved after Build Plan settlement, latest-turn prohibited-intent refusal was tightened, clean-state recruiter messages now use initial extraction instead of refinement blocking, and the local regression baseline passed.
- Phase 7.5 `P7.5-009` regression coverage completed: `scripts/smoke_p75_current_flow_regressions.py` initially covered `P75-QA-001` through `P75-QA-007`, frontend runtime/refusal guardrails, no LLM call on prohibited requests, and is included in `scripts/check_all.ps1`.
- Phase 7.5 `P7.5-005` EN/mixed browser QA completed: 57/57 scenarios were recorded in `docs/phase-7-5-en-browser-qa-results.md`, with 37 pass, 20 fail, 0 blocked, and 1 approved live Tavily execution through visible `Approve & Search`; new findings are `P75-QA-008` through `P75-QA-014`.
- Phase 7.5 `P7.5-011` immediate EN/mixed hardening completed: deterministic chat routing now covers the EN/mixed findings `P75-QA-008` through `P75-QA-014`, frontend post-results follow-up stays local/grounded, and the P7.5 no-network smoke now covers `P75-QA-001` through `P75-QA-014`.
- Phase 7.5 `P7.5-010` docs-only closeout completed: `docs/phase-7-5-closeout.md` records the readiness decision `ready after approved fixes completed`, all `P75-QA-001` through `P75-QA-014` findings are closed as fixed and verified, Phase 7.5 is closed, and Phase 8 became the current active phase starting with `P8-001`.
- Phase 8 `P8-001` docs-only contract completed: `docs/phase-8-candidate-workspace-contract.md` defines Candidate Workspace v0, source data, browser in-memory session/local UI state, workspace run context with a per-run component, `review_status` source-of-truth with derived shortlist state, safe profile-link/manual-click boundaries, security/display rules, table/detail/export/explanation boundaries, and the approved conservative handoff to `P8-002`.

## Current known limitations

- LinkedIn public snippets remain incomplete and inconsistent.
- Tavily search behavior can vary between runs.
- `LinkedIn profiles only` filters by URL pattern only.
- `Location filter` currently has only the first country config: `Ukraine`.
- Future countries need their own country-domain and `target_location_terms` mapping; they should reuse current-location classification instead of introducing finite negative-location blacklists.
- Header/location detection uses Tavily public snippets/content only and is not equivalent to verified profile enrichment.
- `ua.linkedin.com/in/...` is not a guaranteed current physical location.
- Current-location extraction is conservative and can keep ambiguous snippets unknown.
- `RuleBasedQueryPlanner v1` is still the default execution planner. AI draft planning exists behind explicit mode, but AI-generated plans remain non-executable until a later reviewed task enables AI plan execution through deterministic validation and approval.
- Current AI QueryPlan validation now includes strict `AIPlannerCoveragePolicy v0` coverage checks for the Java/Ukraine standard baseline. Unsupported briefs still need future coverage policies and return a visible `coverage_policy_not_configured` warning.
- Candidate quality score is a deterministic v1 signal and should not be treated as final recruiting quality.
- No database, persistent shortlist, authentication, or autonomous AI agent runtime is included. Phase 8 shortlist/review state is browser in-memory only until Phase 9.
- Absolute product boundaries: no direct web-search bypass outside the approved backend pipeline, no direct LinkedIn access/automation, no LinkedIn login, no LinkedIn scraping or restriction bypass, no automatic candidate messaging, no autonomous execution, and no actions with user or third-party accounts.

## Reference documents

- `Roadmap.md`
- `Tasks.md`
- `docs/phase-5-agent-stabilization.md`
- `docs/phase-1-poc-findings.md`
- `docs/phase-3-quality-baseline.md`
- `docs/phase-3-multi-wave-evaluation.md`
