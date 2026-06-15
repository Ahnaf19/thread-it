"""Catalog queries — thin, testable functions over the ORM (ADR-0002)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product


async def list_products(
    session: AsyncSession, *, category: str | None = None
) -> list[Product]:
    """Active products, newest first, optionally filtered by category."""
    stmt = select(Product).where(Product.is_active.is_(True)).order_by(Product.created_at.desc())
    if category is not None:
        stmt = stmt.where(Product.category == category)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_active_product_by_slug(session: AsyncSession, slug: str) -> Product | None:
    """An active product by slug, or None (unknown or inactive)."""
    stmt = select(Product).where(Product.slug == slug, Product.is_active.is_(True))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
