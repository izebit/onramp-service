"""Unit tests for AML checker."""

import pytest

from app.aml_checker.checker import MAX_AMOUNT_EUR, MIN_AMOUNT_EUR, check
from app.schemas import Currency


@pytest.mark.unit
def test_check_eur_below_min_fails() -> None:
    """Amount in EUR below 1000 returns False."""
    assert check(500.0, Currency.EUR, Currency.USD) is False
    assert check(999.99, Currency.EUR, Currency.USD) is False


@pytest.mark.unit
def test_check_eur_at_boundaries_passes() -> None:
    """Amount in EUR at 1000 or 100000 returns True."""
    assert check(MIN_AMOUNT_EUR, Currency.EUR, Currency.USD) is True
    assert check(MAX_AMOUNT_EUR, Currency.EUR, Currency.USD) is True


@pytest.mark.unit
def test_check_eur_in_range_passes() -> None:
    """Amount in EUR between 1000 and 100000 returns True."""
    assert check(50_000.0, Currency.EUR, Currency.USD) is True


@pytest.mark.unit
def test_check_eur_above_max_fails() -> None:
    """Amount in EUR above 100000 returns False."""
    assert check(100_001.0, Currency.EUR, Currency.USD) is False
    assert check(200_000.0, Currency.EUR, Currency.GBP) is False


@pytest.mark.unit
def test_check_usd_converted_to_eur_below_min_fails() -> None:
    """Amount in USD that converts to less than 1000 EUR returns False. (USD->EUR rate 0.92)"""
    assert check(500.0, Currency.USD, Currency.EUR) is False   # 460 EUR
    assert check(1_086.0, Currency.USD, Currency.EUR) is False  # ~999 EUR


@pytest.mark.unit
def test_check_usd_converted_to_eur_in_range_passes() -> None:
    """Amount in USD that converts to 1000–100000 EUR returns True. (USD->EUR rate 0.92)"""
    assert check(1_087.0, Currency.USD, Currency.EUR) is True   # > 1000 EUR
    assert check(2_000.0, Currency.USD, Currency.EUR) is True   # 1840 EUR
    assert check(100_000.0 / 0.92, Currency.USD, Currency.EUR) is True  # exactly 100000 EUR


@pytest.mark.unit
def test_check_usd_converted_to_eur_above_max_fails() -> None:
    """Amount in USD that converts to more than 100000 EUR returns False."""
    assert check(109_000.0, Currency.USD, Currency.EUR) is False  # > 100000 EUR


@pytest.mark.unit
def test_check_gbp_converted_to_eur() -> None:
    """Amount in GBP is converted to EUR using rate 1.16 (GBP->EUR)."""
    # 1000/1.16 ≈ 862.07 GBP -> 1000 EUR
    assert check(861.0, Currency.GBP, Currency.EUR) is False   # below 1000 EUR
    assert check(1000.0 / 1.16, Currency.GBP, Currency.EUR) is True   # 1000 EUR
    assert check(50_000.0, Currency.GBP, Currency.EUR) is True   # 58000 EUR
    assert check(100_000.0 / 1.16, Currency.GBP, Currency.EUR) is True   # 100000 EUR
    assert check(87_000.0, Currency.GBP, Currency.EUR) is False  # 100920 EUR > max


@pytest.mark.unit
def test_check_currency_to_ignored() -> None:
    """check uses only amount and currency_from; currency_to does not affect result."""
    assert check(5_000.0, Currency.EUR, Currency.USD) is True
    assert check(5_000.0, Currency.EUR, Currency.EUR) is True
    assert check(5_000.0, Currency.EUR, Currency.BTC) is True
