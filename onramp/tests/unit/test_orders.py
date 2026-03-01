"""Unit tests for orders API (SQLite)."""

import time
from unittest.mock import patch

import jwt
import pytest
from fastapi.testclient import TestClient

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


def _order_headers(idempotency_key: str = "test-key") -> dict[str, str]:
    """Auth + required Idempotency-Key for POST /orders."""
    return {**_valid_auth_headers(), "Idempotency-Key": idempotency_key}


@pytest.mark.unit
def test_create_order_success(client: TestClient) -> None:
    """POST /api/v1/orders with valid quote and valid JWT returns order_id."""
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
        headers=_order_headers("test-key-123"),
    )
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data


@pytest.mark.unit
def test_create_order_missing_idempotency_key_returns_422(client: TestClient) -> None:
    """POST /api/v1/orders without Idempotency-Key returns 422."""
    response = client.post(
        "/api/v1/orders",
        json={
            "quote": {
                "from": "USD",
                "to": "EUR",
                "amount": 100.0,
                "fee": 0.1,
                "rate": 0.92,
                "expired_at": "2030-01-01T00:00:00+00:00",
                "signature": "fake",
            }
        },
        headers=_valid_auth_headers(),
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_order_unauthorized_without_header(client: TestClient) -> None:
    """POST /api/v1/orders without Authorization returns 401."""
    response = client.post(
        "/api/v1/orders",
        json={
            "quote": {
                "from": "USD",
                "to": "EUR",
                "amount": 100.0,
                "fee": 0.1,
                "rate": 0.92,
                "expired_at": "2030-01-01T00:00:00+00:00",
                "signature": "fake",
            }
        },
        headers={"Idempotency-Key": "req-key"},
    )
    assert response.status_code == 401


@pytest.mark.unit
def test_create_order_unauthorized_invalid_jwt(client: TestClient) -> None:
    """POST /api/v1/orders with invalid JWT returns 401."""
    response = client.post(
        "/api/v1/orders",
        json={
            "quote": {
                "from": "USD",
                "to": "EUR",
                "amount": 100.0,
                "fee": 0.1,
                "rate": 0.92,
                "expired_at": "2030-01-01T00:00:00+00:00",
                "signature": "fake",
            }
        },
        headers={"Authorization": "Bearer invalid.jwt.token", "Idempotency-Key": "req-key"},
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
                "from": "USD",
                "to": "EUR",
                "amount": 100.0,
                "fee": 0.1,
                "rate": 0.92,
                "expired_at": "2030-01-01T00:00:00+00:00",
                "signature": "fake",
            }
        },
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "req-key"},
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
                "from": "USD",
                "to": "EUR",
                "amount": 100.0,
                "fee": 0.1,
                "rate": 0.92,
                "expired_at": "2030-01-01T00:00:00+00:00",
                "signature": "fake",
            }
        },
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "req-key"},
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
                "from": "USD",
                "to": "EUR",
                "amount": 100.0,
                "fee": 0.1,
                "rate": 0.92,
                "expired_at": "2030-01-01T00:00:00+00:00",
                "signature": "fake",
            }
        },
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "req-key"},
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
    with patch("hash_lib.jwt.settings") as mock_settings:
        mock_settings.secret_key = settings.secret_key
        mock_settings.authentication_disabled = True
        response = client.post(
            "/api/v1/orders",
            json={
                "quote": {
                    "from": "USD",
                    "to": "EUR",
                    "amount": 100.0,
                    "fee": 0.1,
                    "rate": 0.92,
                    "expired_at": "2030-01-01T00:00:00+00:00",
                    "signature": "fake",
                }
            },
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "req-key"},
        )
    assert response.status_code == 400
    assert "Invalid or expired quote" in response.json()["detail"]


