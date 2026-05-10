from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductImageCreate(BaseModel):
    image_url: str = Field(min_length=1, max_length=500)
    alt_text: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0)
    is_main: bool = False


class ProductImageRead(ProductImageCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str


class ProductBase(BaseModel):
    sku: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    short_description: str = Field(min_length=5, max_length=500)
    description: str = Field(min_length=10)
    category_id: str
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock_qty: int = Field(ge=0)
    wattage: int = Field(gt=0)
    base_type: str = Field(min_length=1, max_length=50)
    color_temperature: int = Field(gt=0)
    luminous_flux: int = Field(gt=0)
    voltage: int = Field(gt=0)
    lifetime_hours: int = Field(gt=0)
    brand: str = Field(min_length=1, max_length=100)
    series: str = Field(min_length=1, max_length=100)
    is_active: bool = True


class ProductCreate(ProductBase):
    images: list[ProductImageCreate] = []


class ProductUpdate(ProductBase):
    images: list[ProductImageCreate] | None = None


class ProductPatch(BaseModel):
    sku: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    short_description: str | None = Field(default=None, min_length=5, max_length=500)
    description: str | None = Field(default=None, min_length=10)
    category_id: str | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    stock_qty: int | None = Field(default=None, ge=0)
    wattage: int | None = Field(default=None, gt=0)
    base_type: str | None = Field(default=None, min_length=1, max_length=50)
    color_temperature: int | None = Field(default=None, gt=0)
    luminous_flux: int | None = Field(default=None, gt=0)
    voltage: int | None = Field(default=None, gt=0)
    lifetime_hours: int | None = Field(default=None, gt=0)
    brand: str | None = Field(default=None, min_length=1, max_length=100)
    series: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class ProductStatusUpdate(BaseModel):
    is_active: bool


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageRead] = []

