from tests.factories import create_product


async def test_create_product_persists_and_appears_in_catalog(client, admin_headers):
    payload = {
        "name": "Test Jacket",
        "description": "warm",
        "price": 5000,
        "category": "Outerwear",
        "variants": [{"size": "M", "stock": 3}, {"size": "L", "stock": 0}],
        "images": [{"url": "https://img/j.jpg", "alt": "jacket", "position": 0}],
    }
    resp = await client.post("/admin/products", json=payload, headers=admin_headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["slug"] == "test-jacket"
    assert body["name"] == "Test Jacket"
    assert {v["size"]: v["stock"] for v in body["variants"]} == {"M": 3, "L": 0}

    listing = (await client.get("/products")).json()
    assert "test-jacket" in [p["slug"] for p in listing]


async def test_duplicate_name_gets_slug_suffix(client, admin_headers):
    payload = {"name": "Linen Shirt", "price": 1000, "category": "Tops",
               "variants": [{"size": "M", "stock": 1}]}
    r1 = await client.post("/admin/products", json=payload, headers=admin_headers)
    r2 = await client.post("/admin/products", json=payload, headers=admin_headers)
    assert r1.json()["slug"] == "linen-shirt"
    assert r2.json()["slug"] == "linen-shirt-2"


async def test_create_invalid_category_is_422(client, admin_headers):
    payload = {"name": "X", "price": 100, "category": "Sneakers",
               "variants": [{"size": "M", "stock": 1}]}
    resp = await client.post("/admin/products", json=payload, headers=admin_headers)
    assert resp.status_code == 422


async def test_create_requires_auth(client, admin_password):
    payload = {"name": "X", "price": 100, "category": "Tops",
               "variants": [{"size": "M", "stock": 1}]}
    resp = await client.post("/admin/products", json=payload)  # no token
    assert resp.status_code == 401


async def test_update_changes_stock(client, admin_headers, db_session):
    await create_product(db_session, slug="editable", variants=[("M", 1)])

    resp = await client.patch(
        "/admin/products/editable",
        json={"variants": [{"size": "M", "stock": 9}]},
        headers=admin_headers,
    )

    assert resp.status_code == 200
    assert {v["size"]: v["stock"] for v in resp.json()["variants"]} == {"M": 9}


async def test_update_unknown_slug_is_404(client, admin_headers):
    resp = await client.patch("/admin/products/ghost", json={"price": 1}, headers=admin_headers)
    assert resp.status_code == 404


async def test_admin_list_includes_inactive(client, admin_headers, db_session):
    await create_product(db_session, slug="live-one", is_active=True)
    await create_product(db_session, slug="draft-one", is_active=False)

    resp = await client.get("/admin/products", headers=admin_headers)

    assert resp.status_code == 200
    slugs = {p["slug"] for p in resp.json()}
    assert {"live-one", "draft-one"} <= slugs  # inactive shown (public catalog hides it)


async def test_admin_list_requires_auth(client):
    resp = await client.get("/admin/products")
    assert resp.status_code == 401
