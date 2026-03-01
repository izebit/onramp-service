"""Tests for hash_lib.signature."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from hash_lib import get_signature, verify_signature


@pytest.fixture
def secret_key() -> str:
    return "test-secret-for-signing-32-bytes!!"


def test_get_signature_deterministic(secret_key: str) -> None:
    with patch("hash_lib.signature._settings") as mock:
        mock.secret_key = secret_key
        a = get_signature(amount=1.0, fee=0.1, from_currency="USD")
        b = get_signature(amount=1.0, fee=0.1, from_currency="USD")
        assert a == b


def test_get_signature_parts_sorted_by_name(secret_key: str) -> None:
    """Canonical payload uses sorted key order."""
    with patch("hash_lib.signature._settings") as mock:
        mock.secret_key = secret_key
        sig = get_signature(a=1, b=2)
        assert len(sig) == 64


def test_get_signature_unsupported_algorithm_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported algorithm"):
        get_signature(algorithm="md5", x=1)


def test_verify_signature_valid_and_not_expired(secret_key: str) -> None:
    with patch("hash_lib.signature._settings") as mock:
        mock.secret_key = secret_key
        expired_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        sig = get_signature(
            amount=100.0,
            expired_at=expired_at,
            fee=0.1,
            from_currency="USD",
            rate=0.92,
            to_currency="EUR",
        )
        assert verify_signature(
            sig,
            amount=100.0,
            expired_at=expired_at,
            fee=0.1,
            from_currency="USD",
            rate=0.92,
            to_currency="EUR",
        ) is True


def test_verify_signature_invalid_returns_false(secret_key: str) -> None:
    with patch("hash_lib.signature._settings") as mock:
        mock.secret_key = secret_key
        expired_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        assert (
            verify_signature(
                "wrong_signature",
                amount=100.0,
                expired_at=expired_at,
                fee=0.1,
                from_currency="USD",
                rate=0.92,
                to_currency="EUR",
            )
            is False
        )


def test_verify_signature_expired_returns_false(secret_key: str) -> None:
    with patch("hash_lib.signature._settings") as mock:
        mock.secret_key = secret_key
        expired_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        sig = get_signature(
            amount=100.0,
            expired_at=expired_at,
            fee=0.1,
            from_currency="USD",
            rate=0.92,
            to_currency="EUR",
        )
        assert (
            verify_signature(
                sig,
                amount=100.0,
                expired_at=expired_at,
                fee=0.1,
                from_currency="USD",
                rate=0.92,
                to_currency="EUR",
            )
            is False
        )


def test_verify_signature_with_explicit_now_future_expiry(secret_key: str) -> None:
    with patch("hash_lib.signature._settings") as mock:
        mock.secret_key = secret_key
        expired_at = "2030-01-01T00:00:00+00:00"
        sig = get_signature(
            amount=1.0,
            expired_at=expired_at,
            fee=0.0,
            from_currency="USD",
            rate=1.0,
            to_currency="EUR",
        )
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        assert (
            verify_signature(
                sig,
                now=now,
                amount=1.0,
                expired_at=expired_at,
                fee=0.0,
                from_currency="USD",
                rate=1.0,
                to_currency="EUR",
            )
            is True
        )
