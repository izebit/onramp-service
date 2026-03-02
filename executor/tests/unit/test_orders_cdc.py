"""Unit tests for orders CDC listener (onramp.public.orders)."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.listeners.orders_cdc import (
    _get_order_id_from_create_envelope,
    process_cdc_envelope,
)

# Debezium event (onramp.public.orders) - create op
DEBEZIUM_ORDERS_CREATE_EVENT = {
    "schema": {"type": "struct", "fields": []},
    "payload": {
        "before": None,
        "after": {
            "order_id": "fbf500b3-f417-4959-a92d-27eaa1bee7fc",
            "client_ref": "demo-client",
            "idempotency_key": "demo-idem-1772416051",
            "quote": "{\"from\": \"USD\", \"to\": \"EUR\", \"amount\": 5000.0}",
            "status": "PENDING",
            "created_at": "2026-03-02T01:47:32.126473Z",
        },
        "source": {"version": "2.5.4.Final", "connector": "postgresql", "name": "onramp", "db": "onramp", "schema": "public", "table": "orders"},
        "op": "c",
        "ts_ms": 1772416052269,
        "transaction": None,
    },
}

# Debezium event (onramp.public.orders) - update op
DEBEZIUM_ORDERS_UPDATE_EVENT = {
    "schema": {"type": "struct", "fields": []},
    "payload": {
        "before": None,
        "after": {
            "order_id": "fbf500b3-f417-4959-a92d-27eaa1bee7fc",
            "client_ref": "demo-client",
            "idempotency_key": "demo-idem-1772416051",
            "quote": "{\"from\": \"USD\", \"to\": \"EUR\", \"amount\": 5000.0}",
            "status": "PROCESSING",
            "created_at": "2026-03-02T01:47:32.126473Z",
        },
        "source": {"version": "2.5.4.Final", "connector": "postgresql", "name": "onramp", "ts_ms": 1772416052843, "db": "onramp", "schema": "public", "table": "orders", "txId": 745, "lsn": 35823304},
        "op": "u",
        "ts_ms": 1772416053288,
        "transaction": None,
    },
}


@pytest.mark.unit
def test_get_order_id_from_create_envelope_debezium_orders() -> None:
    """Extract order_id from Debezium onramp.orders create event."""
    envelope = DEBEZIUM_ORDERS_CREATE_EVENT["payload"]
    order_id = _get_order_id_from_create_envelope(envelope)
    assert order_id == "fbf500b3-f417-4959-a92d-27eaa1bee7fc"


@pytest.mark.unit
def test_get_order_id_from_update_envelope_returns_none() -> None:
    """Update event (op 'u') is ignored: _get_order_id_from_create_envelope returns None."""
    envelope = DEBEZIUM_ORDERS_UPDATE_EVENT["payload"]
    order_id = _get_order_id_from_create_envelope(envelope)
    assert order_id is None


@pytest.mark.unit
def test_process_cdc_envelope_with_debezium_payload() -> None:
    """process_cdc_envelope with create payload enqueues order (calls insert with order_id)."""
    envelope = DEBEZIUM_ORDERS_CREATE_EVENT["payload"]
    settings = MagicMock()
    mock_session = MagicMock()
    with (
        patch("app.listeners.orders_cdc.SessionLocal", return_value=mock_session),
        patch("app.listeners.orders_cdc._insert_order_processing_step") as mock_insert,
    ):
        result = asyncio.run(process_cdc_envelope(envelope, settings))
        assert result is True
        mock_insert.assert_called_once_with(mock_session, "fbf500b3-f417-4959-a92d-27eaa1bee7fc")
        mock_session.close.assert_called_once()


@pytest.mark.unit
def test_process_cdc_envelope_update_skipped() -> None:
    """process_cdc_envelope with update payload does not insert, returns False."""
    envelope = DEBEZIUM_ORDERS_UPDATE_EVENT["payload"]
    settings = MagicMock()
    with patch("app.listeners.orders_cdc._insert_order_processing_step") as mock_insert:
        result = asyncio.run(process_cdc_envelope(envelope, settings))
        assert result is False
        mock_insert.assert_not_called()
