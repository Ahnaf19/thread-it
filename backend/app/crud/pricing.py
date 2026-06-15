"""The single resolve+price+stock module behind the cart↔checkout seam.

`resolve_lines` is the one place that maps requested (slug, size, qty) lines to the
live catalog: finds the Variant, prices it, clamps to stock, and assigns a status.
Both cart pricing and order creation consume its output — and this is where v2's
concurrency-safe decrement / idempotent fulfilment will live.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.catalog import get_active_product_by_slug
from app.models import Variant
from app.schemas.cart import CartItemIn, LineStatus, PricedCart, PricedLine
from app.schemas.catalog import PrimaryImage


@dataclass
class ResolvedLine:
    """A requested line resolved against the live catalog — rich enough for both
    the cart response and an order snapshot."""

    slug: str
    size: str
    name: str
    primary_image: PrimaryImage | None
    unit_price: int
    requested_qty: int
    effective_qty: int  # clamped to stock (ok/adjusted); == requested for display when unavailable
    available_stock: int
    status: LineStatus
    variant: Variant | None  # carried for order snapshot + stock decrement

    @property
    def line_total(self) -> int:
        if self.status is LineStatus.UNAVAILABLE:
            return 0
        return self.unit_price * self.effective_qty


async def resolve_lines(session: AsyncSession, items: list[CartItemIn]) -> list[ResolvedLine]:
    resolved: list[ResolvedLine] = []
    for item in items:
        product = await get_active_product_by_slug(session, item.slug)
        variant = None
        if product is not None:
            variant = next((v for v in product.variants if v.size == item.size), None)

        if product is None or variant is None or variant.stock == 0:
            resolved.append(
                ResolvedLine(
                    slug=item.slug,
                    size=item.size,
                    name=product.name if product else item.slug,
                    primary_image=PrimaryImage.from_product(product) if product else None,
                    unit_price=product.price if product else 0,
                    requested_qty=item.quantity,
                    effective_qty=item.quantity,
                    available_stock=variant.stock if variant else 0,
                    status=LineStatus.UNAVAILABLE,
                    variant=None,
                )
            )
            continue

        clamped = min(item.quantity, variant.stock)
        resolved.append(
            ResolvedLine(
                slug=item.slug,
                size=item.size,
                name=product.name,
                primary_image=PrimaryImage.from_product(product),
                unit_price=product.price,
                requested_qty=item.quantity,
                effective_qty=clamped,
                available_stock=variant.stock,
                status=LineStatus.ADJUSTED if clamped < item.quantity else LineStatus.OK,
                variant=variant,
            )
        )
    return resolved


def to_priced_cart(resolved: list[ResolvedLine]) -> PricedCart:
    """Project resolved lines to the cart API shape (no variant_id exposed)."""
    lines = [
        PricedLine(
            slug=r.slug,
            name=r.name,
            size=r.size,
            primary_image=r.primary_image,
            unit_price=r.unit_price,
            quantity=r.effective_qty,
            line_total=r.line_total,
            available_stock=r.available_stock,
            status=r.status,
        )
        for r in resolved
    ]
    available = [r for r in resolved if r.status != LineStatus.UNAVAILABLE]
    return PricedCart(
        items=lines,
        subtotal=sum(r.line_total for r in available),
        currency="BDT",
        item_count=sum(r.effective_qty for r in available),
    )
