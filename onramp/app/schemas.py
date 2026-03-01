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
    """Quote response (no quote_id)."""

    model_config = ConfigDict(populate_by_name=True)

    from_: Currency = Field(alias="from")
    to: Currency
    amount: float
    fee: float
    rate: float
    expired_at: datetime
    signature: str


class OrderStatus(StrEnum):
    """Order lifecycle status."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class OrderQuote(BaseModel):
    """Quote payload when creating an order (no id)."""

    model_config = ConfigDict(populate_by_name=True)

    from_: Currency = Field(alias="from")
    to: Currency
    amount: float
    fee: float
    rate: float
    expired_at: datetime
    signature: str


class OrderCreate(BaseModel):
    """Request body for creating an order."""

    quote: OrderQuote


class OrderResponse(BaseModel):
    """Order creation response."""

    order_id: UUID


class OrderDetailResponse(BaseModel):
    """Order detail (by id) for external callers."""

    order_id: UUID
    status: OrderStatus
    client_ref: str
