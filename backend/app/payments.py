"""SSLCOMMERZ gateway client (ADR-0007). Injected via a dependency so tests mock it."""

from typing import Annotated

import httpx
from fastapi import Depends

from app.config import settings


class SslcommerzGateway:
    async def initiate_session(
        self,
        *,
        order_number: str,
        total: int,
        currency: str,
        customer: dict,
        success_url: str,
        fail_url: str,
        cancel_url: str,
        ipn_url: str,
    ) -> str:
        """Create a payment session; return the GatewayPageURL to redirect to."""
        payload = {
            "store_id": settings.sslcommerz_store_id,
            "store_passwd": settings.sslcommerz_store_password,
            "total_amount": total,
            "currency": currency,
            "tran_id": order_number,
            "success_url": success_url,
            "fail_url": fail_url,
            "cancel_url": cancel_url,
            "ipn_url": ipn_url,
            "shipping_method": "NO",
            "product_name": "Thread It order",
            "product_category": "apparel",
            "product_profile": "general",
            "cus_name": customer["name"],
            "cus_email": customer["email"],
            "cus_phone": customer["phone"],
            "cus_add1": customer["address"],
            "cus_city": customer["city"],
            "cus_postcode": customer["postcode"],
            "cus_country": "Bangladesh",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{settings.sslcommerz_api_base}/gwprocess/v4/api.php", data=payload
            )
            resp.raise_for_status()
            body = resp.json()
        url = body.get("GatewayPageURL")
        if not url:
            raise RuntimeError(f"SSLCOMMERZ init failed: {body.get('failedreason') or body}")
        return url


def get_gateway() -> SslcommerzGateway:
    return SslcommerzGateway()


GatewayDep = Annotated[SslcommerzGateway, Depends(get_gateway)]
