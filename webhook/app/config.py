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

    # Order service (REST) – fetch order by id for status
    order_service_url: str = "http://localhost:8000"

    # Sender: notification step delivery
    sending_max_retry: int = 5
    sending_timeout_in_seconds: float = 10.0

    # Kafka (Debezium CDC orders)
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_orders_topic: str = "dbserver1.public.orders"
    kafka_consumer_group: str = "webhook-orders-consumer"
