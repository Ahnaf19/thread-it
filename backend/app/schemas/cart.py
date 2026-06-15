"""Cart request/response schemas. The cart is priced statelessly (ADR-0004)."""

from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.catalog import PrimaryImage


class CartItemIn(BaseModel):
    slug: str
    size: str
    quantity: int = Field(gt=0)  # <= 0 -> 422


class CartRequest(BaseModel):
    items: list[CartItemIn] = []


class LineStatus(StrEnum):
    OK = "ok"
    ADJUSTED = "adjusted"  # quantity clamped down to available stock
    UNAVAILABLE = "unavailable"  # variant gone / inactive / out of stock


class PricedLine(BaseModel):
    slug: str
    name: str
    size: str
    primary_image: PrimaryImage | None
    unit_price: int
    quantity: int
    line_total: int
    available_stock: int
    status: LineStatus


class PricedCart(BaseModel):
    items: list[PricedLine]
    subtotal: int
    currency: str
    item_count: int
