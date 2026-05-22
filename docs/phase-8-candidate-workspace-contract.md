# Phase 8 Candidate Workspace Contract

Task: `P8-001 Define candidate workspace contract`

Status: completed

## Decision

Phase 8 Candidate Workspace v0 turns already approved search results into the recruiter working artifact.

The workspace is built from the current approved search pipeline output:

`recruiter chat -> Search Brief -> Agent Plan -> Build Plan -> visible QueryPlan -> explicit Approve & Search -> approved Tavily-backed results`

Implementation status after `P8-005`: the first frontend-only Candidate Workspace slices are implemented. `P8-002` added explicit workspace run/candidate state and a recruiter-facing workspace list, `P8-003` added workspace view sorting/filtering over already returned candidates, `P8-004` added browser in-memory review status, derived shortlist, escaped plain-text notes, and review-status/shortlist filters, and `P8-005` added deterministic candidate-level explanations grounded only in returned workspace facts. Backend/API/search/runtime behavior, persistence, saved searches, export, and bounded LLM explanation wording remain out of scope until later reviewed tasks.

Candidate explanation path: deterministic candidate-level explanations are implemented in `P8-005`, grounded only in returned workspace facts. The wording path is split into `P8-006 Define bounded candidate explanation wording contract` and later `P8-006.1 Implement explicit selected-candidate wording overlay`. LLM wording can only rewrite deterministic explanation wording after validation and fallback. LLM wording must not decide facts, stable `reason_key`, reason codes, source/version, fit, score, ranking, filters, search execution, review state, notes, shortlist, export, or persistence, and it must not run just because a candidate is opened or selected.

Candidate Workspace v0 is browser in-memory session/local UI state only. Shortlist, notes, and candidate review statuses are not persisted in Phase 8 unless a later reviewed task explicitly changes that boundary. Database, persistent memory, saved searches, saved candidates, and cross-session continuation remain Phase 9.

In Phase 8 v0, reloading the page may clear workspace state. Do not add `localStorage`, `sessionStorage`, IndexedDB, backend save, logs, snapshots, or any other persistence path for workspace state without a separate reviewed task.

## Goal

Make search results usable as a recruiter workspace:

- compare candidates quickly;
- inspect evidence behind quality signals;
- sort and filter candidates;
- mark review status;
- create a shortlist;
- add recruiter notes;
- prepare for export later.

The workspace must preserve the current human-approved execution boundary. It must not execute searches, rerun Tavily, automatically open LinkedIn, scrape LinkedIn, message candidates, or perform account actions.

Manual recruiter navigation is different from agent/app automation: a visible public profile URL may remain a normal external link that the user can click manually when it is a validated safe `http`/`https` LinkedIn profile URL. The agent/app must not click it, open it automatically, log in, automate LinkedIn, scrape it, bypass restrictions, or use it for account actions.

## Source Data

Workspace candidates are derived from `deduped_results` returned by the approved runtime search result.

The current candidate record already contains enough data for Workspace v0:

- `normalized_url`;
- `result.name`;
- `result.headline`;
- `result.title`;
- `result.url`;
- `result.source`;
- `result.snippet`;
- `result.raw_title`;
- `result.raw_content`;
- `result.tavily_score`;
- `result.quality_score`;
- `result.quality_score_version`;
- `result.quality_score_breakdown`;
- `result.quality_score_penalties`;
- `result.review_flags`;
- `result.review_flag_details`;
- `result.role_display`;
- `result.role_fit`;
- `result.role_evidence`;
- `result.technology_display`;
- `result.technology_fit`;
- `result.technology_evidence`;
- `result.stack_display`;
- `result.stack_fit`;
- `result.stack_evidence`;
- `result.seniority_display`;
- `result.seniority_fit`;
- `result.seniority_evidence`;
- `location_signal_status`;
- `location_signal_terms`;
- `header_location_text`;
- `current_location_line`;
- `current_location_lines`;
- `current_location_classifications`;
- `query_sources`;
- optional `wave_sources` when multi-wave search is used.

The workspace may derive display-only fields from these facts, such as a quality bucket or a compact evidence summary, but it must not mutate backend-owned candidate facts.

`normalized_url` is the primary candidate identity and backend dedupe/profile identity source. `result.url` may be used only as a validated link/display fallback when `normalized_url` cannot produce a safe clickable profile href; it must not override candidate identity when `normalized_url` is present.

## Workspace Candidate Model

Candidate Workspace v0 should treat every displayed candidate as:

```json
{
  "candidate_id": "normalized LinkedIn profile URL",
  "identity": {
    "name": "string",
    "headline": "string",
    "profile_url": "string",
    "source": "linkedin"
  },
  "fit": {
    "quality_score": 0,
    "quality_bucket": "optional later display bucket, not a P8-003 source of truth",
    "role": "string",
    "technology": "string",
    "stack": "string",
    "seniority": "string",
    "location": "string"
  },
  "evidence": {
    "snippet": "string",
    "role_evidence": [],
    "technology_evidence": [],
    "stack_evidence": [],
    "seniority_evidence": [],
    "location_signals": [],
    "query_sources": [],
    "wave_sources": []
  },
  "review": {
    "review_flags": [],
    "review_flag_details": [],
    "score_breakdown": [],
    "score_penalties": []
  },
  "workspace_state": {
    "review_status": "new",
    "notes": ""
  },
  "derived_display": {
    "shortlisted": false
  }
}
```

This JSON shape is a contract guide, not a required new backend schema in `P8-001`. `derived_display.shortlisted` is computed from `workspace_state.review_status == "shortlisted"` and must not become an independent source of truth.

## Workspace Run Context

Candidate Workspace v0 should be scoped to the latest approved search run.

The workspace may keep a frontend/session-only `workspace_run_id` to bind local review state to the current result set. `workspace_run_id` must include a per-run component because the same QueryPlan can be approved and executed more than once while Tavily returns a different result set.

It can be derived from current frontend state, for example:

- runtime approval idempotency key or tool-call fingerprint when available;
- approval id or tool-call id when available;
- runtime context fingerprint or selected run mode when useful for diagnostics;
- local session counter or timestamp.

Current QueryPlan fingerprint may be stored as run context, but it is not sufficient by itself as the unique workspace run identifier.

`workspace_run_id` is not a backend persistence key in Phase 8 and must not imply saved searches, saved candidates, cross-session continuity, or database state.

For `P8-002`, runtime approval/tool-call values needed for `workspace_run_id` must be captured before frontend code calls `clearRuntimeApproval()`, because the current runtime approval and tool-call state is cleared after successful rendering.

The workspace may display run context from already returned data:

- Search Brief summary;
- planner mode;
- run mode: single-wave or multi-wave;
- query count;
- report counts;
- QueryPlan fingerprint if useful for diagnostics;
- query contribution/source metadata;
- Agent Response summary.

Run context is display/diagnostic state. It must not become authority to execute, rerun, or mutate searches.

## Workspace State

Workspace state belongs to the frontend/session in Phase 8:

- `review_status`;
- derived `shortlisted` display value;
- `notes`;
- selected/open candidate UI state;
- current sort/filter choices.

Allowed review statuses for v0:

- `new`;
- `reviewing`;
- `shortlisted`;
- `not_a_fit`.

Rules:

- `review_status` is the source of truth for review workflow state;
- `shortlisted` is a derived convenience value: `shortlisted = review_status == "shortlisted"`;
- `shortlisted` must not be stored or mutated as independent state when `review_status` is available;
- changing the shortlist toggle should set `review_status = shortlisted` when enabled;
- disabling shortlist should return `review_status` to `reviewing`, because the recruiter has already touched/reviewed the candidate;
- notes are free-form recruiter notes, session-local only;
- changing notes/status/shortlist must not alter candidate evidence, score, flags, or search facts;
- each approved search creates a new local workspace run by default;
- notes/status/shortlist reset for a new approved search by default;
- reloading the page may clear workspace state in Phase 8 v0;
- do not use browser storage, backend storage, logs, snapshots, or hidden persistence for workspace state without a separate reviewed task;
- carrying state across runs belongs to Phase 9 unless a later reviewed Phase 8 task defines a narrow local-only exception.

## UI Surfaces

Phase 8 should introduce these workspace surfaces:

- candidate table/list as the main results artifact;
- compact candidate rows/cards for scanning;
- candidate detail area or drawer for evidence and score explanation;
- shortlist filter/view;
- notes/status controls;
- query/wave source details;
- export preparation later.

The current dark AI Agent workspace visual direction should be preserved. The workspace should feel like a dense recruiter tool, not a landing page.

The layout should be hybrid and responsive:

- desktop can use a dense recruiter table/list with compact columns;
- narrow screens should preserve readability through stacked rows/cards or a detail-first layout;
- evidence, score details, flags, and query sources can live behind expand/drawer sections;
- text must not overflow controls or overlap neighboring content.

## Table Columns For V0

Recommended default visible columns:

- Candidate;
- Quality;
- Role;
- Technology;
- Stack;
- Location;
- Seniority;
- Flags;
- Source;
- Status;
- Shortlist.

Details that can live behind expand/drawer:

- snippet/public text;
- score breakdown;
- score penalties;
- review flag descriptions;
- role/technology/stack/seniority evidence;
- location signal details;
- query sources;
- wave sources;
- notes.

## Sorting And Filtering Boundaries

Sorting/filtering in Phase 8 should operate on already returned workspace data:

- quality score;
- quality bucket;
- review flags;
- role fit;
- technology fit;
- stack fit;
- seniority fit;
- location signal status;
- query source;
- review status;
- shortlisted state.

Phase 8 sorting/filtering must not change backend scoring, Candidate Quality rules, Tavily queries, QueryPlan generation, dedupe, location filtering, or result inclusion logic unless a later reviewed task explicitly changes those systems.

First implementation slice: `P8-003 Add sorting and filtering by quality signals`.

`P8-003` should stay frontend-only and operate on the explicit workspace state created by `P8-002`. These controls are workspace view controls, not backend search filters:

- keep `workspaceCandidates` as the full current result set from the latest successful approved search;
- compute a derived visible list such as `visibleWorkspaceCandidates`;
- return a new visible candidate array without mutating `workspaceCandidates` or candidate objects;
- preserve the backend `deduped_results` order as the default/reset order;
- use original order as a deterministic tie-breaker for all other sorts;
- use only allowlisted sort/filter values;
- unknown sort mode falls back to original order;
- unknown filter value falls back to `All` only for that specific filter dimension while other valid filters continue to apply;
- normalize sort/filter enum values as local allowlist strings and do not trust raw UI/backend values;
- show visible count vs total workspace candidate count;
- show a distinct empty-view state when candidates exist but current view filters match no candidates;
- reset view state to original order/all filters for every new successful approved workspace run;
- clear sort/filter state with the same workspace stale/reset/error boundaries as `P8-002`.

Recommended first `P8-003` sorting controls:

- `Original order`;
- `Quality: high to low`;
- `Quality: low to high`;
- `Name: A-Z`.

Recommended first `P8-003` filters:

