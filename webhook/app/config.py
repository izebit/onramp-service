"""Application settings using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load from environment and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "webhook"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8001

    # JWT validation (must be at least 32 bytes in production)
    secret_key: str = "change-me-in-production-min-32-bytes!!"
    authentication_disabled: bool = False

    database_url: str = "postgresql://postgres:postgres@localhost:5432/webhook"
