"""Checkout + order fulfillment logic (ADR-0006). Naive decrement; v2 hardens it."""

import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.pricing import resolve_lines, to_priced_cart
from app.enums import OrderStatus
from app.models import Order, OrderItem, Variant
from app.order_state import assert_transition
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
    resolved = await resolve_lines(session, items)
    # Fulfillable only if every line is exactly available (no adjust/unavailable).
    if not resolved or any(line.status != LineStatus.OK for line in resolved):
        raise CartChangedError(to_priced_cart(resolved))

    # No re-resolve: ResolvedLine already carries the Variant + snapshot data.
    order_items = [
        OrderItem(
            variant_id=line.variant.id,
            product_name=line.name,
            size=line.size,
            unit_price=line.unit_price,
            quantity=line.effective_qty,
        )
        for line in resolved
    ]

    order = Order(
        order_number=_order_number(),
        status=OrderStatus.PENDING.value,
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        city=customer.city,
        postcode=customer.postcode,
        total=sum(line.line_total for line in resolved),
        items=order_items,
    )
    session.add(order)
    await session.commit()
    created = await get_order_by_number(session, order.order_number)
    assert created is not None
    return created


async def mark_order_paid(session: AsyncSession, order_number: str) -> Order | None:
    """Flip pending→paid and decrement stock (naive). Guarded: a no-op if not pending.

    The pending-status guard is the idempotency seam (ADR-0008): a duplicate IPN or a
    stale callback on an already-resolved order returns unchanged rather than erroring.
    """
    order = await get_order_by_number(session, order_number)
    if order is None or order.status != OrderStatus.PENDING.value:
        return order
    assert_transition(OrderStatus.PENDING, OrderStatus.PAID)  # legality (always legal here)
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
    """Gateway fail/cancel path. Pending-guarded so a stale callback is a no-op."""
    order = await get_order_by_number(session, order_number)
    if order is None or order.status != OrderStatus.PENDING.value:
        return order
    assert_transition(OrderStatus.PENDING, status)
    order.status = status.value
    await session.commit()
    return order


async def transition_order(
    session: AsyncSession, order_number: str, target: OrderStatus
) -> Order | None:
    """Apply an arbitrary status transition (admin path), enforcing legality.

    Raises IllegalTransition on a move outside the state machine. Re-applying the
    current status is an idempotent no-op. Returns None if the order doesn't exist.
    """
    order = await get_order_by_number(session, order_number)
    if order is None:
        return None
    assert_transition(OrderStatus(order.status), target)
    if order.status != target.value:
        order.status = target.value
        await session.commit()
    return order
