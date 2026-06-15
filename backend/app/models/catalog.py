"""Catalog ORM models: Product, Variant, ProductImage (see backend/CONTEXT.md)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import SIZE_ORDER


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str]
    description: Mapped[str] = mapped_column(default="")
    price: Mapped[int]  # whole Taka (ADR-0001)
    currency: Mapped[str] = mapped_column(String(3), default="BDT")
    category: Mapped[str] = mapped_column(String, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    variants: Mapped[list["Variant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )

    # Derived shape — the single home for these rules (consumed by schemas + pricing).
    @property
    def primary_image(self) -> "ProductImage | None":
        return min(self.images, key=lambda i: i.position) if self.images else None

    @property
    def ordered_images(self) -> list["ProductImage"]:
        return sorted(self.images, key=lambda i: i.position)

    @property
    def ordered_variants(self) -> list["Variant"]:
        return sorted(self.variants, key=lambda v: SIZE_ORDER.get(v.size, 99))

    @property
    def in_stock(self) -> bool:
        return any(v.stock > 0 for v in self.variants)


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    size: Mapped[str] = mapped_column(String)
    stock: Mapped[int] = mapped_column(default=0)

    product: Mapped["Product"] = relationship(back_populates="variants")


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    url: Mapped[str]
    alt_text: Mapped[str] = mapped_column(default="")
    position: Mapped[int] = mapped_column(default=0)

    product: Mapped["Product"] = relationship(back_populates="images")
