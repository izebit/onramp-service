"""Unit tests for order_tasks CDC listener."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.listeners.order_tasks_cdc import (
    _order_id_and_status_from_envelope,
    process_order_task_envelope,
)
from app.schemas import OrderStatus


# Debezium event payload (executor.public.order_tasks) - create op with PROCESSING status
DEBEZIUM_ORDER_TASKS_EVENT = {
    "schema": {
        "type": "struct",
        "fields": [
            {"type": "struct", "fields": [{"field": "order_id", "type": "string"}, {"field": "status", "type": "string"}], "optional": True, "name": "executor.public.order_tasks.Value", "field": "before"},
            {"type": "struct", "fields": [{"field": "order_id", "type": "string"}, {"field": "status", "type": "string"}], "optional": True, "name": "executor.public.order_tasks.Value", "field": "after"},
            {"type": "struct", "fields": [], "optional": False, "name": "io.debezium.connector.postgresql.Source", "field": "source"},
            {"type": "string", "optional": False, "field": "op"},
            {"type": "int64", "optional": True, "field": "ts_ms"},
            {"type": "struct", "fields": [], "optional": True, "field": "transaction"},
        ],
        "optional": False,
        "name": "executor.public.order_tasks.Envelope",
        "version": 1,
    },
    "payload": {
        "before": None,
        "after": {
            "order_id": "fbf500b3-f417-4959-a92d-27eaa1bee7fc",
            "status": "PROCESSING",
        },
        "source": {
            "version": "2.5.4.Final",
            "connector": "postgresql",
            "name": "executor",
            "ts_ms": 1772416052329,
            "snapshot": "false",
            "db": "executor",
            "sequence": "[null,\"35821752\"]",
            "schema": "public",
            "table": "order_tasks",
            "txId": 743,
            "lsn": 35821752,
            "xmin": None,
        },
        "op": "c",
        "ts_ms": 1772416052789,
        "transaction": None,
    },
}

# Debezium event payload (executor.public.order_tasks) - update op with COMPLETED status
DEBEZIUM_ORDER_TASKS_UPDATE_EVENT = {
    "schema": {
        "type": "struct",
        "fields": [
            {"type": "struct", "fields": [{"field": "order_id", "type": "string"}, {"field": "status", "type": "string"}], "optional": True, "name": "executor.public.order_tasks.Value", "field": "before"},
            {"type": "struct", "fields": [{"field": "order_id", "type": "string"}, {"field": "status", "type": "string"}], "optional": True, "name": "executor.public.order_tasks.Value", "field": "after"},
            {"type": "struct", "fields": [], "optional": False, "name": "io.debezium.connector.postgresql.Source", "field": "source"},
            {"type": "string", "optional": False, "field": "op"},
            {"type": "int64", "optional": True, "field": "ts_ms"},
            {"type": "struct", "fields": [], "optional": True, "field": "transaction"},
        ],
        "optional": False,
        "name": "executor.public.order_tasks.Envelope",
        "version": 1,
    },
    "payload": {
        "before": None,
        "after": {
            "order_id": "fbf500b3-f417-4959-a92d-27eaa1bee7fc",
            "status": "COMPLETED",
        },
        "source": {
            "version": "2.5.4.Final",
            "connector": "postgresql",
            "name": "executor",
            "ts_ms": 1772416052937,
            "snapshot": "false",
            "db": "executor",
            "sequence": "[\"35822096\",\"35824272\"]",
            "schema": "public",
            "table": "order_tasks",
            "txId": 747,
            "lsn": 35824272,
            "xmin": None,
        },
        "op": "u",
        "ts_ms": 1772416053302,
        "transaction": None,
    },
}


@pytest.mark.unit
def test_order_id_and_status_from_envelope_debezium_create_processing() -> None:
    """Extract order_id and PROCESSING status from Debezium order_tasks create event."""
    envelope = DEBEZIUM_ORDER_TASKS_EVENT["payload"]
    order_id, order_status = _order_id_and_status_from_envelope(envelope)
    assert order_id == "fbf500b3-f417-4959-a92d-27eaa1bee7fc"
    assert order_status == OrderStatus.PROCESSING


@pytest.mark.unit
def test_order_id_and_status_from_envelope_debezium_update_completed() -> None:
    """Extract order_id and COMPLETED status from Debezium order_tasks update event."""
    envelope = DEBEZIUM_ORDER_TASKS_UPDATE_EVENT["payload"]
    order_id, order_status = _order_id_and_status_from_envelope(envelope)
    assert order_id == "fbf500b3-f417-4959-a92d-27eaa1bee7fc"
    assert order_status == OrderStatus.COMPLETED


@pytest.mark.unit
def test_process_order_task_envelope_updates_order() -> None:
    """process_order_task_envelope calls DB update with order_id and status from envelope."""
    envelope = DEBEZIUM_ORDER_TASKS_EVENT["payload"]
    settings = MagicMock()

    with patch("app.listeners.order_tasks_cdc._apply_order_task_update", return_value=True) as mock_update:
        result = asyncio.run(process_order_task_envelope(envelope, settings))
        assert result is True
        mock_update.assert_called_once_with(
            "fbf500b3-f417-4959-a92d-27eaa1bee7fc",
            OrderStatus.PROCESSING,
        )


@pytest.mark.unit
def test_process_order_task_envelope_update_completed() -> None:
    """process_order_task_envelope calls DB update with order_id and COMPLETED from update envelope."""
    envelope = DEBEZIUM_ORDER_TASKS_UPDATE_EVENT["payload"]
    settings = MagicMock()

    with patch("app.listeners.order_tasks_cdc._apply_order_task_update", return_value=True) as mock_update:
        result = asyncio.run(process_order_task_envelope(envelope, settings))
        assert result is True
        mock_update.assert_called_once_with(
            "fbf500b3-f417-4959-a92d-27eaa1bee7fc",
            OrderStatus.COMPLETED,
        )
