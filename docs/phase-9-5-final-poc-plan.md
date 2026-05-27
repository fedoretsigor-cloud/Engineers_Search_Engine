# Phase 9.5 - Final POC Hardening And Render Deployment

## Summary

Phase 9.5 is the final active POC phase. The project pauses Phase 10+ persistence and future feature tracks for now, finishes a small POC hardening slice, and then deploys the current product to Render with a public URL.

Search providers stay as currently implemented in Phase 9. Provider fanout/reporting changes are deferred unless a later reviewed task explicitly reopens them.

## Tasks

- `P9.5-001 Park Phase 10+ and define final POC closeout`
- `P9.5-002 Enforce English-only recruiter input`
- `P9.5-003 Generalize search from Java/Ukraine baseline to any IT role`
- `P9.5-004 Polish empty and loading Candidate Results states`
- `P9.5-005 Remove duplicate ready/search wording and Workspace Ready label`
- `P9.5-006 Final POC regression pass`
- `P9.5-007 Deploy POC to Render`

## Required Product Changes

- English-only input:
  - Frontend blocks chat messages containing Cyrillic.
  - Backend rejects Cyrillic in recruiter chat, Search Brief, and structured-search fields.
  - The visible POC conversation defaults to English.

- Generic IT search:
  - Keep the existing API field names for compatibility.
  - Treat `role_family` as the recruiter target IT role/title/family string.
  - Accept any English IT/software role when role, main technology, stack, and location are present.
  - Reject non-IT, prohibited, random/noise, or unclear profession-like input.
  - Preserve human-approved runtime execution.

- Candidate Results polish:
  - Before results, align the Candidate Results panel height with Recruiter Chat on desktop.
  - Show a professional empty-state visual placeholder instead of blank space.
  - Show a polished spinner/loading state while search is running.
  - Remove the duplicate chat message `I understood the search. Review the summary...`.
  - Keep the more specific confirmation message that summarizes the concrete search.
  - Remove visible `Workspace Ready`.

- Render deployment:
  - Add a repeatable Render deployment path.
  - Configure secrets only in Render, never in git.
  - Verify public `/api/health` and one UI smoke flow after deployment.

## Test Plan

- Run `scripts/check_all.ps1`.
- Add or update no-network smoke coverage for:
  - Cyrillic input rejection.
  - English IT role accepted.
  - Non-IT role rejected.
  - Missing role, technology, stack, or location asks for clarification.
  - Generic planner returns 10 bounded LinkedIn X-ray queries.
  - Candidate Results empty state renders before search.
  - Candidate Results loading spinner renders during search.
  - Duplicate ready/search message no longer appears.
  - `Workspace Ready` no longer appears.
- Run browser sanity for one English IT search flow.
- For Render, verify the public URL and `/api/health`.

## Boundaries

- Do not change Phase 9 search providers in this phase unless explicitly reopened.
- Do not add persistence, saved searches, accounts, auth, outreach, LinkedIn login/scraping, or autonomous execution.
- Do not commit provider secrets or deployment secrets.
- Keep the approved backend runtime boundary as the only search execution path.

