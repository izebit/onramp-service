"""Unit tests for quotes API."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_create_quote_success(client: TestClient) -> None:
    """POST /api/v1/quotes/USD/EUR returns quote with required fields and mock rate."""
    response = client.post(
        "/api/v1/quotes/USD/EUR",
        json={"amount": 100.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert "quote_id" in data
    assert data["from"] == "USD"
    assert data["to"] == "EUR"
    assert data["amount"] == 100.0
    assert data["rate"] == 0.92  # from mock static data
    assert data["fee"] == 0.1  # 0.1% of 100 from mock static data
    assert "expired_at" in data
    assert "signature" in data


@pytest.mark.unit
def test_create_quote_same_currency(client: TestClient) -> None:
    """POST with same from and to returns 400."""
    response = client.post(
        "/api/v1/quotes/USD/USD",
        json={"amount": 100.0},
    )
    assert response.status_code == 400


@pytest.mark.unit
def test_create_quote_invalid_amount(client: TestClient) -> None:
    """POST with non-positive amount returns 400."""
    response = client.post(
        "/api/v1/quotes/USD/EUR",
        json={"amount": 0},
    )
    assert response.status_code == 400


@pytest.mark.unit
def test_create_quote_rate_unavailable_returns_human_readable_error(
    client: TestClient,
) -> None:
    """When rate cannot be got, log and return rate-specific 400."""
    with patch(
        "app.routers.quotes.rate_provider.get_rate",
        side_effect=ValueError("No rate for USD -> XYZ"),
    ):
        response = client.post(
            "/api/v1/quotes/USD/EUR",
            json={"amount": 100.0},
        )
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "We don't have an exchange rate for this currency pair. The given currency pair is not supported."
    )


@pytest.mark.unit
def test_create_quote_fee_unavailable_returns_internal_error(
    client: TestClient,
) -> None:
    """When fee cannot be got, log and return 500 internal error."""
    with patch(
        "app.routers.quotes.fee_provider.get_fee",
        side_effect=ValueError("No fee for USD -> EUR"),
    ):
        response = client.post(
            "/api/v1/quotes/USD/EUR",
            json={"amount": 100.0},
        )
    assert response.status_code == 500
    assert response.json()["detail"] == (
        "We can't calculate a fee for this currency pair right now. Please try another pair or try again later."
    )
