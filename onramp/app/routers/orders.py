"""Orders API."""

import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException

from app.auth import get_jwt_payload
from app.quotes.signing import verify_signature
from app.schemas import OrderCreate, OrderResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])

INVALID_QUOTE_MESSAGE = "Invalid or expired quote."


@router.post("", response_model=OrderResponse)
def create_order(
    body: OrderCreate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    jwt_payload: dict = Depends(get_jwt_payload),
) -> OrderResponse:
    """Create an order from a quote. Validates JWT, quote signature and expiry."""
    quote = body.quote
    expired_at_str = quote.expired_at.isoformat()
    is_valid = verify_signature(
        quote.signature,
        amount=quote.amount,
        expired_at=expired_at_str,
        fee=quote.fee,
        from_currency=quote.from_,
        quote_id=quote.id,
        rate=quote.rate,
        to_currency=quote.to,
    )
    if not is_valid:
        raise HTTPException(400, detail=INVALID_QUOTE_MESSAGE)

    # Stub: generate order_id; idempotency_key can be used later for deduplication
    order_id: UUID = uuid4()
    return OrderResponse(order_id=order_id)
