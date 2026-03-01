"""Unit tests for orders API (SQLite)."""

import time
from unittest.mock import patch
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.auth import JWT_ALGORITHM
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


@pytest.mark.unit
def test_create_order_success(client: TestClient) -> None:
    """POST /api/v1/orders with valid quote and valid JWT returns order_id."""
    quote_response = client.post(
        "/api/v1/quotes/USD/EUR",
        json={"amount": 100.0},
    )
    assert quote_response.status_code == 200
    quote = quote_response.json()
    body = {
        "quote": {
            "id": quote["quote_id"],
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
        headers={
            **_valid_auth_headers(),
            "Idempotency-Key": "test-key-123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data


@pytest.mark.unit
def test_create_order_unauthorized_without_header(client: TestClient) -> None:
    """POST /api/v1/orders without Authorization returns 401."""
    response = client.post(
        "/api/v1/orders",
        json={
            "quote": {
                "id": str(uuid4()),
                "from": "USD",
                "to": "EUR",
                "amount": 100.0,
                "fee": 0.1,
                "rate": 0.92,
                "expired_at": "2030-01-01T00:00:00+00:00",
                "signature": "fake",
            }
        },
    )
    assert response.status_code == 401


@pytest.mark.unit
def test_create_order_unauthorized_invalid_jwt(client: TestClient) -> None:
    """POST /api/v1/orders with invalid JWT returns 401."""
    response = client.post(
        "/api/v1/orders",
        json={
            "quote": {
                "id": str(uuid4()),
                "from": "USD",
                "to": "EUR",
                "amount": 100.0,
                "fee": 0.1,
                "rate": 0.92,
                "expired_at": "2030-01-01T00:00:00+00:00",
                "signature": "fake",
            }
        },
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response.status_code == 401


@pytest.mark.unit
def test_create_order_unauthorized_jwt_without_client_ref(client: TestClient) -> None:
    """POST /api/v1/orders with JWT missing client_ref returns 401."""
    token = jwt.encode(
        {"expiration_at": int(time.time()) + 3600},
        settings.secret_key,
        algorithm=JWT_ALGORITHM,
    )
    response = client.post(
        "/api/v1/orders",
        json={
            "quote": {
                "id": str(uuid4()),
                "from": "USD",
                "to": "EUR",
                "amount": 100.0,
                "fee": 0.1,
                "rate": 0.92,
                "expired_at": "2030-01-01T00:00:00+00:00",
                "signature": "fake",
            }
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


@pytest.mark.unit
def test_create_order_unauthorized_jwt_without_expiration_at(client: TestClient) -> None:
    """POST /api/v1/orders with JWT missing expiration_at returns 401."""
    token = jwt.encode(
        {"client_ref": "test-client-ref"},
        settings.secret_key,
        algorithm=JWT_ALGORITHM,
    )
    response = client.post(
        "/api/v1/orders",
        json={
            "quote": {
                "id": str(uuid4()),
                "from": "USD",
                "to": "EUR",
                "amount": 100.0,
                "fee": 0.1,
                "rate": 0.92,
                "expired_at": "2030-01-01T00:00:00+00:00",
                "signature": "fake",
            }
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


@pytest.mark.unit
def test_create_order_unauthorized_expired_jwt(client: TestClient) -> None:
    """POST /api/v1/orders with expired JWT returns 401 when auth is enabled."""
    token = jwt.encode(
        {
            "client_ref": "test-client-ref",
            "expiration_at": int(time.time()) - 3600,
        },
        settings.secret_key,
        algorithm=JWT_ALGORITHM,
    )
    response = client.post(
        "/api/v1/orders",
        json={
            "quote": {
                "id": str(uuid4()),
                "from": "USD",
                "to": "EUR",
                "amount": 100.0,
                "fee": 0.1,
                "rate": 0.92,
                "expired_at": "2030-01-01T00:00:00+00:00",
                "signature": "fake",
            }
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


@pytest.mark.unit
def test_create_order_expired_jwt_accepted_when_authentication_disabled(
    client: TestClient,
) -> None:
    """POST /api/v1/orders with expired JWT returns 400 when quote invalid (auth disabled)."""
    token = jwt.encode(
        {
            "client_ref": "test-client-ref",
            "expiration_at": int(time.time()) - 3600,
        },
        settings.secret_key,
        algorithm=JWT_ALGORITHM,
    )
    with patch("app.auth.settings") as mock_settings:
        mock_settings.secret_key = settings.secret_key
        mock_settings.authentication_disabled = True
        response = client.post(
            "/api/v1/orders",
            json={
                "quote": {
                    "id": str(uuid4()),
                    "from": "USD",
                    "to": "EUR",
                    "amount": 100.0,
                    "fee": 0.1,
                    "rate": 0.92,
                    "expired_at": "2030-01-01T00:00:00+00:00",
                    "signature": "fake",
                }
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 400
    assert "Invalid or expired quote" in response.json()["detail"]


@pytest.mark.unit
def test_create_order_invalid_quote_signature(client: TestClient) -> None:
    """POST /api/v1/orders with invalid signature returns 400."""
    quote_response = client.post(
        "/api/v1/quotes/USD/EUR",
        json={"amount": 100.0},
    )
    assert quote_response.status_code == 200
    quote = quote_response.json()
    body = {
        "quote": {
            "id": quote["quote_id"],
            "from": quote["from"],
            "to": quote["to"],
            "amount": quote["amount"],
            "fee": quote["fee"],
            "rate": quote["rate"],
            "expired_at": quote["expired_at"],
            "signature": "invalid_signature",
        }
    }
    response = client.post(
        "/api/v1/orders",
        json=body,
        headers=_valid_auth_headers(),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired quote."
