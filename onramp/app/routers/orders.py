"""Orders API."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from hash_lib import get_jwt_payload, verify_signature
from app.db import get_db
from app.models import Order
from app.schemas import OrderCreate, OrderDetailResponse, OrderResponse, OrderStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])

INVALID_QUOTE_MESSAGE = "Invalid or expired quote."
UNAUTHORIZED_MESSAGE = "Invalid or missing authorization."


def require_jwt_payload(
    authorization: str | None = Header(None, alias="Authorization"),
) -> dict:
    """FastAPI dependency: return JWT payload or raise 401."""
    payload = get_jwt_payload(authorization)
    if payload is None:
        raise HTTPException(401, detail=UNAUTHORIZED_MESSAGE)
    return payload


@router.post("", response_model=OrderResponse)
def create_order(
    body: OrderCreate,
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    jwt_payload: dict = Depends(require_jwt_payload),
) -> OrderResponse:
    """Create an order from a quote. Validates JWT, quote signature and expiry; stores order in DB.
    Idempotency-Key required: same key + same body returns existing order; same key + different body returns 409."""
    client_ref = jwt_payload["client_ref"]
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

    new_quote = quote.model_dump(mode="json", by_alias=True)

    existing = db.execute(
        select(Order).where(
            Order.client_ref == client_ref,
            Order.idempotency_key == idempotency_key,
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.quote == new_quote:
            return OrderResponse(order_id=UUID(existing.order_id))
        raise HTTPException(409, detail="Idempotency key already used with different request body")

    order = Order(
        client_ref=client_ref,
        idempotency_key=idempotency_key,
        quote=new_quote,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return OrderResponse(order_id=UUID(order.order_id))


@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
) -> OrderDetailResponse:
    """Get order by id. Returns 404 if not found."""
    order = db.get(Order, str(order_id))
    if order is None:
        raise HTTPException(404, detail="Order not found")
    return OrderDetailResponse(
        order_id=UUID(order.order_id),
        status=order.status,
        client_ref=order.client_ref,
    )
