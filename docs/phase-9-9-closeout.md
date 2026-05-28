# Phase 9.9 Closeout - AI Agent Semantic Understanding Hardening

## Decision

Phase 9.9 is completed as the final POC semantic-understanding hardening layer.

The project is good enough for the current final POC baseline: the AI Agent can now understand clean-state recruiter requests and existing Search Brief refinements through bounded LLM interpretation while the backend remains authoritative for validation, mutation, planning, approval, and search execution.

This is not a fully autonomous recruiter agent. The approved boundary remains human-approved search execution through the backend runtime.

## Completed Scope

- `P9.9-001` added isolated `SearchBriefExtractor v2` prompt/wrapper foundation.
- `P9.9-002` added strict backend validation for extractor output.
- `P9.9-003` integrated validated clean-state extraction into recruiter chat.
- `P9.9-004` removed or guarded legacy clean-state semantic branches.
- `P9.9-005` added deterministic semantic recruiter UAT for clean-state extraction.
- `P9.9-006` added bounded Search Brief refinement interpretation for existing drafts.

## LLM Boundary

LLM is allowed to:

- extract a raw Search Brief draft from a clean-state recruiter message;
- interpret an existing-draft refinement as a bounded patch intent;
- classify semantic meaning inside the approved contracts.

LLM is not allowed to:

- become authoritative for Search Brief state;
- generate or execute queries directly;
- approve or run search;
- call Tavily, Serper, SerpApi, LinkedIn, or any provider;
- browse, scrape, log in, automate LinkedIn, or bypass restrictions;
- message candidates or perform account actions;
- persist data.

## Backend Authority

The backend remains authoritative for:

- English-only and prohibited-action prechecks;
- strict LLM output schema validation;
- role, technology, stack, location, seniority, search depth, and must-have normalization;
- domain-vs-technology separation;
- Search Brief readiness evidence gate;
- `brief_patch` application;
- stale-state clearing;
- QueryPlan generation;
- runtime approval;
- provider execution;
- candidate scoring/dedupe/result rendering.

## Verification

Local verification passed:

- `scripts/smoke_p99_search_brief_extractor.py`
- `scripts/uat_phase_9_9_semantic_search_brief.py` - 11/11 semantic cases
- `scripts/smoke_p99_search_brief_refinement.py`
- `scripts/check_all.ps1`

CI passed for Phase 9.9 implementation commits through `P9.9-006`.

## Residual Limitations

- OpenAI availability/model quality affects bounded semantic extraction and refinement interpretation; deterministic fallback remains conservative.
- The app still rejects Cyrillic/non-English recruiter input for this POC.
- No persistence, saved searches, authentication, or long-term memory is included.
- No direct LinkedIn access, scraping, login, messaging, or account automation is included.
- Candidate evidence still depends on public search snippets and configured providers.
- Broader live UAT across every possible IT role/location/stack is future work.

## Future Handoff

Phase 10+ persistence, manual candidate evidence intake, resume analysis, and broader agent memory remain parked unless the POC is explicitly reopened.

Any future autonomous behavior must preserve the current hard boundary: LLM may propose or interpret; backend validates; recruiter approval is required before search execution.
