"""JWT validation: Bearer token, payload must contain client_ref and expiration_at."""

import logging
import time
from typing import Any

import jwt

from hash_lib.config import AuthSettings

logger = logging.getLogger(__name__)
settings = AuthSettings()

JWT_ALGORITHM = "HS256"


def get_jwt_payload(authorization: str | None) -> dict[str, Any] | None:
    """Validate Bearer JWT; return payload or None if invalid.

    Payload must contain client_ref (string) and expiration_at (Unix timestamp).
    expiration_at is ignored when authentication_disabled is True.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError as e:
        logger.debug("Invalid JWT: %s", e)
        return None

    if "client_ref" not in payload or not isinstance(payload.get("client_ref"), str):
        logger.debug("JWT missing or invalid client_ref, payload=%s", payload)
        return None
    if "expiration_at" not in payload:
        logger.debug("JWT missing expiration_at, payload=%s", payload)
        return None
    exp_at = payload["expiration_at"]
    if not isinstance(exp_at, (int, float)):
        logger.debug("JWT expiration_at must be numeric, payload=%s", payload)
        return None

    if not settings.authentication_disabled and exp_at <= time.time():
        logger.debug("JWT expired, payload=%s", payload)
        return None

    return payload
