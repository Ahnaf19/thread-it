"""Checkout + order fulfillment logic (ADR-0006). Naive decrement; v2 hardens it."""

import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.cart import price_cart
from app.crud.catalog import get_active_product_by_slug
from app.enums import OrderStatus
from app.models import Order, OrderItem, Variant
from app.schemas.cart import CartItemIn, LineStatus, PricedCart
from app.schemas.checkout import CustomerIn


class CartChangedError(Exception):
    """Raised at checkout when the cart can't be fulfilled exactly as submitted."""

    def __init__(self, priced: PricedCart):
        self.priced = priced


def _order_number() -> str:
    return f"TI-{secrets.token_hex(4).upper()}"


async def get_order_by_number(session: AsyncSession, order_number: str) -> Order | None:
    return await session.scalar(select(Order).where(Order.order_number == order_number))


async def list_orders(session: AsyncSession, *, status: str | None = None) -> list[Order]:
    """Orders newest-first, optionally filtered by status (admin)."""
    stmt = select(Order).order_by(Order.created_at.desc())
    if status is not None:
        stmt = stmt.where(Order.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_pending_order(
    session: AsyncSession, items: list[CartItemIn], customer: CustomerIn
) -> Order:
    priced = await price_cart(session, items)
    # Fulfillable only if every line is exactly available (no adjust/unavailable).
    if not priced.items or any(ln.status != LineStatus.OK for ln in priced.items):
        raise CartChangedError(priced)

    order_items: list[OrderItem] = []
    for line in priced.items:
        product = await get_active_product_by_slug(session, line.slug)
        variant = next(v for v in product.variants if v.size == line.size)
        order_items.append(
            OrderItem(
                variant_id=variant.id,
                product_name=line.name,
                size=line.size,
                unit_price=line.unit_price,
                quantity=line.quantity,
            )
        )

    order = Order(
        order_number=_order_number(),
        status=OrderStatus.PENDING.value,
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        city=customer.city,
        postcode=customer.postcode,
        total=priced.subtotal,
        items=order_items,
    )
    session.add(order)
    await session.commit()
    created = await get_order_by_number(session, order.order_number)
    assert created is not None
    return created


async def mark_order_paid(session: AsyncSession, order_number: str) -> Order | None:
    """Flip pending→paid and decrement stock (naive). Guarded: a no-op if not pending."""
    order = await get_order_by_number(session, order_number)
    if order is None or order.status != OrderStatus.PENDING.value:
        return order
    order.status = OrderStatus.PAID.value
    for item in order.items:
        if item.variant_id is not None:
            variant = await session.get(Variant, item.variant_id)
            if variant is not None:
                variant.stock = variant.stock - item.quantity
    await session.commit()
    return order


async def mark_order_status(
    session: AsyncSession, order_number: str, status: OrderStatus
) -> Order | None:
    order = await get_order_by_number(session, order_number)
    if order is None or order.status != OrderStatus.PENDING.value:
        return order
    order.status = status.value
    await session.commit()
    return order