- `Quality score`: `All`, `80+`, `70+`, `60+`;
- `Stack evidence`: `All`, `Confirmed`, `Query-source only`, `Not visible`;
- `Review flags`: `All`, `No flags`, `Has flags`, `High/medium flags`;
- `Location signal`: `All`, `Target/strong signal`, `Unknown/weak`.

`P8-003` should use existing returned fields only:

- `quality_score` for quality sorting and thresholds;
- safe candidate display label from the workspace view model for name sorting;
- `stack_fit` for stack evidence filters;
- `review_flags` / `review_flag_details` for review flag filters;
- `location_signal_status` for location signal filters;
- `source_index` / `display_index` only for order/tie-break display metadata, never identity.

Comparison and composition rules:

- quality comparisons use safe finite-number conversion; missing, non-numeric, or non-finite values sort to the end and do not pass numeric thresholds;
- name sorting is case-insensitive and uses the safe display label from the workspace candidate view model;
- different filter dimensions combine with AND semantics;
- within one filter dimension, a selected option may map to an explicit OR set of candidate values;
- `All` for one dimension means that dimension does not constrain the visible list;
- sorting applies after filtering to the derived visible list.

Candidate-level location status mapping for `P8-003`:

- `Target/strong signal` includes `target_location`, `country_domain`, and `rescued_header_location`;
- `Unknown/weak` includes `weak_history_only`, `unknown_non_country_domain`, `not_applied`, missing, or equivalent weak/unknown candidate-level statuses;
- `excluded_foreign_current_location` should normally not appear in displayed candidates after backend location filtering; if it does appear, it is not a `Target/strong signal` and must not cause frontend mutation/deletion of the source candidate;
- report/count names such as `weak_location_history_only` and `unknown_non_country_domain_location` are not candidate-level `location_signal_status` values and should not be used as frontend candidate status constants.

Do not add `quality_bucket` as a new source-of-truth field in `P8-003`; use explicit score thresholds until a later reviewed task defines any bucket semantics.

Do not add review-status or shortlist filters in `P8-003`. Those depend on interactive recruiter review state and belong to `P8-004`.

`P8-003` must not trigger Tavily, call runtime execution, rebuild Search Brief, rebuild Agent Plan, rebuild QueryPlan, change runtime approval, change Agent Response, auto-open/fetch profile URLs, mutate `workspaceCandidates`, or change backend/API/search/scoring/filter/dedupe/location behavior.

## Shortlist, Notes, And Status Boundaries

First interactive recruiter review-state slice: approved task `P8-004 Add shortlist, notes, and statuses`.

`P8-004` should stay frontend-only and operate on the explicit workspace state created by `P8-002` and the derived workspace view introduced by `P8-003`.

`P8-004` should be coded only after `P8-002` and `P8-003` are implemented, or as the last slice in the same implementation batch after their workspace state, helper contracts, and derived visible-list behavior already exist.

Review state is recruiter UI state, not candidate fact state:

- keep `review_status` as the source of truth;
- derive `shortlisted` from `review_status == "shortlisted"`;
- do not store or mutate `shortlisted` as an independent source-of-truth field;
- keep notes/status/shortlist state separate from backend-owned candidate facts;
- do not mutate candidate evidence, quality score, score breakdown, flags, role/technology/stack/seniority/location fit, query sources, wave sources, or location signals;
- reset notes/status/shortlist by default for every new successful approved workspace run;
- clear notes/status/shortlist state with the same workspace stale/reset/error boundaries as `P8-002`;
- page reload may clear notes/status/shortlist in Phase 8 v0;
- do not add `localStorage`, `sessionStorage`, IndexedDB, backend save, logs, snapshots, database persistence, saved candidates, saved searches, or cross-session continuation.

Allowed v0 `review_status` values:

- `new`;
- `reviewing`;
- `shortlisted`;
- `not_a_fit`.

Shortlist behavior:

- enabling shortlist sets `review_status = shortlisted`;
- disabling shortlist sets `review_status = reviewing`;
- disabling shortlist should not silently return a candidate to `new`, because the recruiter has already touched/reviewed the candidate;
- manual status selector may still set `review_status = new` when the recruiter explicitly chooses `New`;
- `shortlisted` is a derived display/filter value only.

Notes behavior:

- notes are recruiter-entered plain text;
- notes must be escaped wherever displayed;
- notes must not render markdown or HTML;
- notes should have a conservative length boundary of 1000 characters to protect layout and performance;
- notes textarea should use `maxlength="1000"` or an equivalent visible input constraint;
- note update helpers should also truncate pasted/programmatic values to 1000 characters so the limit does not depend only on DOM behavior;
- changing notes must not trigger Tavily, runtime calls, Build Plan, Agent Plan, QueryPlan, Agent Response, backend calls, LinkedIn navigation, export, persistence, or account actions.

Recommended `P8-004` controls:

- status selector: `New`, `Reviewing`, `Shortlisted`, `Not a fit`;
- shortlist toggle/button derived from status;
- notes field in candidate row/detail surfaces;
- review-state workspace filters: `Review status` and `Shortlist`.

`P8-004` should add review-state filters. They are frontend workspace view filters only:

- `Review status`: `All`, `New`, `Reviewing`, `Shortlisted`, `Not a fit`;
- `Shortlist`: `All`, `Shortlisted only`, `Not shortlisted`;
- different filter dimensions continue to combine with AND semantics;
- review-state filters must not change backend search filters, Tavily queries, Candidate Quality, scoring, dedupe, location filtering, result inclusion, or runtime approval.

State and view composition rules:

- notes/status/shortlist should survive sort/filter re-render inside the same workspace run;
- `Reset filters` should not erase notes/status/shortlist;
- full workspace reset, new successful approved search, stale/error clearing, or page reload may clear notes/status/shortlist;
- if `Shortlisted only` or a review-status filter is active and a recruiter changes a candidate so it no longer matches, the candidate may disappear from the current visible list after state is saved and the view is recomputed;
- disappearing from the current visible list must not delete the underlying workspace candidate or review state.
- `workspaceReviewStateByCandidateId` or equivalent JS state should be the source of truth for notes/status/shortlist;
- DOM inputs/selects should only render current state and submit changes back into JS state;
- re-rendering after sort/filter should restore note/status/shortlist values from JS state;
- do not read DOM controls as the source of truth when recomputing the visible workspace list.

Status normalization and display rules:

- missing/unknown status values during initialization should normalize to `new`;
- unknown status update attempts should be a no-op and preserve the previous valid status;
- status labels and CSS classes must come from local allowlist/map helpers;
- unknown status values must not appear in dynamic CSS class names;
- do not build status labels, status classes, or dynamic class names directly from raw status values.

Render-only fallback ids may be used as current-workspace-run UI keys when `normalized_url` is missing, including surviving sort/filter re-render inside the current workspace run. They must not imply persistence, future carryover, saved-candidate identity, or backend/profile identity.

`P8-004` should add no-network helper smoke coverage for review-state helpers: allowed status normalization, missing/unknown initialization status normalizing to `new`, unknown status update preserving the previous valid status, initial state, status update, status label/class allowlist behavior, unknown status not entering a dynamic CSS class, manual selector returning to `new`, shortlist enable/disable transitions, derived shortlisted state, notes update, notes length behavior at exactly 1000 characters and over 1000 characters, helper-level truncation for pasted/programmatic note values, review-state reset, required review filters, notes/status/shortlist surviving sort/filter re-render, DOM re-render restoring review state from JS state where practical, `Reset filters` preserving review state, full workspace reset clearing review state, active review filter recomputation after status/shortlist changes, and no mutation of candidate facts or `workspaceCandidates`.

## Agent Explanation Boundary

Candidate-level explanations belong to `P8-005`.

`P8-005` must implement deterministic candidate-level explanations first. It must not call OpenAI/LLM, change backend/API/search/runtime behavior, change Candidate Quality, alter sorting/filtering/ranking, execute Tavily, persist data, or automate LinkedIn. The purpose is to explain already returned workspace facts, not to create a second scoring system.

Each explanation should be a structured object before rendering, with fields such as:

- `version = candidate_explanation_v1`;
- `summary`;
- `positive_signals`;
- `cautions`;
- `evidence_items`;
- `source = deterministic_workspace_facts`.

`positive_signals`, `cautions`, and `evidence_items` should be arrays of reason objects with stable local `code` values, display `label` strings, and optional bounded `facts` objects, not raw strings. This keeps future `P8-006` bounded: an LLM may later rewrite labels after validation, but must not invent, remove, reorder for meaning, or change reason codes/facts.

The explanation should be concise and deterministic. Initial display limits should prefer up to 3 positive signals, up to 3 cautions, and up to 4 evidence/provenance items, chosen by fixed priority order.

Initial reason code allowlist:

- `quality_score_high`;
- `quality_score_medium`;
- `quality_score_missing`;
- `target_location`;
- `location_unknown_or_weak`;
- `location_foreign_or_mismatch`;
- `stack_confirmed`;
- `stack_query_source_only`;
- `stack_not_visible`;
- `role_or_technology_visible`;
- `seniority_unknown`;
- `stable_profile_identity`;
- `profile_href_missing_or_unsafe`;
- `review_flags_present`;
- `query_source`;
- `quality_component`;
- `quality_penalty`.

Explanations must be grounded only in returned approved-search workspace candidate facts:

- candidate identity/headline/title;
- quality score, quality bucket as display convenience, score breakdown, and penalties;
- role display/fit/evidence;
- technology display/fit/evidence;
- stack display/fit/evidence and direct selected stack terms;
- missing selected stack terms;
- seniority level/display/fit/evidence;
- review flags and review flag details;
- query/wave sources as discovery provenance;
- location status/group/signals, location terms, current-location line(s), and location classifications;
- public Tavily snippet/content already returned by the approved pipeline;
- safe LinkedIn profile href validation state.

Claim rules:

- confirmed stack may be described only when direct returned stack evidence exists;
- `stack_confirmed` may be emitted only from direct candidate evidence. It must not be emitted from `stack_evidence` entries where `source = query_source` or `evidence_type = stack_query_group`;
- query-source-only stack is discovery provenance, not confirmed candidate skill evidence;
- missing selected stack means not visible in returned public data, not proof the candidate lacks the stack;
- target location may be described only when candidate-level location status/group supports it;
- weak or unknown location must be described as requiring manual review;
- foreign or mismatched current location must use `location_foreign_or_mismatch` as a caution when `candidate.location_group == "foreign"` or the location status is explicitly `foreign_current_location` / `excluded_foreign_current_location`. Do not collapse it into `location_unknown_or_weak`;
- seniority must not be claimed when missing or unknown;
- review flags are cautions, not final rejection;
- snippets/headlines are incomplete returned public text and must preserve uncertainty.
- reason `code` values must come from local deterministic helper constants or allowlists, not raw candidate text;
- summary wording should be derived from selected reason objects and their priorities, not from an independent logic path that can contradict cautions;
- `quality_bucket` must not become a new source of truth or introduce new scoring thresholds;
- helper logic must not hardcode `Java`, `Ukraine`, `Backend Developer`, or other current-flow-specific values. Role, technology, stack, location, and seniority wording must come from returned facts, query/source metadata, or safe generic labels.

