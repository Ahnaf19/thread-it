"""Test data builders — arrange products via the ORM (no admin create endpoint yet)."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderItem, Product, ProductImage, Variant


async def create_product(
    session: AsyncSession,
    *,
    slug: str,
    name: str = "Test Product",
    description: str = "",
    price: int = 1450,
    category: str = "Tops",
    is_active: bool = True,
    created_at: datetime | None = None,
    variants: list[tuple[str, int]] | None = None,
    images: list[tuple[str, str, int]] | None = None,
) -> Product:
    product = Product(
        slug=slug,
        name=name,
        description=description,
        price=price,
        category=category,
        is_active=is_active,
    )
    if created_at is not None:
        product.created_at = created_at
    for size, stock in variants or [("One Size", 1)]:
        product.variants.append(Variant(size=size, stock=stock))
    for url, alt, position in images or []:
        product.images.append(ProductImage(url=url, alt_text=alt, position=position))
    session.add(product)
    await session.commit()
    return product


async def create_order(
    session: AsyncSession,
    *,
    order_number: str,
    status: str = "pending",
    total: int = 1000,
    created_at: datetime | None = None,
    items: list[tuple[str, str, int, int]] | None = None,
) -> Order:
    order = Order(
        order_number=order_number,
        status=status,
        name="Guest",
        email="guest@example.com",
        phone="01700000000",
        address="12 Demo Rd",
        city="Dhaka",
        postcode="1207",
        total=total,
    )
    if created_at is not None:
        order.created_at = created_at
    for product_name, size, unit_price, quantity in items or [("Item", "M", total, 1)]:
        order.items.append(
            OrderItem(
                product_name=product_name, size=size, unit_price=unit_price, quantity=quantity
            )
        )
    session.add(order)
    await session.commit()
    return order
