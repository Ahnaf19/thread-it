"""Domain enums for the catalog — fixed, ordered sets (see backend/CONTEXT.md).

Stored as plain strings in the DB (no Postgres ENUM type, to avoid `ALTER TYPE`
pain when the sets grow); validated and ordered here in code.
"""

from enum import StrEnum


class Category(StrEnum):
    TOPS = "Tops"
    BOTTOMS = "Bottoms"
    OUTERWEAR = "Outerwear"
    DRESSES = "Dresses"
    ACCESSORIES = "Accessories"


class Size(StrEnum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"
    ONE_SIZE = "One Size"


# Display order for sizes (the selector shows S→M→L, never alphabetical).
SIZE_ORDER: dict[str, int] = {size.value: i for i, size in enumerate(Size)}
