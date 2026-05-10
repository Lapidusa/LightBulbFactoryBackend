from datetime import UTC, datetime

import httpx
from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from services.admin_service.config import settings
from services.admin_service.db import Base, engine, get_db
from services.admin_service.deps import get_current_admin
from services.admin_service.models import AdminSession, AdminUser
from services.admin_service.schemas import AdminUserRead, LoginRequest, TokenResponse
from shared.fastapi import create_service_app
from shared.responses import fail, ok
from shared.security import create_session_token, hash_password, verify_password


app = create_service_app(
    title="Admin Panel Service",
    description="Микросервис аутентификации администратора, сессий, дашборда и маршрутизации admin API.",
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        if not db.query(AdminUser).filter(AdminUser.username == settings.admin_username).first():
            db.add(
                AdminUser(
                    username=settings.admin_username,
                    password_hash=hash_password(settings.admin_password),
                    full_name=settings.admin_full_name,
                    role="admin",
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()


def service_headers() -> dict[str, str]:
    return {"X-Internal-Token": settings.internal_api_token}


def service_request(method: str, base_url: str, path: str, request: Request, body: bytes | None = None) -> Response:
    try:
        response = httpx.request(
            method,
            f"{base_url}{path}",
            params=request.query_params,
            content=body,
            headers={**service_headers(), "Content-Type": request.headers.get("content-type", "application/json")},
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        fail("service_unavailable", f"Target service is unavailable: {exc}", 503)
    return Response(content=response.content, status_code=response.status_code, media_type=response.headers.get("content-type"))


@app.post("/api/v1/admin/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.username == payload.username).first()
    if admin is None or not admin.is_active or not verify_password(payload.password, admin.password_hash):
        fail("unauthorized", "Invalid username or password", 401)
    raw_token, token_hash, expires_at = create_session_token(settings.session_ttl_minutes)
    admin.last_login_at = datetime.now(UTC)
    db.add(AdminSession(admin_user_id=admin.id, token=token_hash, expires_at=expires_at))
    db.commit()
    return ok(TokenResponse(access_token=raw_token, expires_at=expires_at).model_dump(mode="json"))


@app.post("/api/v1/admin/auth/logout")
def logout(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    db.query(AdminSession).filter(
        AdminSession.admin_user_id == admin.id,
        AdminSession.revoked_at.is_(None),
        AdminSession.expires_at > datetime.now(UTC),
    ).update({"revoked_at": datetime.now(UTC)})
    db.commit()
    return ok({"logged_out": True})


@app.post("/api/v1/admin/auth/refresh")
def refresh_token(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    raw_token, token_hash, expires_at = create_session_token(settings.session_ttl_minutes)
    db.add(AdminSession(admin_user_id=admin.id, token=token_hash, expires_at=expires_at))
    db.commit()
    return ok(TokenResponse(access_token=raw_token, expires_at=expires_at).model_dump(mode="json"))


@app.get("/api/v1/admin/me")
def get_me(admin: AdminUser = Depends(get_current_admin)):
    return ok(AdminUserRead.model_validate(admin).model_dump(mode="json"))


@app.get("/api/v1/admin/dashboard/summary")
def dashboard_summary(_: AdminUser = Depends(get_current_admin)):
    try:
        products_response = httpx.get(
            f"{settings.product_service_url}/api/v1/admin/products",
            headers=service_headers(),
            params={"page": 1, "page_size": 1},
            timeout=5.0,
        )
        orders_response = httpx.get(
            f"{settings.order_service_url}/api/v1/admin/orders/summary",
            headers=service_headers(),
            timeout=5.0,
        )
    except httpx.HTTPError as exc:
        fail("service_unavailable", f"One of target services is unavailable: {exc}", 503)

    if products_response.status_code >= 400 or orders_response.status_code >= 400:
        fail("service_error", "Dashboard target service returned an error", 502)
    return ok(
        {
            "products_count": products_response.json()["meta"]["total"],
            "active_orders_count": orders_response.json()["data"]["active_orders_count"],
            "orders_by_status": orders_response.json()["data"]["orders_by_status"],
        }
    )


@app.api_route(
    "/api/v1/admin/products{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    dependencies=[Depends(get_current_admin)],
)
async def proxy_products(path: str, request: Request):
    body = await request.body()
    return service_request(request.method, settings.product_service_url, f"/api/v1/admin/products{path}", request, body)


@app.api_route(
    "/api/v1/admin/orders{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    dependencies=[Depends(get_current_admin)],
)
async def proxy_orders(path: str, request: Request):
    body = await request.body()
    return service_request(request.method, settings.order_service_url, f"/api/v1/admin/orders{path}", request, body)

