"""Unit tests for signing module."""

from datetime import datetime, timedelta, timezone

import pytest

from hash_lib import get_signature, verify_signature


@pytest.mark.unit
def test_verify_signature_valid_and_not_expired() -> None:
    """Verify returns True when signature matches and expired_at is in the future."""
    expired_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    signature = get_signature(
        amount=100.0,
        expired_at=expired_at,
        fee=0.1,
        from_currency="USD",
        rate=0.92,
        to_currency="EUR",
    )
    assert verify_signature(
        signature,
        amount=100.0,
        expired_at=expired_at,
        fee=0.1,
        from_currency="USD",
        rate=0.92,
        to_currency="EUR",
    ) is True


@pytest.mark.unit
def test_verify_signature_invalid_returns_false() -> None:
    """Verify returns False when signature does not match."""
    expired_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    get_signature(
        amount=100.0,
        expired_at=expired_at,
        fee=0.1,
        from_currency="USD",
        rate=0.92,
        to_currency="EUR",
    )
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


@pytest.mark.unit
def test_verify_signature_expired_returns_false() -> None:
    """Verify returns False when expired_at is in the past."""
    expired_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    signature = get_signature(
        amount=100.0,
        expired_at=expired_at,
        fee=0.1,
        from_currency="USD",
        rate=0.92,
        to_currency="EUR",
    )
    assert (
        verify_signature(
            signature,
            amount=100.0,
            expired_at=expired_at,
            fee=0.1,
            from_currency="USD",
            rate=0.92,
            to_currency="EUR",
        )
        is False
    )
