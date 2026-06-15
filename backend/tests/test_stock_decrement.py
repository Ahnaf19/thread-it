"""Concurrency-safe per-size stock decrement + the sold-out path (#30, ADR-0011).

The headline is the concurrent race: N buyers paying for the last unit of a size at
once → exactly one wins, the rest get a clean sold-out outcome, stock lands at 0 and
never goes negative. That needs real simultaneous transactions, so it races
`mark_order_paid` over independent sessions (own connection each) — not the shared
single `db_session`, which can't model concurrency.
"""

import asyncio

from sqlalchemy import select

from app.crud.checkout import get_order_by_number, mark_order_paid
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


async def _place(client, slug, size, qty):
    return await client.post(
        "/checkout",
        json={"items": [{"slug": slug, "size": size, "quantity": qty}], "customer": CUSTOMER},
    )


async def _pay(client, num, amount):
    return await client.post(
        "/checkout/success", data={"tran_id": num, "status": "VALID", "amount": amount}
    )


async def test_last_unit_decrements_once_then_sold_out(
    client, db_session, db_sessionmaker, fake_gateway
):
    await create_product(db_session, slug="last", price=1000, variants=[("S", 1)])
    n1 = (await _place(client, "last", "S", 1)).json()["order_number"]
    n2 = (await _place(client, "last", "S", 1)).json()["order_number"]

    await _pay(client, n1, "1000")
    await _pay(client, n2, "1000")

    async with db_sessionmaker() as s:
        o1 = await get_order_by_number(s, n1)
        o2 = await get_order_by_number(s, n2)
        v = await s.scalar(select(Variant).where(Variant.size == "S"))
    assert o1.status == "paid"
    assert o2.status == "failed"  # sold-out path, not a corrupt order
    assert v.stock == 0  # decremented exactly once, never negative


async def test_concurrent_last_unit_exactly_one_winner(
    client, db_session, db_sessionmaker, fake_gateway
):
    await create_product(db_session, slug="hype", name="Hype Tee", price=1450, variants=[("S", 1)])
    n = 10
    nums = []
    for _ in range(n):
        nums.append((await _place(client, "hype", "S", 1)).json()["order_number"])

    async def pay(order_number):
        async with db_sessionmaker() as s:
            order = await mark_order_paid(s, order_number)
            return order.status

    statuses = await asyncio.gather(*[pay(num) for num in nums])

    assert statuses.count("paid") == 1
    assert statuses.count("failed") == n - 1
    async with db_sessionmaker() as s:
        v = await s.scalar(select(Variant).where(Variant.size == "S"))
    assert v.stock == 0  # exactly one decrement, never negative


async def test_multi_line_order_is_all_or_nothing(
    client, db_session, db_sessionmaker, fake_gateway
):
    # S has plenty, M has only one unit.
    await create_product(db_session, slug="combo", price=500, variants=[("S", 5), ("M", 1)])
    # A takes the single M; B (created while M still available) wants 1×S + 1×M.
    n_a = (await _place(client, "combo", "M", 1)).json()["order_number"]
    resp_b = await client.post(
        "/checkout",
        json={
            "items": [
                {"slug": "combo", "size": "S", "quantity": 1},
                {"slug": "combo", "size": "M", "quantity": 1},
            ],
            "customer": CUSTOMER,
        },
    )
    assert resp_b.status_code == 200
    n_b = resp_b.json()["order_number"]

    await _pay(client, n_a, "500")
    await _pay(client, n_b, "1000")

    async with db_sessionmaker() as s:
        o_a = await get_order_by_number(s, n_a)
        o_b = await get_order_by_number(s, n_b)
        s_stock = await s.scalar(select(Variant).where(Variant.size == "S"))
        m_stock = await s.scalar(select(Variant).where(Variant.size == "M"))
    assert o_a.status == "paid"
    assert o_b.status == "failed"
    assert m_stock.stock == 0
    assert s_stock.stock == 5  # untouched — B's S line was NOT decremented


async def test_success_callback_flags_sold_out_in_redirect(client, db_session, fake_gateway):
    await create_product(db_session, slug="solo", price=1000, variants=[("S", 1)])
    n1 = (await _place(client, "solo", "S", 1)).json()["order_number"]
    n2 = (await _place(client, "solo", "S", 1)).json()["order_number"]

    r1 = await _pay(client, n1, "1000")
    r2 = await _pay(client, n2, "1000")

    # Winner → plain confirmation; loser → sold-out flagged for the confirmation page.
    assert "/checkout/success" in r1.headers["location"]
    assert "outcome=sold_out" not in r1.headers["location"]
    assert "outcome=sold_out" in r2.headers["location"]
