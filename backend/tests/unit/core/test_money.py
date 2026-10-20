"""Test-first (constitution Principle III) for the micro-USD money type.

1 micro-USD = 1e-6 USD. All money on the TokenPulse money path is integer micro-USD;
floats are never used for money.
"""

from decimal import Decimal

import pytest

from tokenpulse.core import money


class TestUsdMicrosRoundTrip:
    def test_whole_dollars(self) -> None:
        assert money.usd_to_micros("1") == 1_000_000
        assert money.usd_to_micros(Decimal("12.34")) == 12_340_000
        assert money.usd_to_micros(0) == 0

    def test_micros_to_usd_is_exact(self) -> None:
        assert money.micros_to_usd(12_340_000) == Decimal("12.34")
        assert money.micros_to_usd(1) == Decimal("0.000001")

    def test_round_half_up_at_micro_boundary(self) -> None:
        # 0.0000005 USD -> 0.5 micro-USD -> rounds up to 1
        assert money.usd_to_micros(Decimal("0.0000005")) == 1
        # 0.0000004 USD -> 0.4 micro-USD -> rounds down to 0
        assert money.usd_to_micros(Decimal("0.0000004")) == 0

    def test_negative_values(self) -> None:
        assert money.usd_to_micros(Decimal("-2.50")) == -2_500_000
        assert money.micros_to_usd(-2_500_000) == Decimal("-2.50")


class TestTokenCost:
    @pytest.mark.parametrize(
        ("tokens", "rate_per_mtok", "expected_micros"),
        [
            (1_000_000, "3.00", 3_000_000),  # 1M tokens at $3/Mtok = $3.00
            (0, "75.00", 0),
            (500_000, "15.00", 7_500_000),  # 0.5M at $15/Mtok = $7.50
            (1, "15.00", 15),  # 1 token at $15/Mtok = 15 micro-USD exactly
        ],
    )
    def test_token_cost_micros(self, tokens: int, rate_per_mtok: str, expected_micros: int) -> None:
        assert money.token_cost_micros(tokens, rate_per_mtok) == expected_micros

    def test_token_cost_rounds_half_up(self) -> None:
        # 3 tokens at $0.80/Mtok = 2.4 micro-USD -> 2
        assert money.token_cost_micros(3, "0.80") == 2
        # 5 tokens at $0.30/Mtok = 1.5 micro-USD -> 2 (half up)
        assert money.token_cost_micros(5, "0.30") == 2

    def test_accepts_decimal_rate(self) -> None:
        assert money.token_cost_micros(1_000_000, Decimal("0.08")) == 80_000

    def test_rejects_negative_tokens(self) -> None:
        with pytest.raises(ValueError):
            money.token_cost_micros(-1, "3.00")


class TestFormatUsd:
    def test_basic(self) -> None:
        assert money.format_usd(12_340_000) == "$12.34"
        assert money.format_usd(0) == "$0.00"

    def test_thousands_separator(self) -> None:
        assert money.format_usd(1_234_567_000) == "$1,234.57"

    def test_negative(self) -> None:
        assert money.format_usd(-2_500_000) == "-$2.50"


class TestPctChange:
    def test_normal(self) -> None:
        assert money.pct_change(100, 150) == pytest.approx(50.0)
        assert money.pct_change(200, 100) == pytest.approx(-50.0)

    def test_zero_baseline_returns_none(self) -> None:
        assert money.pct_change(0, 100) is None

    def test_zero_to_zero_returns_none(self) -> None:
        assert money.pct_change(0, 0) is None
