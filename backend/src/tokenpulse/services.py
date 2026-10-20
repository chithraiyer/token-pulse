"""Thin wiring between config and the pure loaders. Not part of the money path."""

from __future__ import annotations

from functools import lru_cache

from tokenpulse.config import Settings
from tokenpulse.core.pricing import PricingCatalog
from tokenpulse.core.recommendations.catalog import RuleCatalog


@lru_cache(maxsize=8)
def _pricing_cached(pricing_dir: str, schema_dir: str) -> PricingCatalog:
    return PricingCatalog.from_dir(pricing_dir, schema_dir=schema_dir)


@lru_cache(maxsize=8)
def _rules_cached(catalog_path: str, schema_dir: str) -> RuleCatalog:
    return RuleCatalog.from_file(catalog_path, schema_dir=schema_dir)


def load_pricing(settings: Settings) -> PricingCatalog:
    return _pricing_cached(str(settings.pricing_dir), str(settings.schema_dir))


def load_rules(settings: Settings) -> RuleCatalog:
    return _rules_cached(str(settings.rules_catalog), str(settings.schema_dir))


def effective_spike_multiple(settings: Settings) -> str:
    """Decimal string: config override wins over the catalog default (FR-023)."""
    if settings.spike_multiple_override is not None:
        return str(settings.spike_multiple_override)
    return str(load_rules(settings).spike.multiple)
