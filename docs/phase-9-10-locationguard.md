# Phase 9.10 - Global LocationGuard v1

## Decision

`P9.10-001 Global LocationGuard v1 for all target locations` is a final POC hardening task after Phase 9.9 semantic understanding.

The issue: Phase 9.5 generalized the POC to any English IT/software role and location, but strict location filtering still depended on a Ukraine-only config. Searches such as `Business Analyst in Poland with SQL` could show candidates whose visible current location was not Poland because the query term `Poland` only constrained provider search text, not backend candidate acceptance.

## Implemented Pattern

LocationGuard v1 is backend-owned and deterministic:

- every non-empty target location gets a `location_filter_config`;
- seeded country presets provide LinkedIn country domains and common country/city aliases for Ukraine, Poland, Spain, Canada, Germany, UK, USA, and Remote;
- unseeded locations use a safe fallback config with the exact requested location term;
- location filtering is enabled by default for normalized structured requests when a target location exists;
- candidates pass the location gate only when the normalized profile URL country domain matches, current/header location text confirms the target, or header evidence is strong enough to rescue;
- candidates with explicit foreign current-location text are hidden;
- weak history-only and unknown non-country-domain location signals are hidden by the location filter;
- if location filtering is not evaluated, candidate status cannot be shown as `Strong match` in the primary UI.

LLM usage remains bounded to Search Brief understanding/refinement. LocationGuard itself does not call OpenAI per candidate or per result; backend validation remains authoritative.

## Boundaries

- No LinkedIn login.
- No LinkedIn scraping.
- No profile-opening automation.
- No direct web-search bypass outside the approved backend provider pipeline.
- No candidate messaging.
- No autonomous execution.
- No persistence or account actions.

## Verification

- `scripts/smoke_p910_location_guard.py`
- `scripts/check_all.ps1`

