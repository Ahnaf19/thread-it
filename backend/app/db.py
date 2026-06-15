"""Async database layer — engine, session, and the declarative base (ADR-0002)."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base all ORM models inherit from."""


# `future`/2.0 style engine over asyncpg. Created lazily-enough at import; tests
# override the session dependency to point at a throwaway Postgres (testcontainers).
engine = create_async_engine(settings.database_url_async or "postgresql+asyncpg://", echo=False)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async session."""
    async with SessionLocal() as session:
        yield session


# Reusable Annotated dependency (modern FastAPI style; avoids Depends-in-defaults).
SessionDep = Annotated[AsyncSession, Depends(get_session)]
