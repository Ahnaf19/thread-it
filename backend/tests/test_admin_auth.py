async def test_login_valid_returns_token(client, admin_password):
    resp = await client.post(
        "/admin/login", json={"username": "owner", "password": admin_password}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_login_wrong_password_is_401(client, admin_password):
    resp = await client.post("/admin/login", json={"username": "owner", "password": "nope"})
    assert resp.status_code == 401


async def test_login_unknown_user_is_401(client, admin_password):
    resp = await client.post(
        "/admin/login", json={"username": "intruder", "password": admin_password}
    )
    assert resp.status_code == 401


async def test_protected_route_requires_token(client, admin_password):
    # No Authorization header → 401
    resp = await client.post("/admin/products", json={})
    assert resp.status_code == 401


async def test_protected_route_rejects_garbage_token(client, admin_password):
    resp = await client.post(
        "/admin/products", json={}, headers={"Authorization": "Bearer not-a-real-jwt"}
    )
    assert resp.status_code == 401
