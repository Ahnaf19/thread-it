from datetime import UTC, datetime, timedelta

from tests.factories import create_product


async def test_list_returns_active_product(client, db_session):
    await create_product(db_session, slug="linen-shirt", name="Linen Shirt", variants=[("M", 3)])

    resp = await client.get("/products")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["slug"] == "linen-shirt"
    assert data[0]["name"] == "Linen Shirt"


async def test_list_excludes_inactive_products(client, db_session):
    await create_product(db_session, slug="live", is_active=True)
    await create_product(db_session, slug="draft", is_active=False)

    data = (await client.get("/products")).json()

    slugs = [p["slug"] for p in data]
    assert slugs == ["live"]


async def test_list_is_newest_first(client, db_session):
    now = datetime.now(UTC)
    await create_product(db_session, slug="older", created_at=now - timedelta(days=3))
    await create_product(db_session, slug="newer", created_at=now - timedelta(days=1))

    data = (await client.get("/products")).json()

    assert [p["slug"] for p in data] == ["newer", "older"]


async def test_summary_shape_and_in_stock(client, db_session):
    await create_product(
        db_session,
        slug="capsule-tee",
        name="Capsule Tee",
        price=950,
        category="Tops",
        variants=[("S", 0), ("M", 2)],
        images=[("https://img/tee-2.jpg", "back", 1), ("https://img/tee-1.jpg", "front", 0)],
    )
    await create_product(db_session, slug="sold-out", variants=[("M", 0), ("L", 0)])

    data = {p["slug"]: p for p in (await client.get("/products")).json()}

    tee = data["capsule-tee"]
    assert tee.keys() == {
        "slug", "name", "price", "currency", "category",
        "is_new", "primary_image", "in_stock",
    }
    assert tee["price"] == 950
    assert tee["currency"] == "BDT"
    assert tee["in_stock"] is True
    # primary image = lowest position
    assert tee["primary_image"] == {"url": "https://img/tee-1.jpg", "alt": "front"}
    assert data["sold-out"]["in_stock"] is False


async def test_is_new_derivation(client, db_session):
    now = datetime.now(UTC)
    await create_product(db_session, slug="fresh", created_at=now - timedelta(days=2))
    await create_product(db_session, slug="stale", created_at=now - timedelta(days=40))

    data = {p["slug"]: p for p in (await client.get("/products")).json()}

    assert data["fresh"]["is_new"] is True
    assert data["stale"]["is_new"] is False


async def test_category_filter(client, db_session):
    await create_product(db_session, slug="a-top", category="Tops")
    await create_product(db_session, slug="a-bag", category="Accessories")

    data = (await client.get("/products?category=Accessories")).json()

    assert [p["slug"] for p in data] == ["a-bag"]


async def test_detail_returns_full_product(client, db_session):
    await create_product(
        db_session,
        slug="wool-coat",
        name="Wool Coat",
        description="A heavy wool overcoat.",
        price=8900,
        category="Outerwear",
        variants=[("L", 0), ("S", 4), ("M", 2)],
        images=[("https://img/coat-b.jpg", "back", 1), ("https://img/coat-a.jpg", "front", 0)],
    )

    resp = await client.get("/products/wool-coat")

    assert resp.status_code == 200
    body = resp.json()
    assert body["slug"] == "wool-coat"
    assert body["description"] == "A heavy wool overcoat."
    # images ordered by position
    assert [i["position"] for i in body["images"]] == [0, 1]
    # variants ordered by size order (S, M, L) with stock
    assert body["variants"] == [
        {"size": "S", "stock": 4},
        {"size": "M", "stock": 2},
        {"size": "L", "stock": 0},
    ]


async def test_detail_unknown_slug_returns_404(client, db_session):
    resp = await client.get("/products/does-not-exist")
    assert resp.status_code == 404


async def test_detail_inactive_product_returns_404(client, db_session):
    await create_product(db_session, slug="hidden", is_active=False)
    resp = await client.get("/products/hidden")
    assert resp.status_code == 404
