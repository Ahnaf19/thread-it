# Idempotent `pending → paid` via `SELECT … FOR UPDATE`

The `pending → paid` transition (and its stock decrement) runs inside **one
transaction that locks the order row**: `SELECT … FOR UPDATE` the order, check
`status == pending`, transition + decrement, `COMMIT`. A duplicate, concurrent, or
out-of-order callback is a clean **no-op** — never an error, never a double
decrement, never a double fulfillment.

```mermaid
sequenceDiagram
    participant R as Browser return
    participant I as IPN (duplicate)
    participant DB as Postgres (order row)
    R->>DB: BEGIN; SELECT … FOR UPDATE (locks row)
    I->>DB: BEGIN; SELECT … FOR UPDATE (blocks — waits for lock)
    R->>DB: status==pending → paid + decrement stock
    R->>DB: COMMIT (lock released)
    DB-->>I: lock acquired; re-read row → status==paid
    I->>DB: status != pending → no-op
    I->>DB: COMMIT (no change)
```

This realizes the seam left by ADR-0008: that ADR's pending-status guard made
*sequential* re-application safe; this ADR makes it **exactly-once under
concurrency**.

## Why

- **`FOR UPDATE` serializes the racing deliveries on the order row.** SSLCOMMERZ can
  deliver the IPN more than once, and the browser-return handler
  (`/checkout/success`) and the server IPN (`/checkout/ipn`) both drive the same
  transition — so two transactions can race on one order. The row lock makes the
  second wait, then observe the committed `paid` status and no-op.
- **READ COMMITTED (Postgres default) is enough.** When a `FOR UPDATE` waiter
  acquires the lock, it re-reads the latest committed row — so the second txn sees
  `paid`. No need for SERIALIZABLE / REPEATABLE READ (which would surface
  serialization failures to retry instead).
- **`populate_existing=True` on the locked fetch is load-bearing.**
  `/checkout/success` loads the order (unlocked, for amount validation) *before*
  calling `mark_order_paid`, so the row is already in the session's identity map.
  By default SQLAlchemy would return that cached `pending` instance from the locked
  `SELECT` without refreshing — defeating the guard. `populate_existing` forces the
  attributes to reflect the locked read.

## Alternatives considered

- **Conditional `UPDATE orders SET status='paid' WHERE … AND status='pending'`,
  branch on rowcount.** Atomic for the flip and lock-free to write, but the winning
  txn still must hold the row to make the *decrement* exactly-once, and the
  read-modify-write reads less clearly than load → check → mutate. Rejected for
  legibility; FOR UPDATE is the showcase mechanism.
- **Dedup / processed-events table keyed by gateway transaction id.** The general
  webhook-idempotency pattern, but over-built for a single gateway and one
  transition. The order row *is* our idempotency key here.
- **SERIALIZABLE isolation.** Correct but pushes retry-on-serialization-failure onto
  the caller for no benefit over a targeted row lock.

## Scope

- **In:** order-row locking + the exactly-once `pending → paid` gate inside
  `mark_order_paid`; concurrency + duplicate-delivery tests. For consistency, the
  other transition paths (`mark_order_status` for fail/cancel, `transition_order`
  for the admin PATCH) lock the same row too — so a fail/cancel callback or admin
  action racing a `paid` IPN observes the committed status instead of overwriting it
  from a stale read.
- **Out / deliberately untouched:** the stock-decrement loop internals — the
  concurrency-safe **per-size** atomic decrement and sold-out path is #30, which
  layers variant-row locking on top of this order-row lock. To stay deadlock-free,
  #30 must keep a consistent lock order (order row first, then variants by id).
