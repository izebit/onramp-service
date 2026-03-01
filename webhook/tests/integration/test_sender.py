"""Integration tests for sender: select pending steps, send to webhooks, mark completed or create retry."""

import hashlib
import hmac
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import select

from app.models import Notification, NotificationProcessingStep, ProcessingStepStatus, WebHook
from app.sender.processor import _run_cycle_sync
from app.sender.selector import select_pending_tasks


def _create_notification_and_step(
    db_session,
    client_ref: str = "client-sender-test",
    order_id: str | None = None,
    order_status: str = "COMPLETED",
) -> tuple[Notification, NotificationProcessingStep]:
    """Insert notification and a PENDING processing step. Returns (notification, step).
    Uses unique order_id if not provided (uuid4) to satisfy (order_id, order_status) unique constraint."""
    import uuid
    if order_id is None:
        order_id = str(uuid.uuid4())
    notification = Notification(
        client_ref=client_ref,
        order_id=order_id,
        order_status=order_status,
    )
    db_session.add(notification)
    db_session.flush()
    step = NotificationProcessingStep(
        notification_id=notification.id,
        status=ProcessingStepStatus.PENDING,
        process_after=datetime.now(timezone.utc),
    )
    db_session.add(step)
    db_session.commit()
    db_session.refresh(notification)
    db_session.refresh(step)
    return notification, step


def _create_webhook(db_session, client_ref: str, url: str = "https://example.com/hook", signature_secret: str = "secret") -> WebHook:
    """Insert a webhook for client_ref."""
    wh = WebHook(client_ref=client_ref, url=url, signature_secret=signature_secret)
    db_session.add(wh)
    db_session.commit()
    return wh


@pytest.mark.integration
def test_sender_step_completed_when_webhook_succeeds(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """Pending step with registered webhook: when send succeeds, step is marked COMPLETED."""
    notification, step = _create_notification_and_step(db_session, client_ref="client-a")
    _create_webhook(db_session, "client-a", url="https://example.com/callback")

    with patch("app.sender.processor.send_to_webhooks", return_value=True):
        _run_cycle_sync(settings)

    db_session.refresh(step)
    assert step.status == ProcessingStepStatus.COMPLETED


@pytest.mark.integration
def test_sender_step_completed_when_no_webhooks(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """Pending step with no webhooks for client_ref: step is marked COMPLETED (nothing to send)."""
    notification, step = _create_notification_and_step(db_session, client_ref="client-no-webhooks")

    _run_cycle_sync(settings)

    db_session.refresh(step)
    assert step.status == ProcessingStepStatus.COMPLETED


@pytest.mark.integration
def test_sender_step_failed_creates_retry_when_webhook_fails(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """When send fails, step is FAILED and a new PENDING step is created with process_after set."""
    notification, step = _create_notification_and_step(db_session, client_ref="client-retry")
    _create_webhook(db_session, "client-retry")

    with patch("app.sender.processor.send_to_webhooks", return_value=False):
        _run_cycle_sync(settings)

    db_session.refresh(step)
    assert step.status == ProcessingStepStatus.FAILED

    retries = list(
        db_session.scalars(
            select(NotificationProcessingStep)
            .where(NotificationProcessingStep.notification_id == notification.id)
            .order_by(NotificationProcessingStep.id)
        ).all()
    )
    assert len(retries) == 2
    new_step = retries[1]
    assert new_step.status == ProcessingStepStatus.PENDING
    assert new_step.process_after is not None
    assert new_step.attempt_count == 2


@pytest.mark.integration
def test_sender_webhook_sent_only_on_second_attempt(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """First send fails, retry step is created; second cycle sends successfully and marks step COMPLETED."""
    from datetime import timedelta

    notification, step = _create_notification_and_step(db_session, client_ref="client-second-time")
    _create_webhook(db_session, "client-second-time")

    with patch("app.sender.processor.send_to_webhooks", side_effect=[False, True]):
        _run_cycle_sync(settings)
        db_session.refresh(step)
        assert step.status == ProcessingStepStatus.FAILED

        retries = list(
            db_session.scalars(
                select(NotificationProcessingStep)
                .where(NotificationProcessingStep.notification_id == notification.id)
                .order_by(NotificationProcessingStep.id)
            ).all()
        )
        assert len(retries) == 2
        retry_step = retries[1]
        retry_step.process_after = datetime.now(timezone.utc) - timedelta(seconds=1)
        db_session.commit()

        _run_cycle_sync(settings)

        db_session.refresh(retry_step)
        assert retry_step.status == ProcessingStepStatus.COMPLETED


@pytest.mark.integration
def test_sender_tasks_not_run_when_process_after_in_future(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """When steps have process_after in the future, they are not selected and stay PENDING."""
    from datetime import timedelta

    notification, step = _create_notification_and_step(db_session, client_ref="client-delayed")
    _create_webhook(db_session, "client-delayed")
    step.process_after = datetime.now(timezone.utc) + timedelta(seconds=60)
    db_session.commit()
    db_session.refresh(step)

    with patch("app.sender.processor.send_to_webhooks") as mock_send:
        _run_cycle_sync(settings)

    mock_send.assert_not_called()
    db_session.refresh(step)
    assert step.status == ProcessingStepStatus.PENDING


@pytest.mark.integration
def test_sender_select_pending_tasks_returns_ready_steps(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """select_pending_tasks returns only steps that are PENDING, step count <= max, process_after <= now."""
    from datetime import timedelta

    notification, step = _create_notification_and_step(db_session, client_ref="client-select")
    step.process_after = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    db_session.refresh(step)

    tasks = select_pending_tasks(db_session, settings)
    assert len(tasks) == 1
    s, n, whs = tasks[0]
    assert s.id == step.id
    assert n.client_ref == "client-select"
    assert whs == []
    assert s.attempt_count == 1


def _expected_signature(payload_bytes: bytes, secret: str) -> str:
    """Compute X-Webhook-Signature the same way as sending._sign_payload."""
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()


@pytest.mark.integration
def test_sender_payload_and_signature_sent_to_webhook(
    settings,
    db_session,
    _patch_app_db,
) -> None:
    """When sending, request body is JSON with order_id/order_status and X-Webhook-Signature is HMAC-SHA256 of body."""
    order_id = "ord-payload-test-123"
    order_status = "COMPLETED"
    signature_secret = "my-secret-key"
    notification, step = _create_notification_and_step(
        db_session, client_ref="client-payload", order_id=order_id, order_status=order_status
    )
    _create_webhook(
        db_session, "client-payload", url="https://example.com/webhook", signature_secret=signature_secret
    )

    requests_captured: list[dict] = []

    def capture_post(url, content=None, headers=None, **kwargs):
        requests_captured.append({"url": url, "content": content, "headers": headers or {}})
        response = MagicMock()
        response.raise_for_status = MagicMock()
        return response

    with patch("app.sender.sending.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post.side_effect = capture_post
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client_class.return_value = mock_client

        _run_cycle_sync(settings)

    assert len(requests_captured) == 1
    req = requests_captured[0]
    assert req["url"] == "https://example.com/webhook"
    assert req["headers"].get("Content-Type") == "application/json"

    payload = json.loads(req["content"].decode())
    assert payload["order_id"] == order_id
    assert payload["order_status"] == order_status

    expected_sig = _expected_signature(req["content"], signature_secret)
    assert req["headers"].get("X-Webhook-Signature") == expected_sig