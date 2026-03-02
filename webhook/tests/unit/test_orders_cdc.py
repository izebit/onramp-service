"""Unit tests for orders CDC listener (onramp.public.orders)."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.listeners.orders_cdc import (
    _get_client_ref_from_envelope,
    _get_order_id_from_envelope,
    _get_status_from_envelope,
    process_cdc_envelope,
)

# Debezium create event (onramp.public.orders) - op "c"
CDC_CREATE_ORDER_EVENT = {
    "schema": {
        "type": "struct",
        "fields": [
            {"type": "struct", "fields": [{"field": "order_id", "type": "string"}, {"field": "client_ref", "type": "string"}, {"field": "idempotency_key", "type": "string"}, {"field": "quote", "type": "string"}, {"field": "status", "type": "string"}, {"field": "created_at", "type": "string"}], "optional": True, "name": "onramp.public.orders.Value", "field": "before"},
            {"type": "struct", "fields": [{"field": "order_id", "type": "string"}, {"field": "client_ref", "type": "string"}, {"field": "idempotency_key", "type": "string"}, {"field": "quote", "type": "string"}, {"field": "status", "type": "string"}, {"field": "created_at", "type": "string"}], "optional": True, "name": "onramp.public.orders.Value", "field": "after"},
            {"type": "struct", "fields": [], "optional": False, "name": "io.debezium.connector.postgresql.Source", "field": "source"},
            {"type": "string", "optional": False, "field": "op"},
            {"type": "int64", "optional": True, "field": "ts_ms"},
            {"type": "struct", "fields": [], "optional": True, "field": "transaction"},
        ],
        "optional": False,
        "name": "onramp.public.orders.Envelope",
        "version": 1,
    },
    "payload": {
        "before": None,
        "after": {
            "order_id": "fbf500b3-f417-4959-a92d-27eaa1bee7fc",
            "client_ref": "demo-client",
            "idempotency_key": "demo-idem-1772416051",
            "quote": "{\"from\": \"USD\", \"to\": \"EUR\", \"amount\": 5000.0, \"fee\": 5.0, \"rate\": 0.92, \"expired_at\": \"2026-03-02T01:52:31Z\", \"signature\": \"02d43f395841594857f2e525d34024765cccd4d30375d43a00b61a2cb3f22648\"}",
            "status": "PENDING",
            "created_at": "2026-03-02T01:47:32.126473Z",
        },
        "source": {
            "version": "2.5.4.Final",
            "connector": "postgresql",
            "name": "onramp",
            "ts_ms": 1772416052127,
            "snapshot": "false",
            "db": "onramp",
            "sequence": "[null,\"35820056\"]",
            "schema": "public",
            "table": "orders",
            "txId": 742,
            "lsn": 35820056,
            "xmin": None,
        },
        "op": "c",
        "ts_ms": 1772416052269,
        "transaction": None,
    },
}

# Debezium update event (onramp.public.orders) - op "u"
CDC_UPDATE_ORDER_EVENT = {
    "schema": {
        "type": "struct",
        "fields": [
            {"type": "struct", "fields": [{"field": "order_id", "type": "string"}, {"field": "client_ref", "type": "string"}, {"field": "idempotency_key", "type": "string"}, {"field": "quote", "type": "string"}, {"field": "status", "type": "string"}, {"field": "created_at", "type": "string"}], "optional": True, "name": "onramp.public.orders.Value", "field": "before"},
            {"type": "struct", "fields": [{"field": "order_id", "type": "string"}, {"field": "client_ref", "type": "string"}, {"field": "idempotency_key", "type": "string"}, {"field": "quote", "type": "string"}, {"field": "status", "type": "string"}, {"field": "created_at", "type": "string"}], "optional": True, "name": "onramp.public.orders.Value", "field": "after"},
            {"type": "struct", "fields": [], "optional": False, "name": "io.debezium.connector.postgresql.Source", "field": "source"},
            {"type": "string", "optional": False, "field": "op"},
            {"type": "int64", "optional": True, "field": "ts_ms"},
            {"type": "struct", "fields": [], "optional": True, "field": "transaction"},
        ],
        "optional": False,
        "name": "onramp.public.orders.Envelope",
        "version": 1,
    },
    "payload": {
        "before": None,
        "after": {
            "order_id": "fbf500b3-f417-4959-a92d-27eaa1bee7fc",
            "client_ref": "demo-client",
            "idempotency_key": "demo-idem-1772416051",
            "quote": "{\"from\": \"USD\", \"to\": \"EUR\", \"amount\": 5000.0, \"fee\": 5.0, \"rate\": 0.92, \"expired_at\": \"2026-03-02T01:52:31Z\", \"signature\": \"02d43f395841594857f2e525d34024765cccd4d30375d43a00b61a2cb3f22648\"}",
            "status": "PROCESSING",
            "created_at": "2026-03-02T01:47:32.126473Z",
        },
        "source": {
            "version": "2.5.4.Final",
            "connector": "postgresql",
            "name": "onramp",
            "ts_ms": 1772416052843,
            "snapshot": "false",
            "db": "onramp",
            "sequence": "[\"35821168\",\"35823304\"]",
            "schema": "public",
            "table": "orders",
            "txId": 745,
            "lsn": 35823304,
            "xmin": None,
        },
        "op": "u",
        "ts_ms": 1772416053288,
        "transaction": None,
    },
}


@pytest.mark.unit
def test_get_order_id_from_envelope_cdc_create_order_event() -> None:
    """Extract order_id from CDC_CREATE_ORDER_EVENT payload."""
    envelope = CDC_CREATE_ORDER_EVENT["payload"]
    order_id = _get_order_id_from_envelope(envelope)
    assert order_id == "fbf500b3-f417-4959-a92d-27eaa1bee7fc"


@pytest.mark.unit
def test_get_status_from_envelope_cdc_create_order_event() -> None:
    """Extract status from CDC_CREATE_ORDER_EVENT payload."""
    envelope = CDC_CREATE_ORDER_EVENT["payload"]
    status = _get_status_from_envelope(envelope)
    assert status == "PENDING"


@pytest.mark.unit
def test_get_client_ref_from_envelope_cdc_create_order_event() -> None:
    """Extract client_ref from CDC_CREATE_ORDER_EVENT payload."""
    envelope = CDC_CREATE_ORDER_EVENT["payload"]
    client_ref = _get_client_ref_from_envelope(envelope)
    assert client_ref == "demo-client"


@pytest.mark.unit
def test_process_cdc_envelope_cdc_create_order_event() -> None:
    """process_cdc_envelope with CDC_CREATE_ORDER_EVENT uses payload only (no HTTP), upserts notification."""
    envelope = CDC_CREATE_ORDER_EVENT["payload"]
    settings = MagicMock()
    mock_session = MagicMock()
    with (
        patch("app.db.SessionLocal", return_value=mock_session),
        patch("app.listeners.orders_cdc._upsert_notification", return_value=True) as mock_upsert,
    ):
        result = asyncio.run(process_cdc_envelope(envelope, settings))
        assert result is True
        mock_upsert.assert_called_once_with(
            mock_session,
            "demo-client",
            "fbf500b3-f417-4959-a92d-27eaa1bee7fc",
            "PENDING",
        )
        mock_session.close.assert_called_once()


@pytest.mark.unit
def test_get_order_id_from_envelope_cdc_update_order_event() -> None:
    """Extract order_id from CDC_UPDATE_ORDER_EVENT payload."""
    envelope = CDC_UPDATE_ORDER_EVENT["payload"]
    order_id = _get_order_id_from_envelope(envelope)
    assert order_id == "fbf500b3-f417-4959-a92d-27eaa1bee7fc"


@pytest.mark.unit
def test_get_status_from_envelope_cdc_update_order_event() -> None:
    """Extract status from CDC_UPDATE_ORDER_EVENT payload."""
    envelope = CDC_UPDATE_ORDER_EVENT["payload"]
    status = _get_status_from_envelope(envelope)
    assert status == "PROCESSING"


@pytest.mark.unit
def test_get_client_ref_from_envelope_cdc_update_order_event() -> None:
    """Extract client_ref from CDC_UPDATE_ORDER_EVENT payload."""
    envelope = CDC_UPDATE_ORDER_EVENT["payload"]
    client_ref = _get_client_ref_from_envelope(envelope)
    assert client_ref == "demo-client"


@pytest.mark.unit
def test_process_cdc_envelope_cdc_update_order_event() -> None:
    """process_cdc_envelope with CDC_UPDATE_ORDER_EVENT uses payload only (no HTTP), upserts notification."""
    envelope = CDC_UPDATE_ORDER_EVENT["payload"]
    settings = MagicMock()
    mock_session = MagicMock()
    with (
        patch("app.db.SessionLocal", return_value=mock_session),
        patch("app.listeners.orders_cdc._upsert_notification", return_value=True) as mock_upsert,
    ):
        result = asyncio.run(process_cdc_envelope(envelope, settings))
        assert result is True
        mock_upsert.assert_called_once_with(
            mock_session,
            "demo-client",
            "fbf500b3-f417-4959-a92d-27eaa1bee7fc",
            "PROCESSING",
        )
        mock_session.close.assert_called_once()
