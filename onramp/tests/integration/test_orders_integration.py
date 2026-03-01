"""Integration tests for orders API (real PostgreSQL via Testcontainers)."""

import time

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from hash_lib import JWT_ALGORITHM

from app.config import Settings

settings = Settings()


def _valid_auth_headers() -> dict[str, str]:
    token = jwt.encode(
        {
            "client_ref": "test-client-ref",
            "expiration_at": int(time.time()) + 3600,
        },
        settings.secret_key,
        algorithm=JWT_ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
def test_create_order_persisted_in_postgres(
    client: TestClient,
    integration_session_factory,
) -> None:
    """Create order via API and verify it is stored in PostgreSQL."""
    quote_response = client.post(
        "/api/v1/quotes/USD/EUR",
        json={"amount": 2_000.0},
    )
    assert quote_response.status_code == 200
    quote = quote_response.json()
    body = {
        "quote": {
            "from": quote["from"],
            "to": quote["to"],
            "amount": quote["amount"],
            "fee": quote["fee"],
            "rate": quote["rate"],
            "expired_at": quote["expired_at"],
            "signature": quote["signature"],
        }
    }
    response = client.post(
        "/api/v1/orders",
        json=body,
        headers={**_valid_auth_headers(), "Idempotency-Key": "integration-test-key"},
    )
    assert response.status_code == 200
    data = response.json()
    order_id = data["order_id"]
    assert order_id

    # Verify the order is in PostgreSQL
    session: Session = integration_session_factory()
    try:
        from app.models import Order

        order = session.get(Order, order_id)
        assert order is not None
        assert order.client_ref == "test-client-ref"
        assert order.status.value == "PENDING"
        assert order.quote["from"] == "USD"
        assert order.quote["to"] == "EUR"
        assert order.quote["amount"] == 2_000.0
    finally:
        session.close()
