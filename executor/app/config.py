"""Application settings using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load from environment and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "executor"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8002

    database_url: str = "postgresql://postgres:postgres@localhost:5432/executor"

    # Invoker: process order_processing_steps (payment + retry)
    execution_max_retry: int = 5
    order_service_url: str = "http://localhost:8000"

    # Kafka (Debezium CDC orders)
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_orders_topic: str = "onramp.public.orders"
    kafka_consumer_group: str = "executor-orders-consumer"
