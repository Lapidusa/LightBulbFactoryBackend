from enum import StrEnum


class DeliveryType(StrEnum):
    pickup = "pickup"
    courier = "courier"


class PaymentType(StrEnum):
    cash_on_delivery = "cash_on_delivery"
    online_stub = "online_stub"


class OrderStatus(StrEnum):
    created = "created"
    confirmed = "confirmed"
    processing = "processing"
    shipped = "shipped"
    completed = "completed"
    canceled = "canceled"

