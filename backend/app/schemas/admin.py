"""Admin product create/update schemas. Enums validate category/size (422)."""

from pydantic import BaseModel, Field

from app.enums import Category, Size


class VariantIn(BaseModel):
    size: Size
    stock: int = Field(ge=0)


class ImageIn(BaseModel):
    url: str
    alt: str = ""
    position: int = 0


class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    price: int = Field(ge=0)
    category: Category
    is_active: bool = True
    variants: list[VariantIn] = Field(min_length=1)
    images: list[ImageIn] = []


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    price: int | None = Field(default=None, ge=0)
    category: Category | None = None
    is_active: bool | None = None
    variants: list[VariantIn] | None = None
    images: list[ImageIn] | None = None
