# Phase 8.75.1 Conversation UX UAT

Task: `P8.75.1-001 Run UI conversation UX UAT before persistence`

## Purpose

Phase 8.75 proved the backend/runtime/workspace acceptance gate. Phase 8.75.1 adds the missing recruiter-facing layer: simulated real user behavior through the actual frontend chat UI.

The goal is to verify that the AI Agent v0 flow is not only safe and contract-correct, but also understandable, polite, and usable when a recruiter types natural messages into the UI.

## Scope

The UAT covers the current supported flow:

- `Backend Developer + Java + Ukraine`;
- public LinkedIn profile sourcing through the existing backend runtime path only;
- recruiter chat collection/refinement/confirmation;
- current candidate workspace display after an approved search.

## Scenario Classes

The UI runner must cover:

- positive ready search requests in English, Russian, and mixed wording;
- incomplete requests that need one clear clarification;
- pending clarification answers, including Russian stack/location answers;
- harmless small talk and greetings;
- unclear/noisy input;
- off-topic but harmless questions;
- prohibited requests;
- search refinements before execution;
- chat confirmation that starts search only through the safe runtime path;
- post-search compact response and candidate table visibility.

## UX Acceptance Rules

Every scenario is evaluated against both state and wording:

- the reply must be polite, brief, and useful;
- the reply must match the user's language where practical;
- the reply must not expose internal implementation terms such as `QueryPlan`, `backend planner`, `fingerprint`, `runtime`, `approval`, `Tavily`, `Build Plan`, or `Frontend ready`;
- the reply must not be harsh for harmless input;
- unclear input should get a polite "I did not understand" style answer and a candidate-search redirect;
- off-topic input should be handled conservatively without pretending to answer external factual questions;
- prohibited input must be refused without preserving executable stale state;
- ready searches must ask for natural confirmation before starting;
- chat confirmation may start search only through the existing runtime path with mocked execution in this local UAT;
- no live Tavily/OpenAI calls are used by the UI UAT runner.

## Commands

Run the UI conversation UX UAT locally:

```powershell
.\.venv\Scripts\python.exe scripts\uat_phase_8_75_1_ui_conversation.py --write-report docs\phase-8-75-1-conversation-ux-report.md
```

The runner starts a local FastAPI server, opens the real frontend with Playwright, types recruiter messages into the chat, and reads visible UI state. External services are replaced with local deterministic doubles.

## Boundaries

This gate must not add persistence, database storage, direct web-search bypass, direct LinkedIn access/login/scraping, candidate messaging, account actions, autonomous execution, or new providers.

The runner must not commit screenshots, raw profile URLs, raw candidate payloads, Tavily payloads, OpenAI payloads, or secrets.
