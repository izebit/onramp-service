"""Application settings using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load from environment and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "onramp"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # How long a quote signature is valid (seconds)
    signature_valid_seconds: int = 300

    # Shared secret for JWT validation and for signing quote payloads (HMAC-SHA256).
    # Must be at least 32 bytes in production (set via SECRET_KEY env).
    secret_key: str = "change-me-in-production-min-32-bytes!!"

    # If True, JWT expiration_at is not checked during validation
    authentication_disabled: bool = False

    # PostgreSQL
    database_url: str = "postgresql://postgres:postgres@localhost:5432/onramp"
