from functools import lru_cache
from typing import Annotated

from pydantic import AnyHttpUrl, BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_csv(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NEXUS_", env_file=".env", extra="ignore")

    app_name: str = "NEXUS"
    environment: str = "development"
    database_url: str = "sqlite:///./nexus.db"
    redis_url: str = "redis://localhost:6379/0"
    temporal_address: str = "localhost:7233"
    secret_key: str = Field(min_length=32, default="local-development-secret-change-for-production")
    access_token_minutes: int = 60 * 12
    refresh_token_days: int = 14
    cors_origins: Annotated[list[str], BeforeValidator(parse_csv)] = ["http://localhost:3000"]
    rate_limit_per_minute: int = 180
    seed_demo: bool = True
    encryption_key: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: AnyHttpUrl | None = None
    openai_api_key: str | None = None
    otlp_endpoint: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()