@pytest.mark.unit
def test_create_order_invalid_quote_signature(client: TestClient) -> None:
    """POST /api/v1/orders with invalid signature returns 400."""
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
            "signature": "invalid_signature",
        }
    }
    response = client.post(
        "/api/v1/orders",
        json=body,
        headers=_order_headers(),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired quote."


@pytest.mark.unit
def test_create_order_idempotency_same_key_same_body_returns_existing(client: TestClient) -> None:
    """POST twice with same Idempotency-Key and same body returns same order_id (ignore second)."""
    quote_response = client.post("/api/v1/quotes/USD/EUR", json={"amount": 2_000.0})
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
    headers = _order_headers("idem-same-123")
    r1 = client.post("/api/v1/orders", json=body, headers=headers)
    assert r1.status_code == 200
    order_id_1 = r1.json()["order_id"]
    r2 = client.post("/api/v1/orders", json=body, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["order_id"] == order_id_1


@pytest.mark.unit
def test_create_order_idempotency_same_key_different_body_returns_409(client: TestClient) -> None:
    """POST with same Idempotency-Key but different body returns 409 Conflict."""
    quote_response = client.post("/api/v1/quotes/USD/EUR", json={"amount": 2_000.0})
    assert quote_response.status_code == 200
    quote = quote_response.json()
    body1 = {
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
    headers = _order_headers("idem-diff-456")
    r1 = client.post("/api/v1/orders", json=body1, headers=headers)
    assert r1.status_code == 200

    quote2_response = client.post("/api/v1/quotes/USD/GBP", json={"amount": 2_000.0})
    assert quote2_response.status_code == 200
    quote2 = quote2_response.json()
    body2 = {
        "quote": {
            "from": quote2["from"],
            "to": quote2["to"],
            "amount": quote2["amount"],
            "fee": quote2["fee"],
            "rate": quote2["rate"],
            "expired_at": quote2["expired_at"],
            "signature": quote2["signature"],
        }
    }
    r2 = client.post("/api/v1/orders", json=body2, headers=headers)
    assert r2.status_code == 409
    assert "different" in r2.json()["detail"].lower()


@pytest.mark.unit
def test_create_order_idempotency_different_keys_same_client_creates_two_orders(
    client: TestClient,
) -> None:
    """Same client with different Idempotency-Keys creates two distinct orders."""
    quote_response = client.post("/api/v1/quotes/USD/EUR", json={"amount": 2_000.0})
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
    r1 = client.post("/api/v1/orders", json=body, headers=_order_headers("key-alpha"))
    assert r1.status_code == 200
    order_id_1 = r1.json()["order_id"]
    r2 = client.post("/api/v1/orders", json=body, headers=_order_headers("key-beta"))
    assert r2.status_code == 200
    order_id_2 = r2.json()["order_id"]
    assert order_id_1 != order_id_2


@pytest.mark.unit
def test_create_order_idempotency_same_key_different_clients_creates_two_orders(
    client: TestClient,
) -> None:
    """Same Idempotency-Key used by different clients (client_ref) creates two distinct orders."""
    quote_response = client.post("/api/v1/quotes/USD/EUR", json={"amount": 2_000.0})
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
    headers_client_a = _order_headers("shared-key")
    r1 = client.post("/api/v1/orders", json=body, headers=headers_client_a)
    assert r1.status_code == 200
    order_id_1 = r1.json()["order_id"]

    token_b = jwt.encode(
        {"client_ref": "other-client-ref", "expiration_at": int(time.time()) + 3600},
        settings.secret_key,
        algorithm=JWT_ALGORITHM,
    )
    headers_client_b = {"Authorization": f"Bearer {token_b}", "Idempotency-Key": "shared-key"}
    r2 = client.post("/api/v1/orders", json=body, headers=headers_client_b)
    assert r2.status_code == 200
    order_id_2 = r2.json()["order_id"]
    assert order_id_1 != order_id_2


@pytest.mark.unit
def test_create_order_idempotency_same_key_same_body_third_request_returns_same_order(
    client: TestClient,
) -> None:
    """Multiple POSTs with same Idempotency-Key and same body all return the same order_id."""
    quote_response = client.post("/api/v1/quotes/USD/EUR", json={"amount": 2_000.0})
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
    headers = _order_headers("idem-multi-789")
    r1 = client.post("/api/v1/orders", json=body, headers=headers)
    assert r1.status_code == 200
    order_id = r1.json()["order_id"]
    for _ in range(2):
        r = client.post("/api/v1/orders", json=body, headers=headers)
        assert r.status_code == 200
        assert r.json()["order_id"] == order_id


@pytest.mark.unit
def test_create_order_idempotency_409_returns_conflict_detail(client: TestClient) -> None:
    """POST with same key and different body returns 409 with descriptive detail."""
    quote_response = client.post("/api/v1/quotes/USD/EUR", json={"amount": 2_000.0})
    assert quote_response.status_code == 200
    quote = quote_response.json()
    body1 = {
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
    r1 = client.post("/api/v1/orders", json=body1, headers=_order_headers("conflict-key"))
    assert r1.status_code == 200

    quote2 = client.post("/api/v1/quotes/USD/GBP", json={"amount": 2_000.0}).json()
    body2 = {
        "quote": {
            "from": quote2["from"],
            "to": quote2["to"],
            "amount": quote2["amount"],
            "fee": quote2["fee"],
            "rate": quote2["rate"],
            "expired_at": quote2["expired_at"],
            "signature": quote2["signature"],
        }
    }
    r2 = client.post("/api/v1/orders", json=body2, headers=_order_headers("conflict-key"))
    assert r2.status_code == 409
    detail = r2.json()["detail"]
    assert "idempotency" in detail.lower() or "different" in detail.lower()
