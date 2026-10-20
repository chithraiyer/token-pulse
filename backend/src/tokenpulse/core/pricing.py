"""Versioned pricing tables and cost computation.

A record's cost is the sum over token classes of ``tokens * rate`` in integer micro-USD.
Rates are per 1,000,000 tokens, given as decimal strings in the bundled JSON, parsed with
``Decimal`` (never float). Past periods reprice with the table in effect for that date
(constitution Principle I / FR-012).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from tokenpulse.core.money import token_cost_micros


@dataclass(frozen=True)
class ModelRates:
    input_per_mtok: Decimal
    output_per_mtok: Decimal
    cache_write_per_mtok: Decimal
    cache_read_per_mtok: Decimal
    batch_multiplier: Decimal


@dataclass(frozen=True)
class PricingTable:
    version: str
    effective_start: date
    effective_end: date
    currency: str
    models: Mapping[str, ModelRates]


@dataclass(frozen=True)
class TokenCounts:
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int


def _load_schema(schema_dir: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (schema_dir / "pricing-table.schema.json").read_text(encoding="utf-8")
    )
    return data


def _parse_table(raw: dict[str, Any]) -> PricingTable:
    models = {
        model_id: ModelRates(
            input_per_mtok=Decimal(str(rates["input_per_mtok"])),
            output_per_mtok=Decimal(str(rates["output_per_mtok"])),
            cache_write_per_mtok=Decimal(str(rates["cache_write_per_mtok"])),
            cache_read_per_mtok=Decimal(str(rates["cache_read_per_mtok"])),
            batch_multiplier=Decimal(str(rates.get("batch_multiplier", "0.5"))),
        )
        for model_id, rates in raw["models"].items()
    }
    return PricingTable(
        version=raw["version"],
        effective_start=date.fromisoformat(raw["effective_start"]),
        effective_end=date.fromisoformat(raw["effective_end"]),
        currency=raw["currency"],
        models=models,
    )


class PricingCatalog:
    """All bundled pricing tables, indexed by version and by effective date range."""

    def __init__(self, tables: Sequence[PricingTable]) -> None:
        if not tables:
            raise ValueError("PricingCatalog needs at least one table")
        # Deterministic order: by effective_start then version.
        self._tables = tuple(sorted(tables, key=lambda t: (t.effective_start, t.version)))
        self._by_version = {t.version: t for t in self._tables}

    @classmethod
    def from_dir(cls, pricing_dir: Path | str, *, schema_dir: Path | str) -> PricingCatalog:
        pricing_dir = Path(pricing_dir)
        schema = _load_schema(Path(schema_dir))
        try:
            import jsonschema
        except ModuleNotFoundError as exc:  # pragma: no cover - dev dep always present
            raise RuntimeError("jsonschema is required to load pricing tables") from exc

        tables: list[PricingTable] = []
        for path in sorted(pricing_dir.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            try:
                jsonschema.validate(raw, schema)
            except jsonschema.ValidationError as exc:
                raise ValueError(
                    f"{path.name} is not a valid pricing table: {exc.message}"
                ) from exc
            tables.append(_parse_table(raw))
        return cls(tables)

    def versions(self) -> list[str]:
        return [t.version for t in self._tables]

    def table_by_version(self, version: str) -> PricingTable:
        try:
            return self._by_version[version]
        except KeyError as exc:
            raise LookupError(f"no pricing table with version {version!r}") from exc

    def table_for_date(self, on: date) -> PricingTable:
        for table in self._tables:
            if table.effective_start <= on <= table.effective_end:
                return table
        raise LookupError(f"no pricing table effective on {on.isoformat()}")

    def _worst_case_rates(self) -> ModelRates:
        """Upper-bound rates across every known model, for pricing an unknown model."""
        return ModelRates(
            input_per_mtok=max(m.input_per_mtok for m in self._all_models()),
            output_per_mtok=max(m.output_per_mtok for m in self._all_models()),
            cache_write_per_mtok=max(m.cache_write_per_mtok for m in self._all_models()),
            cache_read_per_mtok=max(m.cache_read_per_mtok for m in self._all_models()),
            batch_multiplier=Decimal("0.5"),
        )

    def _all_models(self) -> list[ModelRates]:
        return [rates for table in self._tables for rates in table.models.values()]

    def cost_micros(
        self,
        tokens: TokenCounts,
        model: str,
        *,
        on: date | None = None,
        version: str | None = None,
    ) -> tuple[int, bool]:
        """Return ``(cost_micros, is_estimate)``.

        ``is_estimate`` is ``True`` when ``model`` is absent from the selected table; in
        that case a conservative upper bound (worst-case rates across known models) is
        returned so an unpriced model is surfaced, not hidden (FR-011, US5 scenario 5).
        """
        if (on is None) == (version is None):
            raise ValueError("pass exactly one of on= or version=")
        table = self.table_by_version(version) if version is not None else self.table_for_date(on)  # type: ignore[arg-type]

        rates = table.models.get(model)
        is_estimate = rates is None
        if rates is None:
            rates = self._worst_case_rates()

        cost = (
            token_cost_micros(tokens.input_tokens, rates.input_per_mtok)
            + token_cost_micros(tokens.output_tokens, rates.output_per_mtok)
            + token_cost_micros(tokens.cache_read_tokens, rates.cache_read_per_mtok)
            + token_cost_micros(tokens.cache_write_tokens, rates.cache_write_per_mtok)
        )
        return cost, is_estimate
