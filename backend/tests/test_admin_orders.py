from datetime import UTC, datetime, timedelta

from tests.factories import create_order


async def test_admin_orders_requires_auth(client):
    resp = await client.get("/admin/orders")
    assert resp.status_code == 401


async def test_admin_orders_newest_first_with_items(client, db_session, admin_headers):
    now = datetime.now(UTC)
    await create_order(
        db_session, order_number="TI-OLD", status="paid",
        created_at=now - timedelta(hours=2), items=[("Tee", "M", 1000, 2)],
    )
    await create_order(
        db_session, order_number="TI-NEW", status="pending",
        created_at=now - timedelta(hours=1), items=[("Cap", "One Size", 500, 1)],
    )

    data = (await client.get("/admin/orders", headers=admin_headers)).json()

    assert [o["order_number"] for o in data] == ["TI-NEW", "TI-OLD"]
    old = next(o for o in data if o["order_number"] == "TI-OLD")
    assert old["status"] == "paid"
    assert old["items"][0] == {
        "product_name": "Tee", "size": "M", "unit_price": 1000, "quantity": 2,
    }


async def test_admin_orders_status_filter(client, db_session, admin_headers):
    await create_order(db_session, order_number="TI-P", status="paid")
    await create_order(db_session, order_number="TI-X", status="pending")

    data = (await client.get("/admin/orders?status=paid", headers=admin_headers)).json()

    assert [o["order_number"] for o in data] == ["TI-P"]