Quality reason codes must follow the existing workspace `qualityBucket(score)` semantics: `quality_score_high` for high (`score >= 70`), `quality_score_medium` for medium (`score >= 40` and `< 70`), and `quality_score_missing` only when `has_quality_score == false`. Low quality (`score < 40`) should not become a caution by itself unless an existing returned review flag, score penalty, or other allowed fact supports a caution.

Structured evidence does not automatically mean positive signal. Returned role/technology evidence may produce `role_or_technology_visible` only when returned fit/evidence is not missing, ambiguous, or related-only. Stack positive signal must be emitted only through `stack_confirmed` from direct candidate evidence. Seniority evidence may be shown as evidence/provenance, but must not become a positive signal unless a later reviewed task adds a dedicated allowlisted seniority reason code.

Quality breakdown components may be represented with `quality_component` as evidence/provenance only, not as positive signals. `quality_component` facts should be bounded to fields such as `{ component, points, max_points, fit }`; the UI should not expose or render the full raw breakdown object.

Location explanation should prefer structured/capped fields: `current_location_line`, `current_location_lines`, and `location_signal_terms`. Raw `header_location_text` or long snippets may be used only as escaped, capped fallback context and must not become the primary location proof when structured fields are present.

Recruiter workflow state is not candidate evidence. `review_status`, derived `shortlisted`, and recruiter `notes` may be shown near the explanation, but must not change explanation facts, summary, positive signals, cautions, or evidence items.

The UI label should avoid implying that the app inspected LinkedIn profiles. Prefer labels such as `Candidate explanation` or `Why this candidate`.

`P8-005` should keep candidate explanation labels/copy in English to match the current Candidate Workspace UI. RU/EN localization for candidate explanations requires a later reviewed task.

Bounded LLM wording for candidate explanations is split into two steps:

- `P8-006 Define bounded candidate explanation wording contract`;
- `P8-006.1 Implement explicit selected-candidate wording overlay`.

`P8-006` is contract-first and should be docs-only. It must define the payload, output shape, validation, fallback, routing, provenance, and implementation handoff before any code starts. `P8-006.1` may later implement the overlay after separate review and approval.

The deterministic `P8-005` explanation remains the source of truth. A future LLM overlay may only rewrite display wording:

- explanation `summary`;
- existing reason `label` text.

The future LLM overlay must be stored separately from the deterministic explanation, for example as a current-run `wording_overlay` / `display_overlay`. It must not overwrite or mutate the deterministic `P8-005` explanation object, workspace candidate facts, review state, notes, shortlist state, filters, or exported data.

The future LLM overlay must not:

- add, remove, reorder, or change reason objects;
- change reason `code`;
- change `facts`;
- change `source`;
- change `version`;
- change candidate facts, fit, score, ranking, filters, search execution, review state, notes, shortlist, export, persistence, or inclusion/exclusion;
- introduce new facts;
- claim direct LinkedIn inspection or profile verification;
- create executable next steps.

The future implementation must separate the frontend-to-backend request payload from the backend-to-OpenAI model payload. The frontend-to-backend request payload should contain only bounded deterministic explanation fields: `wording_use_case = candidate_explanation`, `request_payload_contract_version = candidate_explanation_wording_request_v1`, target language, `workspace_run_id`, an opaque current-run `wording_target_key`, `request_explanation_fingerprint` as a request-integrity/UI correlation value, explanation version, locked `source = deterministic_workspace_facts`, deterministic summary, and existing reason keys/codes/labels/wording-safe bounded facts. It must not include raw candidate records, raw Tavily payloads, raw snippets/content, raw query text, profile URLs, LinkedIn URLs, current workspace `candidate_id` when it contains or is derived from `normalized_url` / profile URL, any URL-derived profile-identifying string, recruiter notes, review status, shortlisted state, browser storage state, frontend-supplied prompt rules, hard boundaries, trusted `allowed_numbers`, frontend-supplied OpenAI/provider execution controls, or account/action instructions.

`P8-005` currently builds deterministic candidate explanations in frontend workspace state. A future `P8-006.1` backend-owned OpenAI call must not receive raw candidates or raw search results. The frontend may send only the bounded deterministic explanation wording request payload. The backend must validate the submitted request payload contract version, shape, source, explanation version, reason-code allowlist, stable reason keys, `workspace_run_id`, opaque `wording_target_key`, forbidden fields, and `request_explanation_fingerprint` before attempting wording. The backend must reject payloads that include raw candidate/search fields, URLs/profile links, URL-derived candidate ids, recruiter notes, review state, frontend-supplied prompt rules/hard boundaries/allowed numbers, frontend-supplied model/provider execution controls such as `model`, `temperature`, `max_tokens`, `max_completion_tokens`, prompts, tool names, provider config, or API key references, unknown reason codes, duplicate reason keys, bad source, bad version, missing/unknown request contract version, or request-level fingerprint mismatch.

`P8-006.1` must not blindly forward all deterministic `P8-005` facts. It should add a wording-safe facts mapper by reason code. The mapper may include only explicitly allowlisted recruiter-visible scalar or shallow bounded values that are safe for wording, such as score/bucket, stack terms, fit/status enums, coarse location status/group, query-source ids, and bounded reason-code-specific values. It must exclude raw candidate text fields such as headline/raw title/current location line unless a later reviewed task explicitly approves a normalized safe variant, and it must always exclude snippets/content, profile URLs, URL-derived identifiers, raw query text, recruiter notes, review state, arbitrary nested objects, unknown fact keys, and unbounded arrays/strings.

`P8-006.1` should treat the current `EXPLANATION_REASON_CODES` set as an explicit wording-semantics snapshot. The mapper, prompt, validator, and smoke tests should use the same snapshot:

| Reason code | Allowed wording meaning | Forbidden wording meaning | Allowed wording-safe fact keys |
| --- | --- | --- | --- |
| `quality_score_high` | Returned quality score is high under existing workspace `qualityBucket` semantics. | Best candidate, guaranteed fit, independent ranking, changed score, or LinkedIn/profile verification. | `score`, `bucket` |
| `quality_score_medium` | Returned quality score is medium under existing workspace `qualityBucket` semantics. | High/low quality claim, guaranteed fit, independent ranking, or changed score. | `score`, `bucket` |
| `quality_score_missing` | No usable quality score is present in the returned workspace facts. | Poor quality, weak candidate, or failed screening claim. | none |
| `target_location` | Returned location classification contains a target-location signal. | Verified current residence, work authorization, relocation, availability, or direct profile inspection. | `status`, `group`, `terms` |
| `location_unknown_or_weak` | Location evidence is missing, weak, or needs recruiter review. | Target-location confirmation, foreign-location confirmation, or verified current location. | `status`, `group`, `terms` |
| `location_foreign_or_mismatch` | Returned current-location classification appears outside or mismatched with target location. | Permanent exclusion, legal/work authorization claim, direct profile verification, or target-location confirmation. | `status`, `group`, `terms` |
| `stack_confirmed` | Selected stack terms are visible in returned direct candidate evidence. | Seniority/expertise depth, all selected stack confirmed, or experience duration. | `terms`, `source` |
| `stack_query_source_only` | Stack signal came only from query/source context and is not confirmed in returned candidate text. | Confirmed stack, direct candidate evidence, or strong stack fit. | none |
| `stack_not_visible` | Selected stack is not visible in returned public candidate data. | Candidate lacks the skill, failed screening, or technology mismatch beyond returned data. | `missing_terms` |
| `role_or_technology_visible` | Returned structured role or technology fit is visible and not missing/ambiguous/related-only. | Confirmed job readiness, current employment truth, full role match, or direct profile inspection. | `role_fit`, `technology`, `technology_fit`; explicitly not `role` |
| `seniority_unknown` | Seniority is unknown or not visible in returned data. | Junior/senior classification, experience duration, or seniority downgrade. | none |
| `stable_profile_identity` | A safe/stable LinkedIn profile identity was derived for manual recruiter click-through. | Identity verification, account ownership, direct LinkedIn access, or profile inspection. | `profile_href_present` |
| `profile_href_missing_or_unsafe` | Safe profile link is missing or failed validation. | Candidate invalid/fake, no LinkedIn profile exists, or profile is inaccessible. | none |
| `review_flags_present` | Returned review flags need recruiter attention. | Automatic rejection, risk conclusion beyond flags, or new review reason. | `codes` |
| `query_source` | Candidate was found through returned query source identifiers/categories. | Candidate quality, stack confirmation, or profile fact proof. | `ids`, `categories` |
| `quality_component` | Quality breakdown components are available as scoring provenance. | New score computation, candidate ranking change, or standalone positive signal. | top-level `components` array; nested `component`, `points`, `max_points`, `fit` |
| `quality_penalty` | Quality penalties are present in returned scoring provenance. | Automatic rejection, negative character judgment, or non-returned risk claim. | top-level `penalties` array; nested `points`, `reason` |

The wording-safe facts mapper should reject any fact key outside the allowed list for that reason code. If a needed fact is not in this table, the implementation should omit it or create a reviewed contract update before using it.

For nested facts, the top-level container must also be explicitly allowed. For example, `quality_component` may carry only a `components` array whose items contain allowed nested keys, and `quality_penalty` may carry only a `penalties` array whose items contain allowed nested keys. Unknown nested keys, unknown item shapes, and arbitrary nested objects must be omitted or rejected before fingerprinting and before building the backend-to-OpenAI model payload.

The `role` fact currently present in deterministic `P8-005` `role_or_technology_visible` facts must be stripped by the wording-safe mapper. It can come from headline/raw-title fallback and is therefore too close to raw candidate text for the first wording payload. Future wording may use normalized role text only through a later reviewed safe variant.

Allowed wording-safe string values should be controlled or normalized values, not arbitrary candidate/search text. Examples: known review flag codes, known quality component names, known quality penalty reasons, query source ids/categories, selected stack/location terms already shown to the recruiter, and fit/status enum values. Unknown strings, arbitrary labels, raw headline/title/location/snippet text, raw query text, and unexpected object-derived strings should be omitted or rejected.

Hard boundaries are backend-owned prompt/policy text, not request data. `allowed_numbers` must be derived by the backend before prompting and output validation, but only from user-visible wording fields: deterministic summary, current reason labels, and wording-safe allowlisted bounded facts that can be shown to the recruiter. `allowed_numbers` must not be derived from `reason_key`, `section`, `code`, request/model/prompt/validator versions, fingerprints, cache keys, provenance, workspace/run ids, or other technical metadata. OpenAI/model routing and execution parameters are backend-owned; frontend must not provide model name, temperature, max tokens, max completion tokens, prompts, tool names, provider config, or API key references. Candidate explanation wording v1 supports only `en`; unsupported languages must no-call before OpenAI and return deterministic fallback/no-call metadata with nested `wording_provenance.no_call_reason = unsupported_language`. The backend must also recompute the request-level explanation fingerprint from sanitized request-bounded fields and compare it to the submitted `request_explanation_fingerprint` before using it for request validation. The request-level explanation fingerprint should cover only the bounded frontend-to-backend request content used for wording request validation: wording use case, target language, `request_payload_contract_version`, deterministic explanation version/source, summary, final renderable reason arrays, `reason_key`, `section`, `code`, `label`, and wording-safe bounded `facts`. It must not include backend-only model/prompt/validator versions, URLs, URL-derived ids, `candidate_id`, review state, notes, shortlist state, sorting/filter state, runtime state, browser storage state, cache keys, or provenance fields.

