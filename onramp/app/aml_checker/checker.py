"""AML check: amount and currency pair."""

from app.schemas import Currency


def check(
    amount: float,
    currency_from: Currency,
    currency_to: Currency,
) -> bool:
    """Run AML check on quote amount and currency pair. Returns True if check passes, False otherwise."""
    # Stub: replace with real AML rules (limits, restricted pairs, etc.)
    return True
