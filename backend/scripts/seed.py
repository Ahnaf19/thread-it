"""Idempotent catalog seed — demo products that exercise every stock state.

Run once against the target DB (DATABASE_URL must be set):

    uv run python -m scripts.seed

Upserts by slug (delete-then-insert), so re-running refreshes the data without
duplicating. NOT run automatically on deploy — it would fight real admin data (#3).
"""

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Product, ProductImage, Variant


def _images(slug: str) -> list[tuple[str, str, int]]:
    # External placeholder images for v1; real shots live in the Supabase bucket later.
    return [
        (f"https://picsum.photos/seed/{slug}-1/800/1000", f"{slug} front", 0),
        (f"https://picsum.photos/seed/{slug}-2/800/1000", f"{slug} detail", 1),
    ]


# (slug, name, price, category, days_old, [(size, stock)])
SEED: list[tuple[str, str, int, str, int, list[tuple[str, int]]]] = [
    ("linen-oversized-shirt", "Linen Oversized Shirt", 2450, "Tops", 2,
     [("S", 4), ("M", 8), ("L", 0)]),                       # low-stock S, sold-out L
    ("ribbed-knit-top", "Ribbed Knit Top", 1850, "Tops", 1,
     [("XS", 3), ("S", 5), ("M", 7)]),                      # new
    ("tailored-trousers", "Tailored Trousers", 3200, "Bottoms", 30,
     [("S", 6), ("M", 5), ("L", 3)]),
    ("pleated-midi-skirt", "Pleated Midi Skirt", 2750, "Bottoms", 45,
     [("S", 0), ("M", 0), ("L", 0)]),                       # fully sold out
    ("wool-overcoat", "Wool Overcoat", 8900, "Outerwear", 10,
     [("S", 2), ("M", 1), ("L", 0)]),                       # all low / one sold out
    ("bias-slip-dress", "Bias Slip Dress", 4100, "Dresses", 5,
     [("XS", 0), ("S", 3), ("M", 0)]),
    ("canvas-tote", "Canvas Tote", 1200, "Accessories", 20,
     [("One Size", 12)]),
    ("leather-belt", "Leather Belt", 1650, "Accessories", 60,
     [("One Size", 0)]),                                    # fully sold out, one-size
]


async def seed() -> None:
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        for slug, name, price, category, days_old, variants in SEED:
            existing = await session.scalar(select(Product).where(Product.slug == slug))
            if existing is not None:
                await session.delete(existing)
                await session.flush()
            product = Product(
                slug=slug,
                name=name,
                description=f"{name} — part of the Thread It demo collection.",
                price=price,
                category=category,
                is_active=True,
                created_at=now - timedelta(days=days_old),
            )
            product.variants = [Variant(size=s, stock=st) for s, st in variants]
            product.images = [
                ProductImage(url=u, alt_text=a, position=p) for u, a, p in _images(slug)
            ]
            session.add(product)
        await session.commit()
    print(f"Seeded {len(SEED)} products.")


if __name__ == "__main__":
    asyncio.run(seed())