Prompt/data separation is a hard backend boundary. All submitted `summary`, current reason `label` values, wording-safe `facts`, selected stack/location terms, query-source ids/categories, and any other candidate/user-derived values are data, not instructions. The backend-to-OpenAI model payload must serialize or delimit these values as data and must include backend-owned instructions telling the model not to follow, execute, or treat as policy any instruction-like text contained inside data fields. If bounded data contains text such as "ignore previous instructions", "change the score", "verify this profile", or similar prompt-injection content, the model must still only rewrite `summary` and existing reason `label` text within the approved schema and semantic guardrails. Future smoke coverage should include instruction-like strings inside allowed data fields and verify they do not alter policy, output shape, reason keys, reason codes, facts, scores, provenance, or execution behavior.

The backend wording cache key is a separate backend-owned key. If current-run cache is implemented, the backend cache key may include the recomputed request-level explanation fingerprint plus backend-owned version fields such as `model_payload_contract_version`, `prompt_contract_version`, `prompt_version`, `validator_version`, `deterministic_builder_version`, `reason_semantics_version`, and `canonicalizer_version`. The frontend must not be required to know or submit backend-only model/prompt/validator version fields.

Canonical fingerprinting should use deterministic JSON canonicalization with a concrete hash format. The canonicalized value should be UTF-8 JSON with sorted object keys, reason arrays kept in final render order, strings normalized to the same trimmed/plain-text form used for the model payload, finite numbers consistently serialized, and missing optional values represented consistently so `undefined`, omitted fields, and `null` cannot produce accidental mismatches. The fingerprint should be emitted as `sha256:<hex>`. `P8-006.1` should include JS/Python fixture coverage so frontend request construction and backend recomputation produce the same fingerprint for the same wording-safe bounded payload. The fingerprint must change when any source wording field changes: summary, reason order, reason key, section, code, label, or wording-safe bounded facts.

Wording-safe `facts` must be shallow, allowlisted, controlled, and bounded before they enter either the request-level explanation fingerprint or backend-to-OpenAI payload. Allowed values are strings, finite numbers, booleans, arrays of strings, arrays of finite numbers, or explicitly allowed shallow objects. Wording-safe `facts` must not contain raw snippets/content, URLs, profile identifiers, arbitrary nested objects, executable/action text, or unbounded arrays/strings. Each reason code in the future code-semantics guardrail map should define allowed fact keys, controlled string sources, and basic value limits; unknown fact keys should be rejected unless explicitly allowed by that reason code.

This validation is contract/integrity validation, not candidate-fact verification. In `P8-006.1`, candidate fact truth remains the deterministic frontend workspace explanation from `P8-005`. The backend owns the wording call, payload validation, output validation, fallback, and provenance, but it does not independently reconstruct candidate facts from `candidate_id`, prove that the payload matches the latest search result, or prove that `workspace_run_id` is the latest successful workspace run. In this slice, `workspace_run_id` validation is contract/format/consistency validation only. The request-level explanation fingerprint protects request integrity and UI stale-correlation only; it is not backend stale/latest-run proof. The frontend pending key only prevents duplicate in-flight submissions before backend response, and the backend cache key protects validated overlay reuse/cache behavior. Neither proves candidate truth. Backend-owned candidate facts would require a later reviewed task, such as moving/rebuilding the candidate explanation producer on the backend or adding workspace-run persistence.

The current workspace `candidate_id` must not be blindly reused in the future wording payload because the current implementation may use `normalized_url` as `candidate_id`. `P8-006.1` should introduce a separate opaque `wording_target_key` for request/response correlation. This key is current-run scoped and must not be a LinkedIn URL, profile href, normalized URL, email, external id, stable cross-run candidate identity, or URL-derived profile-identifying string. It must be stable for the same candidate within one workspace run across re-render, sort, filter, details open/close, and repeated wording clicks, but it must reset on new search, workspace clear, page reload, or stale workspace reset. It should be generated once when the workspace candidate view-model is created, kept in memory only, and not derived from URL/profile fields or persisted in browser storage.

After backend request validation passes, the backend may construct a separate backend-to-OpenAI model payload. The model payload should contain only wording-use-case, `model_payload_contract_version = candidate_explanation_wording_model_v1`, target language, deterministic explanation version/source, deterministic summary, final renderable reason arrays with `reason_key`/`section`/`code`/current `label`/wording-safe bounded `facts`, backend-owned prompt boundaries, and backend-derived `allowed_numbers` from user-visible wording fields only. Before calling OpenAI, the backend must build and validate its own model payload with a known model payload contract version; missing or unknown model payload contract version is an internal backend model-payload-build failure and must stop before OpenAI. The frontend request must not provide or control the model payload contract version. The backend-to-OpenAI model payload must keep policy/instructions structurally separate from data: backend-owned prompt boundaries and schema instructions are the only instructions, while candidate/user-derived values from the bounded request must be placed in data fields or clearly delimited data sections and must never be concatenated into instruction text in a way that lets those values redefine task, policy, schema, allowed numbers, provenance, or execution boundaries. The model payload must not contain `workspace_run_id`, `wording_target_key`, submitted or recomputed request-level explanation fingerprint, backend cache keys, `candidate_id`, `normalized_url`, profile hrefs, profile URLs, LinkedIn URLs, URL-derived identifiers, recruiter notes, review status, shortlist state, sorting/filter state, runtime/tool-call identifiers, browser storage state, provenance/fallback/no-call metadata, or frontend-supplied model/provider execution controls. These fields are useful for backend validation, correlation, duplicate-call protection, and cache behavior, but they are not useful for wording and should not be sent to OpenAI.

The implementation must generate stable `reason_key` values before sending the payload, such as `positive_signals[0]:quality_score_high`, `cautions[1]:stack_not_visible`, or `evidence_items[0]:query_source`. Reason keys must be generated only after the deterministic explanation has been fully built, capped, and ordered for rendering, so they represent the final renderable explanation rather than intermediate evidence. The LLM must return the same renderable `reason_key` set. Reason keys are bounded-payload contract keys for validation and mapping; they are not candidate facts and do not imply backend ownership of candidate fact truth.

The future LLM output must be strict JSON and must validate before use. `P8-006.1` should prefer provider-supported structured output / JSON schema when available, because the allowed output shape is small and fixed. Local backend validation remains mandatory even when structured output is used; schema output reduces malformed responses but does not replace reason-key/code/number/semantic validation. The first implementation should allow only `summary` and `reasons` output. Validation must require exactly the top-level keys `summary` and `reasons`; every output reason object must contain exactly `reason_key`, `code`, and `label`; output reason keys must exactly match existing input reason keys intended for rendering; output reason count must equal input renderable reason count; output reason codes must match the input code for each reason key; no `facts` are returned or changed; output does not return or change `source` or `version`; output numbers are a subset of backend-derived allowed numbers; v1 `en` output should be English-oriented plain text and reject obvious unsupported-language/script mismatch, but validation should not fail just because bounded wording contains technology tokens, product names, locations, query ids, or common abbreviations such as `Java`, `AWS`, `Kafka`, `Kyiv`, `Q01`, `C#`, or `.NET`; `summary` is non-empty plain text capped at 320 characters; every reason `label` is non-empty plain text capped at 160 characters; no HTML, Markdown links, bullet/list-as-structure formatting, control characters, model-returned `warnings`, or unsafe/prohibited content is present. Invalid output must fall back to deterministic `P8-005` wording.

The current Phase 7 wording validator cannot be reused directly for candidate explanations because it validates `message` / `warnings` / `limitations`. `P8-006.1` should add a candidate-explanation-specific validator or a strictly separated `candidate_explanation` branch with the `summary` / `reasons` output shape.

Validation must also preserve code-specific semantics. For example, `stack_query_source_only` must still mean not confirmed, `stack_not_visible` must still mean not visible in returned public data, `location_unknown_or_weak` must still require manual review, and `location_foreign_or_mismatch` must remain a caution. Backend-owned `llm_warnings` may exist as internal/debug/provenance metadata, but model-returned `warnings` should be rejected in the first implementation and must not become rendered candidate facts.

`P8-006.1` should define a code-semantics guardrail map for all current `EXPLANATION_REASON_CODES`, not only stack/location examples. Each reason code should have explicit allowed wording meaning and forbidden wording meaning, and smoke coverage should include at least one semantic guardrail or documented allowed/forbidden meaning for every current code.

The future backend response envelope should be backend-owned and should not rely on the LLM to provide provenance. Expected metadata should follow the established Phase 7 pattern where applicable: `wording_mode`, `fallback_reason` when fallback happened after attempted call or validation failure, nested `wording_provenance`, `surface = candidate_workspace`, `source_owner = candidate_workspace`, `source_object = candidate_explanation`, `wording_use_case = candidate_explanation`, `request_payload_contract_version`, `model_payload_contract_version`, `reason_semantics_version`, `canonicalizer_version`, `prompt_contract_version`, `prompt_version`, `validator_version`, `deterministic_builder_version`, internal `llm_warnings` if present, and `model` only when an OpenAI call was actually attempted and the configured model is known. Avoid ambiguous generic `payload_contract_version` metadata for this endpoint; request/model payload versions should be explicit. `no_call_reason` should live only inside nested `wording_provenance` when OpenAI was intentionally not called, not as a new top-level response field. `fallback_reason` may be top-level only if the new endpoint intentionally mirrors the existing Phase 7 compatibility pattern; it should also be copied into nested `wording_provenance` for fallback cases. The LLM output itself must not set provenance, source, model, fallback, no-call, warning, validation metadata, or `llm_warnings`.

Do not auto-call OpenAI for every candidate in a result set. The implementation handoff for `P8-006.1` should use a conservative route: no call by default, backend-owned OpenAI call only, explicit user action only, current-run browser-memory cache at most, and stale workspace/search reset clearing overlay state. Opening candidate details or selecting a candidate must not call OpenAI by itself.

The future UI control should use neutral wording-polish language such as `Improve wording` or `Polish explanation`. It must avoid labels like `Verify with AI`, `Check profile`, or anything that implies LinkedIn inspection, candidate verification, or new fact discovery.

Pending request state should prevent duplicate calls for the same candidate/explanation/language while a request is in flight. After a validated overlay exists, repeated clicks for the same backend wording cache key should reuse that current-run overlay when available instead of creating duplicate calls. Timeout, network failure, missing OpenAI configuration, unsupported language, invalid output, or validation failure should fall back to the deterministic `P8-005` explanation.

