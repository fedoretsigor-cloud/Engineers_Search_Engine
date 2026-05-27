# Render Deployment

This is the repeatable deployment path for the final POC.

## Service

- Use `render.yaml` as the Render Blueprint.
- Service type: web service.
- Runtime: Python.
- Plan: free by default for the POC.
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Health check: `/api/health`.

## Secrets

Configure these in Render environment variables only. Do not commit real values.

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `TAVILY_API_KEY`
- `SERPER_API_KEY`
- `SERPAPI_API_KEY`

## Verification

After deployment:

1. Open the public Render URL.
2. Check `<public-url>/api/health` returns `status = ok`.
3. Run one UI smoke flow in English:
   `Find frontend developers in Poland, main technology TypeScript, stack React and Next.js.`
4. Confirm the app creates a search summary, prepares a plan, asks for confirmation, and runs search only after explicit confirmation.

## Boundaries

Render deployment must not add persistence, accounts, auth, LinkedIn login/scraping, candidate messaging, account actions, or autonomous execution.
