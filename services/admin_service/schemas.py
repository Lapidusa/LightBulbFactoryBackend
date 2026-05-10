from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    full_name: str
    role: str
    is_active: bool
    last_login_at: datetime | None

