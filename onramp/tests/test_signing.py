"""Tests for signing module."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.quotes.signing import get_signature, verify_signature


def test_verify_signature_valid_and_not_expired() -> None:
    """Verify returns True when signature matches and expired_at is in the future."""
    quote_id = uuid4()
    expired_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    signature = get_signature(
        amount=100.0,
        expired_at=expired_at,
        fee=0.1,
        from_currency="USD",
        quote_id=quote_id,
        rate=0.92,
        to_currency="EUR",
    )
    assert verify_signature(
        signature,
        amount=100.0,
        expired_at=expired_at,
        fee=0.1,
        from_currency="USD",
        quote_id=quote_id,
        rate=0.92,
        to_currency="EUR",
    ) is True


def test_verify_signature_invalid_returns_false() -> None:
    """Verify returns False when signature does not match."""
    quote_id = uuid4()
    expired_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    get_signature(
        amount=100.0,
        expired_at=expired_at,
        fee=0.1,
        from_currency="USD",
        quote_id=quote_id,
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
            quote_id=quote_id,
            rate=0.92,
            to_currency="EUR",
        )
        is False
    )


def test_verify_signature_expired_returns_false() -> None:
    """Verify returns False when expired_at is in the past."""
    quote_id = uuid4()
    expired_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    signature = get_signature(
        amount=100.0,
        expired_at=expired_at,
        fee=0.1,
        from_currency="USD",
        quote_id=quote_id,
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
            quote_id=quote_id,
            rate=0.92,
            to_currency="EUR",
        )
        is False
    )
