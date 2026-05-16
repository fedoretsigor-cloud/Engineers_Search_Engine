# Engineers_Search_Engine
AI-powered sourcing search engine

## Current Status

Planner-based Tavily/LinkedIn X-ray sourcing prototype.

Status:

- Phase 1 POC completed successfully.
- Phase 1.1 behavior tuning completed.
- Phase 2 multi-query search + baseline query planner completed.
- Phase 3 Candidate Quality Layer completed.
- Phase 4 AI Agent Foundation is in progress.
- Phase 4 `P4-003`-`P4-008` are implemented: Search Brief validation/adapter, Agent Tools v0 metadata, explicit AI planner mode, deterministic AI QueryPlan validation/fallback, planner explanation UI, and backend approval gate before Tavily execution.

Current pipeline:

- structured inputs: `Role Family`, `Technology`, `Stack`, `Location`;
- `RuleBasedQueryPlanner v1` generates a visible 10-query `QueryPlan`;
- optional explicit AI planner mode can draft and explain a non-executable plan;
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
- Tavily execution must stay inside the approved backend pipeline.
- The legacy raw `/api/search` Tavily path is disabled.
- AI-generated plans remain non-executable until a later reviewed task explicitly enables that path.

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
- `docs/phase-1-poc-findings.md`
- `docs/phase-3-quality-baseline.md`
- `docs/phase-3-multi-wave-evaluation.md`
