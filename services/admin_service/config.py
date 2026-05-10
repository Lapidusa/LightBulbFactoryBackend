from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    database_url: str = Field(
        "postgresql+psycopg://admin_user:admin_password@localhost:15435/admin_db",
        validation_alias="ADMIN_DATABASE_URL",
    )
    admin_username: str = "admin"
    admin_password: str = "admin123"
    admin_full_name: str = "System Administrator"
    session_ttl_minutes: int = 1440
    product_service_url: str = "http://127.0.0.1:18001"
    order_service_url: str = "http://127.0.0.1:18002"
    internal_api_token: str = Field("dev-internal-token", validation_alias=AliasChoices("INTERNAL_API_TOKEN", "ADMIN_INTERNAL_API_TOKEN"))

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = AdminSettings()
