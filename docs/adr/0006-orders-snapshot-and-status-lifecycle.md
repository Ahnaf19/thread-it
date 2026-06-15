# Orders snapshot their line items and move through a status lifecycle

An `Order` is created in **`pending`** status at checkout (before the payment
redirect) and transitions to **`paid`** on a successful SSLCOMMERZ callback, or
**`failed`/`cancelled`** otherwise. Each `OrderItem` **snapshots** the product name,
size, unit price, and quantity at checkout time, alongside a `variant_id` reference
used only for the stock decrement.

## Why

- **Snapshotting** keeps order history correct and immutable even if a product is later
  renamed, repriced, or unpublished — an order must reflect what was bought, not the
  current catalog.
- A **pending order created before redirect** means every payment attempt has a server
  record to reconcile against when the gateway calls back (and is the foundation v2's
  full state machine builds on).
- The **`variant_id`** ref is kept so payment success can decrement the right stock.

## v1 vs v2 (deliberate)

- v1 decrement is **naive** (plain subtract, no row locking) — the concurrency-safe
  atomic decrement is v2's headline.
- The `pending → paid` transition is **guarded by current status** so a duplicate
  callback (browser `success` + server `ipn`) can't double-decrement. This is a minimal
  guard, not full idempotency — exactly-once IPN handling is v2.
