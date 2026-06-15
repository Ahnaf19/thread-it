# Thread It — Versioned Roadmap

`thread-it` — a single-shop apparel storefront built to prove you can ship and
deploy a full-stack, real-world transactional app — and to show a potential client
a working store on the gateway they'd actually use. (Repo and in-app brand both
"Thread It".)

**Guiding philosophy:** _thin slice live first, then deepen._ Every version is a
complete, deployed, demoable milestone. You can stop at any version and still
have something real to show. Nothing is a "stretch goal" dangling off an
unfinished core — each version IS the finished product at that depth.

**Hard constraints:** zero cost (free tiers only), realistic single-shop scope,
SSLCOMMERZ sandbox for payments.

---

## The Client Story

A small Dhaka-based apparel boutique — clothing and accessories — sells ~15–30
products. They currently take orders over WhatsApp/Facebook and lose track of
them. They need a real storefront: customers browse the collection, pick a size,
add to cart, check out, and pay via a gateway they recognize (SSLCOMMERZ); and the
owner needs a simple admin to manage products and stock (including per-size stock)
and see orders come in.

One shop. One owner. Real orders. No marketplace, no multi-vendor, no reviews
engine. This is the realistic freelance brief — and keeping it this tight is what
makes it shippable.

Note: apparel means **per-size stock** (a product has sizes, each with its own
count) — which makes the v2 inventory race-condition handling even more concrete
(two people buying the last size S).

---

## Locked Decisions

- **Scope shape:** single-tenant (one shop owner = you / the demo). Sidesteps all
  multi-tenant complexity.
- **Customer side:** guest checkout + optional account (guest keeps v1 lean;
  accounts can come in a later version).
- **Payments:** SSLCOMMERZ sandbox — free, self-serve registration, instant test
  credentials by email. Redirect-based flow + IPN listener.
- **Slicing:** thin slice live first, deepen each version.

### Stack

- **Backend:** Python + FastAPI. Libs: uv, ruff, pydantic, loguru, alembic.
- **Frontend:** Next.js / React.
- **Styling:** shadcn/ui + Tailwind (fastest path to "looks decent"; you own the
  component code).
- **Database:** PostgreSQL.
- **Repo structure:** monorepo, NOT submodules. Repo name `thread-it`. Two
  top-level dirs:
  ```
  thread-it/
    backend/      # FastAPI + uv/ruff/pydantic/loguru/alembic
    frontend/     # Next.js + shadcn/Tailwind
    CLAUDE.md     # root context, with backend/ and frontend/ sub-context
    README.md
  ```
  Splitting into two repos later is trivial if ever needed; un-submoduling is not.

### Hosting (all free tier, three providers)

- **Frontend → Vercel** (Hobby/free). Made by the Next.js team; static/edge, no
  cold-start penalty. Mark all secrets as "sensitive" in env settings.
- **Backend → Render** (free web service). Deploys from repo, supports Docker +
  background workers/cron (needed for v2 async order handling).
  - **Known limitation — cold start:** free web services spin down after ~15 min
    idle; the next request waits ~30-50s while the process boots. Only affects the
    backend (Vercel frontend is always instant).
  - **Mitigation (build in v1):** on frontend page load, fire a cheap `fetch` to
    the backend `/health` endpoint to warm it up while the user reads the page.
    A mitigation, not a fix — helps because there's usually a gap between landing
    and the first real action. Document honestly: "cold-start mitigated by warm-up
    ping; production would use a paid always-on tier."
- **Database → Supabase** (free Postgres tier; extras available if needed later).
  FastAPI on Render connects via the Supabase connection string.

### Consequences to design for from v1

- **CORS is now unavoidable** (separated frontend + backend = cross-origin). Use
  FastAPI's `CORSMiddleware`, allowlist the Vercel frontend origin. This is the
  exact thing the single-origin approaches would have dodged — now a real,
  worthwhile lesson.
