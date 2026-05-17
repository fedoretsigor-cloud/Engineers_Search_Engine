# Engineers_Search_Engine
AI-powered sourcing search engine

## Current Status

Planner-based Tavily/LinkedIn X-ray sourcing prototype.

Status:

- Phase 1 POC completed successfully.
- Phase 1.1 behavior tuning completed.
- Phase 2 multi-query search + baseline query planner completed.
- Phase 3 Candidate Quality Layer completed.
- Phase 4 AI Agent Foundation completed.
- Phase 4 `P4-003`-`P4-011` are completed: Search Brief validation/adapter, Agent Tools v0 metadata, explicit AI planner mode, deterministic AI QueryPlan validation/fallback, planner explanation UI, backend approval gate before Tavily execution, AI planner baseline evaluation, AI planner coverage diagnosis/improvement, and Phase 4 closeout.
- Current active phase: Phase 5 `Recruiter Chat UX + Search Brief conversation`.
- Completed Phase 5 tasks: `P5-001 Define recruiter chat and Search Brief conversation contract`, `P5-002 Add backend chat-to-brief adapter`, `P5-003 Replace structured form with recruiter chat UI`, `P5-004 Make Build Plan produce an approvable Search Plan`, `P5-005 Instantiate human-approved Agent v0 for Java/Ukraine baseline`.
- Phase 5 tasks added for review, not yet approved or implemented: `P5-006 Add post-results Agent Response in chat`, `P5-007 Add LLM-assisted Agent Plan/Response with deterministic fallback`.
- `P5-002` added `POST /api/recruiter-chat/turn` and is limited to `chat messages -> draft Search Brief -> validation -> one assistant response`.
- `P5-003` made recruiter chat the primary frontend input and keeps execution tied to planner response `adapted_structured_request`.
- `P5-004` made primary chat `Build Plan` produce an approvable deterministic backend Search Plan as a safe executable bridge toward the AI Agent flow. AI planner capability remains in the product and should be evolved through reviewed tasks.
- `P5-005` added `POST /api/agent/plan`, shows Agent Plan in chat for the supported Java/Ukraine baseline, and makes `Build Plan` execute the current `agent_plan.proposed_action` with backend fingerprint validation.

Current pipeline:

- recruiter chat collects a validated `Search Brief` from natural-language recruiter messages;
- the supported Java/Ukraine baseline gets a current Agent Plan in chat before planning;
- `Build Plan` executes the Agent Plan's proposed backend action and converts the chat-produced brief into a visible approvable Search Plan;
- `RuleBasedQueryPlanner v1` generates a visible 10-query `QueryPlan`;
- optional explicit AI planner mode can draft and explain a plan for backend validation/fallback;
- backend validates AI draft plans deterministically and can show rule-based fallback;
- rule-based Tavily execution requires explicit approval bound to action, query count, and current `QueryPlan` fingerprint;
- Tavily executes the generated queries;
- LinkedIn profile URLs are normalized and deduped;
- visible `LinkedIn profiles only` and `Location filter` controls are applied;
- Ukraine location filtering uses current-location classification instead of a finite negative-location blacklist;
- Candidate Quality Layer adds role/tech/stack/seniority signals, review flags, and explainable quality score;
- local structured-search snapshots are saved under `logs/search-runs/` and ignored by git.

Execution boundary:

- AI planner output is planning/explanation only and is not executable.
- AI Agent behavior must stay human-approved, not autonomous: it may suggest, prepare, explain, validate, and analyze, but search/deep/multi-wave execution requires explicit approval.
- Tavily execution must stay inside the approved backend pipeline.
- The legacy raw `/api/search` Tavily path is disabled.
- AI-generated plans remain non-executable until a later reviewed task explicitly enables that path.
- AI plan validation includes strict `AIPlannerCoveragePolicy v0` coverage checks for the Java/Ukraine standard baseline; unsupported briefs return a visible coverage-policy warning.
- Direct LinkedIn access/automation is prohibited: no LinkedIn login, no scraping, no restriction bypass, no direct profile automation/opening, no candidate messaging, and no account actions.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Optional AI planner configuration:

```powershell
$env:OPENAI_API_KEY="..."
$env:OPENAI_MODEL="..."
```

Open:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/api/health
```

## Project Documents

- `ProjectStatus.md`
- `Roadmap.md`
- `Tasks.md`
- `docs/phase-4-ai-planner-baseline.md`
- `docs/phase-1-poc-findings.md`
- `docs/phase-3-quality-baseline.md`
- `docs/phase-3-multi-wave-evaluation.md`
