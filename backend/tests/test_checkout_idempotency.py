"""Idempotent checkout: a double-clicked / retried /checkout creates the Order once (ADR-0013).

The create side is the mirror of the IPN's exactly-once paid transition: the
Idempotency-Key + unique column serialize concurrent attempts so one purchase
intent yields one Order, never duplicates.
"""

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.crud import checkout as crud
from app.models import Order
from app.schemas.cart import CartItemIn
from app.schemas.checkout import CustomerIn
from tests.factories import create_product

CUSTOMER = {
    "name": "Guest Buyer",
    "email": "guest@example.com",
    "phone": "01700000000",
    "address": "12 Demo Rd",
    "city": "Dhaka",
    "postcode": "1207",
}


async def _count_orders(session) -> int:
    return await session.scalar(select(func.count()).select_from(Order))


async def test_duplicate_checkout_same_key_returns_one_order(client, db_session, fake_gateway):
    # Double-click: the same Idempotency-Key submitted twice must yield one Order and
    # the same order_number, not two pending Orders.
    await create_product(db_session, slug="linen-shirt", price=2450, variants=[("M", 5)])
    body = {"items": [{"slug": "linen-shirt", "size": "M", "quantity": 1}], "customer": CUSTOMER}
    headers = {"Idempotency-Key": "attempt-abc-123"}

    first = await client.post("/checkout", json=body, headers=headers)
    second = await client.post("/checkout", json=body, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["order_number"] == second.json()["order_number"]
    assert await _count_orders(db_session) == 1


async def test_checkout_without_key_creates_distinct_orders(client, db_session, fake_gateway):
    # Backward-compatible: no key → no dedup, each submit is its own Order (NULL keys
    # stay distinct in Postgres).
    await create_product(db_session, slug="tee", price=900, variants=[("M", 5)])
    body = {"items": [{"slug": "tee", "size": "M", "quantity": 1}], "customer": CUSTOMER}

    first = await client.post("/checkout", json=body)
    second = await client.post("/checkout", json=body)

    assert first.json()["order_number"] != second.json()["order_number"]
    assert await _count_orders(db_session) == 2


async def test_concurrent_checkout_same_key_creates_one_order(
    client, db_session, fake_gateway, postgres_url
):
    # The showcase: two simultaneous /checkout attempts with one key genuinely race on
    # independent transactions. The unique constraint serializes them — one INSERT wins,
    # the other re-fetches the winner. Exactly one Order, same number from both.
    await create_product(db_session, slug="rush", price=1000, variants=[("M", 5)])
    items = [CartItemIn(slug="rush", size="M", quantity=1)]
    customer = CustomerIn(**CUSTOMER)
    key = "attempt-race-1"

    engine = create_async_engine(postgres_url)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s1, maker() as s2:
        o1, o2 = await asyncio.gather(
            crud.create_pending_order(s1, items, customer, idempotency_key=key),
            crud.create_pending_order(s2, items, customer, idempotency_key=key),
        )
    await engine.dispose()

    assert o1.order_number == o2.order_number
    db_session.expire_all()
    assert await _count_orders(db_session) == 1
