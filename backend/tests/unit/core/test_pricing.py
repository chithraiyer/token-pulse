"""Test-first for the pricing catalog and cost computation (constitution Principle III)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from tokenpulse.core.pricing import PricingCatalog, TokenCounts

REPO_CONFIG = Path(__file__).resolve().parents[3] / "config"


@pytest.fixture
def catalog() -> PricingCatalog:
    return PricingCatalog.from_dir(REPO_CONFIG / "pricing", schema_dir=REPO_CONFIG / "schemas")


def test_loads_bundled_table(catalog: PricingCatalog) -> None:
    assert "anthropic-2026-09-01" in catalog.versions()
    table = catalog.table_by_version("anthropic-2026-09-01")
    assert table.currency == "USD"
    assert "claude-sonnet-4" in table.models


def test_table_selected_by_record_date(catalog: PricingCatalog) -> None:
    table = catalog.table_for_date(date(2026, 9, 1))
    assert table.version == "anthropic-2026-09-01"


def test_table_for_date_out_of_range_raises(catalog: PricingCatalog) -> None:
    with pytest.raises(LookupError):
        catalog.table_for_date(date(1990, 1, 1))


def test_cost_is_sum_of_all_token_classes(catalog: PricingCatalog) -> None:
    # Sonnet: input 3.00, output 15.00, cache_write 3.75, cache_read 0.30 (USD / Mtok)
    tokens = TokenCounts(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_read_tokens=1_000_000,
        cache_write_tokens=1_000_000,
    )
    cost, is_estimate = catalog.cost_micros(tokens, "claude-sonnet-4", on=date(2026, 9, 1))
    # 3.00 + 15.00 + 0.30 + 3.75 = 22.05 USD = 22_050_000 micro-USD
    assert cost == 22_050_000
    assert is_estimate is False


def test_zero_tokens_cost_zero(catalog: PricingCatalog) -> None:
    cost, is_estimate = catalog.cost_micros(
        TokenCounts(0, 0, 0, 0), "claude-opus-4", on=date(2026, 9, 1)
    )
    assert cost == 0
    assert is_estimate is False


def test_unknown_model_is_flagged_as_estimate(catalog: PricingCatalog) -> None:
    cost, is_estimate = catalog.cost_micros(
        TokenCounts(1_000_000, 0, 0, 0), "claude-future-9", on=date(2026, 9, 1)
    )
    assert is_estimate is True
    # Conservative upper bound: never cheaper than the priciest known model's input rate.
    assert cost >= 15_000_000


def test_cost_by_explicit_version_matches_by_date(catalog: PricingCatalog) -> None:
    tokens = TokenCounts(123_456, 7_890, 1_000, 2_000)
    by_date, _ = catalog.cost_micros(tokens, "claude-haiku-4", on=date(2026, 9, 1))
    by_version, _ = catalog.cost_micros(tokens, "claude-haiku-4", version="anthropic-2026-09-01")
    assert by_date == by_version


def test_from_dir_rejects_schema_invalid_table(tmp_path: Path) -> None:
    bad = tmp_path / "pricing"
    bad.mkdir()
    (bad / "broken.json").write_text(json.dumps({"version": "x", "models": {}}))
    with pytest.raises(ValueError):
        PricingCatalog.from_dir(bad, schema_dir=REPO_CONFIG / "schemas")
