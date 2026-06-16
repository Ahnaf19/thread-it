"""Admin API — login + product management (ADR-0005)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.crud import admin as crud
from app.crud import checkout as checkout_crud
from app.db import SessionDep
from app.order_state import IllegalTransition
from app.rate_limit import LOGIN_PER_MINUTE, rate_limit
from app.schemas.admin import ProductCreate, ProductUpdate
from app.schemas.catalog import ProductDetail
from app.schemas.order import OrderOut, OrderStatusUpdate
from app.security import create_access_token, require_admin, verify_password

# Two routers share the /admin prefix: `login_router` is public (chicken-and-egg —
# you can't authenticate to get a token), while `router` enforces the admin guard at
# the router level so every endpoint on it is protected by construction, not by
# remembering a per-endpoint dependency (ADR-0005). A route-introspecting test locks
# this in (tests/test_admin_authz.py).
login_router = APIRouter(prefix="/admin", tags=["admin"])
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@login_router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(scope="login", limit=LOGIN_PER_MINUTE))],
)
async def login(req: LoginRequest) -> TokenResponse:
    if req.username != settings.admin_username or not verify_password(
        req.password, settings.admin_password_hash
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return TokenResponse(access_token=create_access_token(req.username))


@router.get("/products", response_model=list[ProductDetail])
async def list_products(session: SessionDep) -> list[ProductDetail]:
    products = await crud.list_all_products(session)
    return [ProductDetail.from_product(p, settings.new_window_days) for p in products]


@router.post("/products", response_model=ProductDetail, status_code=201)
async def create_product(data: ProductCreate, session: SessionDep) -> ProductDetail:
    product = await crud.create_product(session, data)
    return ProductDetail.from_product(product, settings.new_window_days)


@router.patch("/products/{slug}", response_model=ProductDetail)
async def update_product(
    slug: str, data: ProductUpdate, session: SessionDep
) -> ProductDetail:
    product = await crud.update_product(session, slug, data)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetail.from_product(product, settings.new_window_days)


@router.get("/orders", response_model=list[OrderOut])
async def list_orders(
    session: SessionDep, status: str | None = None
) -> list[OrderOut]:
    orders = await checkout_crud.list_orders(session, status=status)
    return [OrderOut.model_validate(o) for o in orders]


@router.patch("/orders/{order_number}", response_model=OrderOut)
async def update_order_status(
    order_number: str, data: OrderStatusUpdate, session: SessionDep
) -> OrderOut:
    """Admin status transition (e.g. paid → fulfilled). Illegal moves → 409 (ADR-0008)."""
    try:
        order = await checkout_crud.transition_order(session, order_number, data.status)
    except IllegalTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderOut.model_validate(order)