Frontend pending state and backend cache state must be separate. The frontend may use `frontend_pending_key = workspace_run_id + wording_target_key + request_explanation_fingerprint + language` only to prevent duplicate in-flight submissions before the backend responds. The frontend pending key must not be treated as a validated backend cache identity. After the backend responds, validated overlay reuse should be keyed by the backend-owned `backend_wording_cache_key`, which may include backend-only version fields that the frontend did not submit.

Frontend response binding must be explicit. When a wording response arrives, the frontend must apply the overlay only if the current workspace still matches the response target: same `workspace_run_id`, same `wording_target_key`, same `request_explanation_fingerprint`, same language, and no intervening new search, workspace clear, page reload, stale workspace reset, or candidate identity reset. If any binding check fails, the response must be discarded and the deterministic `P8-005` explanation remains visible. Sorting, filtering, and opening/closing details should not break the binding as long as the same current-run candidate view-model and target key remain valid.

If `P8-006.1` adds current-run cache, its backend cache key should include `workspace_run_id`, opaque `wording_target_key`, recomputed request-level explanation fingerprint, `request_payload_contract_version`, `model_payload_contract_version`, `prompt_contract_version`, `prompt_version`, `validator_version`, `deterministic_builder_version`, `reason_semantics_version`, `canonicalizer_version`, deterministic explanation version, and language. The cache must clear on new search, reset, stale workspace state, search failure, or page reload, and must not use browser storage or backend persistence.

The wording request payload, model payload, and model response must not be written to persistent logs, snapshots, search-run logs, browser storage, backend persistence, or database storage. Current-run memory cache and redacted operational metadata/counters are acceptable; raw wording payloads and model responses should stay ephemeral.

Backend error responses and frontend status/error UI must not expose raw wording request payloads, backend-to-OpenAI model payloads, or raw model responses. Error/status surfaces should use bounded status, fallback, and provenance codes only, with a safe short user-facing message that keeps the deterministic explanation visible.

The agent must not invent candidate facts, infer private data, open profiles, scrape LinkedIn, message candidates, or claim verified truth beyond the returned public-search evidence.

Implementation verification for `P8-005` should split helper and render safety checks: helper smoke should verify plain structured data, reason code allowlist behavior, and no mutation; browser/frontend render sanity should include malicious candidate text in headline/snippet/review flag/query source labels to confirm labels render as escaped text and never as raw HTML.

## Export Boundary

Export belongs to `P8-007`.

Review status: `P8-007` is partially implemented. `P8-007A` completed the DOM-free export model, CSV/Markdown serializers, filename/MIME helpers, and no-network helper smoke coverage. `P8-007B` remains not implemented and still requires separate explicit approval before adding export UI, Blob/object URL download glue, CSS, or browser sanity.

`P8-007` should prepare a local, explicit, browser-triggered export workflow for the current Candidate Workspace. Export is a user action that creates a local file from current frontend state; it is not persistence, sync, CRM integration, outreach, or an account action.

Default export format should be CSV, because the primary consumer is Excel on Windows. Markdown must remain available as an explicit selectable format in the first export version.

Export should use only allowlisted workspace data available in the current session:

- candidate display identity and stable identity flag, but not `candidate_id`;
- safe validated profile URL / profile href;
- score/fit fields;
- recruiter-facing role, technology, location, seniority, and source display fields where available;
- review flags;
- shortlist/status;
- recruiter notes;
- evidence snippets;
- deterministic candidate explanation summary and reason codes when already available;
- query source ids/categories and run metadata if useful.

Exported `profile_url` must be derived only from `candidate.profile_href` after applying the same safe LinkedIn profile href validation used by the workspace helpers at export-model build time. Do not use `candidate.profile_url` as an export URL source, because it may contain unsafe display fallback text. If `candidate.profile_href` is empty or fails export-time validation, export `profile_url` as an empty string. Export-time revalidation must not silently change existing Candidate Workspace profile-link rendering or validation behavior; use an export-specific wrapper/helper if stricter export behavior is needed.

When `profile_url` is emitted, it must be canonicalized for the exported file: force `https`, keep only a validated LinkedIn host and a path that starts with `/in/`, and strip query string, hash, and tracking parameters. A valid `http://...linkedin.../in/...` value may normalize to `https://...`; unsafe hosts, non-profile paths, username/password credentials, or malformed values must export as an empty `profile_url`. Do not silently strip credentials and keep the URL, because credential-bearing URLs are not trusted export profile links.

Export-specific profile URL canonicalization should be stricter than the current workspace link-rendering helper. After URL parsing, require `linkedin.com` or a `.linkedin.com` host, no username/password credentials, path segment `in`, and a non-empty profile slug segment after `/in/`. The `/in` path segment may be matched case-insensitively, but the exported canonical path must use lowercase `/in/{slug}`. The exported canonical URL should use `https`, a lowercase host, and only the profile root path `/in/{slug}`; strip query, hash, trailing slash, and any extra path segments such as `/details/...`. Preserve the profile slug as parsed by `URL` path segmentation: do not manually decode it, do not lowercase it, and reject empty slug, `.` / `..`, or values with encoded slash/backslash ambiguity such as `%2F` or `%5C`. If the URL cannot be reduced to that canonical profile root, export an empty `profile_url`.

Required canonicalization examples for helper tests:

- `https://www.linkedin.com/in/foo/details/experience` -> `https://www.linkedin.com/in/foo`;
- `https://linkedin.com/in/foo?trk=x#about` -> `https://linkedin.com/in/foo`;
- `http://ua.linkedin.com/in/foo/` -> `https://ua.linkedin.com/in/foo`;
- `https://linkedin.com/in/` -> empty `profile_url`;
- `https://linkedin.com.evil/in/foo` -> empty `profile_url`;
- `https://user:pass@linkedin.com/in/foo` -> empty `profile_url`;
- `javascript:alert(1)` -> empty `profile_url`.

Export candidate rows should be normalized after scope selection. `display_index` is a 1-based row number within the selected export order, not the candidate's original `display_index` when the current scope is sorted or filtered. `identity_stable` and `shortlisted` should serialize as `yes` / `no`. `quality_score` should serialize as an empty string when `candidate.has_quality_score` is false, and `quality_bucket` should also be empty in that case instead of exporting a misleading derived low bucket.

Current workspace `candidate_id` may be used only inside export helpers as an internal review-state lookup key. It must not be included in export model candidate rows and must not be serialized in CSV or Markdown v1, because current workspace candidate ids may contain or derive from normalized profile URLs or fallback identity values.

`identity_stable` must be exported as `yes` only when the candidate has an explicit stable identity signal and the export-time profile href validation succeeds. It must be `no` for display-only URLs, fallback candidate ids, `candidate.profile_url`-only values, unsafe or missing profile hrefs, or any value derived only from unvalidated URL text.

When `quality_score` is present, serialize it as an invariant base-10 numeric string without locale formatting, thousands separators, percent signs, or display words. When `candidate.has_quality_score` is false, serialize both `quality_score` and `quality_bucket` as empty strings. When a finite score is present, derive `quality_bucket` from that numeric score using the current approved workspace `qualityBucket` semantics; do not trust `candidate.quality_bucket` as a source of truth.

Scope ordering must be deterministic inside `buildWorkspaceExportModel`: `visible` preserves the order of the passed `visibleCandidates`; `all` uses the full `allCandidates` set sorted by `candidate.order_index` with stable input-order fallback; `shortlisted` filters from `allCandidates` by derived review status and then uses the same original-order sort. Non-finite, missing, or malformed `order_index` falls back to the candidate's input index in the `allCandidates` array, and duplicate `order_index` ties are broken by that same input index. This keeps `all` and `shortlisted` tied to approved-result order even if the caller passes malformed, duplicate, mutated, or previously sorted data.

If `reviewStateByCandidateId[candidate_id]` is missing for an exported candidate, the export helper must use the same deterministic fallback as the workspace UI: `review_status = new`, `shortlisted = no`, and `notes = ""`. If `candidate_id` itself is missing, non-string, or empty after normalization, do not attempt review-state lookup; use the same fallback values.

Exported `review_status` should use the normalized v0 enum value in both CSV and Markdown: `new`, `reviewing`, `shortlisted`, or `not_a_fit`. UI display labels are render-only and should not become the export serialization contract.

Display-field fallback order should be deterministic:

- `candidate_name`: `candidate.display_name`;
- `headline`: `candidate.headline`, then `candidate.raw_title`;
- `role`: `candidate.raw.result.role_display`;
- `role_fit`: `candidate.raw.result.role_fit`;
- `technology`: `candidate.raw.result.technology_display`;
- `technology_fit`: `candidate.raw.result.technology_fit`;
- `seniority`: `candidate.seniority_level`, then `candidate.raw.result.seniority_display`, then `candidate.raw.result.seniority_level`;
- `location`: `candidate.raw.current_location_line`, then `candidate.raw.result.current_location_line`, then the first useful value from `candidate.raw.current_location_lines`, then the first useful value from `candidate.raw.result.current_location_lines`;
- `location_status`: `candidate.location_status`;
- `source`: `candidate.source`;
- `stack_fit`: `candidate.stack_fit`.

Export scopes must be explicit:

- `visible`: export the current filtered/sorted workspace view recomputed from `workspaceCandidates`, `workspaceViewState`, and `workspaceReviewStateByCandidateId` at export-click time;
- `shortlisted`: export all candidates from `workspaceCandidates` whose browser in-memory review state derives to shortlisted, ignoring current view filters and preserving original approved-result order;
- `all`: export the full current `workspaceCandidates` set in the original approved-result order.

The default export scope should be `visible`, because it matches the recruiter view currently on screen. `shortlisted` and `all` should remain explicit selectable scopes.

Export must read from explicit frontend state, not from parsed rendered DOM. Export must use an allowlist model and must not serialize the raw returned candidate payload, raw Tavily objects, unbounded raw content, or internal helper objects.

The export model may read only allowlisted raw paths needed to construct recruiter-facing fields, such as `candidate.raw.result.role_display`, `candidate.raw.result.role_fit`, `candidate.raw.result.technology_display`, `candidate.raw.result.technology_fit`, `candidate.raw.result.seniority_display`, `candidate.raw.result.seniority_level`, `candidate.raw.result.seniority_fit`, `candidate.raw.current_location_line`, `candidate.raw.current_location_lines`, `candidate.raw.result.current_location_line`, `candidate.raw.result.current_location_lines`, and `candidate.raw.result.review_flag_details`. It must never include raw objects or blindly serialize `candidate.raw`. Location display should prefer structured current-location fields such as `current_location_line` or the first useful `current_location_lines` value; do not export long noisy `header_location_text` as the location display field.

