# Per-IP rate limiting, hand-rolled and in-process

Public endpoints had no abuse ceiling: `/admin/login` could be brute-forced, and
`/checkout` / `/cart` could be scripted without bound. v3 hardens this.

**Decision:** a small hand-rolled **fixed-window counter**, in-process, applied as a
FastAPI dependency to the abuse-sensitive public endpoints — `/admin/login` (strictest,
the brute-force target), `/checkout`, and `/cart`. Each caller is keyed by
`scope:client-ip`; exceeding the per-minute cap returns **429 with `Retry-After`**.
Catalog reads (`GET /products`, `/products/{slug}`) are left lenient — they're cached by
the Next data layer and cheap.

The caller's IP is the first hop of **`X-Forwarded-For`** (Render terminates TLS and
proxies), falling back to the socket peer when there's no proxy.

## Considered Options

- **slowapi / the `limits` library** — the usual FastAPI choice. Rejected: it's a
  dependency (and ultimately Redis for anything shared) for what is, on a single free-tier
  Render instance, an in-memory counter. The repo deliberately hand-rolls thin utilities
  (`persistentStore`, `useResource`, the pricing module) rather than pull weight it doesn't
  need; a ~40-line limiter fits that ethos and stays fully testable.
- **Redis-backed counter** — correct for a multi-instance deploy. Deferred: there's one
  instance today. Named here so the upgrade path is explicit.
- **Sliding-window log** — smoother, but holds per-request timestamps. Rejected: a
  fixed-window counter is O(1) and the worst case (a 2x burst across a window boundary) is
  fine for blunting abuse, which is the goal — not precise metering.

## Consequences

- State is per-process and resets on Render's cold-start spin-down — acceptable for abuse
  control (a fresh process simply starts counting again).
- Behind a single trusted proxy, trusting the first `X-Forwarded-For` hop is correct; a
  client can't usefully spoof it (Render overwrites the chain). A multi-proxy setup would
  need a configured trusted-hop count.
- A module-level singleton holds the counts; tests reset it between cases (autouse fixture)
  so limits can't bleed across the suite, and the limiter takes an injectable clock so
  window-expiry is testable without real sleeps.
- Limits live as constants (`LOGIN/CHECKOUT/CART_PER_MINUTE`); `rate_limit_enabled` (default
  on) is the kill switch.
