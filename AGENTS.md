# Codex Project Context

## Project

Engineers Search Engine is a Phase 1 POC for AI-assisted recruiter sourcing. It uses FastAPI to serve a static UI and a Tavily-backed LinkedIn X-ray search endpoint.

## Stack

- Python FastAPI backend in `app/main.py`
- Static frontend in `app/static/index.html`, `app/static/styles.css`, and `app/static/app.js`
- Dependencies are listed in `requirements.txt`
- Local secrets are loaded from `.env`

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000`.

Health check: `http://localhost:8000/api/health`.

## Current Status

Phase 1 POC and Phase 1.1 behavior tuning are complete. The recommended next phase is Phase 2: sequential multi-query search with deduplication.

Key product rule: the editable Boolean query is the source of truth. Form fields may help build it, but the backend should not apply hidden role, stack, or location filters.

## Working Rules

- Read `instructions`, `ProjectStatus.md`, `Roadmap.md`, `Tasks.md`, and `docs/phase-1-poc-findings.md` before changing behavior.
- Follow the collaboration rules in `instructions`.
- Keep the project within the public-search POC scope: no LinkedIn login automation, scraping, restriction bypass, database, shortlist, or AI agent unless explicitly agreed.
- Prefer focused, small changes with verification.

## Verification

Useful checks:

```powershell
.\.venv\Scripts\python.exe -m compileall app
node --check app/static/app.js
```
