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
async def db_engine(postgres_url):
    """One engine over a freshly created+dropped schema, per test (isolation)."""
    engine = create_async_engine(postgres_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
def db_sessionmaker(db_engine):
    """A maker of *independent* sessions (own connection each) — for concurrency tests
    that need real simultaneous transactions, not the single shared `db_session`."""
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(db_sessionmaker):
    async with db_sessionmaker() as session:
        yield session


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


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear the process-wide rate limiter before each test so per-IP counts from
    one test (the shared httpx client looks like a single IP) can't trip limits in
    the next (ADR-0014)."""
    from app.rate_limit import limiter

    limiter.reset()
    yield


class FakeGateway:
    """Stand-in for SSLCOMMERZ — records the last init and returns a fixed URL."""

    def __init__(self):
        self.last_call: dict | None = None

    async def initiate_session(self, **kwargs) -> str:
        self.last_call = kwargs
        return "https://sandbox.example/gateway/redirect"


@pytest.fixture
def fake_gateway():
    """Override the SSLCOMMERZ gateway dependency with a fake."""
    from app.payments import get_gateway

    gateway = FakeGateway()
    app.dependency_overrides[get_gateway] = lambda: gateway
    yield gateway
    app.dependency_overrides.pop(get_gateway, None)
