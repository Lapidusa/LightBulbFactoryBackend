from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OrderSettings(BaseSettings):
    database_url: str = Field(
        "postgresql+psycopg://order_user:order_password@localhost:15434/order_db",
        validation_alias="ORDER_DATABASE_URL",
    )
    product_service_url: str = Field("http://127.0.0.1:18001", validation_alias="PRODUCT_SERVICE_URL")
    internal_api_token: str = Field("dev-internal-token", validation_alias=AliasChoices("INTERNAL_API_TOKEN", "ORDER_INTERNAL_API_TOKEN"))

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = OrderSettings()
