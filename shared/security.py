import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session_token(ttl_minutes: int) -> tuple[str, str, datetime]:
    token = secrets.token_urlsafe(40)
    return token, hash_token(token), datetime.now(UTC) + timedelta(minutes=ttl_minutes)

