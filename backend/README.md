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
uv run pytest -q   # spins a real Postgres via testcontainers (needs Docker, see ADR-0003)
```

## Database (migrations + seed)

Migrations are Alembic-managed (ADR-0002). `DATABASE_URL` must be set (Supabase
session-pooler string locally; Render env in prod).

```bash
uv run alembic upgrade head          # apply migrations
uv run alembic revision --autogenerate -m "msg"   # create a migration from model changes
uv run alembic check                 # fail if models drift from migrations
uv run python -m scripts.seed        # idempotent demo catalog (run once; not on deploy)
```

## Admin auth (single admin; ADR-0005)

Set in env (Render / local `.env`), never in the repo:
`ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` (bcrypt), `SECRET_KEY` (JWT signing, ≥32 bytes).

Generate the password hash:

```bash
uv run python -c "import bcrypt,getpass; print(bcrypt.hashpw(getpass.getpass().encode(), bcrypt.gensalt()).decode())"
```

`POST /admin/login` → `{access_token}` (JWT, ~12h); send it as `Authorization: Bearer <token>`
to the `/admin/*` product-management endpoints.

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
