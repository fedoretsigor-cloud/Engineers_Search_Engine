# Phase 9.7 PendingAnswerInterpreter Contract

## Decision

Phase 9.7 introduces `PendingAnswerInterpreter v1` as a bounded semantic layer for recruiter chat replies that answer an active clarification or update a selected Search Brief field.

The pipeline is:

```text
message -> deterministic safety precheck -> bounded LLM semantic interpreter -> strict backend validator -> deterministic brief patch/action
```

The LLM interprets meaning only. It does not execute searches, approve runtime actions, generate queries, call providers, open LinkedIn, scrape, message candidates, act on accounts, or persist data.

## Input

The interpreter receives only bounded context:

- latest recruiter message;
- UI language;
- expected pending field, when the assistant is waiting for one field;
- pending update field, when the recruiter selected a field to update;
- current draft Search Brief without secrets, provider payloads, profile URLs, or candidate data.

## Output

The model must return JSON only:

```json
{
  "intent": "answer_pending_field",
  "field": "stack",
  "values": ["Java"],
  "confidence": "high",
  "reason_code": "natural_stack_answer"
}
```

Allowed intents:

- `answer_pending_field`
- `ask_explanation`
- `change_field`
- `provide_update_value`
- `unclear`
- `unsafe`

Allowed fields:

- `role_family`
- `technology`
- `stack`
- `location`
- `seniority`
- `search_depth`

## Backend Authority

`app/pending_answer_interpreter.py` owns the backend validator. It rejects:

- malformed output;
- extra fields;
- unknown intents or fields;
- low confidence;
- unsafe values;
- URLs, account/action instructions, or prompt-like payloads;
- Cyrillic/non-English values for the current POC;
- more than 3 stack values;
- unsupported field values.

Validated output is still not applied directly. `app/main.py` converts it into existing `brief_patch` operations only after field-specific validation.

## Field Behavior

Stack:

- direct simple values keep deterministic fast path;
- natural phrases such as `Java only` use the interpreter;
- extracted values are revalidated through existing stack-signal validation.

Location:

- direct simple values keep deterministic fast path;
- natural phrases such as `Madrid would work` use the interpreter;
- the phase does not add a country/city database or change location-filter mapping.

Update/refinement:

- selected field updates can use the interpreter when a recruiter phrase contains the new value semantically;
- interpretation alone never starts search.

## Boundaries

No autonomous execution, direct web-search bypass, LinkedIn login/access automation/scraping, candidate messaging, account actions, persistence, provider fanout changes, candidate scoring changes, location-filter mapping changes, or runtime approval changes are included.
