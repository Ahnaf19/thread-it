"""Cart API — stateless pricing + validation (ADR-0004)."""

from fastapi import APIRouter

from app.crud import cart as crud
from app.db import SessionDep
from app.schemas.cart import CartRequest, PricedCart

router = APIRouter(tags=["cart"])


@router.post("/cart", response_model=PricedCart)
async def price_cart(request: CartRequest, session: SessionDep) -> PricedCart:
    return await crud.price_cart(session, request.items)
