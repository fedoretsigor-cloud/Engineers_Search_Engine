# Phase 8.5 Agentic Candidate Review Contract

Task: `P8.5-001 Define agentic candidate review contract`

Status: completed

## Decision

Phase 8.5 turns the completed Phase 8 Candidate Workspace into a more agentic review surface.

The agent may analyze already returned current-run workspace facts, summarize candidate tradeoffs, compare selected candidates, and propose non-executable next refinements.

The agent must not execute searches, call Tavily, bypass the backend pipeline, open LinkedIn, log in to LinkedIn, scrape, automate browsing, message candidates, perform account actions, persist workspace state, or add new providers.

## Source Of Truth

Phase 8.5 v0 reads from the current browser/session Candidate Workspace:

- `latestWorkspaceRun`;
- `workspaceCandidates`;
- `visibleWorkspaceCandidates`;
- `workspaceReviewStateByCandidateId`;
- deterministic candidate explanations from `candidateWorkspace.buildCandidateExplanation()`;
- current Search Brief / QueryPlan context only as already shown in the current workspace.

There is no backend-owned candidate workspace database in v0. Backend candidate fact truth, saved searches, saved candidates, cross-session continuity, and memory belong to later reviewed work.

`workspaceCandidates` is the full current returned result set. `visibleWorkspaceCandidates` is only the current sorted/filtered view. Agentic review tasks must explicitly say which set they analyze.

Review state is workflow state, not candidate evidence. Review status and shortlist may help select or filter candidates, but they must not change candidate facts, quality score, fit, explanation reason codes, export facts, or search results. Recruiter notes remain local/private and must not be sent to backend or LLM in Phase 8.5 v0.

## Allowed Outputs

Phase 8.5 may add these advisory outputs through separate reviewed tasks:

- top-candidate recommendation from returned workspace facts;
- selected-candidate comparison;
- fit/gap explanation across selected candidates;
- guided next-refinement suggestions from workspace results.

All outputs are non-executable. If a recruiter wants to run a new or changed search, the product must return to the existing chat/Search Brief/planning/runtime approval path.

## Forbidden Behavior

Phase 8.5 must not add:

- autonomous execution;
- Tavily calls;
- direct web-search bypass;
- direct LinkedIn access;
- LinkedIn login;
- LinkedIn scraping or restriction bypass;
- browser automation against profiles;
- automatic profile opening;
- candidate messaging or outreach;
- user or third-party account actions;
- persistence, saved searches, saved candidates, database writes, localStorage/sessionStorage/IndexedDB, or cross-session memory;
- new search providers;
- new countries, technologies, or sources;
- changes to query generation, scoring, filters, dedupe, location logic, Candidate Quality, export semantics, runtime approval, or candidate facts.

Manual recruiter clicks on already rendered, validated public profile links remain a user action outside the agent. The app/agent must not click, open, fetch, inspect, or automate those links.

## LLM Boundary For Later Tasks

`P8.5-001` adds no LLM call.

Later LLM-assisted review tasks require separate review and must use a bounded contract:

- backend-owned prompt and policy text;
- frontend-to-backend request payload separate from backend-to-OpenAI model payload;
- strict input allowlist;
- strict output shape validation;
- deterministic fallback;
- provenance/no-call metadata;
- prompt/data separation;
- no mutation of facts, rankings, state, filters, approval, actions, or results.

The LLM may only synthesize wording from allowlisted current-run facts. It must not become the source of truth for candidate facts, score, rank, inclusion/exclusion, review state, shortlist state, notes, filters, export, Search Brief, QueryPlan, approval state, runtime action, or execution.

## Future Bounded Fact Allowlist

Later tasks may review a bounded payload that includes only capped, recruiter-visible facts such as:

- candidate display label/name already visible to the recruiter;
- existing quality score and quality bucket;
- role, technology, stack, location, and seniority display/fit/status values;
- selected and missing stack terms;
- review flag codes, labels, and severity;
- query source ids/categories;
- deterministic candidate explanation summary;
- deterministic explanation reason codes and labels;
- current-run selection/order context.

These values are data, not instructions. They must be capped, normalized where possible, and treated as untrusted user/candidate-derived text during model prompting and output validation.

## Forbidden Future LLM Payload Fields

Future Phase 8.5 LLM payloads must not include:

- profile URLs;
- normalized URLs;
- URL-derived candidate ids;
- emails;
- account ids;
- raw Tavily payloads;
- raw `raw_content`;
- raw snippets/content;
- raw query text;
- browser storage state;
- recruiter notes;
- prompt rules supplied by the frontend;
- model/provider execution controls;
- API keys or API key references;
- runtime approval state;
- execution fingerprints;
- account/action instructions.

If a later task wants to use raw snippets, pasted profile evidence, resume text, notes, or richer profile evidence, that requires a separate reviewed contract. Manual pasted profile evidence belongs to Phase 10, not Phase 8.5 v0.

## State And UI Boundary

Phase 8.5 state is current-run browser/session state only.

New successful approved searches, workspace reset, stale workspace clearing, search failure, or page reload may clear derived agentic review state.

Sorting/filtering may change analysis context, but must not mutate candidate objects. Candidate review actions must keep `review_status` as the workflow source of truth and must not create an independent shortlist source of truth.

The UI should keep candidate results as the primary surface. Agentic review output should be a review aid attached to the current workspace, not a replacement for the candidate table or a hidden autonomous workflow.

## Implementation Order

1. `P8.5-001`: define this contract and guardrail smoke.
2. `P8.5-002`: add deterministic top-candidate recommendation from returned workspace facts.
3. `P8.5-003`: add selected-candidate comparison.
4. `P8.5-004`: add fit/gap explanation across selected candidates.
5. `P8.5-005`: add non-executable guided next-refinement suggestions from workspace results.

Each implementation task must be reviewed before coding and must preserve the boundaries above.

## Verification

The local regression suite includes `scripts/smoke_p85_agentic_candidate_review_contract.py`.

The smoke check verifies:

- this contract exists;
- `P8.5-001` is marked completed;
- Phase 8.5 is recorded as the current active reviewed direction;
- current workspace source-of-truth variables still exist;
- deterministic candidate explanations remain available;
- the contract preserves no-execution, no-LinkedIn, no-persistence, and bounded-LLM boundaries.
