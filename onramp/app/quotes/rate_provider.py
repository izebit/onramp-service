"""Rate provider for FX/crypto rates."""

from app.schemas import Currency

# Mock static rates: (from_currency, to_currency) -> rate (1 unit of from = rate units of to)
MOCK_RATES: dict[tuple[Currency, Currency], float] = {
    (Currency.USD, Currency.EUR): 0.92,
    (Currency.USD, Currency.GBP): 0.79,
    (Currency.USD, Currency.BTC): 0.000024,
    (Currency.USD, Currency.ETH): 0.00038,
    (Currency.EUR, Currency.USD): 1.09,
    (Currency.EUR, Currency.GBP): 0.86,
    (Currency.EUR, Currency.BTC): 0.000026,
    (Currency.EUR, Currency.ETH): 0.00041,
    (Currency.GBP, Currency.USD): 1.27,
    (Currency.GBP, Currency.EUR): 1.16,
    (Currency.GBP, Currency.BTC): 0.000030,
    (Currency.GBP, Currency.ETH): 0.00048,
    (Currency.BTC, Currency.USD): 41_666.67,
    (Currency.BTC, Currency.EUR): 38_461.54,
    (Currency.BTC, Currency.GBP): 33_333.33,
    (Currency.BTC, Currency.ETH): 15.5,
    (Currency.ETH, Currency.USD): 2_631.58,
    (Currency.ETH, Currency.EUR): 2_439.02,
    (Currency.ETH, Currency.GBP): 2_083.33,
    (Currency.ETH, Currency.BTC): 0.0645,
}


class RateProvider:
    """Provides conversion rates (mock implementation with static data)."""

    def get_rate(self, from_currency: Currency, to_currency: Currency) -> float:
        """Return the rate to convert 1 unit of from_currency to to_currency."""
        key = (from_currency, to_currency)
        if key not in MOCK_RATES:
            raise ValueError(f"No rate for {from_currency} -> {to_currency}")
        return MOCK_RATES[key]


def get_rate_provider() -> RateProvider:
    """Return the rate provider instance (singleton-style for now)."""
    return RateProvider()
