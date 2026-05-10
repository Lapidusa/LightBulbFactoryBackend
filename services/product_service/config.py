from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProductSettings(BaseSettings):
    database_url: str = Field(
        "postgresql+psycopg://product_user:product_password@localhost:15433/product_db",
        validation_alias="PRODUCT_DATABASE_URL",
    )
    internal_api_token: str = Field("dev-internal-token", validation_alias=AliasChoices("INTERNAL_API_TOKEN", "PRODUCT_INTERNAL_API_TOKEN"))

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = ProductSettings()
