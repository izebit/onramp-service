"""Idempotency key from client_ref, order_id, order_status."""

import hashlib


def idempotency_key(client_ref: str, order_id: str, order_status: str) -> str:
    """Compute Idempotency-Key value: SHA256(client_ref|order_id|order_status).hex."""
    raw = f"{client_ref}|{order_id}|{order_status}"
    return hashlib.sha256(raw.encode()).hexdigest()
