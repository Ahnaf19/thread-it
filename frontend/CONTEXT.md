# Frontend

The Thread It storefront and admin UI (Next.js App Router). Holds no domain rules —
the backend owns the model (see [backend](../backend/CONTEXT.md)). Its own language is
about how the UI *behaves while talking to that backend*: the states a fetched view
moves through, and how cold starts surface to the shopper.

## Language

### Fetch states

**Async resource**:
A view's data that is fetched from the backend at runtime in the browser — the priced
cart, the admin product list, the admin order list. Distinct from the **catalog**
(home + product detail), which is server-rendered and cached, never fetched client-side.
Only Async resources have a **Resource status**.
_Avoid_: data, request (reserve these for the mechanics; the resource is the view's data)

**Resource status**:
The single state an Async resource is in, from a fixed, mutually-exclusive set:
`idle → loading → ready | error`. Exactly one is shown at a time. The four together
are what issue #31 means by "loading / empty / error states."
_Avoid_: phase, mode

**Loading**:
A fetch is in flight and there is no data yet to show. Rendered as a shape-matched
**skeleton** (a grid of cards, a table of rows), not a spinner or bare text.
_Avoid_: pending, fetching, busy (reserve "busy" for an in-flight form submit, which is
not an Async resource)

**Ready**:
The fetch succeeded and returned data. The view shows that data — unless it is **Empty**.
_Avoid_: success, loaded, done

**Empty**:
A successful fetch (or a known-empty client state) that has nothing to show: no products,
no orders, an empty bag. A first-class outcome, **never** an **Error**. Note the bag's
empty state is *client* state (the cart lives in the browser), not a fetched result.
_Avoid_: no-data, blank (and never conflate Empty with Error)

**Error**:
The fetch failed — network, backend 5xx, or a **cold start** that timed out. Always
paired with a **Retry affordance**. The bug #31 fixes was admin views that swallowed
errors and sat on **Loading** forever, with no Error state at all.
_Avoid_: failure, broken

**Idle**:
A resource that is not being fetched because it has nothing to fetch yet — e.g. the cart
view before there is anything in the bag. Distinct from **Loading** (which is actively
waiting).

**Retry affordance**:
A control that re-runs a failed fetch in place, without a full page reload. The required
companion to every **Error** state on an Async resource.
_Avoid_: reload, refresh (those imply a full navigation; a retry is in-place)

### Catalog HTTP responses

**Soft 404**:
A response that shows the shopper the "not found" page but still replies with HTTP `200`.
Search tools, link-checkers, uptime monitors and analytics trust the status code over the
page text, so a dead URL reads as live. The defect issue #34 fixes for product detail.
_Avoid_: fake 404, false 404

**True 404**:
A not-found outcome that also carries the HTTP `404` status — what a missing product URL
should return.

**Streamed response**:
A response Next begins sending to the browser before the page has finished rendering; a
loading **skeleton** is what triggers it. Once it starts, the `200` is already committed
and the response can no longer become a **True 404** — the trade-off behind product
detail's status handling (ADR-0011).
_Avoid_: progressive response, partial response

### Cold start (shared with the deployment story)

**Cold start**:
The ~30–50s delay while the Render free-tier backend boots after idling. The dominant
real-world cause of slow **Loading** and timed-out **Error** states — the reason these
states matter for this app specifically rather than as generic polish.

**Warm-up ping**:
The cheap `/health` fetch fired on page load to wake the backend while the shopper reads,
mitigating (not removing) the **Cold start**. Lives in `warm-up-ping.tsx`.
_Avoid_: keep-alive, healthcheck (it is a one-shot warm-up, not a recurring probe)