- **Three deploy targets** in v1, not one. More deploy surface to learn = more of
  exactly the confidence-building you're after.
- **Secrets management** across three providers (SSLCOMMERZ store creds, Supabase
  connection string, etc.) — keep them in each platform's env settings, never in
  the repo.

### Monorepo deploy hygiene (configure during the hello-world step)

A naive monorepo setup over-triggers: a frontend-only push would needlessly
rebuild the backend (wasted build minutes, an avoidable cold-start reset) and vice
versa. Fix it by telling each of the three systems to care only about its own
subdirectory:

- **Render (backend):** set **Root Directory** = `backend/`, and set a **Build
  Filter** so deploys only fire on `backend/**` changes.
- **Vercel (frontend):** set **Root Directory** = `frontend/` (Next.js monorepo
  detection mostly handles the rest); use the **Ignored Build Step** lever if you
  need to force-skip when `frontend/` didn't change.
- **GitHub Actions (CI):** use **path filters** — `on: pull_request: paths:
['backend/**']` for the backend test job, a separate job with `['frontend/**']`
  for frontend. A frontend-only PR then runs only frontend checks, not the whole
  pytest suite.

Net result: touch frontend → only Vercel deploys; touch backend → only Render
deploys; touch both (e.g. an API contract change + its matching frontend call in
one PR) → both deploy, which is correct. The goal is killing _accidental_
cross-triggers, not legitimate ones. "Independent path-filtered deploys from a
monorepo" is a real, senior-flavored detail worth keeping for the deployment story.

### Design direction (locked)

- **Brand:** Thread It (shown in-app as the storefront name; repo is `thread-it`).
- **Concept:** editorial-bold. Near-monochrome base lets the clothing photos carry
  color; oversized type does the "bold" work, not lots of competing colors. Reads
  as a real fashion brand, not loud.
- **Base palette:** off-white background (~`#FAFAF8`), near-black ink (~`#1A1A1A`).
- **Accent (use sparingly):** acid chartreuse / lime — only on the primary CTA
  ("Add to bag"), NEW tags, cart badge, key links. Everything else neutral. One
  pop against neutral is the whole discipline.
- **Type:** big characterful display sans for headings (oversized product names /
  hero), quiet readable sans for body. Size contrast _is_ the boldness.
- **Layout:** image-dominant product grid, generous whitespace, minimal chrome.
- **Currency:** Taka (৳).
- **Build approach:** shadcn/ui components assembled into this layout (Card, Button,
  form inputs, table) — composing pre-styled pieces, not hand-writing CSS. Claude
  Design / mockups are for _direction only_; production components live in
  `frontend/` and go through the normal CI/deploy loop.
- **Design ↔ engineering link:** the "Only N left in size S" stock indicator on
  the product page is the visible surface of v2's race-condition handling — apparel
  has per-size stock, so the UI shows the per-size scarcity the backend must get
  right under concurrency (two people buying the last size S).
- **v1 screens (~8):** product list (home), product detail, cart, checkout,
  SSLCOMMERZ return pages (success/fail/cancel), admin login, admin product
  list/add/edit, admin order list. No more than this in v1.

---

## The Master List of "Good Stuff"

Everything worth building, parked here so nothing is forgotten. Each item is
tagged with the version that owns it. The point of the list is that we _capture_
ambition and then _sequence_ it — you're not cutting anything, you're ordering it.

### Core flow

- Product catalog: list + detail pages (products have sizes) — **v1**
- Cart (line items track product + size) — **v1**
- Checkout → SSLCOMMERZ sandbox → order created — **v1**
- Admin: add/edit products, manage per-size stock, view orders — **v1**
- Guest checkout — **v1**
- Optional customer accounts + order history — **v3**

### Senior touches (justified by the e-commerce domain)

