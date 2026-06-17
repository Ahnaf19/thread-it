"""Input-validation pass on public endpoints (#42): malformed / out-of-bounds
input is rejected with 422 (or 422-class), never silently accepted or 500'd."""

CUSTOMER = {
    "name": "Guest Buyer",
    "email": "guest@example.com",
    "phone": "01700000000",
    "address": "12 Demo Rd",
    "city": "Dhaka",
    "postcode": "1207",
}


def _item(**over):
    return {"slug": "linen-shirt", "size": "M", "quantity": 1, **over}


# ---- /cart ----

async def test_cart_rejects_quantity_over_cap(client):
    resp = await client.post("/cart", json={"items": [_item(quantity=10**9)]})
    assert resp.status_code == 422


async def test_cart_rejects_zero_quantity(client):
    resp = await client.post("/cart", json={"items": [_item(quantity=0)]})
    assert resp.status_code == 422


async def test_cart_rejects_unknown_size(client):
    resp = await client.post("/cart", json={"items": [_item(size="BOGUS")]})
    assert resp.status_code == 422


async def test_cart_rejects_overlong_slug(client):
    resp = await client.post("/cart", json={"items": [_item(slug="x" * 1000)]})
    assert resp.status_code == 422


async def test_cart_rejects_too_many_lines(client):
    resp = await client.post("/cart", json={"items": [_item() for _ in range(101)]})
    assert resp.status_code == 422


# ---- /products?category= ----

async def test_products_rejects_unknown_category(client):
    resp = await client.get("/products", params={"category": "Nonsense"})
    assert resp.status_code == 422


async def test_products_accepts_known_category(client):
    resp = await client.get("/products", params={"category": "Tops"})
    assert resp.status_code == 200


# ---- /checkout customer ----

async def test_checkout_rejects_malformed_email(client):
    bad = {**CUSTOMER, "email": "not-an-email"}
    resp = await client.post("/checkout", json={"items": [_item()], "customer": bad})
    assert resp.status_code == 422


async def test_checkout_rejects_overlong_name(client):
    bad = {**CUSTOMER, "name": "n" * 1000}
    resp = await client.post("/checkout", json={"items": [_item()], "customer": bad})
    assert resp.status_code == 422


async def test_checkout_rejects_empty_items(client):
    resp = await client.post("/checkout", json={"items": [], "customer": CUSTOMER})
    assert resp.status_code == 422
