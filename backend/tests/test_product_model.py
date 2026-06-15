from tests.factories import create_product


async def test_primary_image_is_lowest_position(db_session):
    p = await create_product(
        db_session,
        slug="p",
        images=[("https://img/b.jpg", "back", 1), ("https://img/a.jpg", "front", 0)],
    )
    assert p.primary_image is not None
    assert p.primary_image.url == "https://img/a.jpg"


async def test_primary_image_none_when_no_images(db_session):
    p = await create_product(db_session, slug="noimg", images=[])
    assert p.primary_image is None


async def test_in_stock_derivation(db_session):
    live = await create_product(db_session, slug="live", variants=[("S", 0), ("M", 2)])
    gone = await create_product(db_session, slug="gone", variants=[("S", 0), ("M", 0)])
    assert live.in_stock is True
    assert gone.in_stock is False


async def test_ordered_variants_follow_size_order(db_session):
    p = await create_product(db_session, slug="ord", variants=[("L", 1), ("S", 1), ("M", 1)])
    assert [v.size for v in p.ordered_variants] == ["S", "M", "L"]
