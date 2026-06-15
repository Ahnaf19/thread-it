"""Pydantic response schemas for the catalog API, kept separate from ORM models.

Derived shape (primary image, in-stock, ordered variants/images) lives on the
Product model; these builders just project it. `is_new` stays here — it needs the
config window, which isn't the model's concern.
"""

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from app.models import Product


def _is_new(product: Product, new_window_days: int) -> bool:
    return datetime.now(UTC) - product.created_at <= timedelta(days=new_window_days)


class PrimaryImage(BaseModel):
    url: str
    alt: str

    @classmethod
    def from_product(cls, product: Product) -> "PrimaryImage | None":
        img = product.primary_image
        return cls(url=img.url, alt=img.alt_text) if img else None


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
        return cls(
            slug=product.slug,
            name=product.name,
            price=product.price,
            currency=product.currency,
            category=product.category,
            is_new=_is_new(product, new_window_days),
            primary_image=PrimaryImage.from_product(product),
            in_stock=product.in_stock,
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
        return cls(
            slug=product.slug,
            name=product.name,
            description=product.description,
            price=product.price,
            currency=product.currency,
            category=product.category,
            is_new=_is_new(product, new_window_days),
            is_active=product.is_active,
            images=[
                ImageOut(url=i.url, alt=i.alt_text, position=i.position)
                for i in product.ordered_images
            ],
            variants=[VariantOut(size=v.size, stock=v.stock) for v in product.ordered_variants],
        )