The export must not create email, phone, contact, or outreach fields. To avoid turning returned public snippets into a contact export, obvious email-like and phone-like substrings in returned candidate text fields such as candidate names, headlines, snippets, explanation labels, and query-source labels should be masked as `[contact omitted]` before CSV or Markdown serialization. Do not apply this contact-like masking to recruiter notes in v1: notes are user-authored workflow text exported only by explicit user action, and they still pass through normal text normalization, formula guarding, Markdown neutralization, and length caps.

Contact-like masking must be conservative and deterministic. It should mask obvious email-like strings with an `@` and plausible domain, and obvious phone-like strings only when there is enough digit density plus phone-specific separators, grouping, or leading `+` / parentheses to plausibly be contact data. If a phone-like match is ambiguous, preserve the text rather than masking it. It must not mask common recruiting/technical evidence such as years, scores, query ids, versions, or technology names, including `Java 17`, `Spring 6`, `Node.js 20`, `.NET 6`, `C#`, `2024`, `Q01`, `5+ years`, `10 years`, `+5 quality points`, `C++`, or similar non-contact tokens.

Export text normalization should follow one deterministic pipeline per field type: coerce null/undefined to empty text; normalize control characters and whitespace according to whether the field is single-line or line-preserving; apply contact-like masking only for returned candidate text fields; cap to the v1 field limit; then apply format-specific handling such as CSV formula guarding/quote escaping or Markdown neutralization/autolink breaking; finally serialize. Recruiter notes follow the same pipeline except they skip contact-like masking. URL-like text neutralization should be shared across CSV and Markdown for untrusted fields, with validated `profile_url` / Markdown `Profile` as the only plain-URL exception.

For CSV v1, every dynamic data cell should serialize as a single-line cell. Embedded `\r`, `\n`, or `\r\n` inside candidate text, snippets, explanation text, query-source labels, review-flag labels, and recruiter notes must be normalized to safe spaces before CSV quote escaping. CSV CRLF must be used only as the row separator emitted by the serializer, never as preserved content inside a quoted data cell. Formula-guard detection must still account for values that originally started with tab, carriage return, or newline before line-break normalization.

The primary CSV consumer is Excel on Windows. CSV export should therefore be Excel-friendly: UTF-8 with BOM, CRLF row endings, deterministic delimiter handling, and an explicit, stable column order. For v1, the serialized CSV string must start exactly with `\ufeffsep=,\r\n` followed by a comma-delimited header row so double-click/open behavior is predictable in Excel. If a strict machine-ingestion CSV is needed later, add it as a separate reviewed format instead of weakening the Excel-oriented export.

CSV v1 should be a candidate table only after the `sep=,` directive: no metadata rows, no repeated metadata columns, and no internal fingerprint/debug rows. Export metadata is available in the export model for Markdown summary, filenames, and internal helper assertions, not as CSV table content.

CSV framing must be deterministic for tests and Excel: the serialized string should be `BOM + sep=,` line, one bare header row, then exactly `candidate_count` data rows. Every row must end with CRLF, including the final data row. Dynamic data cells must not contain embedded CR or LF after CSV normalization, so row-count assertions can treat CRLF as serializer-owned row delimiters. If the serializer is called with zero candidates, it should still produce the `sep=,` line and header row with final CRLF; the browser UI still must not download an intentionally empty selected-scope export.

`workspace_run_id` may stay in the internal export model metadata for helper assertions and current-run correlation, but CSV and Markdown v1 must not serialize it. The current `workspace_run_id` can include internal runtime/planner-derived values through the existing run context, so it is not a recruiter-facing export field. If a visible run label is needed later, add a separate sanitized public run label in a reviewed task.

`candidate_count` means the number of rows in the selected export scope after scope selection, not `latestWorkspaceRun.total_candidates` or the full workspace candidate count.

Internal format values are exactly `csv` and `markdown`. UI labels should be `CSV` and `Markdown`. Filename extensions are `.csv` for `csv` and `.md` for `markdown`.

CSV header names should be emitted as stable bare column names. Every data cell must be CSV-quoted after text normalization, formula guarding, and quote escaping, even when the cell does not strictly require quotes. This keeps Excel behavior and smoke assertions deterministic.

CSV column order should be stable and recruiter-oriented:

- `display_index`;
- `candidate_name`;
- `headline`;
- `profile_url`;
- `identity_stable`;
- `quality_score`;
- `quality_bucket`;
- `role`;
- `role_fit`;
- `technology`;
- `technology_fit`;
- `seniority`;
- `location`;
- `location_status`;
- `source`;
- `stack_fit`;
- `selected_stack_terms`;
- `missing_stack_terms`;
- `review_flags`;
- `review_status`;
- `shortlisted`;
- `notes`;
- `explanation_summary`;
- `explanation_codes`;
- `query_source_ids`;
- `snippet`.

Array-valued export fields should serialize deterministically with `; ` as the join separator. Preserve meaningful deterministic source order when present, especially for explanation codes and query source ids; only sort arrays whose source order is not meaningful.

Array-valued export fields must normalize each item independently through allowlisted scalar extraction before joining. Only non-empty normalized strings or explicitly allowed finite numbers may enter joined export text. Known object-array fields such as review flags, query sources, and explanation reasons may be read only through their field-specific scalar extractors, for example `code`, `label`, `id`, or `category`. Unknown objects, nested arrays, `null`/`undefined`, unknown shapes, and unsupported values must be skipped, not stringified. Export must never emit `[object Object]`, JSON blobs, raw nested structures, or raw array/object debug text in CSV or Markdown.

`review_flags` should serialize as `code: label` joined by `; ` in the normalized review flag order. If a label is missing, serialize the code only. `explanation_codes` should serialize reason codes in deterministic rendered explanation order: positive signals first, then cautions, then evidence items.

`query_source_ids` should serialize `source.id`, falling back to `source.category` only when `id` is missing. If neither `id` nor `category` exists, skip that source. De-duplicate query source ids while preserving first occurrence order. Do not export raw query text, placeholder `unknown`, or raw source objects in CSV or Markdown v1.

If `candidateWorkspace.buildCandidateExplanation` is available and returns `source = deterministic_workspace_facts`, export must include `explanation_summary` and `explanation_codes`. The explanation version may be checked internally to reject incompatible helper output, but CSV and Markdown v1 must not serialize `explanation_version`. If the helper is unavailable or returns an invalid object/source/version, export those fields as empty strings.

V1 text caps:

- `candidate_name`: 160 characters;
- `headline`: 240 characters;
- compact display/fit/status/source fields: 160 characters each;
- joined array fields such as `selected_stack_terms`, `missing_stack_terms`, `review_flags`, `explanation_codes`, and `query_source_ids`: 600 characters each;
- `notes`: existing `NOTE_MAX_LENGTH`;
- `explanation_summary`: 400 characters;
- `snippet`: 600 characters.

CSV export must defend against formula injection and malformed cells. Candidate text, recruiter notes, snippets, query labels, and all other dynamic fields are untrusted; cells must be escaped, normalized, capped, and protected from formula execution before serialization. Formula protection must use a deterministic algorithm: coerce null/undefined to empty text; normalize embedded line breaks to spaces, normalize control characters, and cap text while preserving enough leading content to detect formula risk; if the original or normalized value starts with tab, carriage return, or newline, or if the first non-whitespace character of the normalized value is one of `=`, `+`, `-`, or `@`, prefix the cell value with a single apostrophe (`'`) before CSV quote escaping. CSV v1 must not preserve embedded CR/LF inside quoted cells.

CSV must also neutralize URL-like text in every dynamic field except the validated `profile_url` column, because Excel may turn plain URL-like text into clickable links. This applies to candidate names, headlines, snippets, recruiter notes, explanation text/codes/labels, review flag labels, query-source ids/categories/labels, and any other untrusted CSV text. Use the same deterministic URL-like breaking behavior as Markdown where possible, for example `https://` -> `https: //`, `http://` -> `http: //`, `www.` -> `www .`, and bare `linkedin.com/in/...` / `*.linkedin.com/in/...` text must not remain clickable-looking outside the validated `profile_url` column.

Markdown export is required in the first export version. Its format should be deterministic and simple: run summary first, then one candidate section per exported candidate in the chosen scope/order. Candidate text and notes must be Markdown-escaped or otherwise neutralized. The Markdown serializer must not emit raw HTML from candidate data, notes, snippets, query text, or explanation labels. Candidate-provided text must serialize as neutralized plain text and must not be able to create headings, links, autolinks, HTML blocks, tables, or list structure. Candidate names used in `## N. Candidate Name` headings must be normalized to single-line neutralized plain text. For Markdown v1, all candidate fields, including notes and snippets, should serialize as single-line normalized values; normalize line breaks to spaces before Markdown emission rather than preserving multiline candidate content. Only the validated `Profile` field may contain a plain URL; URL-like text in candidate names, headlines, notes, snippets, explanation text, query labels, and other untrusted fields must be neutralized so Markdown renderers cannot auto-link it.

Markdown neutralization should be implemented as a deterministic helper, not ad hoc field-by-field string replacement. The helper should normalize control characters, normalize line breaks to safe spaces for v1, cap text before emission, escape or neutralize Markdown control characters that can create headings/lists/tables/links/code/HTML, and break URL-like text in untrusted fields so common Markdown renderers do not auto-link it. For example, untrusted `https://...` can be emitted as `https: //...` and untrusted `www.` can be emitted as `www .`; the validated `Profile` field is the only exception.

Serialized Markdown should use LF (`\n`) line endings and end with a final LF. CSV remains the only export format that uses CRLF.

Markdown structure:

```md
# Candidate Workspace Export

Exported at: ...
Scope: visible
Format: markdown
Candidates: 12
Execution mode: single_wave
Queries: 10

## 1. Candidate Name

- Headline: ...
- Profile: ...
- Quality: 86 high
- Role: ...
- Role fit: ...
- Technology: ...
- Technology fit: ...
- Seniority: ...
- Location: ...
- Location status: ...
- Source: ...
- Stack fit: ...
- Review flags: ...
- Review status: ...
- Shortlisted: yes
- Notes: ...
- Explanation: ...
- Explanation codes: ...
- Query sources: ...
- Snippet: ...
```

Allowed internal export model metadata is limited to `workspace_run_id`, `exported_at`, `scope`, `format`, `candidate_count`, `execution_mode`, and `query_count`. CSV and Markdown serializers must not emit `workspace_run_id`, because the current value can include internal runtime/planner-derived identifiers. CSV and Markdown v1 also must not emit `explanation_version`; explanation version may be checked internally only. Runtime/tool-call/query-plan fingerprints should not be included in v1 recruiter-facing CSV or Markdown exports.

Markdown summary metadata must be normalized before serialization. `execution_mode` should be emitted only from a small allowlist such as `single_wave`, `multi_wave`, or `search`; unknown or unsafe values should serialize as `search`. `query_count` should serialize only as a finite non-negative integer, defaulting to `0`. `exported_at` should be the ISO timestamp from the export-click `Date` value used by the export model, not a value copied from `workspaceRun` or rendered DOM.

