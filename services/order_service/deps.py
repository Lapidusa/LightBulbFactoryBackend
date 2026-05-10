from fastapi import Header

from services.order_service.config import settings
from shared.responses import fail


def require_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    if x_internal_token != settings.internal_api_token:
        fail("forbidden", "Internal service token is invalid", 403)

