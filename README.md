# Engineers_Search_Engine
AI-powered sourcing search engine

## Current Status

Planner-based Tavily/LinkedIn X-ray sourcing prototype.

Status:

- Phase 1 POC completed successfully.
- Phase 1.1 behavior tuning completed.
- Phase 2 multi-query search + baseline query planner completed.

Current pipeline:

- structured inputs: `Role Family`, `Technology`, `Stack`, `Location`;
- `RuleBasedQueryPlanner v1` generates a visible 10-query `QueryPlan`;
- Tavily executes the generated queries;
- LinkedIn profile URLs are normalized and deduped;
- visible `LinkedIn profiles only` and `Location filter` controls are applied;
- Ukraine location filtering uses current-location classification instead of a finite negative-location blacklist;
- local structured-search snapshots are saved under `logs/search-runs/` and ignored by git.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
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
