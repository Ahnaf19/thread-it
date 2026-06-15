"""Stateless cart pricing — the TDD'd money + stock logic (ADR-0004).

Resolves each line's Variant by (slug, size) against the live catalog, clamps
quantity to current stock, and sums the subtotal. Stores nothing.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.catalog import get_active_product_by_slug
from app.schemas.cart import CartItemIn, LineStatus, PricedCart, PricedLine
from app.schemas.catalog import PrimaryImage


def _primary_image(product) -> PrimaryImage | None:
    images = sorted(product.images, key=lambda i: i.position)
    return PrimaryImage(url=images[0].url, alt=images[0].alt_text) if images else None


async def price_cart(session: AsyncSession, items: list[CartItemIn]) -> PricedCart:
    lines: list[PricedLine] = []
    for item in items:
        product = await get_active_product_by_slug(session, item.slug)
        variant = None
        if product is not None:
            variant = next((v for v in product.variants if v.size == item.size), None)

        if product is None or variant is None or variant.stock == 0:
            lines.append(
                PricedLine(
                    slug=item.slug,
                    name=product.name if product else item.slug,
                    size=item.size,
                    primary_image=_primary_image(product) if product else None,
                    unit_price=product.price if product else 0,
                    quantity=item.quantity,
                    line_total=0,
                    available_stock=variant.stock if variant else 0,
                    status=LineStatus.UNAVAILABLE,
                )
            )
            continue

        clamped = min(item.quantity, variant.stock)
        status = LineStatus.ADJUSTED if clamped < item.quantity else LineStatus.OK
        lines.append(
            PricedLine(
                slug=item.slug,
                name=product.name,
                size=item.size,
                primary_image=_primary_image(product),
                unit_price=product.price,
                quantity=clamped,
                line_total=product.price * clamped,
                available_stock=variant.stock,
                status=status,
            )
        )

    available = [ln for ln in lines if ln.status != LineStatus.UNAVAILABLE]
    return PricedCart(
        items=lines,
        subtotal=sum(ln.line_total for ln in available),
        currency="BDT",
        item_count=sum(ln.quantity for ln in available),
    )
