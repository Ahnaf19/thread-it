"""Order ORM models (see backend/CONTEXT.md, ADR-0006). Items snapshot the sale."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import OrderStatus


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    status: Mapped[str] = mapped_column(String, default=OrderStatus.PENDING.value, index=True)

    # Guest contact / shipping (no accounts in v1).
    name: Mapped[str]
    email: Mapped[str]
    phone: Mapped[str]
    address: Mapped[str]
    city: Mapped[str]
    postcode: Mapped[str]

    total: Mapped[int]  # whole Taka (ADR-0001), snapshot at checkout
    currency: Mapped[str] = mapped_column(String(3), default="BDT")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    # Kept for the stock decrement; nullable so a later variant delete doesn't orphan history.
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("variants.id", ondelete="SET NULL"), nullable=True
    )

    # Snapshot of the sale (stable even if the catalog changes).
    product_name: Mapped[str]
    size: Mapped[str]
    unit_price: Mapped[int]
    quantity: Mapped[int]

    order: Mapped["Order"] = relationship(back_populates="items")
