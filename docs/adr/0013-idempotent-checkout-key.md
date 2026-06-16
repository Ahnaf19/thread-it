# Idempotent checkout via a client-supplied Idempotency-Key

`POST /checkout` creates a `pending` Order and starts an SSLCOMMERZ session. The
handler minted a fresh `order_number` on every call, so a double-clicked "Pay" button —
or a client retry after a dropped response — created **two pending Orders and two gateway
sessions** for one purchase intent. (Stock was never double-decremented: that happens on
`pending→paid`, already exactly-once via [ADR-0010](0010-idempotent-pending-to-paid-row-lock.md).
The defect is duplicate *Orders*, not a double charge of stock.)

**Decision:** the client sends an `Idempotency-Key` header — a UUID it generates once per
checkout attempt and resends on retry. Orders carry a nullable, `unique` `idempotency_key`
column. On checkout: if an Order already exists for the key, return it; otherwise create it
with the key. Two concurrent requests with the same key race on the unique constraint — one
INSERT wins, the other catches the `IntegrityError`, re-fetches, and returns the winner's
Order. NULL keys stay distinct in Postgres, so a flow that sends no key behaves exactly as
before (no dedup) — the contract is backward-compatible.

No double charge is then guaranteed by composition: one Order per intent, and the
`pending→paid` transition is itself exactly-once (ADR-0010) — so even if two gateway sessions
exist for one `tran_id`, payment applies once.

## Considered Options

- **Cart-content hash as the key** — dedupe Orders with the same (items + customer) hash.
  Rejected: it collides on a legitimate intentional re-order, and a trivially different cart
  dodges it. The key should identify the *attempt*, not the contents.
- **Reuse the latest pending Order for the customer** — no client change. Rejected: ambiguous
  (which pending Order? for how long?) and couples dedup to a customer identity we don't model
  for guests.
- **No key (status quo)** — rejected: that is the defect.

## Consequences

- New nullable `unique` column `orders.idempotency_key` (Alembic migration; applied manually,
  consistent with the current deploy flow).
- The frontend generates and persists a key per checkout attempt and sends it as
  `Idempotency-Key`; without it the endpoint still works (no dedup).
- A duplicate request re-initiates a gateway session for the *same* `order_number`. Reusing a
  key after the Order has left `pending` is outside the realistic double-click/retry window
  (the client mints a fresh key per attempt) and is not specially handled.
- Showcase test: concurrent + duplicate `/checkout` with one key → exactly one Order (modelled
  on ADR-0010's IPN test).
