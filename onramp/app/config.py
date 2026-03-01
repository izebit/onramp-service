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
