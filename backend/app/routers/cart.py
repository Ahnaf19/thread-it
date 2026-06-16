"""Cart API — stateless pricing + validation (ADR-0004)."""

from fastapi import APIRouter, Depends

from app.crud import cart as crud
from app.db import SessionDep
from app.rate_limit import CART_PER_MINUTE, rate_limit
from app.schemas.cart import CartRequest, PricedCart

router = APIRouter(tags=["cart"])


@router.post(
    "/cart",
    response_model=PricedCart,
    dependencies=[Depends(rate_limit(scope="cart", limit=CART_PER_MINUTE))],
)
async def price_cart(request: CartRequest, session: SessionDep) -> PricedCart:
    return await crud.price_cart(session, request.items)
