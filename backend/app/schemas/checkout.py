"""Checkout request/response schemas (ADR-0006, ADR-0007)."""

import re

from pydantic import BaseModel, Field, field_validator

from app.schemas.cart import MAX_CART_LINES, CartItemIn

# A shape check, not full RFC 5322 — enough to reject obvious garbage without
# pulling in email-validator (EmailStr would be the upgrade if deliverability matters).
_EMAIL_SHAPE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class CustomerIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    phone: str = Field(min_length=1, max_length=30)
    address: str = Field(min_length=1, max_length=500)
    city: str = Field(min_length=1, max_length=100)
    postcode: str = Field(min_length=1, max_length=20)

    @field_validator("email")
    @classmethod
    def _validate_email_shape(cls, v: str) -> str:
        if not _EMAIL_SHAPE.match(v):
            raise ValueError("invalid email address")
        return v


class CheckoutRequest(BaseModel):
    items: list[CartItemIn] = Field(min_length=1, max_length=MAX_CART_LINES)
    customer: CustomerIn


class CheckoutResponse(BaseModel):
    gateway_url: str
    order_number: str
