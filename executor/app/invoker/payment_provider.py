"""Payment provider: fetch order from onramp service via REST, then mock success/error."""

import logging
import random
from typing import Any, Literal

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

OperationResult = Literal["success", "error"]


def get_order(order_id: str, settings: Settings) -> dict[str, Any] | None:
    """GET order by id from onramp service. Returns response JSON or None on failure."""
    base = settings.order_service_url.rstrip("/")
    url = f"{base}/api/v1/orders/{order_id}"
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(url)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error("Failed to fetch order %s from onramp: %s", order_id, e)
        return None


def execute_payment(order_id: str, settings: Settings) -> OperationResult:
    """Fetch order from onramp; mock 80% success, 20% error. Returns error if fetch fails."""
    order = get_order(order_id, settings)
    if order is None:
        return "error"

    if random.random() < 0.2:
        return "error"
    return "success"