Unsafe, missing, or unvalidated profile URLs must not remove the candidate from export, but the exported `profile_url` value must be empty. Do not export unsafe profile URLs even as escaped plain text, because Excel and Markdown renderers may still make plain URLs clickable.

The DOM-free export helper boundary should be explicit. `buildWorkspaceExportModel` should accept `{ workspaceRun, allCandidates, visibleCandidates, reviewStateByCandidateId, scope, format, exportedAt }` and return plain data with `metadata` and `candidates`. Plain data means JSON-serializable scalars, arrays, and shallow export row objects only: no `Date` objects, DOM nodes, functions, raw candidate object references, mutable frontend state objects, raw nested candidate payloads, runtime/tool-call objects, or query-plan objects. CSV and Markdown serializers should operate only on that export model. Use separate text helpers such as `normalizeExportText`, `sanitizeCsvCell`, `escapeMarkdownText`, and shared URL-like neutralization because CSV and Markdown have different escaping rules but both must avoid untrusted autolinks. Unknown export scope should normalize to `visible`; unknown export format should normalize to `csv`. Filename and MIME behavior should be helper-owned through functions such as `buildWorkspaceExportFilename(exportedAt, scope, format)` and `workspaceExportMimeType(format)` so no-network helper coverage can assert the download contract without browser side effects.

DOM-free helpers should be tolerant of malformed frontend inputs. `buildWorkspaceExportModel` and serializers should normalize null arrays, missing `workspaceRun`, missing review state, missing candidate fields, and malformed candidate objects to defaults/empty strings where safe instead of throwing. Throwing should be reserved for genuinely unexpected serializer/runtime failures in the browser download path, which the UI catches and reports through bounded inline status.

`P8-007A` implementation status: completed in `app/static/candidate_workspace.js` with helper smoke coverage in `scripts/smoke_p8_candidate_workspace_helpers.js`. The completed slice adds only DOM-free helper/model/serializer behavior and intentionally does not add export controls, `workspaceExportState`, Blob/object URL download dispatch, CSS, backend/API/search/runtime calls, persistence, browser storage, or external-service behavior.

The browser UI glue should maintain a small current-run `workspaceExportState` for selected scope, selected format, and inline status so toolbar rerenders do not silently reset the recruiter's export selections. Store `workspaceExportState.scope` and `workspaceExportState.format` only after normalization through `CandidateWorkspace.normalizeExportScope` and `CandidateWorkspace.normalizeExportFormat`. This state resets on new workspace run and workspace clear only, and must not use browser storage. Stale export inline status should clear when scope/format changes, view filters/sort change, review status changes, shortlist changes, notes change, filters reset, a new workspace run starts, or workspace state is cleared. Clearing stale export status on note input must not rerender the full workspace or replace the active textarea; update only export state/status target so recruiter typing, cursor position, and note focus are preserved. Export controls must live in a compact, visually distinct grouped export block such as `candidate-workspace-export`, not simply appended into the existing filter/sort grid, so the toolbar remains scannable on desktop and mobile. The export feedback target should use `role="status"` and `aria-live="polite"`. Export controls must use export-specific attributes such as `data-workspace-export-control` and `data-workspace-export-action`, not the existing `data-workspace-control` / `data-workspace-action` attributes. Export event delegation should use `event.target.closest("[data-workspace-export-control]")` and `event.target.closest("[data-workspace-export-action]")` rather than reading only `event.target.dataset`, so nested button content or future icons still route correctly. On export click, the visible scope should be recomputed from `workspaceCandidates`, `workspaceViewState`, and `workspaceReviewStateByCandidateId` before building the export model instead of trusting a potentially stale `visibleWorkspaceCandidates` cache. If the selected export scope has zero candidates, do not create a `Blob`, object URL, or temporary anchor click; show a bounded inline status such as `No candidates to export for selected scope.` instead. After a successful export, inline status should be bounded, for example `Exported 12 candidates as CSV`, and must not include file paths, candidate names, profile URLs, or recruiter notes.

Browser file creation is allowed only as an explicit user-clicked local download, for example through a `Blob` and object URL that is revoked after use. Export filenames should be generic and safe, and should not embed candidate names or sensitive recruiter notes.

Export filename pattern should be `engineers-search-candidates-{scope}-{YYYYMMDD-HHmmss}.{csv|md}`. Filename generation must normalize scope and format before building the file name. Timestamp components use local date/time getters from the export-click `Date` object and must be zero-padded to `YYYYMMDD-HHmmss`. Browser download glue should use MIME type `text/csv;charset=utf-8` for CSV and `text/markdown;charset=utf-8` for Markdown.

Export model building, serialization, Blob creation, object URL creation, temporary anchor click, and cleanup should be wrapped in a bounded `try`/`catch`/`finally` path. If export fails, show a bounded inline error such as `Export failed. Try again.`; do not throw into the page, do not use `alert()`, and do not include raw exception details, candidate names, profile URLs, notes, file paths, or payload data in the user-visible status. Temporary anchors and object URLs should be cleaned up even when serialization or download dispatch fails.

`exportedAt` must be created at the moment the recruiter clicks Export, not when the toolbar renders. The click handler should create one `Date` object and pass that same object/value through the export flow. Export model metadata should use `exportedAt.toISOString()`, while filename generation should use local date/time getters from the same `Date` object. Helper tests may pass a fixed `Date` object to avoid timestamp flakiness.

The temporary download anchor should be removed after the click is dispatched, and object URL revocation should be deferred, for example with `setTimeout(..., 0)`, so browser download handling is not interrupted.

Export must not add persistence by itself, must not create accounts, must not upload/share/send data, and must not send messages or perform outreach. Export must not call OpenAI/LLM, Tavily, backend runtime/search endpoints, LinkedIn, or any external service.

Verification should split pure helper checks from app/browser checks. Pure no-network helper smoke should load only `app/static/candidate_workspace.js` through the existing VM pattern and cover export model, CSV, Markdown, filename, MIME, normalization, helper tolerance for malformed inputs, contact-like masking for returned candidate text, contact-like false positives such as `Java 17`, `Spring 6`, `Node.js 20`, `.NET 6`, `C#`, `2024`, `Q01`, `5+ years`, `10 years`, `+5 quality points`, and `C++`, ambiguous phone-like text preservation, exact CSV framing/final CRLF with no embedded CR/LF inside quoted data cells, Markdown LF/final LF, Markdown v1 single-line normalization for all candidate fields, normalized and zero-padded filenames, deterministic order fallback for malformed/duplicate `order_index`, export-time profile href revalidation without changing existing workspace profile-link behavior, canonical HTTPS `profile_url` output with query/hash/tracking stripped, extra path segments reduced to the profile root, username/password credential-bearing URLs rejected, all required profile URL canonicalization examples, slug policy cases for case-insensitive `/in`, preserved slug case, empty slug, `.` / `..`, and encoded slash/backslash ambiguity, CSV URL-like neutralization for every untrusted field outside `profile_url`, conservative `identity_stable` serialization, invariant numeric `quality_score` serialization, derived `quality_bucket` serialization, normalized enum `review_status` serialization, missing or malformed `candidate_id` review-state fallback, malformed array item skipping, known object-array extraction only through field-specific scalar extractors, no `[object Object]`/JSON blob/raw nested structure emission, `candidate_id` exclusion from export rows/CSV/Markdown, `explanation_version` exclusion from CSV/Markdown, plain JSON-serializable export data, and no mutation. App/browser sanity or focused frontend-static checks should cover `workspaceExportState`, stale success/error status clearing without replacing the active notes textarea on note input, grouped export UI layout, accessible live status, export-specific data attributes, delegated export events, click-time visible recomputation, visible CSV, shortlisted Markdown, all scope export, zero-candidate selected export stopping before Blob/object URL/anchor click, bounded success/error statuses, and download glue. Download flow should be verified with a Playwright download event where available, or with controlled monkeypatches for `URL.createObjectURL`, anchor click, and `URL.revokeObjectURL`.

Implementation order should stay narrow and testable: DOM-free model/normalization helpers first, CSV/Markdown serializers second, UI state/rendering third, browser download glue fourth, and browser sanity last. Required execution split: `P8-007A` implements only DOM-free export model, normalization/sanitization helpers, CSV/Markdown serializers, filename/MIME helpers, and no-network helper smoke coverage; this slice is now completed. `P8-007B` should then implement export UI controls, current-run `workspaceExportState`, click-time visible recomputation, local Blob download glue, bounded inline status, cleanup, CSS, and browser/frontend sanity checks only after separate approval. Do not wire the download action before helper serialization tests pass. If implementation pressure adds materially more behavior than these slices describe, split again instead of expanding P8-007 further.

## Security And Display Rules

Candidate data comes from external public-search results, and notes come from recruiter input. The frontend must treat both as untrusted display text.

Rules for `P8-002+`:

- escape all displayed candidate text and notes;
- do not render raw HTML from Tavily, snippets, titles, candidate names, headlines, query strings, or notes;
- escape dynamic HTML attributes such as `title` and `aria-label` when values come from candidate/query/runtime data;
- keep external profile links as user-clicked links only;
- render a clickable profile link only when the URL passes strict browser `URL()`-based validation as a safe LinkedIn profile URL;
- failed profile URL validation must not remove or hide the candidate row; it may only disable/hide the clickable link or show the URL as escaped plain text;
- allow only `http:` or `https:` protocols;
- allow only `linkedin.com` or hostnames ending with `.linkedin.com`;
- reject lookalike hostnames such as `linkedin.com.evil.com`;
- require LinkedIn profile path shape, especially `/in/...`;
- unsafe, empty, unsupported, or unvalidated URLs should be hidden or rendered as escaped plain text, not as clickable links;
- external links should use `target="_blank"` with `rel="noopener noreferrer"`;
- dynamic CSS class names must come from local allowlist/map helpers and must not be built directly from backend/public candidate data;
- frontend workspace mapping must not recalculate quality, fit, role-match, stack-match, location, seniority, or score decisions;
- the candidate table/list should preserve backend `deduped_results` order until a later sorting/filtering task explicitly changes it;
- if `normalized_url` is missing, frontend rendering may use a local render-only fallback id, but it must not treat that fallback as stable candidate identity or persistence identity;
- `source_index` or `display_index` may be used for display/order only and must not become candidate identity;
- do not auto-navigate to candidate URLs;
- do not fetch candidate profile pages from the frontend or backend;
- do not add LinkedIn login, LinkedIn automation, scraping, browser control, or restriction bypass;
- do not infer private contact details from profile URLs or snippets.

## Implementation Handoff

`P8-002 Build recruiter-facing candidate table` should start from the existing frontend `renderResults` path and reshape the current candidate-card results into a read-only workspace table/list foundation.

`P8-002` should not implement interactive sorting/filtering, shortlist, notes, editable statuses, candidate-level AI explanations, export, backend schema/API changes, or persistence. Those belong to later Phase 8 tasks.

