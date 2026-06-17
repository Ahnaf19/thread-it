"""Catalog API — product list and detail."""

from fastapi import APIRouter, HTTPException, Path

from app.config import settings
from app.crud import catalog as crud
from app.db import SessionDep
from app.enums import Category
from app.schemas.catalog import ProductDetail, ProductSummary

router = APIRouter(tags=["catalog"])


@router.get("/products", response_model=list[ProductSummary])
async def list_products(
    session: SessionDep,
    category: Category | None = None,  # unknown category → 422, not a silent empty list
) -> list[ProductSummary]:
    products = await crud.list_products(session, category=category)
    return [ProductSummary.from_product(p, settings.new_window_days) for p in products]


@router.get("/products/{slug}", response_model=ProductDetail)
async def get_product(
    session: SessionDep, slug: str = Path(min_length=1, max_length=200)
) -> ProductDetail:
    product = await crud.get_active_product_by_slug(session, slug)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetail.from_product(product, settings.new_window_days)
