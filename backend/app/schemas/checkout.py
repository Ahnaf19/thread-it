"""Checkout request/response schemas (ADR-0006, ADR-0007)."""

from pydantic import BaseModel, Field

from app.schemas.cart import CartItemIn


class CustomerIn(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    phone: str = Field(min_length=1)
    address: str = Field(min_length=1)
    city: str = Field(min_length=1)
    postcode: str = Field(min_length=1)


class CheckoutRequest(BaseModel):
    items: list[CartItemIn] = Field(min_length=1)
    customer: CustomerIn


class CheckoutResponse(BaseModel):
    gateway_url: str
    order_number: str
