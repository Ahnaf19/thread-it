"""Pydantic response schemas for the catalog API, kept separate from ORM models.

The `from_product` builders own the derived fields (`is_new`, `in_stock`,
`primary_image`) so the API contract lives in one place.
"""

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from app.enums import SIZE_ORDER
from app.models import Product


def _is_new(product: Product, new_window_days: int) -> bool:
    return datetime.now(UTC) - product.created_at <= timedelta(days=new_window_days)


def _in_stock(product: Product) -> bool:
    return any(v.stock > 0 for v in product.variants)


class PrimaryImage(BaseModel):
    url: str
    alt: str


class ImageOut(BaseModel):
    url: str
    alt: str
    position: int


class VariantOut(BaseModel):
    size: str
    stock: int


class ProductSummary(BaseModel):
    slug: str
    name: str
    price: int
    currency: str
    category: str
    is_new: bool
    primary_image: PrimaryImage | None
    in_stock: bool

    @classmethod
    def from_product(cls, product: Product, new_window_days: int) -> "ProductSummary":
        images = sorted(product.images, key=lambda i: i.position)
        primary = images[0] if images else None
        return cls(
            slug=product.slug,
            name=product.name,
            price=product.price,
            currency=product.currency,
            category=product.category,
            is_new=_is_new(product, new_window_days),
            primary_image=PrimaryImage(url=primary.url, alt=primary.alt_text) if primary else None,
            in_stock=_in_stock(product),
        )


class ProductDetail(BaseModel):
    slug: str
    name: str
    description: str
    price: int
    currency: str
    category: str
    is_new: bool
    is_active: bool
    images: list[ImageOut]
    variants: list[VariantOut]

    @classmethod
    def from_product(cls, product: Product, new_window_days: int) -> "ProductDetail":
        images = sorted(product.images, key=lambda i: i.position)
        variants = sorted(product.variants, key=lambda v: SIZE_ORDER.get(v.size, 99))
        return cls(
            slug=product.slug,
            name=product.name,
            description=product.description,
            price=product.price,
            currency=product.currency,
            category=product.category,
            is_new=_is_new(product, new_window_days),
            is_active=product.is_active,
            images=[ImageOut(url=i.url, alt=i.alt_text, position=i.position) for i in images],
            variants=[VariantOut(size=v.size, stock=v.stock) for v in variants],
        )
