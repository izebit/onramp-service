"""Mock payment provider: returns operation result (success, timeout, error)."""

from typing import Literal

from app.models import OrderProcessingStep

OperationResult = Literal["success", "timeout", "error"]


def execute_payment(step: OrderProcessingStep) -> OperationResult:
    """Execute payment for the order step. Mock implementation returns a result.
    Replace with real payment provider in production."""
    # Mock: always success (replace with real call or configurable mock)
    return "success"
