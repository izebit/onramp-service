"""Shared JWT authorization. Expects payload: client_ref (str), expiration_at (Unix timestamp)."""

from authorization.config import AuthSettings
from authorization.jwt import (
    JWT_ALGORITHM,
    UNAUTHORIZED_MESSAGE,
    get_jwt_payload,
)

__all__ = [
    "AuthSettings",
    "JWT_ALGORITHM",
    "UNAUTHORIZED_MESSAGE",
    "get_jwt_payload",
]
