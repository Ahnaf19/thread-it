from app.crud.pricing import resolve_lines
from app.schemas.cart import CartItemIn
from tests.factories import create_product


def _items(*triples):
    return [CartItemIn(slug=s, size=z, quantity=q) for s, z, q in triples]


async def test_resolve_empty(db_session):
    assert await resolve_lines(db_session, []) == []


async def test_resolve_ok_line_carries_variant_and_price(db_session):
    await create_product(db_session, slug="tee", name="Tee", price=1000, variants=[("M", 5)])

    [line] = await resolve_lines(db_session, _items(("tee", "M", 2)))

    assert line.status == "ok"
    assert line.effective_qty == 2
    assert line.unit_price == 1000
    assert line.line_total == 2000
    assert line.variant is not None  # carried for the order snapshot (no re-resolve)


async def test_resolve_clamps_over_stock_to_adjusted(db_session):
    await create_product(db_session, slug="scarf", price=800, variants=[("One Size", 2)])

    [line] = await resolve_lines(db_session, _items(("scarf", "One Size", 5)))

    assert line.status == "adjusted"
    assert line.effective_qty == 2
    assert line.line_total == 1600


async def test_resolve_unavailable_cases(db_session):
    await create_product(db_session, slug="sold-out", price=500, variants=[("M", 0)])
    await create_product(db_session, slug="hidden", price=500, is_active=False, variants=[("M", 5)])
    await create_product(db_session, slug="live", price=500, variants=[("M", 5)])

    lines = await resolve_lines(
        db_session,
        _items(
            ("sold-out", "M", 1),   # stock 0
            ("hidden", "M", 1),     # inactive
            ("ghost", "M", 1),      # unknown slug
            ("live", "XXL", 1),     # size not offered
        ),
    )

    assert [line.status for line in lines] == ["unavailable"] * 4
    assert all(line.variant is None for line in lines)
    assert all(line.line_total == 0 for line in lines)