- Inventory race-condition handling at the **per-size** level (row-level locking /
  atomic decrement on the size's stock) — **v2**
- Idempotent IPN/webhook-driven order fulfillment — **v2**
- Order state machine (pending → paid → fulfilled / failed) — **v2**
- Rate limiting + input validation pass on public endpoints — **v3**
- Structured logging — **v3**
- Telemetry + a minimal metrics view in admin — **v4**
- Caching on hot read paths (product catalog) — **v4**

### Polish & UX

- Fluid, responsive frontend — **threaded through every version**, not a phase
- Loading/empty/error states — **v2 onward**
- Admin order notifications (in-app first) — **v3**
- Email notifications (needs a verified domain — deferred, ~$1 cost) — **v5 / optional**

### Explicitly OUT of scope for now (name these in your README as future work —

naming them is itself a senior signal)

- Message broker (Kafka/RabbitMQ) — a background task is correct at this scale;
  a broker for ~4 orders would be the over-engineering tell to avoid
- Multi-vendor / marketplace
- Recommendations engine, reviews
- Full observability stack (tracing, dashboards beyond the minimal admin view)

---

## Version Roadmap

### v1 — Thin Slice, LIVE _(the seal-breaker)_

**Goal:** the entire flow works end-to-end and is _deployed to a real URL_. This
is the most important version — not because it's impressive, but because it puts
the scary deploy step first, while the app is simplest.

**Scope:**

- Product list + product detail pages
- Cart (can be session/cookie-based; no need for persistence sophistication yet)
- Checkout form → redirect to SSLCOMMERZ sandbox → return → order recorded
- Basic admin: log in, add/edit products, list orders
- Guest checkout only
- Inventory decrement can be _naive_ here (just subtract) — correctness is v2's
  headline, and that's fine; v1 is about proving the flow + deploy
- **Cold-start warm-up ping** from frontend on page load
- **CI pipeline + TDD from the first feature** (see Testing & CI section below)

**Definition of done:** a stranger can visit the URL, browse, add to cart, "pay"
in the sandbox, and the order shows up in your admin — all on the deployed app,
not localhost. **CI is green; backend logic was built test-first.**

**What you learn / prove:** deployment end-to-end, the SSLCOMMERZ redirect+IPN
basics, the full request lifecycle in production.

---

### v2 — Correctness & Reliability _(the senior-engineering headline)_

**Goal:** make the order pipeline _correct under concurrency and unreliable
networks_ — the stuff that separates a toy from a real store. This is your
strongest material (RailBook + Kafka-commit-boundary thinking), now domain-justified.

**Scope:**

- **Inventory race condition:** two customers, one unit left, both buy → handled
  correctly with row-level locking / atomic decrement + a clean "just sold out" path
- **Idempotent IPN handler:** SSLCOMMERZ (like any gateway) can deliver the
  notification more than once, or the customer may lose connectivity on return —
  the IPN listener must update the order reliably and exactly once
- **Order state machine:** pending-payment → paid → fulfilled / failed, with the
  pending state created _before_ the redirect and confirmed by the IPN
- Loading / empty / error states across the UI

