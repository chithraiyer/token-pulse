"""Test-first for the rule-catalog loader (constitution Principle II / III)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from tokenpulse.core.recommendations.catalog import RuleCatalog

REPO_CONFIG = Path(__file__).resolve().parents[3] / "config"


@pytest.fixture
def catalog() -> RuleCatalog:
    return RuleCatalog.from_file(
        REPO_CONFIG / "rules" / "catalog-v1.yaml", schema_dir=REPO_CONFIG / "schemas"
    )


def test_version_and_rule_count(catalog: RuleCatalog) -> None:
    assert catalog.version == "v1"
    assert {r.id for r in catalog.rules} == {
        "opus-on-lightweight",
        "low-cache-utilisation",
        "steady-high-volume",
        "model-mix-shift",
    }


def test_spike_params_parsed_as_decimal(catalog: RuleCatalog) -> None:
    assert catalog.spike.multiple == Decimal("2.5")
    assert catalog.spike.baseline_window_days == 7
    assert catalog.spike.high_floor_usd == Decimal("50")
    assert catalog.spike.critical_floor_usd == Decimal("200")
    assert catalog.spike.critical_at == Decimal("5")


def test_flag_only_rule_produces_no_savings(catalog: RuleCatalog) -> None:
    mix = catalog.rule("model-mix-shift")
    assert mix.produces_savings is False
    assert mix.savings_formula is None

    opus = catalog.rule("opus-on-lightweight")
    assert opus.produces_savings is True
    assert opus.savings_formula
    assert opus.thresholds["opus_cost_share_min"] == Decimal("0.60")


def test_unknown_rule_raises(catalog: RuleCatalog) -> None:
    with pytest.raises(LookupError):
        catalog.rule("no-such-rule")


def test_schema_invalid_catalog_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "catalog-vX.yaml"
    bad.write_text("version: vX\nrules: []\n")  # missing `spike`, empty rules
    with pytest.raises(ValueError):
        RuleCatalog.from_file(bad, schema_dir=REPO_CONFIG / "schemas")
