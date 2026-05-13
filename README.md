# Engineers_Search_Engine
AI-powered sourcing search engine

## Phase 1 POC

Minimal FastAPI skeleton for the Tavily-powered LinkedIn X-ray search POC.

Status: Phase 1 POC completed successfully.

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
