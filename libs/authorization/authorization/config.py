"""Auth-related settings. Read SECRET_KEY and AUTHENTICATION_DISABLED from env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    """Settings used for JWT validation. Load from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str = "change-me-in-production-min-32-bytes!!"
    authentication_disabled: bool = False
