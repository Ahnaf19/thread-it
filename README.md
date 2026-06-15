# Thread It

A single-shop apparel storefront — browse the collection, pick a size, add to
cart, check out, and pay via SSLCOMMERZ. A realistic full-stack, deployed,
transactional app built thin-slice-first.

See [docs/roadmap.md](docs/roadmap.md) for the versioned roadmap and scope.

## Monorepo layout

```
thread-it/
  backend/    # FastAPI + uv/ruff/pydantic/loguru — deployed to Render
  frontend/   # Next.js + Tailwind (+ shadcn) — deployed to Vercel
  docs/       # roadmap and design notes
  render.yaml # Render Blueprint for the backend
  .github/    # CI (ruff + pytest, path-filtered per subdir)
```

## Stack

- **Backend:** Python 3.12, FastAPI, uv, ruff, pydantic, loguru
- **Frontend:** Next.js 16 (App Router), React 19, Tailwind
- **Database:** PostgreSQL (Supabase)
- **Payments:** SSLCOMMERZ sandbox
- **Hosting:** Vercel (frontend) · Render (backend) · Supabase (DB) — all free tier

## Architecture notes

- **Separated frontend + backend** → cross-origin, so the API allowlists the
  frontend origin via CORS (`CORS_ORIGINS` env var).
- **Cold-start mitigation:** Render's free tier sleeps after ~15 min idle. The
  frontend pings `/health` on page load to warm it while the user reads the page.
  A mitigation, not a fix — production would use a paid always-on tier.
- **CI vs CD:** GitHub Actions runs CI only (ruff + pytest, lint + build). Vercel
  and Render own CD, auto-deploying on merge to `main`.

## Running locally

Backend — see [backend/README.md](backend/README.md):

```bash
cd backend && uv sync && uv run uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend && npm install && cp .env.example .env.local && npm run dev
```

## Future work (intentionally out of scope)

Per-size inventory race-condition handling, idempotent payment webhooks, an order
state machine, rate limiting, customer accounts, caching, and telemetry are
sequenced across later versions — see the roadmap. Explicitly **not** building:
a message broker, multi-vendor/marketplace, recommendations, or reviews — they'd
be over-engineering at single-shop scale.
