"""Cart request/response schemas. The cart is priced statelessly (ADR-0004)."""

from enum import StrEnum

from pydantic import BaseModel, Field

from app.enums import Size
from app.schemas.catalog import PrimaryImage

# Defensive bounds for the public cart/checkout surface (#42). A real cart is a
# handful of lines; the caps keep a malformed or hostile payload from reaching the
# pricing/DB layer at all (422, not a 500 or silent clamp).
MAX_CART_LINES = 100
MAX_QUANTITY_PER_LINE = 100
MAX_SLUG_LENGTH = 200


class CartItemIn(BaseModel):
    slug: str = Field(min_length=1, max_length=MAX_SLUG_LENGTH)
    size: Size  # must be a known size, not an arbitrary string
    quantity: int = Field(gt=0, le=MAX_QUANTITY_PER_LINE)


class CartRequest(BaseModel):
    items: list[CartItemIn] = Field(default=[], max_length=MAX_CART_LINES)


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
