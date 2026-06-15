"""Stateless cart pricing (ADR-0004) — a thin projection over the pricing module."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.pricing import resolve_lines, to_priced_cart
from app.schemas.cart import CartItemIn, PricedCart


async def price_cart(session: AsyncSession, items: list[CartItemIn]) -> PricedCart:
    return to_priced_cart(await resolve_lines(session, items))
