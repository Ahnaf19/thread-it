from sqlalchemy import select

from app.crud.checkout import get_order_by_number
from app.models import Variant
from tests.factories import create_product

CUSTOMER = {
    "name": "Guest Buyer",
    "email": "guest@example.com",
    "phone": "01700000000",
    "address": "12 Demo Rd",
    "city": "Dhaka",
    "postcode": "1207",
}


async def test_checkout_creates_pending_order_and_returns_gateway_url(
    client, db_session, fake_gateway
):
    await create_product(db_session, slug="linen-shirt", name="Linen Shirt", price=2450,
                         variants=[("M", 5)])

    resp = await client.post(
        "/checkout",
        json={"items": [{"slug": "linen-shirt", "size": "M", "quantity": 2}], "customer": CUSTOMER},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["gateway_url"] == "https://sandbox.example/gateway/redirect"
    assert body["order_number"].startswith("TI-")
    # SSLCOMMERZ init was called with tran_id == order_number and the server-side total
    assert fake_gateway.last_call["order_number"] == body["order_number"]
    assert fake_gateway.last_call["total"] == 4900


async def _place(client, slug, size, qty):
    """Run a checkout for one line; return the response."""
    return await client.post(
        "/checkout",
        json={"items": [{"slug": slug, "size": size, "quantity": qty}], "customer": CUSTOMER},
    )


async def test_order_persisted_with_snapshot(client, db_session, fake_gateway):
    await create_product(db_session, slug="tee", name="Tee", price=1000, variants=[("M", 5)])
    num = (await _place(client, "tee", "M", 2)).json()["order_number"]

    order = await get_order_by_number(db_session, num)
    assert order.status == "pending"
    assert order.total == 2000
    assert len(order.items) == 1
    it = order.items[0]
    assert (it.product_name, it.size, it.unit_price, it.quantity) == ("Tee", "M", 1000, 2)


async def test_checkout_over_stock_is_409_no_order(client, db_session, fake_gateway):
    await create_product(db_session, slug="rare", price=500, variants=[("M", 1)])
    resp = await _place(client, "rare", "M", 3)
    assert resp.status_code == 409
    assert resp.json()["items"][0]["status"] == "adjusted"


async def test_success_marks_paid_and_decrements(client, db_session, fake_gateway):
    await create_product(db_session, slug="cap", price=800, variants=[("One Size", 10)])
    num = (await _place(client, "cap", "One Size", 3)).json()["order_number"]

    r = await client.post(
        "/checkout/success", data={"tran_id": num, "status": "VALID", "amount": "2400"}
    )

    assert r.status_code == 303
    assert "/checkout/success" in r.headers["location"]
    order = await get_order_by_number(db_session, num)
    assert order.status == "paid"
    v = await db_session.scalar(select(Variant).where(Variant.size == "One Size"))
    assert v.stock == 7  # 10 - 3


async def test_duplicate_success_does_not_double_decrement(client, db_session, fake_gateway):
    await create_product(db_session, slug="belt", price=600, variants=[("One Size", 5)])
    num = (await _place(client, "belt", "One Size", 2)).json()["order_number"]

    for _ in range(2):
        await client.post(
            "/checkout/success", data={"tran_id": num, "status": "VALID", "amount": "1200"}
        )

    v = await db_session.scalar(select(Variant).where(Variant.size == "One Size"))
    assert v.stock == 3  # decremented once (5->3), guard prevents twice


async def test_duplicate_ipn_delivery_decrements_once(client, db_session, fake_gateway):
    # AC: the same IPN arriving twice produces a single pending→paid transition.
    await create_product(db_session, slug="sock", price=300, variants=[("One Size", 5)])
    num = (await _place(client, "sock", "One Size", 2)).json()["order_number"]

    for _ in range(2):
        await client.post("/checkout/ipn", data={"tran_id": num, "status": "VALID"})

    order = await get_order_by_number(db_session, num)
    assert order.status == "paid"
    v = await db_session.scalar(select(Variant).where(Variant.size == "One Size"))
    assert v.stock == 3  # decremented once


async def test_amount_mismatch_not_paid(client, db_session, fake_gateway):
    await create_product(db_session, slug="scarf", price=900, variants=[("One Size", 4)])
    num = (await _place(client, "scarf", "One Size", 1)).json()["order_number"]

    r = await client.post(
        "/checkout/success", data={"tran_id": num, "status": "VALID", "amount": "100"}
    )

    assert "/checkout/fail" in r.headers["location"]
    order = await get_order_by_number(db_session, num)
    assert order.status == "pending"


async def test_fail_callback_after_paid_is_ignored(client, db_session, fake_gateway):
    # The idempotency seam (ADR-0008): a late gateway callback on an already-resolved
    # order must be a silent no-op, never override the status or 500 back to the gateway.
    await create_product(db_session, slug="hat", price=700, variants=[("One Size", 5)])
    num = (await _place(client, "hat", "One Size", 1)).json()["order_number"]
    await client.post(
        "/checkout/success", data={"tran_id": num, "status": "VALID", "amount": "700"}
    )

    r = await client.post("/checkout/fail", data={"tran_id": num})

    assert r.status_code == 303
    order = await get_order_by_number(db_session, num)
    assert order.status == "paid"


async def test_cancel_sets_cancelled(client, db_session, fake_gateway):
    await create_product(db_session, slug="dress", price=3000, variants=[("S", 2)])
    num = (await _place(client, "dress", "S", 1)).json()["order_number"]

    r = await client.post("/checkout/cancel", data={"tran_id": num})

    assert r.status_code == 303
    order = await get_order_by_number(db_session, num)
    assert order.status == "cancelled"