`P8-002` should code only the mapper, workspace run state, recruiter-facing table/list, and read-only candidate details. It can leave inert view-model fields or markup structure for later Phase 8 tasks, but interactive sorting/filtering belongs to `P8-003`, shortlist/notes/statuses belong to `P8-004`, candidate-level explanations belong to `P8-005`, bounded LLM wording contract/implementation belongs to `P8-006`/`P8-006.1`, and export belongs to `P8-007`.

`P8-002` should limit layout changes to the results area (`#results-list`), candidate rendering, and related result/candidate CSS. It should not redesign or structurally change recruiter chat, Search Brief, QueryPlan, Report, Agent Actions, approval controls, or the overall workspace shell except for minimal compatibility.

`P8-002` product behavior changes should be frontend-only. No-network regression/check changes in `scripts/` and `scripts/check_all.ps1` are allowed for this task, but backend app/API/search/runtime behavior must not change.

The recruiter-facing table/list should be implemented as a responsive CSS grid/list, not a native HTML `<table>`, because candidate rows contain long profile URLs, snippets, evidence, flags, query sources, and expandable details.

The implementation should not parse the rendered DOM to recover candidate data. The approved search response should be mapped into explicit JavaScript state, and all workspace UI surfaces should render from that state.

Recommended conservative implementation path:

1. Keep backend search response contracts unchanged at first.
2. Put pure workspace helpers in a DOM-free frontend helper file such as `app/static/candidate_workspace.js`, expose them through a namespace such as `window.CandidateWorkspace`, and load it before `app/static/app.js`. The helper file should not touch `document` directly so it can be tested from Node smoke coverage without loading the full UI.
3. Build a frontend mapper from current `deduped_results` to the workspace candidate view model.
4. Store the mapped run in explicit frontend state such as `latestWorkspaceRun` and `workspaceCandidates`.
5. Add a single `clearWorkspaceState()` helper or equivalent and call it from existing stale/reset/error result-clearing paths.
6. Capture runtime approval/context values needed for `workspace_run_id` before `clearRuntimeApproval()` runs.
7. Capture current runtime approval/tool-call values before they are nulled, such as idempotency key, approval id, tool-call id, tool-call fingerprint, selected run mode, runtime context fingerprint, and QueryPlan fingerprint when available.
8. Create or replace the workspace run only after a successful approved runtime search result; failed searches must not create a new successful workspace run.
9. Clear workspace state when Search Brief changes, safety/refusal turns, reset paths, plan/query/runtime stale paths, search start, or search failure clear visible results.
10. Use `item.normalized_url` as the primary `candidate_id` and backend dedupe/profile identity source. Current backend `normalized_url` values are scheme-less, for example `ua.linkedin.com/in/example`, so clickable href generation must be handled separately.
11. Never let `result.url` override `item.normalized_url` as candidate identity. `result.url` is only fallback/display data after validation.
12. If `item.normalized_url` is missing, create a local render-only fallback id such as `row_${index}` so rendering does not crash, but never treat it as stable profile identity, backend dedupe identity, persistence identity, or future shortlist carryover identity.
13. Add `source_index` or `display_index` to the view model for display/order, but do not use it as candidate identity.
14. Preserve the backend `deduped_results` order and do not add frontend sorting/filtering in `P8-002`.
15. Do not recalculate quality, fit, role, stack, location, seniority, or score semantics in the frontend; map backend fields into a display model only.
16. If candidate `name` is missing or `unknown`, use a safe fallback such as headline, title, or profile id as the primary visible candidate label.
17. Render the table/list and read-only details from frontend workspace state, not from DOM parsing.
18. Preserve the current candidate cards/evidence as fallback details while introducing the table/list.
19. Keep room in the view model for future `review_status`, notes, shortlist, sorting/filtering, and explanations, but do not make them interactive in `P8-002`.
20. If a successful approved runtime search returns zero candidates, create/replace the workspace run with empty `workspaceCandidates` and show the visible empty state.
21. If runtime/search execution fails, do not create a new successful workspace run and do not leave stale candidates shown as current results.
22. Build clickable profile hrefs through a helper such as `buildSafeLinkedInProfileHref(item)`: use `item.normalized_url` first, add `https://` when it is scheme-less, validate with browser `URL()`, and use `result.url` only as fallback if `item.normalized_url` cannot produce a valid safe profile href.
23. Failed profile URL validation must not filter the candidate out of the workspace; it should only make the link non-clickable, hidden, or escaped plain text.
24. Use local allowlist/map helpers for dynamic CSS classes such as quality bucket, flag severity, source type, location status, or fit status.
25. Preserve basic accessibility: native `details`/`summary` is acceptable for expandable evidence, profile URLs should remain normal links, entire rows should not become clickable `div`s, and labels should remain readable or screen-reader-available.
26. Add mandatory no-network helper smoke coverage, for example `scripts/smoke_p8_candidate_workspace_helpers.js`, and wire it into `scripts/check_all.ps1` through the existing `$node` variable.
27. Add focused frontend/static and browser sanity checks.

If a backend workspace schema or endpoint becomes necessary, it requires a separate reviewed task.

Recommended `P8-002` checks:

- current `renderResults` behavior still renders candidates after approved search;
- the mapper handles missing optional fields without crashing;
- pure workspace helpers can be tested without loading DOM-bound `app/static/app.js`;
- helper tests can use a fake `window` with Node built-ins such as `vm`, without adding npm dependencies;
- `app/static/index.html` loads the workspace helper before `app/static/app.js`;
- workspace run state is created only for successful approved runtime search results;
- successful approved searches with zero candidates create an empty workspace run and visible empty state;
- failed runtime/search execution does not create a successful workspace run and does not leave stale candidates visible as current results;
- Search Brief changes, safety/refusal turns, reset paths, plan/query/runtime stale paths, search start, and search failure clear workspace state consistently with visible results state;
- runtime approval/context values needed for `workspace_run_id` are captured before runtime approval is cleared;
- current runtime approval/tool-call values are read before `clearRuntimeApproval()` clears them;
- `item.normalized_url` is primary for `candidate_id` and backend dedupe/profile identity;
- `result.url` never overrides `item.normalized_url` as candidate identity when `item.normalized_url` exists;
- missing `item.normalized_url` gets a clearly render-only fallback id and does not crash rendering;
- render-only fallback ids and display indexes are not treated as stable candidate identity;
- frontend mapping preserves backend `deduped_results` order and does not sort/filter;
- frontend mapping does not recalculate quality, fit, role, stack, location, seniority, or score semantics;
- missing/unknown candidate names fall back to headline, title, or profile id for the primary visible label;
- scheme-less normalized URLs such as `ua.linkedin.com/in/example` become canonical href candidates such as `https://ua.linkedin.com/in/example` before strict URL validation;
- `result.url` is used only as validated fallback/display data when `item.normalized_url` cannot produce a valid safe profile href;
- candidate text, snippets, query strings, notes, and dynamic HTML attributes such as `title` or `aria-label` are escaped;
- external profile links remain manual user-click links only and are clickable only after safe LinkedIn URL validation;
- failed profile URL validation disables/hides only the clickable link and does not filter out the candidate row;
- URL validation rejects non-http(s), non-LinkedIn, non-profile, and lookalike hostnames;
- dynamic CSS classes use local allowlists/maps rather than raw backend/public values;
- workspace UI renders from explicit JS state, not from parsed DOM;
- workspace table/list uses responsive grid/list markup, not native HTML `<table>`;
- layout changes stay limited to results/candidate rendering and related CSS;
- new approved search resets local workspace state by default;
- page reload can clear workspace state in v0 and does not silently restore notes/status/shortlist;
- shortlist/status/notes controls are not interactive in `P8-002`;
- expandable details remain keyboard-accessible, profile URLs remain normal links, whole rows are not clickable `div`s, and field labels remain readable on mobile;
- mandatory no-network helper smoke checks cover mapper, helper loadability, helper syntax check, index load order, scheme-less normalized URL href creation, URL validation including lookalike hosts, failed URL validation preserving candidate rows, dynamic class allowlists, workspace run id uniqueness, order preservation, render-only fallback id behavior, display index behavior, candidate-label fallback, and workspace clear/reset behavior where practical;
- helper smoke checks are included in `scripts/check_all.ps1`;
- `scripts/check_all.ps1` uses its existing `$node` resolver for both the helper syntax check and helper smoke script, without hardcoding a different Node executable path;
- mobile/narrow layout remains readable.

## Non-Goals

`P8-001` and the initial Workspace v0 contract do not add:

- backend code;
- frontend code;
- database;
- persistence;
- saved searches;
- saved candidates;
- memory;
- authentication;
- user accounts;
- new countries;
- new technologies;
- new search sources;
- executable AI-generated QueryPlans;
- autonomous execution;
- direct web-search bypass;
- direct LinkedIn access or automation;
- LinkedIn login;
- LinkedIn scraping or restriction bypass;
- automatic candidate messaging;
- user or third-party account actions.

## Acceptance Criteria

- Workspace v0 uses approved search result data as the source of truth.
- Candidate facts and recruiter UI state are explicitly separated.
- Shortlist, notes, and statuses are session/local UI state until Phase 9.
- Session/local UI state is in-memory for Phase 8 v0; browser/backend persistence is out of scope.
- `workspace_run_id` requires a per-run component and cannot rely only on QueryPlan fingerprint.
- `shortlisted` is documented as derived from `review_status`, not as independent state.
- `P8-002` must map successful approved search results into explicit frontend state and must not parse rendered DOM as data source.
- `P8-002` should put pure workspace helpers in a DOM-free frontend helper file and include mandatory helper smoke coverage in `scripts/check_all.ps1`.
- `P8-002` should clear workspace state through the same stale/reset/error boundaries that clear visible results.
- `P8-002` should preserve backend `deduped_results` order and must not recalculate quality, fit, role, stack, location, seniority, or score semantics.
- `P8-002` should keep invalid/unsafe-link candidates visible while disabling or hiding only unsafe clickable links.
- `P8-002` should define render-only fallback ids and display indexes without treating either as stable candidate identity.
- `P8-002` is scoped to a read-only candidate table/list foundation; sorting/filtering, shortlist, notes, editable statuses, explanations, export, backend changes, and persistence remain later tasks.
- `P8-002` implementation scope is limited to mapper, workspace run state, recruiter-facing table/list, and read-only candidate details; later task architecture can be prepared only as inert structure.
- `P8-002` may update no-network regression scripts, but product behavior changes remain frontend-only and backend app/API/search/runtime behavior remains unchanged.
- `P8-002` should use responsive grid/list markup rather than native HTML `<table>` and should keep layout changes limited to the results area.
- `P8-002` should define empty-result and failed-search workspace behavior.
- Profile links require strict `URL()`-based safe LinkedIn profile URL validation before becoming clickable.
- Dynamic CSS classes require local allowlists/maps.
- Basic keyboard/link/label accessibility remains part of the `P8-002` boundary.
- Candidate table/list, detail view, shortlist, notes/statuses, sorting/filtering, explanations, and export boundaries are defined.
- `P8-002` can implement the first recruiter-facing candidate table without redesigning data ownership.
- Absolute product restrictions remain intact.
