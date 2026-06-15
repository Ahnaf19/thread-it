# Product detail returns a true 404 by not streaming its segment

`/products/[slug]` is prerendered for known slugs (`generateStaticParams`) with
`dynamicParams` left at its default `true`, so products added through the admin
later still render on-demand. When a slug doesn't exist — never did, or the product
was removed/deactivated — `fetchProduct` returns `null` and the page calls
`notFound()`. The not-found page rendered correctly, but the HTTP status was **200,
not 404** (issue #34) — a *soft 404*. Crawlers, link-checkers, uptime monitors and
analytics key off the status code, so a dead URL read as a live, successful page.

The cause is a Next.js 16 streaming rule, not a logic bug. Once a response has begun
**streaming**, its `200` headers are already sent and the status can no longer change —
so a `notFound()` thrown mid-stream renders the not-found UI but keeps the `200`. (Next
does inject `<meta name="robots" content="noindex">`, which prevents *indexation* but
not the wrong status.) A `loading` skeleton is a Suspense fallback, and a Suspense
fallback is exactly what starts the stream. The loading-states feature (issue #31) is
what turned this into a soft 404 — and there is a **root** `app/loading.tsx`, so the
segment streams even if its own `loading.tsx` is removed.

**Decision:** make the product-detail response **non-streamed** so `notFound()` returns
a real `404` (the framework returns `404` for non-streamed responses, `200` for streamed
ones). Concretely, scope every loading boundary off `/products/[slug]`: move the home
route into a `(home)` route group that owns the grid skeleton, and remove both the root
and the `[slug]` `loading.tsx`, so the product-detail segment inherits no Suspense
fallback. `dynamicParams` stays `true` and `revalidate` stays `60`.

We accept losing the loading skeleton on the *first uncached render* of a product. In
steady state every detail page is static (prerendered or ISR-cached) and shows no
skeleton anyway; the skeleton only ever appeared on the first-ever view of a not-yet-
cached product. That marginal, cold-start-only cost (mitigated by the warm-up ping) buys
a correct status code for every dead URL with no new runtime infrastructure.

## Considered Options

- **`dynamicParams = false`** — unknown slugs 404 at the routing layer, before any render
  (the cleanest 404, immune to the streaming issue). Rejected: `generateStaticParams`
  only runs at build, so an admin-added product would 404 until a redeploy — the catalog
  grid would link to 404s, a worse bug than the soft 404, and it breaks the on-demand
  design.
- **Existence check in `proxy` (middleware)** — keep streaming *and* get a true 404 by
  checking the slug before the stream starts. Rejected: a per-request hop plus a fast
  slug-existence lookup for a single-shop, ~30-product catalog is the over-engineering the
  roadmap warns against. Revisit only if streamed loading on product detail becomes worth
  keeping.
- **Do nothing** — `noindex` already prevents indexation. Rejected: link-checkers, uptime
  monitors and analytics read the status code, not the meta tag; a 200 on a dead URL is
  still a defect.

## Consequences

- Product detail no longer streams; the first uncached render awaits the full server
  render before responding (cold-start latency surfaces there, mitigated by the warm-up
  ping). Prerendered/ISR-cached views are unaffected.
- Other routes keep their loading behaviour; this is a deliberate, documented exception
  for the one route that must express "not found" as an HTTP status.
- Streaming inheritance is subtle (a root `loading.tsx` cascades), so the fix is verified
  by **HTTP status**, not a unit test: `next build && next start`, then
  `curl -sI /products/ghost-slug` → `404` and a real slug → `200`.
