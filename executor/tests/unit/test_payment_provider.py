"""Unit tests for payment_provider: get_order and execute_payment."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.config import Settings
from app.invoker.payment_provider import execute_payment, get_order


@pytest.fixture
def settings() -> Settings:
    return Settings(order_service_url="https://onramp.example.com")


class TestGetOrder:
    """Tests for get_order."""

    def test_returns_json_on_200(self, settings: Settings) -> None:
        """GET 200 returns response JSON."""
        data = {"order_id": "ord-123", "status": "PENDING", "client_ref": "client-a"}
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = data

        with patch("app.invoker.payment_provider.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            result = get_order("ord-123", settings)

        assert result == data
        mock_client.get.assert_called_once_with("https://onramp.example.com/api/v1/orders/ord-123")

    def test_strips_trailing_slash_from_base_url(self, settings: Settings) -> None:
        """order_service_url with trailing slash is stripped when building URL."""
        settings = Settings(order_service_url="https://api.test/")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {}

        with patch("app.invoker.payment_provider.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            get_order("id-456", settings)

        mock_client.get.assert_called_once_with("https://api.test/api/v1/orders/id-456")

    def test_returns_none_on_404(self, settings: Settings) -> None:
        """GET 404 returns None."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock(status_code=404)
        )
        with patch("app.invoker.payment_provider.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            result = get_order("missing", settings)

        assert result is None

    def test_returns_none_on_connection_error(self, settings: Settings) -> None:
        """Connection/request error returns None."""
        with patch("app.invoker.payment_provider.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.side_effect = httpx.ConnectError(
                "connection failed"
            )

            result = get_order("ord-1", settings)

        assert result is None


class TestExecutePayment:
    """Tests for execute_payment."""

    def test_returns_error_when_get_order_fails(self, settings: Settings) -> None:
        """When get_order returns None, execute_payment returns 'error'."""
        with patch("app.invoker.payment_provider.get_order", return_value=None):
            result = execute_payment("ord-1", settings)
        assert result == "error"

    def test_returns_success_when_get_order_ok_and_random_above_threshold(
        self, settings: Settings
    ) -> None:
        """When get_order returns data and random >= 0.2, returns 'success'."""
        with (
            patch("app.invoker.payment_provider.get_order", return_value={"order_id": "ord-1"}),
            patch("app.invoker.payment_provider.random.random", return_value=0.5),
        ):
            result = execute_payment("ord-1", settings)
        assert result == "success"

    def test_returns_error_when_get_order_ok_and_random_below_threshold(
        self, settings: Settings
    ) -> None:
        """When get_order returns data and random < 0.2, returns 'error'."""
        with (
            patch("app.invoker.payment_provider.get_order", return_value={"order_id": "ord-1"}),
            patch("app.invoker.payment_provider.random.random", return_value=0.1),
        ):
            result = execute_payment("ord-1", settings)
        assert result == "error"

    def test_passes_order_id_and_settings_to_get_order(self, settings: Settings) -> None:
        """execute_payment calls get_order with the given order_id and settings."""
        with (
            patch("app.invoker.payment_provider.get_order", return_value={}) as mock_get_order,
            patch("app.invoker.payment_provider.random.random", return_value=0.5),
        ):
            execute_payment("my-order-id", settings)
        mock_get_order.assert_called_once_with("my-order-id", settings)
