"""Send notification payload to webhook URLs."""

import hashlib
import hmac
import json
import logging

import httpx
from hash_lib import idempotency_key

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


def send_to_webhooks(
    payload: dict,
    webhooks: list[WebHook],
    *,
    client_ref: str,
    timeout_seconds: float = 10.0,
) -> bool:
    """POST payload to each webhook URL (sync). Returns True if all succeed."""
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    idem_key = idempotency_key(
        client_ref,
        payload["order_id"],
        payload["order_status"],
    )
    with httpx.Client(timeout=timeout_seconds) as client:
        for wh in webhooks:
            try:
                signature = _sign_payload(payload_bytes, wh.signature_secret or "")
                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "Idempotency-Key": idem_key,
                }
                r = client.post(wh.url, content=payload_bytes, headers=headers)
                r.raise_for_status()
            except Exception as e:
                logger.warning("Webhook delivery failed url=%s: %s", wh.url, e)
                return False
    return True
