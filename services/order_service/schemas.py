from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from services.order_service.enums import DeliveryType, OrderStatus, PaymentType


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, le=100)


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=255)
    customer_phone: str = Field(min_length=5, max_length=30)
    customer_email: EmailStr
    city: str = Field(min_length=2, max_length=100)
    address: str = Field(min_length=5, max_length=255)
    delivery_type: DeliveryType
    payment_type: PaymentType
    comment: str | None = None
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    product_name: str
    product_sku: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class OrderStatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    old_status: str | None
    new_status: str
    changed_by: str
    changed_at: datetime


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_number: str
    customer_name: str
    customer_phone: str
    customer_email: str
    city: str
    address: str
    delivery_type: str
    payment_type: str
    comment: str | None
    admin_comment: str | None
    status: str
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]
    history: list[OrderStatusHistoryRead] = []


class OrderPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_number: str
    status: str
    total_amount: Decimal
    created_at: datetime
    items: list[OrderItemRead]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderCommentUpdate(BaseModel):
    admin_comment: str | None = Field(default=None, max_length=5000)

