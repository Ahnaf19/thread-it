# Per-size atomic stock decrement on the paid transition

The naive v1 decrement read each variant's stock and subtracted in app memory, so two
customers paying for the last unit of a size concurrently could both succeed — overselling
and driving stock negative. We make the decrement **correct under concurrency**: on the
`pending → paid` transition we lock the order's variant rows with `SELECT … FOR UPDATE`
(in a deterministic `id` order to avoid deadlock), check that **every** line still has
enough stock, and only then decrement them all — one transaction, all-or-nothing. Exactly
one concurrent buyer of the last unit wins; the rest take the **sold-out path**.

This decrement nests *inside* the order-row lock of ADR-0010 (#29): one transaction locks
the order row (exactly-once paid), then locks the variant rows (no oversell). READ
COMMITTED is sufficient — `FOR UPDATE` blocks the second buyer until the first commits,
then returns the freshly-committed stock, so the `stock >= qty` check sees reality.

## The sold-out path

The race loser has already paid, but its stock is gone, so the order **cannot be fulfilled**.
It transitions `pending → failed` (already a legal terminal) and **nothing is decremented**.
We deliberately do *not* add a new `sold_out` status or a `failure_reason` column: the
SSLCOMMERZ success redirect is only reached after a *valid payment*, so on the confirmation
page `failed` can only mean "sold out after paying." The success callback reflects this by
appending `&outcome=sold_out` to the redirect; the frontend shows a sold-out confirmation
instead of "order confirmed."

A real shop would auto-refund the loser; that is out of v2 scope (the sandbox has no capture
to reverse) and noted as manual.

## Data flow (two buyers, last unit)

```mermaid
sequenceDiagram
    participant A as Buyer A (paid)
    participant B as Buyer B (paid)
    participant DB as Postgres

    Note over A,B: both hold a pending order for size S (stock = 1)
    A->>DB: BEGIN; SELECT variant FOR UPDATE
    B->>DB: BEGIN; SELECT variant FOR UPDATE (blocks)
    A->>DB: stock 1 >= 1 ✓ → stock = 0; order = paid; COMMIT
    DB-->>B: lock released, returns stock = 0
    B->>DB: stock 0 >= 1 ✗ → order = failed (sold out); COMMIT
    Note over A,B: exactly one paid, stock = 0, never negative
```

## Considered Options

- **Conditional `UPDATE … WHERE stock >= qty` (rowcount check)** — the idiomatic atomic
  decrement, lock-minimal. Rejected as the primary: a multi-line order needs all-or-nothing,
  which forces partial-decrement rollback/compensation bookkeeping; `FOR UPDATE`
  check-then-act expresses all-or-nothing in one clean transaction.
- **New `OrderStatus.SOLD_OUT` terminal** — rejected: expands the enum, state machine, and
  admin filters for a state that is, to the customer, a failed order. The redirect param
  carries the nuance the confirmation page needs.
- **Public `GET /orders/{order_number}` status endpoint** — rejected: exposes order state by
  guessable `TI-` number for no gain over the gateway-validated redirect param.

## Consequences

- `failed` is now reached by two routes (payment declined → `/checkout/fail`; sold-out after
  payment → `/checkout/success?...&outcome=sold_out`). They are unambiguous *by which page is
  reached*, so no persisted reason is required.
- The concurrency guarantee is enforced by a row lock, exercised by a real-connection
  concurrent test (N buyers, 1 unit → one winner). It cannot be proven by the shared
  single-session test harness.
