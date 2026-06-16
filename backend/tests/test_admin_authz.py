"""The admin authz boundary (ADR-0005): every /admin/* route except login rejects
anonymous and bad-token access with 401.

The route-introspecting test enumerates the live app's routes, so a future admin
endpoint that forgets the auth guard fails this test automatically — the boundary
is structural, not per-endpoint discipline.
"""

import re
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import settings
from app.main import app
from app.security import ALGORITHM


def _iter_api_routes(routes):
    """Flatten (path, methods), descending into included routers.

    This Starlette wraps included routers in `_IncludedRouter` (exposing the real
    APIRouter as `.original_router`) rather than flattening them into `app.routes`.
    """
    for route in routes:
        original = getattr(route, "original_router", None)
        if original is not None:
            yield from _iter_api_routes(original.routes)
            continue
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if path and methods:
            yield path, methods


def _protected_admin_routes() -> list[tuple[str, str]]:
    """(method, path) for every /admin route that should require auth (login excluded)."""
    routes: list[tuple[str, str]] = []
    for path, methods in _iter_api_routes(app.routes):
        if not path.startswith("/admin") or path == "/admin/login":
            continue
        for method in methods - {"HEAD", "OPTIONS"}:
            routes.append((method, path))
    return sorted(routes)


@pytest.mark.parametrize("method,path", _protected_admin_routes())
async def test_admin_route_rejects_anonymous(client, method, path):
    # Substitute any path params (e.g. {slug}) so routing matches; the auth guard
    # fires before body validation, so an empty body still yields 401, not 422.
    url = re.sub(r"\{[^}]+\}", "x", path)
    resp = await client.request(method, url, json={})
    assert resp.status_code == 401, f"{method} {path} did not 401 without a token"


async def test_admin_route_rejects_malformed_token(client):
    resp = await client.get("/admin/products", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


async def test_admin_route_rejects_expired_token(client, admin_password):
    expired = jwt.encode(
        {"sub": settings.admin_username, "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    resp = await client.get("/admin/products", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


async def test_admin_route_rejects_valid_signature_wrong_subject(client, admin_password):
    # A correctly-signed token whose subject isn't the admin must not pass — guards
    # against any future token minted for a non-admin (e.g. a customer in #44).
    forged = jwt.encode(
        {"sub": "not-the-admin", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    resp = await client.get("/admin/products", headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401


async def test_login_is_public(client, admin_password):
    # The one /admin route that must NOT require a token (chicken-and-egg).
    resp = await client.post(
        "/admin/login", json={"username": "owner", "password": admin_password}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]
