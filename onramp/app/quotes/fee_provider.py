"""Fee provider for quote fees."""

from app.schemas import Currency

# Mock static fee (as decimal, e.g. 0.001 = 0.1%): (from_currency, to_currency) -> fee fraction
MOCK_FEE_FRACTIONS: dict[tuple[Currency, Currency], float] = {
    (Currency.USD, Currency.EUR): 0.001,
    (Currency.USD, Currency.GBP): 0.001,
    (Currency.USD, Currency.BTC): 0.002,
    (Currency.USD, Currency.ETH): 0.002,
    (Currency.EUR, Currency.USD): 0.001,
    (Currency.EUR, Currency.GBP): 0.001,
    (Currency.EUR, Currency.BTC): 0.002,
    (Currency.EUR, Currency.ETH): 0.002,
    (Currency.GBP, Currency.USD): 0.001,
    (Currency.GBP, Currency.EUR): 0.001,
    (Currency.GBP, Currency.BTC): 0.002,
    (Currency.GBP, Currency.ETH): 0.002,
    (Currency.BTC, Currency.USD): 0.005,
    (Currency.BTC, Currency.EUR): 0.005,
    (Currency.BTC, Currency.GBP): 0.005,
    (Currency.BTC, Currency.ETH): 0.003,
    (Currency.ETH, Currency.USD): 0.005,
    (Currency.ETH, Currency.EUR): 0.005,
    (Currency.ETH, Currency.GBP): 0.005,
    (Currency.ETH, Currency.BTC): 0.003,
}


class FeeProvider:
    """Provides fee for a quote (mock implementation with static data)."""

    def get_fee(self, from_currency: Currency, to_currency: Currency, amount: float) -> float:
        """Return the fee amount in from_currency for the given amount."""
        key = (from_currency, to_currency)
        if key not in MOCK_FEE_FRACTIONS:
            raise ValueError(f"No fee for {from_currency} -> {to_currency}")
        fraction = MOCK_FEE_FRACTIONS[key]
        return round(amount * fraction, 4)


def get_fee_provider() -> FeeProvider:
    """Return the fee provider instance (singleton-style for now)."""
    return FeeProvider()
