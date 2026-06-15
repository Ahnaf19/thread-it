"""Test harness: a real Postgres via testcontainers (ADR-0003).

The container is session-scoped (the slow part); each test gets a freshly
created+dropped schema for isolation, and an httpx client whose DB session is the
same one the test arranges data with.
"""

import bcrypt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.config import settings
from app.db import Base, get_session
from app.main import app


@pytest.fixture(scope="session")
def postgres_url() -> str:
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        yield pg.get_connection_url()


@pytest_asyncio.fixture
async def db_session(postgres_url):
    engine = create_async_engine(postgres_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    async def _override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def admin_password() -> str:
    """Configure a known admin and return the plaintext password."""
    pw = "s3cret-pw"
    settings.admin_username = "owner"
    settings.admin_password_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    settings.secret_key = "test-secret-key-at-least-32-bytes-long!"
    return pw


@pytest_asyncio.fixture
async def admin_headers(client, admin_password) -> dict[str, str]:
    """An Authorization header for the admin (logs in via the API)."""
    resp = await client.post("/admin/login", json={"username": "owner", "password": admin_password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
