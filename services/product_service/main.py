from decimal import Decimal
from typing import Literal

from fastapi import Depends, Query
from sqlalchemy import asc, desc, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from services.product_service.db import Base, engine, get_db
from services.product_service.deps import require_internal_token
from services.product_service.models import Category, Product, ProductImage
from services.product_service.schemas import (
    CategoryRead,
    ProductCreate,
    ProductImageCreate,
    ProductPatch,
    ProductRead,
    ProductStatusUpdate,
    ProductUpdate,
)
from services.product_service.seed import seed_catalog
from shared.fastapi import create_service_app
from shared.responses import fail, ok


app = create_service_app(
    title="Product Service",
    description="Микросервис каталога товаров, категорий, изображений и остатков.",
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_catalog(db)
        db.commit()
    finally:
        db.close()


def serialize_product(product: Product) -> dict:
    return ProductRead.model_validate(product).model_dump(mode="json")


def get_product_or_404(db: Session, product_id: str, public_only: bool = False) -> Product:
    query = db.query(Product).options(selectinload(Product.images)).filter(Product.id == product_id)
    if public_only:
        query = query.filter(Product.is_active.is_(True))
    product = query.first()
    if product is None:
        fail("not_found", "Product not found", 404)
    return product


@app.get("/api/v1/categories")
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).filter(Category.is_active.is_(True)).order_by(Category.name).all()
    return ok([CategoryRead.model_validate(category).model_dump(mode="json") for category in categories])


@app.get("/api/v1/products")
def list_products(
    db: Session = Depends(get_db),
    category_id: str | None = None,
    lamp_type: str | None = None,
    base_type: str | None = None,
    wattage: int | None = None,
    color_temperature: int | None = None,
    brand: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    search: str | None = None,
    sort_by: Literal["price", "name", "newest"] = "newest",
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
):
    query = db.query(Product).options(selectinload(Product.images)).filter(Product.is_active.is_(True))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if lamp_type:
        query = query.join(Category).filter(Category.slug == lamp_type)
    if base_type:
        query = query.filter(Product.base_type == base_type)
    if wattage:
        query = query.filter(Product.wattage == wattage)
    if color_temperature:
        query = query.filter(Product.color_temperature == color_temperature)
    if brand:
        query = query.filter(Product.brand == brand)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Product.name.ilike(like), Product.sku.ilike(like)))

    total = query.count()
    sort_column = {"price": Product.price, "name": Product.name, "newest": Product.created_at}[sort_by]
    query = query.order_by(asc(sort_column) if sort_order == "asc" else desc(sort_column))
    products = query.offset((page - 1) * page_size).limit(page_size).all()
    return ok([serialize_product(product) for product in products], {"page": page, "page_size": page_size, "total": total})


@app.get("/api/v1/products/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    return ok(serialize_product(get_product_or_404(db, product_id, public_only=True)))


@app.get("/api/v1/internal/products/{product_id}", dependencies=[Depends(require_internal_token)])
def internal_get_product(product_id: str, db: Session = Depends(get_db)):
    return ok(serialize_product(get_product_or_404(db, product_id, public_only=True)))


@app.post("/api/v1/internal/products/reserve", dependencies=[Depends(require_internal_token)])
def reserve_products(payload: dict, db: Session = Depends(get_db)):
    items = payload.get("items") or []
    snapshots = []
    for item in items:
        product = get_product_or_404(db, item["product_id"], public_only=True)
        quantity = int(item["quantity"])
        if product.stock_qty < quantity:
            fail("validation_error", f"Product {product.sku} stock limit exceeded", 400)
        product.stock_qty -= quantity
        snapshots.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "product_sku": product.sku,
                "unit_price": str(product.price),
                "quantity": quantity,
                "line_total": str(product.price * quantity),
            }
        )
    db.commit()
    return ok({"items": snapshots})


@app.get("/api/v1/admin/products", dependencies=[Depends(require_internal_token)])
def admin_list_products(
    db: Session = Depends(get_db),
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    query = db.query(Product).options(selectinload(Product.images))
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Product.name.ilike(like), Product.sku.ilike(like)))
    total = query.count()
    products = query.order_by(desc(Product.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return ok([serialize_product(product) for product in products], {"page": page, "page_size": page_size, "total": total})


@app.post("/api/v1/admin/products", status_code=201, dependencies=[Depends(require_internal_token)])
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    if db.get(Category, payload.category_id) is None:
        fail("validation_error", "Category not found", 400)
    product = Product(**payload.model_dump(exclude={"images"}))
    product.images = [ProductImage(**image.model_dump()) for image in payload.images]
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        fail("conflict", "Product SKU or slug already exists", 409)
    db.refresh(product)
    return ok(serialize_product(product))


@app.put("/api/v1/admin/products/{product_id}", dependencies=[Depends(require_internal_token)])
def update_product(product_id: str, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = get_product_or_404(db, product_id)
    if db.get(Category, payload.category_id) is None:
        fail("validation_error", "Category not found", 400)
    for field, value in payload.model_dump(exclude={"images"}).items():
        setattr(product, field, value)
    if payload.images is not None:
        product.images = [ProductImage(**image.model_dump()) for image in payload.images]
    db.commit()
    db.refresh(product)
    return ok(serialize_product(product))


@app.patch("/api/v1/admin/products/{product_id}", dependencies=[Depends(require_internal_token)])
def patch_product(product_id: str, payload: ProductPatch, db: Session = Depends(get_db)):
    product = get_product_or_404(db, product_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return ok(serialize_product(product))


@app.delete("/api/v1/admin/products/{product_id}", status_code=204, dependencies=[Depends(require_internal_token)])
def delete_product(product_id: str, db: Session = Depends(get_db)):
    db.delete(get_product_or_404(db, product_id))
    db.commit()
    return None


@app.patch("/api/v1/admin/products/{product_id}/status", dependencies=[Depends(require_internal_token)])
def update_product_status(product_id: str, payload: ProductStatusUpdate, db: Session = Depends(get_db)):
    product = get_product_or_404(db, product_id)
    product.is_active = payload.is_active
    db.commit()
    db.refresh(product)
    return ok(serialize_product(product))


@app.post("/api/v1/admin/products/{product_id}/images", status_code=201, dependencies=[Depends(require_internal_token)])
def add_product_image(product_id: str, payload: ProductImageCreate, db: Session = Depends(get_db)):
    product = get_product_or_404(db, product_id)
    db.add(ProductImage(product_id=product.id, **payload.model_dump()))
    db.commit()
    db.refresh(product)
    return ok(serialize_product(product))

