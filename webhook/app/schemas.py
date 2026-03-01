"""API request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, HttpUrl


class WebhookCreate(BaseModel):
    """Request body for registering a webhook."""

    url: HttpUrl
    signature_secret: str


class WebhookResponse(BaseModel):
    """Response after creating a webhook."""

    id: UUID
