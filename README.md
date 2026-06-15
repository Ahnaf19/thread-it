# Thread It

A single-shop apparel storefront — browse the collection, pick a size, add to
cart, check out, and **pay via SSLCOMMERZ** — built thin-slice-first as a real,
deployed, transactional full-stack app.

**Live demo**

- Storefront → **https://thread-it-nu.vercel.app**
- API + OpenAPI docs → **https://thread-it-api.onrender.com/docs**

> _Heads-up:_ the API is on Render's free tier, which sleeps after ~15 min idle —
> the first request may take ~30–50s to wake (the storefront fires a warm-up ping
> on load to hide it). See [docs/roadmap.md](docs/roadmap.md) for the full plan.

## v1 — what's shipped

A stranger can browse the catalog, add sized items to a cart, check out, pay in
the SSLCOMMERZ sandbox, and the order is recorded — and the shop owner can manage
the catalog and see orders. All on real URLs, behind a green CI pipeline.

- **Catalog** — product grid + detail with per-size stock ("Only N left", sold-out states)
- **Cart** — client-side, server-priced; live subtotal
- **Checkout** — guest checkout → SSLCOMMERZ redirect → order recorded, stock decremented
- **Admin** — JWT login; add/edit products + per-size stock; order list

## Monorepo layout

```
thread-it/
  backend/      # FastAPI + uv/ruff/pydantic/SQLAlchemy/alembic — deployed to Render
  frontend/     # Next.js 16 + React 19 + Tailwind + shadcn — deployed to Vercel
  docs/         # roadmap, ADRs (docs/adr/), agent docs
  CONTEXT-MAP.md# domain glossary map (→ backend/CONTEXT.md)
  render.yaml   # Render Blueprint for the backend
  .github/      # CI — ruff+pytest (backend), lint+build (frontend), path-filtered
```

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2 (async/asyncpg), Alembic, pydantic, uv, ruff
- **Frontend:** Next.js 16 (App Router), React 19, Tailwind, shadcn/ui
- **Database:** PostgreSQL (Supabase)
- **Payments:** SSLCOMMERZ sandbox (redirect flow)
- **Hosting:** Vercel · Render · Supabase — all free tier

## Architecture notes

- **Separated frontend + backend → cross-origin.** The API allowlists the frontend
  origin via CORS (`CORS_ORIGINS`). The same cross-site constraint drives two design
  choices: the **cart lives client-side** (`localStorage`) and **admin auth is a JWT
  bearer token** — both avoid a cookie that would be a blocked third-party cookie
  (see [ADR-0004](docs/adr/0004-client-side-cart-stateless-pricing.md),
  [ADR-0005](docs/adr/0005-admin-auth-jwt-bearer-single-admin.md)).
- **Cold-start mitigation.** Render free sleeps after ~15 min idle; the frontend pings
  `/health` on load to warm it. A mitigation, not a fix — production would use a paid
  always-on tier.
- **Caching for resilience.** Product pages are ISR (prerendered + revalidated) and
  catalog reads use Next's data cache, so the storefront serves from the CDN rather than
  hitting a function + the backend on every view. This was pulled forward from a later
  version after a live Vercel edge incident made the cost of per-request SSR obvious.
- **Money as whole-Taka integers** (no floats, no minor units — BDT has no practical
  sub-unit in retail; [ADR-0001](docs/adr/0001-money-as-whole-taka-integer.md)).
- **CI vs CD.** GitHub Actions runs CI only (ruff + pytest against a real Postgres via
  testcontainers; lint + build). Vercel and Render own CD, auto-deploying on merge to `main`.
- **Decisions** live in [docs/adr/](docs/adr/); domain language in
  [backend/CONTEXT.md](backend/CONTEXT.md).

## Known tradeoffs (free-tier, single-shop)

- **Backend region** is Render's Oregon — higher latency from Bangladesh. A paid tier
  would let us pick Singapore. Acceptable for a portfolio/demo.
- **Cold start** on the free backend (mitigated, not eliminated).
- **SSLCOMMERZ sandbox**, not live credentials (live needs business docs).
- **Single admin** via env credentials — no user table until accounts arrive.

## Running locally

Backend — see [backend/README.md](backend/README.md):

```bash
cd backend && uv sync && cp .env.example .env   # fill DATABASE_URL, admin + SSLCOMMERZ creds
uv run alembic upgrade head && uv run python -m scripts.seed
uv run uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend && npm install && cp .env.example .env.local && npm run dev
```

## Future work (intentionally out of scope, sequenced by version)

- **v2 — correctness:** concurrency-safe per-size stock decrement (row-level locking),
  idempotent SSLCOMMERZ IPN, a hardened order state machine. _(The pricing module and the
  `pending→paid` status guard are the groundwork already in place.)_
- **v3 — hardening & accounts:** rate limiting, input-validation pass, idempotent checkout,
  optional customer accounts + order history, structured logging.
- **v4 — performance & observability:** broader caching, a metrics view, query/indexing pass.
- **Explicitly not building:** a message broker, multi-vendor/marketplace, recommendations,
  or reviews — over-engineering at single-shop scale. Naming the non-goals is the point.
