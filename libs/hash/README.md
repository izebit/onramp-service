# hash

Shared hash helpers and JWT auth. Used by webhook, onramp.

- `idempotency_key(client_ref, order_id, order_status) -> str` — SHA256 of `client_ref|order_id|order_status` (hex).
- `get_jwt_payload(authorization=Header(...))` — Validate Bearer JWT; payload: client_ref, expiration_at.
- `get_signature(**parts)`, `verify_signature(signature, **parts)` — HMAC-SHA256 quote signing (uses AuthSettings.secret_key).
- `AuthSettings`, `JWT_ALGORITHM`, `UNAUTHORIZED_MESSAGE`.
