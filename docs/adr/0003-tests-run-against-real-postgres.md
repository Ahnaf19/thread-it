# Tests run against real Postgres, not SQLite

Backend tests run against a **real Postgres** instance (provisioned per test session via
**testcontainers-python**, same mechanism locally and in CI), not SQLite. Each test runs
inside a transaction rolled back at teardown; migrations are applied once per session.

## Why

The obvious default is in-memory SQLite for speed. We reject it because the app relies on
Postgres-specific behavior (UUIDs, constraints, and — critically — **v2's per-size
row-level locking / `SELECT … FOR UPDATE`**, which SQLite cannot model at all). Testing on
SQLite now would mean rewriting the suite at v2. testcontainers gives identical Postgres
behavior in local dev and CI from one mechanism, avoiding config drift.

## Consequences

- Tests require a running Docker daemon (local) and Docker-in-CI (GitHub Actions provides it).
- The backend CI job gains a short container startup cost in exchange for prod-parity and a
  foundation v2's concurrency tests can build on directly.
- Alternative considered: GitHub Actions `services: postgres` + a local Docker/compose setup —
  lighter, but two configs to keep in sync; rejected in favor of single-mechanism parity.
