# Frontend async-state via one tested `useResource` hook

Client-fetched views (priced cart, admin product/order lists) each re-implemented
loading/error/empty with ad-hoc booleans, and `useAdminResource` collapsed "loading"
and "failed" into a single `data: T | null` — so a cold-start failure left admin pages
on "Loading…" forever with no error or retry (issue #31). We consolidated this behind
one hook, `useResource`, exposing an explicit `idle | loading | ready | error` status
plus `reload()`; `useAdminResource` composes it (adding the token guard and the
`401 → clear → redirect` path, which is deliberately *not* an error state). Pages derive
the **Empty** state by inspecting `ready` data, keeping the hook generic.

We hand-rolled the hook rather than adopt TanStack Query or SWR: only three surfaces
fetch client-side (the catalog is server-rendered and cached), and the repo's ethos is
thin, owned code (shadcn components, the hand-rolled `persistentStore`). A data library
would be more weight and lock-in than three fetches justify.

## Considered Options

- **TanStack Query / SWR** — out-of-the-box caching, retry, dedupe. Rejected: heavyweight
  for three surfaces; the storefront's read-caching already lives in Next's data cache.
- **Per-page booleans (status quo)** — rejected: it is exactly what produced the
  swallowed-error bug, and it can't be tested once.

## Consequences

- This is the **first frontend test infrastructure** — Vitest + React Testing Library,
  the setup the bundled Next 16 docs recommend. It is a deliberate, narrow exception to
  CLAUDE.md's "test the frontend lightly": we TDD the **logic** (`useResource`'s state
  machine, race-safety, retry, 401 handling) and leave the **presentational** shells
  (skeletons, empty/error copy) untested. Async Server Components aren't unit-testable
  anyway (per those docs), so the client hook is precisely the testable seam.
- New client-fetched views should use `useResource` rather than re-introducing booleans.
