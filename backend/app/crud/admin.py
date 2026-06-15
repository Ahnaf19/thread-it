"""Admin catalog mutations — create/update products with slug generation."""

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, ProductImage, Variant
from app.schemas.admin import ProductCreate, ProductUpdate


def slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return base or "product"


async def _unique_slug(session: AsyncSession, base: str) -> str:
    candidate, n = base, 1
    while await session.scalar(select(Product.id).where(Product.slug == candidate)) is not None:
        n += 1
        candidate = f"{base}-{n}"
    return candidate


async def get_product_by_slug(session: AsyncSession, slug: str) -> Product | None:
    """Fetch by slug regardless of active state (admin edits drafts too)."""
    return await session.scalar(select(Product).where(Product.slug == slug))


async def list_all_products(session: AsyncSession) -> list[Product]:
    """All products incl. inactive, newest first (admin list)."""
    result = await session.execute(select(Product).order_by(Product.created_at.desc()))
    return list(result.scalars().all())


async def create_product(session: AsyncSession, data: ProductCreate) -> Product:
    slug = await _unique_slug(session, slugify(data.name))
    product = Product(
        slug=slug,
        name=data.name,
        description=data.description,
        price=data.price,
        category=data.category.value,
        is_active=data.is_active,
        variants=[Variant(size=v.size.value, stock=v.stock) for v in data.variants],
        images=[
            ProductImage(url=i.url, alt_text=i.alt, position=i.position) for i in data.images
        ],
    )
    session.add(product)
    await session.commit()
    created = await get_product_by_slug(session, slug)
    assert created is not None  # just inserted
    return created


async def update_product(
    session: AsyncSession, slug: str, data: ProductUpdate
) -> Product | None:
    product = await get_product_by_slug(session, slug)
    if product is None:
        return None

    if data.name is not None:
        product.name = data.name
    if data.description is not None:
        product.description = data.description
    if data.price is not None:
        product.price = data.price
    if data.category is not None:
        product.category = data.category.value
    if data.is_active is not None:
        product.is_active = data.is_active
    if data.variants is not None:
        product.variants = [Variant(size=v.size.value, stock=v.stock) for v in data.variants]
    if data.images is not None:
        product.images = [
            ProductImage(url=i.url, alt_text=i.alt, position=i.position) for i in data.images
        ]

    await session.commit()
    return await get_product_by_slug(session, slug)
