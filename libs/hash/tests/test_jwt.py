"""Tests for hash_lib.jwt."""

import time
from unittest.mock import patch

import jwt
import pytest

from hash_lib import JWT_ALGORITHM, get_jwt_payload


@pytest.fixture
def secret_key() -> str:
    return "test-secret-key-min-32-bytes-long!!"


def _encode(payload: dict, secret: str) -> str:
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def test_get_jwt_payload_none_returns_none() -> None:
    assert get_jwt_payload(None) is None


def test_get_jwt_payload_empty_string_returns_none() -> None:
    assert get_jwt_payload("") is None


def test_get_jwt_payload_no_bearer_prefix_returns_none() -> None:
    assert get_jwt_payload("not-bearer token") is None


def test_get_jwt_payload_bearer_only_whitespace_token_returns_none() -> None:
    assert get_jwt_payload("Bearer   ") is None


def test_get_jwt_payload_valid_returns_payload(secret_key: str) -> None:
    with patch("hash_lib.jwt.settings") as mock:
        mock.secret_key = secret_key
        mock.authentication_disabled = True
        payload = {"client_ref": "client-1", "expiration_at": 0}
        token = _encode(payload, secret_key)
        result = get_jwt_payload(f"Bearer {token}")
    assert result == payload


def test_get_jwt_payload_invalid_token_returns_none(secret_key: str) -> None:
    with patch("hash_lib.jwt.settings") as mock:
        mock.secret_key = secret_key
        result = get_jwt_payload("Bearer invalid-token")
    assert result is None


def test_get_jwt_payload_wrong_secret_returns_none(secret_key: str) -> None:
    with patch("hash_lib.jwt.settings") as mock:
        mock.secret_key = "other-secret-min-32-bytes-long!!!"
        payload = {"client_ref": "c", "expiration_at": 9999999999}
        token = _encode(payload, secret_key)
        result = get_jwt_payload(f"Bearer {token}")
    assert result is None


def test_get_jwt_payload_missing_client_ref_returns_none(secret_key: str) -> None:
    with patch("hash_lib.jwt.settings") as mock:
        mock.secret_key = secret_key
        mock.authentication_disabled = True
        payload = {"expiration_at": 9999999999}
        token = _encode(payload, secret_key)
        result = get_jwt_payload(f"Bearer {token}")
    assert result is None


def test_get_jwt_payload_missing_expiration_at_returns_none(secret_key: str) -> None:
    with patch("hash_lib.jwt.settings") as mock:
        mock.secret_key = secret_key
        mock.authentication_disabled = True
        payload = {"client_ref": "c"}
        token = _encode(payload, secret_key)
        result = get_jwt_payload(f"Bearer {token}")
    assert result is None


def test_get_jwt_payload_expired_returns_none_when_auth_enabled(secret_key: str) -> None:
    with patch("hash_lib.jwt.settings") as mock:
        mock.secret_key = secret_key
        mock.authentication_disabled = False
        payload = {"client_ref": "c", "expiration_at": int(time.time()) - 60}
        token = _encode(payload, secret_key)
        result = get_jwt_payload(f"Bearer {token}")
    assert result is None


def test_get_jwt_payload_expired_returns_payload_when_auth_disabled(secret_key: str) -> None:
    with patch("hash_lib.jwt.settings") as mock:
        mock.secret_key = secret_key
        mock.authentication_disabled = True
        payload = {"client_ref": "c", "expiration_at": 0}
        token = _encode(payload, secret_key)
        result = get_jwt_payload(f"Bearer {token}")
    assert result == payload
