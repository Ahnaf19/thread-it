"""Admin API — login + product management (ADR-0005)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.crud import admin as crud
from app.crud import checkout as checkout_crud
from app.db import SessionDep
from app.schemas.admin import ProductCreate, ProductUpdate
from app.schemas.catalog import ProductDetail
from app.schemas.order import OrderOut
from app.security import AdminDep, create_access_token, verify_password

router = APIRouter(prefix="/admin", tags=["admin"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest) -> TokenResponse:
    if req.username != settings.admin_username or not verify_password(
        req.password, settings.admin_password_hash
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return TokenResponse(access_token=create_access_token(req.username))


@router.get("/products", response_model=list[ProductDetail])
async def list_products(_admin: AdminDep, session: SessionDep) -> list[ProductDetail]:
    products = await crud.list_all_products(session)
    return [ProductDetail.from_product(p, settings.new_window_days) for p in products]


@router.post("/products", response_model=ProductDetail, status_code=201)
async def create_product(
    data: ProductCreate, _admin: AdminDep, session: SessionDep
) -> ProductDetail:
    product = await crud.create_product(session, data)
    return ProductDetail.from_product(product, settings.new_window_days)


@router.patch("/products/{slug}", response_model=ProductDetail)
async def update_product(
    slug: str, data: ProductUpdate, _admin: AdminDep, session: SessionDep
) -> ProductDetail:
    product = await crud.update_product(session, slug, data)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetail.from_product(product, settings.new_window_days)


@router.get("/orders", response_model=list[OrderOut])
async def list_orders(
    _admin: AdminDep, session: SessionDep, status: str | None = None
) -> list[OrderOut]:
    orders = await checkout_crud.list_orders(session, status=status)
    return [OrderOut.model_validate(o) for o in orders]
