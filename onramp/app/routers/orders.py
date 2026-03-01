"""Orders API."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_jwt_payload
from app.db import get_db
from app.models import Order
from app.quotes.signing import verify_signature
from app.schemas import OrderCreate, OrderResponse, OrderStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])

INVALID_QUOTE_MESSAGE = "Invalid or expired quote."


@router.post("", response_model=OrderResponse)
def create_order(
    body: OrderCreate,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    jwt_payload: dict = Depends(get_jwt_payload),
) -> OrderResponse:
    """Create an order from a quote. Validates JWT, quote signature and expiry; stores order in DB."""
    quote = body.quote
    expired_at_str = quote.expired_at.isoformat()
    is_valid = verify_signature(
        quote.signature,
        amount=quote.amount,
        expired_at=expired_at_str,
        fee=quote.fee,
        from_currency=quote.from_,
        rate=quote.rate,
        to_currency=quote.to,
    )
    if not is_valid:
        raise HTTPException(400, detail=INVALID_QUOTE_MESSAGE)

    order = Order(
        client_ref=jwt_payload["client_ref"],
        quote=quote.model_dump(mode="json", by_alias=True),
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return OrderResponse(order_id=UUID(order.order_id))
