"""Webhooks API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_jwt_payload
from app.db import get_db
from app.models import WebHook
from app.schemas import WebhookCreate, WebhookResponse

router = APIRouter(prefix="/clients/webhooks", tags=["webhooks"])

DUPLICATE_WEBHOOK_MESSAGE = "A webhook with this URL is already registered for this client."


@router.post("", response_model=WebhookResponse)
def create_webhook(
    body: WebhookCreate,
    db: Session = Depends(get_db),
    jwt_payload: dict = Depends(get_jwt_payload),
) -> WebhookResponse:
    """Register a webhook URL for the client identified by JWT (client_ref). (client_ref, url) is unique."""
    client_ref = jwt_payload["client_ref"]
    webhook = WebHook(
        client_ref=client_ref,
        url=str(body.url),
        signature_secret=body.signature_secret,
    )
    db.add(webhook)
    try:
        db.commit()
        db.refresh(webhook)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail=DUPLICATE_WEBHOOK_MESSAGE) from None
    return WebhookResponse(id=UUID(webhook.id))
