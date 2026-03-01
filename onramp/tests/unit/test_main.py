"""Unit tests for main API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health(client: TestClient) -> None:
    """Health endpoint returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.unit
def test_root(client: TestClient) -> None:
    """Root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "onramp" in data["message"]
