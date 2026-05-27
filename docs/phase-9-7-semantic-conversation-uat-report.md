# Phase 9.7 Semantic Conversation UAT Report

## Scope

This UAT is no-live and uses deterministic doubles for LLM calls. It validates semantic pending-answer behavior without Tavily, provider calls, LinkedIn access, screenshots, secrets, raw profile URLs, or candidate PII.

## Covered Scenarios

- Validator accepts strict bounded interpreter output.
- Validator rejects extra fields.
- Validator rejects low confidence.
- Validator rejects unsafe URL-like values.
- Pending stack answer `Java only` becomes `stack = ["Java"]`.
- Pending location answer `Madrid would work` becomes `location = "Madrid"`.
- Pending update/refinement `replace Kafka with Selenium` becomes a safe stack replacement through existing brief patch behavior.
- Low-confidence interpreter output does not mutate the current Search Brief.

## Result

Pass.

`scripts/smoke_p97_semantic_interpreter.py` covers the Phase 9.7 semantic conversation UAT and is included in `scripts/check_all.ps1`.

## Boundaries Confirmed

- No autonomous execution.
- No search execution.
- No query generation.
- No provider fanout changes.
- No LinkedIn automation, scraping, login, messaging, or account actions.
- No persistence.
- Existing runtime approval boundary remains unchanged.
