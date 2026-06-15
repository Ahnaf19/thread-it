# Thread It — Backend

FastAPI service for the Thread It storefront. Managed with [uv](https://docs.astral.sh/uv/).

## Local development

```bash
cd backend
uv sync                 # create .venv and install deps
cp .env.example .env    # then edit as needed
uv run uvicorn app.main:app --reload   # http://localhost:8000
```

- API docs: http://localhost:8000/docs
- Health check / warm-up ping target: http://localhost:8000/health

## Checks (what CI runs)

```bash
uv run ruff check .
uv run pytest -q
```

## Layout

```
backend/
  app/
    main.py     # FastAPI app, CORS, /health
    config.py   # env-driven settings (pydantic-settings)
  tests/        # pytest + FastAPI TestClient
```

Deployed to Render (free tier) via the repo-root `render.yaml`. Secrets live in
Render's env settings, never in the repo.
