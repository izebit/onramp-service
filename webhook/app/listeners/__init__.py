"""Kafka listeners (e.g. Debezium CDC)."""

from app.listeners.orders_cdc import run_orders_cdc_consumer

__all__ = ["run_orders_cdc_consumer"]
