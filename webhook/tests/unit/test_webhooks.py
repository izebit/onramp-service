"""Unit tests for webhooks API."""

import time

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


@pytest.mark.unit
def test_create_webhook_success(client: TestClient) -> None:
    """POST /api/v1/clients/webhooks with valid JWT and url returns id."""
    response = client.post(
        "/api/v1/clients/webhooks",
        json={"url": "https://example.com/hook", "signature_secret": "my-secret"},
        headers=_valid_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert len(data["id"]) == 36


@pytest.mark.unit
def test_create_webhook_unauthorized_without_header(client: TestClient) -> None:
    """POST without Authorization returns 401."""
    response = client.post(
        "/api/v1/clients/webhooks",
        json={"url": "https://example.com/hook", "signature_secret": "my-secret"},
    )
    assert response.status_code == 401


@pytest.mark.unit
def test_create_webhook_invalid_url(client: TestClient) -> None:
    """POST with invalid url returns 422."""
    response = client.post(
        "/api/v1/clients/webhooks",
        json={"url": "not-a-url", "signature_secret": "s"},
        headers=_valid_auth_headers(),
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_webhook_missing_signature_secret(client: TestClient) -> None:
    """POST without signature_secret returns 422."""
    response = client.post(
        "/api/v1/clients/webhooks",
        json={"url": "https://example.com/hook"},
        headers=_valid_auth_headers(),
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_webhook_duplicate_client_ref_url_returns_409(client: TestClient) -> None:
    """POST same (client_ref, url) twice returns 409."""
    payload = {"url": "https://example.com/hook-unique-for-dup-test", "signature_secret": "secret"}
    headers = _valid_auth_headers()
    r1 = client.post("/api/v1/clients/webhooks", json=payload, headers=headers)
    assert r1.status_code == 200
    r2 = client.post("/api/v1/clients/webhooks", json=payload, headers=headers)
    assert r2.status_code == 409
    assert "already registered" in r2.json().get("detail", "")
