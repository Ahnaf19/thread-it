"""Checkout + order fulfillment logic (ADR-0006). Atomic per-size decrement: ADR-0012."""

import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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


async def get_order_by_idempotency_key(session: AsyncSession, key: str) -> Order | None:
    return await session.scalar(select(Order).where(Order.idempotency_key == key))


async def _lock_order(session: AsyncSession, order_number: str) -> Order | None:
    """Fetch the order under a row-level write lock (SELECT … FOR UPDATE).

    `populate_existing` refreshes any instance already in the session's identity map
    so its status reflects the *locked* read — without it, a caller that pre-loaded
    the order (e.g. /checkout/success validating the amount) would see a stale
    `pending` snapshot and wrongly re-apply the transition (ADR-0010).
    """
    return await session.scalar(
        select(Order)
        .where(Order.order_number == order_number)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


async def list_orders(session: AsyncSession, *, status: str | None = None) -> list[Order]:
    """Orders newest-first, optionally filtered by status (admin)."""
    stmt = select(Order).order_by(Order.created_at.desc())
    if status is not None:
        stmt = stmt.where(Order.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_pending_order(
    session: AsyncSession,
    items: list[CartItemIn],
    customer: CustomerIn,
    idempotency_key: str | None = None,
) -> Order:
    # Idempotent create (ADR-0013): one checkout intent → one Order. A key already on
    # file returns its Order; a concurrent first-time race is settled by the unique
    # constraint below. NULL keys (no header) skip dedup entirely.
    if idempotency_key is not None:
        existing = await get_order_by_idempotency_key(session, idempotency_key)
        if existing is not None:
            return existing

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
        idempotency_key=idempotency_key,
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
    try:
        await session.commit()
    except IntegrityError:
        # A concurrent request with the same key won the unique constraint; return its
        # Order rather than erroring (the loser of the create race — mirrors ADR-0010).
        await session.rollback()
        if idempotency_key is not None:
            existing = await get_order_by_idempotency_key(session, idempotency_key)
            if existing is not None:
                return existing
        raise
    created = await get_order_by_number(session, order.order_number)
    assert created is not None
    return created


async def _reserve_stock(session: AsyncSession, order: Order) -> bool:
    """Decrement stock for every line atomically, all-or-nothing (ADR-0012).

    Locks each needed Variant row ``FOR UPDATE`` one at a time in a deterministic id order,
    so any two concurrent orders that share variants acquire them in the same order and
    can't deadlock. Only if *every* line still has enough stock does it decrement them all;
    on any shortfall it returns ``False`` having changed nothing — the sold-out path. Under
    READ COMMITTED the lock makes a concurrent buyer wait and then read the freshly-committed
    stock, so stock can never go negative.
    """
    needed: dict[uuid.UUID, int] = {}
    for item in order.items:
        if item.variant_id is not None:
            needed[item.variant_id] = needed.get(item.variant_id, 0) + item.quantity

    locked: list[tuple[Variant, int]] = []
    for vid in sorted(needed):  # stable lock-acquisition order across transactions
        variant = await session.scalar(select(Variant).where(Variant.id == vid).with_for_update())
        if variant is None or variant.stock < needed[vid]:
            return False
        locked.append((variant, needed[vid]))

    for variant, qty in locked:
        variant.stock -= qty
    return True


async def mark_order_paid(session: AsyncSession, order_number: str) -> Order | None:
    """Flip pending→paid, decrementing stock atomically. Guarded: a no-op if not pending.

    Exactly-once under concurrency (ADR-0010): the order row is locked FOR UPDATE for the
    whole transaction, so a duplicate/concurrent/out-of-order callback blocks, then observes
    the committed status and returns unchanged — never double-applying. Nested inside that
    lock, the per-size stock decrement is concurrency-safe and all-or-nothing (ADR-0012): if
    a concurrent buyer took the last unit first, the order takes the sold-out path to `failed`
    rather than overselling.
    """
    order = await _lock_order(session, order_number)
    if order is None or order.status != OrderStatus.PENDING.value:
        return order
    if await _reserve_stock(session, order):
        assert_transition(OrderStatus.PENDING, OrderStatus.PAID)
        order.status = OrderStatus.PAID.value
    else:
        assert_transition(OrderStatus.PENDING, OrderStatus.FAILED)  # sold-out path
        order.status = OrderStatus.FAILED.value
    await session.commit()
    return order


async def mark_order_status(
    session: AsyncSession, order_number: str, status: OrderStatus
) -> Order | None:
    """Gateway fail/cancel path. Pending-guarded so a stale callback is a no-op.

    Locks the order row (ADR-0010) so a fail/cancel callback racing a `paid` IPN
    observes the committed status instead of overwriting it from a stale read.
    """
    order = await _lock_order(session, order_number)
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
    Locks the order row (ADR-0010) so the legality check runs against the committed
    status, not a stale read that races a concurrent gateway transition.
    """
    order = await _lock_order(session, order_number)
    if order is None:
        return None
    assert_transition(OrderStatus(order.status), target)
    if order.status != target.value:
        order.status = target.value
        await session.commit()
    return order
