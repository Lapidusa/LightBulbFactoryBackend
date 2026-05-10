from datetime import UTC, datetime

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from services.admin_service.db import get_db
from services.admin_service.models import AdminSession, AdminUser
from shared.responses import fail
from shared.security import hash_token


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    if credentials is None:
        fail("unauthorized", "Authorization Bearer token is required", 401)
    session = (
        db.query(AdminSession)
        .join(AdminUser)
        .filter(
            AdminSession.token == hash_token(credentials.credentials),
            AdminSession.revoked_at.is_(None),
            AdminSession.expires_at > datetime.now(UTC),
            AdminUser.is_active.is_(True),
        )
        .first()
    )
    if session is None:
        fail("unauthorized", "Invalid or expired token", 401)
    return session.admin_user

