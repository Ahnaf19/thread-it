"""Admin order read schemas (serialized straight from the ORM)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import OrderStatus


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_name: str
    size: str
    unit_price: int
    quantity: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_number: str
    status: str
    name: str
    email: str
    phone: str
    address: str
    city: str
    postcode: str
    total: int
    currency: str
    created_at: datetime
    items: list[OrderItemOut]


class OrderStatusUpdate(BaseModel):
    """Admin request to move an order to a new status (validated by the state machine)."""

    status: OrderStatus
