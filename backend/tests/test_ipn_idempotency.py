"""Exactly-once pending→paid under concurrent / duplicate delivery (ADR-0010).

These tests open *independent* sessions on the same Postgres so the transactions
genuinely race the way the browser-return and IPN callbacks do in production.
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.crud import checkout as crud
from app.crud.checkout import get_order_by_number
from app.enums import OrderStatus
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


async def _checkout(client, slug, size, qty) -> str:
    """Place a real order (sets variant_id on the items) and return its number."""
    resp = await client.post(
        "/checkout",
        json={"items": [{"slug": slug, "size": size, "quantity": qty}], "customer": CUSTOMER},
    )
    return resp.json()["order_number"]


async def test_concurrent_paid_delivery_decrements_exactly_once(
    client, db_session, fake_gateway, postgres_url
):
    # The showcase: the browser-return and a duplicate IPN hit mark_order_paid at the
    # same time. The order-row lock must serialize them into a single transition.
    await create_product(db_session, slug="rush", price=1000, variants=[("M", 5)])
    num = await _checkout(client, "rush", "M", 2)

    engine = create_async_engine(postgres_url)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s1, maker() as s2:
        await asyncio.gather(crud.mark_order_paid(s1, num), crud.mark_order_paid(s2, num))
    await engine.dispose()

    db_session.expire_all()
    order = await get_order_by_number(db_session, num)
    assert order.status == "paid"
    v = await db_session.scalar(select(Variant).where(Variant.size == "M"))
    assert v.stock == 3  # 5 - 2, decremented exactly once


async def test_paid_after_stale_preload_does_not_double_decrement(
    client, db_session, fake_gateway, postgres_url
):
    # /checkout/success pre-loads the order (unlocked) before mark_order_paid. If an IPN
    # marks it paid in between, the locked re-read must NOT trust the stale `pending`
    # snapshot in the session's identity map (this is the populate_existing fix).
    await create_product(db_session, slug="belt", price=600, variants=[("One Size", 5)])
    num = await _checkout(client, "belt", "One Size", 2)

    engine = create_async_engine(postgres_url)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s_success, maker() as s_ipn:
        await get_order_by_number(s_success, num)  # stale pending snapshot
        await crud.mark_order_paid(s_ipn, num)  # IPN wins: paid + decrement
        await crud.mark_order_paid(s_success, num)  # must observe paid and no-op
    await engine.dispose()

    db_session.expire_all()
    v = await db_session.scalar(select(Variant).where(Variant.size == "One Size"))
    assert v.stock == 3  # decremented once, despite the stale preload


async def test_fail_callback_concurrent_with_paid_stays_consistent(
    client, db_session, fake_gateway, postgres_url
):
    # A `fail` callback racing a `paid` IPN must not overwrite a committed paid (with
    # the stock already gone). Whichever wins the order-row lock, status and stock stay
    # consistent: paid ⟺ decremented, failed ⟺ untouched. Never paid-status-lost.
    await create_product(db_session, slug="rng", price=1000, variants=[("M", 5)])
    num = await _checkout(client, "rng", "M", 2)

    engine = create_async_engine(postgres_url)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s_paid, maker() as s_fail:
        await asyncio.gather(
            crud.mark_order_paid(s_paid, num),
            crud.mark_order_status(s_fail, num, OrderStatus.FAILED),
        )
    await engine.dispose()

    db_session.expire_all()
    order = await get_order_by_number(db_session, num)
    v = await db_session.scalar(select(Variant).where(Variant.size == "M"))
    assert order.status in ("paid", "failed")
    assert v.stock == (3 if order.status == "paid" else 5)
