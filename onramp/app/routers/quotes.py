"""Quotes API."""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.quotes.fee_provider import get_fee_provider
from app.quotes.rate_provider import get_rate_provider
from app.config import Settings
from app.schemas import Currency, QuoteRequest, QuoteResponse

settings = Settings()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quotes", tags=["quotes"])
rate_provider = get_rate_provider()
fee_provider = get_fee_provider()

RATE_UNAVAILABLE_MESSAGE = (
    "We don't have an exchange rate for this currency pair right now. Please try another pair or try again later."
)
FEE_UNAVAILABLE_MESSAGE = (
    "We can't calculate a fee for this currency pair right now. Please try another pair or try again later."
)


@router.post("/{currency_from}/{currency_to}", response_model=QuoteResponse)
def create_quote(
    currency_from: Currency,
    currency_to: Currency,
    body: QuoteRequest,
) -> QuoteResponse:
    """Create a quote for converting amount from one currency to another."""
    if currency_from == currency_to:
        raise HTTPException(400, detail="from and to currencies must differ")

    if body.amount <= 0:
        raise HTTPException(400, detail="amount must be positive")

    try:
        rate = rate_provider.get_rate(currency_from, currency_to)
    except ValueError as e:
        logger.exception(
            "Failed to get rate for %s -> %s: %s",
            currency_from,
            currency_to,
            e,
        )
        raise HTTPException(404, detail=RATE_UNAVAILABLE_MESSAGE) from e

    try:
        fee = fee_provider.get_fee(currency_from, currency_to, body.amount)
    except ValueError as e:
        logger.exception(
            "Failed to get fee for %s -> %s: %s",
            currency_from,
            currency_to,
            e,
        )
        raise HTTPException(404, detail=FEE_UNAVAILABLE_MESSAGE) from e

    quote_id = uuid4()
    expired_at = datetime.now(timezone.utc).replace(microsecond=0)
    expired_at = expired_at + timedelta(seconds=settings.signature_valid_seconds)

    payload = f"{quote_id}{currency_from}{currency_to}{body.amount}{fee}{rate}{expired_at.isoformat()}"
    signature = hashlib.sha256(payload.encode()).hexdigest()

    return QuoteResponse(
        quote_id=quote_id,
        from_=currency_from,
        to=currency_to,
        amount=body.amount,
        fee=fee,
        rate=rate,
        expired_at=expired_at,
        signature=signature,
    )
