"""AML check: amount and currency pair."""

from app.quotes.rate_provider import get_rate_provider
from app.schemas import Currency

MIN_AMOUNT_EUR = 1_000.0
MAX_AMOUNT_EUR = 100_000.0


def _amount_in_eur(amount: float, currency_from: Currency) -> float:
    """Convert amount from given currency to EUR."""
    if currency_from == Currency.EUR:
        return amount
    rate = get_rate_provider().get_rate(currency_from, Currency.EUR)
    return amount * rate


def _is_amount_in_allowed_range(amount: float, currency_from: Currency) -> bool:
    """Return True if amount in EUR is between MIN and MAX inclusive."""
    amount_eur = _amount_in_eur(amount, currency_from)
    return MIN_AMOUNT_EUR <= amount_eur <= MAX_AMOUNT_EUR


def check(
    amount: float,
    currency_from: Currency,
    currency_to: Currency,
) -> bool:
    """Run AML check on quote amount and currency pair. Returns True if check passes, False otherwise.
    Rule: amount (in EUR equivalent) must be between 1000 EUR and 100000 EUR inclusive."""
    return _is_amount_in_allowed_range(amount, currency_from)