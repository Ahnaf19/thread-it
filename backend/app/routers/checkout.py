"""Checkout + SSLCOMMERZ callbacks (ADR-0007)."""

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.crud import checkout as crud
from app.db import SessionDep
from app.enums import OrderStatus
from app.payments import GatewayDep
from app.rate_limit import CHECKOUT_PER_MINUTE, rate_limit
from app.schemas.checkout import CheckoutRequest, CheckoutResponse

router = APIRouter(tags=["checkout"])

_PAID_STATUSES = {"VALID", "VALIDATED"}


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    dependencies=[Depends(rate_limit(scope="checkout", limit=CHECKOUT_PER_MINUTE))],
)
async def checkout(
    req: CheckoutRequest,
    request: Request,
    session: SessionDep,
    gateway: GatewayDep,
    idempotency_key: str | None = Header(default=None),
):
    try:
        order = await crud.create_pending_order(
            session, req.items, req.customer, idempotency_key=idempotency_key
        )
    except crud.CartChangedError as exc:
        # The cart can't be fulfilled as-is — hand back the re-priced cart so the client re-syncs.
        return JSONResponse(status_code=409, content=exc.priced.model_dump())

    base = str(request.base_url).rstrip("/")
    gateway_url = await gateway.initiate_session(
        order_number=order.order_number,
        total=order.total,
        currency=order.currency,
        customer=req.customer.model_dump(),
        success_url=f"{base}/checkout/success",
        fail_url=f"{base}/checkout/fail",
        cancel_url=f"{base}/checkout/cancel",
        ipn_url=f"{base}/checkout/ipn",
    )
    return CheckoutResponse(gateway_url=gateway_url, order_number=order.order_number)


def _amount_matches(amount: str | None, total: int) -> bool:
    try:
        return amount is not None and round(float(amount)) == total
    except ValueError:
        return False


@router.post("/checkout/success")
async def payment_success(request: Request, session: SessionDep) -> RedirectResponse:
    form = await request.form()
    tran_id = form.get("tran_id")
    order = await crud.get_order_by_number(session, tran_id) if tran_id else None
    valid = (
        order is not None
        and form.get("status") in _PAID_STATUSES
        and _amount_matches(form.get("amount"), order.total)
    )
    if valid:
        resolved = await crud.mark_order_paid(session, tran_id)
        # Payment was valid but the last unit was taken first → sold-out path (ADR-0011).
        # Flag it so the confirmation page shows "just sold out", not "order confirmed".
        sold_out = resolved is not None and resolved.status == OrderStatus.FAILED.value
        target = f"{settings.frontend_url}/checkout/success?order={tran_id}"
        if sold_out:
            target += "&outcome=sold_out"
    else:
        target = f"{settings.frontend_url}/checkout/fail"
    return RedirectResponse(target, status_code=303)


@router.post("/checkout/ipn")
async def payment_ipn(request: Request, session: SessionDep) -> dict:
    """Server-to-server notification. Idempotent via the pending-status guard."""
    form = await request.form()
    tran_id = form.get("tran_id")
    if tran_id and form.get("status") in _PAID_STATUSES:
        await crud.mark_order_paid(session, tran_id)
    return {"ok": True}


@router.post("/checkout/fail")
async def payment_fail(request: Request, session: SessionDep) -> RedirectResponse:
    form = await request.form()
    if (tran_id := form.get("tran_id")):
        await crud.mark_order_status(session, tran_id, OrderStatus.FAILED)
    return RedirectResponse(f"{settings.frontend_url}/checkout/fail", status_code=303)


@router.post("/checkout/cancel")
async def payment_cancel(request: Request, session: SessionDep) -> RedirectResponse:
    form = await request.form()
    if (tran_id := form.get("tran_id")):
        await crud.mark_order_status(session, tran_id, OrderStatus.CANCELLED)
    return RedirectResponse(f"{settings.frontend_url}/checkout/cancel", status_code=303)
