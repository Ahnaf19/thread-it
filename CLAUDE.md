# Thread It — Project Context

A single-shop apparel storefront proving a full-stack, deployed, transactional
app. Built thin-slice-first: every version is a complete, deployed, demoable
milestone. The full plan lives in [docs/roadmap.md](docs/roadmap.md) — treat it
as the spec/backlog.

## Working principles (from the roadmap)

- **Get v1 live before deepening.** Deploy while the app is simplest; correctness
  (concurrency, idempotency) is v2's headline, not v1's.
- **TDD the backend logic** (cart totals, stock rules, order state machine, IPN
  handler) test-first with pytest. Test the frontend lightly — don't force TDD on UI.
- **A version is done only when its tests pass in CI.**
- Keep process lightweight; don't over-build the app or the process.

## Monorepo

```
backend/    FastAPI + uv/ruff/pydantic/loguru. Deployed to Render (render.yaml).
frontend/   Next.js 16 App Router + React 19 + Tailwind. Deployed to Vercel.
docs/       roadmap.md (the spec).
.github/    CI — ruff+pytest (backend) and lint+build (frontend), path-filtered.
```

Each deploy target watches only its own subdir (Render rootDir+buildFilter,
Vercel root dir, CI path filters) so a one-side change doesn't trigger the other.

### Backend (`backend/`)

- Python 3.12, managed with **uv**. `uv sync`, `uv run <cmd>`.
- Checks: `uv run ruff check .` and `uv run pytest -q`.
- App: `app/main.py` (FastAPI + CORS + `/health`), `app/config.py` (env settings).
- `/health` is the cold-start warm-up ping target — keep it cheap (no DB).
- Run: `uv run uvicorn app.main:app --reload`.

### Frontend (`frontend/`)

- **Next.js 16 / React 19 — newer than training data.** Read the bundled docs in
  `frontend/node_modules/next/dist/docs/` before writing Next-specific code; see
  `frontend/AGENTS.md`.
- Backend URL via `NEXT_PUBLIC_API_URL` (`src/lib/api.ts`).
- The warm-up ping lives in `src/components/backend-status.tsx`.

## Conventions

- **Secrets** live in each platform's env settings (Render, Vercel, Supabase),
  never in the repo. `.env` files are gitignored; `.env.example` files document keys.
- **CI = GitHub Actions; CD = Vercel/Render auto-deploy on merge to `main`.** Don't
  hand-roll deploys in Actions.
- **Branches:** `main` + short-lived `feature/*` branches → PR → CI → merge.
- **Currency:** Taka (৳). **Design:** editorial-bold, off-white `#FAFAF8` / ink
  `#1A1A1A`, lime accent used sparingly (primary CTA, NEW tags, cart badge).

## Agent skills

This repo uses the [mattpocock/skills](https://github.com/mattpocock/skills) engineering
skills (installed under `.agents/skills/`, linked into `.claude/skills/`).

### Issue tracker

Issues and PRDs live as **GitHub issues** in `Ahnaf19/thread-it`, managed via the `gh`
CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles map to their default label names (`needs-triage`,
`needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See
`docs/agents/triage-labels.md`.

### Domain docs

**Multi-context** (monorepo): a root `CONTEXT-MAP.md` points at per-context `CONTEXT.md`
files under `backend/` and `frontend/`, with `docs/adr/` for decisions. These are created
lazily by `/grill-with-docs`. See `docs/agents/domain.md`.
