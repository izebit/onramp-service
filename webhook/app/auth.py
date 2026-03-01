"""JWT authentication. Expects client_ref and expiration_at in payload."""

import logging
import time
from typing import Any

import jwt
from fastapi import Header, HTTPException

from app.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

JWT_ALGORITHM = "HS256"
UNAUTHORIZED_MESSAGE = "Invalid or missing authorization."


def get_jwt_payload(
    authorization: str | None = Header(None, alias="Authorization"),
) -> dict[str, Any]:
    """Extract and validate Bearer JWT; return payload (must contain client_ref, expiration_at) or raise 401."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, detail=UNAUTHORIZED_MESSAGE)
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, detail=UNAUTHORIZED_MESSAGE)
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError as e:
        logger.debug("Invalid JWT: %s", e)
        raise HTTPException(401, detail=UNAUTHORIZED_MESSAGE) from e

    if "client_ref" not in payload or not isinstance(payload.get("client_ref"), str):
        logger.debug("JWT missing or invalid client_ref, payload=%s", payload)
        raise HTTPException(401, detail=UNAUTHORIZED_MESSAGE)
    if "expiration_at" not in payload:
        logger.debug("JWT missing expiration_at, payload=%s", payload)
        raise HTTPException(401, detail=UNAUTHORIZED_MESSAGE)
    exp_at = payload["expiration_at"]
    if not isinstance(exp_at, (int, float)):
        logger.debug("JWT expiration_at must be numeric, payload=%s", payload)
        raise HTTPException(401, detail=UNAUTHORIZED_MESSAGE)

    if not settings.authentication_disabled and exp_at <= time.time():
        logger.debug("JWT expired, payload=%s", payload)
        raise HTTPException(401, detail=UNAUTHORIZED_MESSAGE)

    return payload