**Definition of done:** you can demonstrate the race (e.g. a concurrent test like
RailBook's) and show the IPN is safe against duplicate delivery.

**What you learn / prove:** concurrency control and idempotency in a real payment
context — the most interview-legible part of the whole project.

---

### v3 — Hardening & Accounts

**Goal:** make it safe to point at the open internet and a little richer.

**Scope:**

- Rate limiting (per-IP) + thorough input validation on public endpoints
- Admin/customer authz boundary — customers can't reach admin routes
- Idempotent checkout (no double-charge on double-click)
- Structured logging
- Optional customer accounts + order history
- In-app admin notification of new orders

**Definition of done:** a basic security pass you could walk a reviewer through;
accounts work alongside guest checkout.

**What you learn / prove:** the real-traffic security surface you wanted hands-on
exposure to.

---

### v4 — Performance & Observability

**Goal:** show you can make it fast and see inside it.

**Scope:**

- Caching on hot read paths (product catalog, product detail)
- Telemetry + a minimal metrics/orders view in admin
- Query optimization / indexing pass

**Definition of done:** measurable before/after on a cached path; a basic metrics
view in admin.

---

### v5 — Optional / Real-World Extras

- Email notifications (requires a verified domain — ~$1, the one place a tiny cost
  unlocks a real feature _and_ the full SPF/DKIM deliverability lesson)
- Embeddable / multi-shop considerations (only if you ever want to go multi-tenant)
- SSLCOMMERZ live credentials (requires business docs — only relevant for a real
  client engagement, not the portfolio build)

---

## How to Work This

1. **Build v1 to "live" before touching v2.** Resist deepening early — the whole
   point of thin-slice is that deploy happens while it's simple.
2. **Let your own skills emerge from friction** (the mattpocock approach): the
   first time you do the deploy checklist, capture it; the first time you do the
   security pass in v3, capture that into a skill you understand.
3. **Each version is a git tag / a LinkedIn-able checkpoint.** "Shipped v1 of a
   store today" → "added concurrency-safe inventory in v2" tells a progression
   story, which is itself compelling.
4. **The README is a deliverable.** The "out of scope / future work" section is
   where you show scoping judgment — arguably as senior a signal as the code.

---

## Still Open (smaller decisions, resolve as you start v1)

- **Admin auth approach:** roll-your-own (FastAPI + JWT/session — you know this
  cold) vs Supabase Auth (since you're already on Supabase). For a single admin
  user in v1, simplest wins; Supabase Auth becomes more attractive in v3 when
  optional customer accounts arrive. Lean: roll-your-own for the single admin now,
  reconsider at v3.
- **Cart persistence:** session/cookie-based (leaner, fine for guest checkout) vs
  DB-backed. Lean cookie-based for v1.
- **Data model:** almost certainly just Postgres through every version — resist
  NoSQL entirely; caching (Redis or in-process) only enters at v4 where it's
  justified on hot read paths. Don't add it sooner.

## Testing, TDD & CI/CD

**Tests gate every milestone.** A version is not "done" until its tests pass in
CI. This is the objective definition of done for each version.

**TDD from v1 — where it fits:**

- **Backend logic & API behavior → TDD rigorously** (test-first): cart totals,
  stock decrement rules, validation, the order state machine, the IPN handler.
  This is where you learn TDD by practicing it, and where it's most natural.
- **Frontend → test more lightly:** a few component/integration tests, not
  test-first for every button. TDD-everywhere on UI is awkward and not how it's
  practiced. Don't force it.
- **Tools:** pytest + FastAPI `TestClient`/`httpx` for the backend. v2's
  concurrency and idempotency are the showcase tests (model: RailBook's
  concurrent race-condition test).

**CI (GitHub Actions) — what it does:**

- On every PR: run `ruff check` + `pytest`. Failing checks block the merge.
- v1: this exists and stays green, even with few tests. The _pipeline being real_
  is the v1 goal, not coverage.
- Later: branch protection (no merge to `main` if CI red), coverage reporting.

**CD — platform-native, on purpose:**

- Vercel (frontend) and Render (backend) **watch the repo and auto-deploy on merge
  to `main`**. They own the deploy: preview URLs, rollbacks, build caching, logs —
  all free, all out of the box.
- **GitHub Actions does NOT deploy.** Hand-rolling CD in Actions would re-implement
  what the platforms already do, and do it worse. So Actions = CI only; platforms
  = CD. This is correct for this stack, not a shortcut.
- **Later learning step (one tasteful piece):** wire ONE real Actions-driven deploy
  task — e.g. run Alembic migrations via Actions before Render deploys — so you've
  _done_ CD-in-Actions and understand it, without replacing the platform defaults.

**Branches — fewer than you think (you're solo):**

- v1: **`main` + short-lived feature branches.** Work on `feature/xyz` → PR →
  CI runs → merge → auto-deploy. This is a complete professional workflow.
- The real concept to learn isn't a `dev`/`staging` _branch_ — it's
  **preview/staging deploys**: Vercel gives every PR its own preview URL for free.
  That's how you "test before prod" without managing extra branches.
- The full main/dev/staging model solves a _team coordination_ problem you don't
  have yet. Add it only if/when you actually need it.

## Workflow & Process (how the roadmap drives development)

**Mental model — the roadmap is the spine:**

- The **roadmap doc** = your product backlog / spec (lives in the repo as
  `docs/ROADMAP.md`).
- Each **version (v1, v2…)** = an epic → a GitHub **Milestone**.
- Each **bullet under a version** = a feature → a GitHub **Issue**.
- The **loop below runs per FEATURE**, not per version. You don't PRD the whole
  project — you PRD one feature at a time, pulling from the current version.

**GitHub Issues / Kanban mapping:**

- **Milestones** = versions (v1, v2…). Assign each issue to its version's milestone.
- **Issues** = features (the bullets). Use `Closes #N` in PRs to auto-close.
- **Labels** = phase (`phase:grill`, `phase:plan`, `phase:execute`, `phase:qa`)
  and area (`backend`, `frontend`, `infra`).
- **Project board columns** = Backlog → In Progress → In Review → Done (Kanban).
- mattpocock's `to-issues` skill breaks a plan into grabbable issues — use it for
  "roadmap bullets → issues."

**The per-feature loop (where each phase layer lives):**

| Phase           | What it is                              | Tool / artifact                                                                           |
| --------------- | --------------------------------------- | ----------------------------------------------------------------------------------------- |
| **Request**     | Pick next bullet from current version   | Roadmap line → GitHub Issue                                                               |
| **PRD / spec**  | Grill the feature details before code   | `grill-me` / `grill-with-docs` → short spec, updates `CONTEXT.md`, ADR for real decisions |
| **Plan**        | Claude proposes _how_ (files, approach) | Claude Code plan mode + your review                                                       |
| **Execute**     | Build it, test-first for backend logic  | `tdd` skill → code on a feature branch                                                    |
| **QA / review** | Automated + manual                      | CI (ruff+pytest) green; `diagnose` for bugs; you review the diff                          |
| **Ship**        | Merge → auto-deploy → verify live       | PR `Closes #N`; git tag at version boundaries                                             |

**Keep the process lightweight — on purpose.** The grill _is_ the PRD at this
scale; don't write a 5-page doc for "add a product detail page." Heavyweight
process is for teams. Yours = the minimum that keeps you organized. If the process
becomes the work, you've over-built it — same failure mode as over-building the app.

## v1 Kickoff Checklist (prerequisites before/while building)

These have lead time or external dependencies — start them early so they're not
last-minute blockers:

1. **Create the monorepo** with `backend/` + `frontend/` + root CLAUDE.md +
   `docs/ROADMAP.md` (this doc, in the repo).
2. **Register the SSLCOMMERZ sandbox account** (instant test credentials by email)
   — do this early so the payment flow isn't blocked later.
3. **Create the Supabase project** and grab the Postgres connection string.
4. **Set up Vercel + Render accounts**, connected to the repo (let them own CD).
5. **Set up GitHub Project board** (Backlog/In Progress/In Review/Done) + create
   the **v1 Milestone** + seed it with one Issue per v1 bullet.
6. **Deploy a "hello world" through the full pipeline FIRST** — a trivial FastAPI
   endpoint on Render, a trivial Next.js page on Vercel calling it across CORS,
   talking to Supabase. Include a green GitHub Actions CI run (ruff + a trivial
   pytest). De-risk deployment + the pipeline on day one while there's nothing to
   debug but the plumbing. **This is the single most important step.**
