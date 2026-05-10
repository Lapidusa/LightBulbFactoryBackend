from datetime import UTC, datetime
from decimal import Decimal

import httpx
from fastapi import Depends, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, selectinload

from services.order_service.config import settings
from services.order_service.db import Base, engine, get_db
from services.order_service.deps import require_internal_token
from services.order_service.enums import OrderStatus
from services.order_service.models import Order, OrderItem, OrderStatusHistory
from services.order_service.schemas import OrderCommentUpdate, OrderCreate, OrderPublicRead, OrderRead, OrderStatusUpdate
from shared.fastapi import create_service_app
from shared.responses import fail, ok


app = create_service_app(
    title="Order Service",
    description="Микросервис создания, хранения и обработки заказов.",
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


def generate_order_number() -> str:
    return "LB-" + datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:-3]


def get_order_or_404(db: Session, order_id: str) -> Order:
    order = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.history))
        .filter(Order.id == order_id)
        .first()
    )
    if order is None:
        fail("not_found", "Order not found", 404)
    return order


def reserve_products(items: list[dict]) -> list[dict]:
    try:
        response = httpx.post(
            f"{settings.product_service_url}/api/v1/internal/products/reserve",
            headers={"X-Internal-Token": settings.internal_api_token},
            json={"items": items},
            timeout=5.0,
        )
    except httpx.HTTPError as exc:
        fail("service_unavailable", f"Product service is unavailable: {exc}", 503)
    if response.status_code >= 400:
        detail = response.json()
        fail("product_service_error", "Product service rejected order items", response.status_code, detail)
    return response.json()["data"]["items"]


@app.post("/api/v1/orders", status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    snapshots = reserve_products([item.model_dump() for item in payload.items])
    total = sum(Decimal(item["line_total"]) for item in snapshots)
    order = Order(
        order_number=generate_order_number(),
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        customer_email=str(payload.customer_email),
        city=payload.city,
        address=payload.address,
        delivery_type=payload.delivery_type.value,
        payment_type=payload.payment_type.value,
        comment=payload.comment,
        status=OrderStatus.created.value,
        total_amount=total,
        items=[
            OrderItem(
                product_id=item["product_id"],
                product_name=item["product_name"],
                product_sku=item["product_sku"],
                unit_price=Decimal(item["unit_price"]),
                quantity=item["quantity"],
                line_total=Decimal(item["line_total"]),
            )
            for item in snapshots
        ],
        history=[OrderStatusHistory(old_status=None, new_status=OrderStatus.created.value, changed_by="customer")],
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return ok(OrderPublicRead.model_validate(order).model_dump(mode="json"))


@app.get("/api/v1/orders/{order_number}")
def get_public_order(order_number: str, db: Session = Depends(get_db)):
    order = (
        db.query(Order).options(selectinload(Order.items)).filter(Order.order_number == order_number).first()
    )
    if order is None:
        fail("not_found", "Order not found", 404)
    return ok(OrderPublicRead.model_validate(order).model_dump(mode="json"))


@app.get("/api/v1/admin/orders", dependencies=[Depends(require_internal_token)])
def admin_list_orders(
    db: Session = Depends(get_db),
    status: OrderStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    query = db.query(Order).options(selectinload(Order.items), selectinload(Order.history))
    if status:
        query = query.filter(Order.status == status.value)
    if date_from:
        query = query.filter(Order.created_at >= date_from)
    if date_to:
        query = query.filter(Order.created_at <= date_to)
    total = query.count()
    orders = query.order_by(desc(Order.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return ok(
        [OrderRead.model_validate(order).model_dump(mode="json") for order in orders],
        {"page": page, "page_size": page_size, "total": total},
    )


@app.get("/api/v1/admin/orders/summary", dependencies=[Depends(require_internal_token)])
def orders_summary(db: Session = Depends(get_db)):
    active_orders = db.query(func.count(Order.id)).filter(Order.status != OrderStatus.completed.value).scalar()
    status_rows = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    orders_by_status = {status.value: 0 for status in OrderStatus}
    orders_by_status.update({row[0]: row[1] for row in status_rows})
    return ok({"active_orders_count": active_orders, "orders_by_status": orders_by_status})


@app.get("/api/v1/admin/orders/{order_id}", dependencies=[Depends(require_internal_token)])
def admin_get_order(order_id: str, db: Session = Depends(get_db)):
    return ok(OrderRead.model_validate(get_order_or_404(db, order_id)).model_dump(mode="json"))


@app.patch("/api/v1/admin/orders/{order_id}/status", dependencies=[Depends(require_internal_token)])
def update_order_status(order_id: str, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = get_order_or_404(db, order_id)
    old_status = order.status
    order.status = payload.status.value
    order.history.append(OrderStatusHistory(old_status=old_status, new_status=payload.status.value, changed_by="admin"))
    db.commit()
    db.refresh(order)
    return ok(OrderRead.model_validate(order).model_dump(mode="json"))


@app.patch("/api/v1/admin/orders/{order_id}/comment", dependencies=[Depends(require_internal_token)])
def update_order_comment(order_id: str, payload: OrderCommentUpdate, db: Session = Depends(get_db)):
    order = get_order_or_404(db, order_id)
    order.admin_comment = payload.admin_comment
    db.commit()
    db.refresh(order)
    return ok(OrderRead.model_validate(order).model_dump(mode="json"))

