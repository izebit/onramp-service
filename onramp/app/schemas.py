"""API request/response schemas."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Currency(StrEnum):
    """Supported currency code."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    BTC = "BTC"
    ETH = "ETH"


class QuoteRequest(BaseModel):
    """Request body for creating a quote."""

    amount: float


class QuoteResponse(BaseModel):
    """Quote response."""

    model_config = ConfigDict(populate_by_name=True)

    quote_id: UUID
    from_: Currency = Field(alias="from")
    to: Currency
    amount: float
    fee: float
    rate: float
    expired_at: datetime
    signature: str
