# Phase 8 Candidate Workspace Contract

Task: `P8-001 Define candidate workspace contract`

Status: completed

## Decision

Phase 8 Candidate Workspace v0 turns already approved search results into the recruiter working artifact.

The workspace is built from the current approved search pipeline output:

`recruiter chat -> Search Brief -> Agent Plan -> Build Plan -> visible QueryPlan -> explicit Approve & Search -> approved Tavily-backed results`

Implementation status after `P8-004`: the first frontend-only Candidate Workspace batch is implemented. `P8-002` added explicit workspace run/candidate state and a recruiter-facing workspace list, `P8-003` added workspace view sorting/filtering over already returned candidates, and `P8-004` added browser in-memory review status, derived shortlist, escaped plain-text notes, and review-status/shortlist filters. Backend/API/search/runtime behavior, persistence, saved searches, export, and candidate-level AI explanations remain out of scope until later reviewed tasks.

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

Candidate-level agent explanations belong to later Phase 8 work, not `P8-001`.

When implemented, explanations must be grounded only in visible workspace candidate facts:

- candidate identity/headline;
- quality score and score breakdown;
- review flags;
- evidence fields;
- query/wave sources;
- location signals;
- public Tavily snippet/content already returned by the approved pipeline.

The agent must not invent candidate facts, infer private data, open profiles, scrape LinkedIn, message candidates, or claim verified truth beyond the returned public-search evidence.

## Export Boundary

Export belongs to `P8-006`.

Export should use only workspace data available in the current session:

- candidate identity;
- profile URL;
- score/fit fields;
- review flags;
- shortlist/status;
- recruiter notes;
- evidence snippets;
- query/run metadata if useful.

Export must not add persistence by itself, must not create accounts, and must not send messages or perform outreach.

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

`P8-002` should code only the mapper, workspace run state, recruiter-facing table/list, and read-only candidate details. It can leave inert view-model fields or markup structure for later Phase 8 tasks, but interactive sorting/filtering belongs to `P8-003`, shortlist/notes/statuses belong to `P8-004`, candidate-level explanations belong to `P8-005`, and export belongs to `P8-006`.

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
