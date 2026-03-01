"""Send notification payload to webhook URLs."""

import hashlib
import hmac
import json
import logging

import httpx

from app.models import Notification, WebHook

logger = logging.getLogger(__name__)


def _sign_payload(payload: bytes, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()


def build_payload(notification: Notification) -> dict:
    """Build JSON payload for webhook delivery."""
    return {
        "order_id": notification.order_id,
        "order_status": notification.order_status,
    }


def send_to_webhooks(payload: dict, webhooks: list[WebHook], timeout_seconds: float = 10.0) -> bool:
    """POST payload to each webhook URL (sync). Returns True if all succeed."""
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    with httpx.Client(timeout=timeout_seconds) as client:
        for wh in webhooks:
            try:
                signature = _sign_payload(payload_bytes, wh.signature_secret or "")
                headers = {
                    "Content-Type": "application/json", 
                    "X-Webhook-Signature": signature
                }
                r = client.post(wh.url, content=payload_bytes, headers=headers)
                r.raise_for_status()
            except Exception as e:
                logger.warning("Webhook delivery failed url=%s: %s", wh.url, e)
                return False
    return True
