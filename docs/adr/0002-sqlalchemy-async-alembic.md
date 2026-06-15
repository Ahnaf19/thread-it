# Data access: SQLAlchemy 2.0 (async) + asyncpg + Alembic

The backend uses **SQLAlchemy 2.0 ORM in async mode** over the **asyncpg** driver, with
**Alembic** for migrations and **Pydantic** schemas kept separate from ORM models.
Query logic lives in a thin `crud`/service layer, not a full Repository abstraction.

## Why

- Async SQLAlchemy + asyncpg matches FastAPI's async model and the Supabase session-pooler
  connection (`postgresql+asyncpg://`). Alembic and Pydantic are already in the project stack.
- Separate Pydantic response schemas keep ORM models from leaking across the API boundary.

## Considered and rejected

- **SQLModel** (Pydantic + SQLAlchemy in one) — less boilerplate, but less mature for
  non-trivial queries and fiddlier Alembic integration; too much risk on the foundational layer.
- **Raw asyncpg / no ORM** — more control but hand-rolled migrations and row mapping;
  ORM + Alembic is the more productive, conventional fit at this scale.

## Consequences

- The `DATABASE_URL` (Supabase) is rewritten to the `postgresql+asyncpg://` scheme in config.
- A thin `crud` layer (not Repository) keeps query functions testable without ceremony.
