from tests.factories import create_product


async def test_price_cart_single_line(client, db_session):
    await create_product(
        db_session, slug="linen-shirt", name="Linen Shirt", price=2450,
        variants=[("M", 8)], images=[("https://img/1.jpg", "front", 0)],
    )

    resp = await client.post(
        "/cart", json={"items": [{"slug": "linen-shirt", "size": "M", "quantity": 2}]}
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["subtotal"] == 4900
    assert body["currency"] == "BDT"
    assert body["item_count"] == 2
    assert len(body["items"]) == 1
    line = body["items"][0]
    assert line["slug"] == "linen-shirt"
    assert line["name"] == "Linen Shirt"
    assert line["size"] == "M"
    assert line["unit_price"] == 2450
    assert line["quantity"] == 2
    assert line["line_total"] == 4900
    assert line["status"] == "ok"
    assert line["primary_image"] == {"url": "https://img/1.jpg", "alt": "front"}


async def test_price_empty_cart(client, db_session):
    resp = await client.post("/cart", json={"items": []})
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"items": [], "subtotal": 0, "currency": "BDT", "item_count": 0}


async def test_price_multiple_lines_sums_subtotal(client, db_session):
    await create_product(db_session, slug="tee", price=1000, variants=[("M", 5)])
    await create_product(db_session, slug="cap", price=500, variants=[("One Size", 5)])

    resp = await client.post("/cart", json={"items": [
        {"slug": "tee", "size": "M", "quantity": 2},
        {"slug": "cap", "size": "One Size", "quantity": 3},
    ]})

    body = resp.json()
    assert body["subtotal"] == 2 * 1000 + 3 * 500
    assert body["item_count"] == 5


async def test_quantity_clamped_to_stock_is_adjusted(client, db_session):
    await create_product(db_session, slug="scarf", price=800, variants=[("One Size", 2)])

    resp = await client.post("/cart", json={"items": [
        {"slug": "scarf", "size": "One Size", "quantity": 5},
    ]})

    line = resp.json()["items"][0]
    assert line["status"] == "adjusted"
    assert line["quantity"] == 2
    assert line["line_total"] == 1600
    assert resp.json()["subtotal"] == 1600


async def test_unavailable_lines_excluded_from_subtotal(client, db_session):
    await create_product(db_session, slug="live", price=1000, variants=[("M", 3)])
    await create_product(db_session, slug="sold-out", price=999, variants=[("M", 0)])
    await create_product(db_session, slug="hidden", price=999, is_active=False, variants=[("M", 5)])

    resp = await client.post("/cart", json={"items": [
        {"slug": "live", "size": "M", "quantity": 1},
        {"slug": "sold-out", "size": "M", "quantity": 1},      # stock 0
        {"slug": "hidden", "size": "M", "quantity": 1},        # inactive product
        {"slug": "ghost", "size": "M", "quantity": 1},         # unknown slug
        {"slug": "live", "size": "XXL", "quantity": 1},        # size not offered
    ]})

    body = resp.json()
    statuses = {(i["slug"], i["size"]): i["status"] for i in body["items"]}
    assert statuses[("live", "M")] == "ok"
    assert statuses[("sold-out", "M")] == "unavailable"
    assert statuses[("hidden", "M")] == "unavailable"
    assert statuses[("ghost", "M")] == "unavailable"
    assert statuses[("live", "XXL")] == "unavailable"
    assert body["subtotal"] == 1000   # only the one ok line
    assert body["item_count"] == 1


async def test_non_positive_quantity_rejected(client, db_session):
    resp = await client.post("/cart", json={"items": [
        {"slug": "x", "size": "M", "quantity": 0},
    ]})
    assert resp.status_code == 422
