"""Loader for the versioned, operator-tunable rule catalog.

Holds the spike-detection parameters (FR-019 / FR-020a) and the recommendation rules
(FR-029). Everything numeric is parsed as ``Decimal``. The catalog is a single
reviewable artifact with a stable version; any threshold change is a new file + version
bump (constitution Principle II, FR-029a).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml


@dataclass(frozen=True)
class SpikeParams:
    multiple: Decimal
    baseline_window_days: int
    high_floor_usd: Decimal
    critical_floor_usd: Decimal
    moderate_at: Decimal
    high_at: Decimal
    critical_at: Decimal


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    enabled: bool
    window_days: int
    subject: str
    produces_savings: bool
    thresholds: MappingProxyType[str, Decimal]
    savings_formula: str | None
    assumptions: str | None


@dataclass(frozen=True)
class RuleCatalog:
    version: str
    spike: SpikeParams
    rules: tuple[Rule, ...]

    @classmethod
    def from_file(cls, path: Path | str, *, schema_dir: Path | str) -> RuleCatalog:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        schema = json.loads(
            (Path(schema_dir) / "rule-catalog.schema.json").read_text(encoding="utf-8")
        )
        try:
            import jsonschema

            jsonschema.validate(raw, schema)
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError("jsonschema is required to load the rule catalog") from exc
        except jsonschema.ValidationError as exc:
            raise ValueError(f"invalid rule catalog {Path(path).name}: {exc.message}") from exc

        return cls(
            version=raw["version"],
            spike=_parse_spike(raw["spike"]),
            rules=tuple(_parse_rule(r) for r in raw["rules"]),
        )

    def rule(self, rule_id: str) -> Rule:
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        raise LookupError(f"no rule with id {rule_id!r} in catalog {self.version}")


def _parse_spike(raw: dict[str, Any]) -> SpikeParams:
    bands = raw["severity_ratio_bands"]
    return SpikeParams(
        multiple=Decimal(str(raw["multiple"])),
        baseline_window_days=int(raw.get("baseline_window_days", 7)),
        high_floor_usd=Decimal(str(raw["high_floor_usd"])),
        critical_floor_usd=Decimal(str(raw["critical_floor_usd"])),
        moderate_at=Decimal(str(bands["moderate_at"])),
        high_at=Decimal(str(bands["high_at"])),
        critical_at=Decimal(str(bands["critical_at"])),
    )


def _parse_rule(raw: dict[str, Any]) -> Rule:
    thresholds = {k: Decimal(str(v)) for k, v in raw.get("thresholds", {}).items()}
    return Rule(
        id=raw["id"],
        title=raw["title"],
        enabled=bool(raw["enabled"]),
        window_days=int(raw["window_days"]),
        subject=raw["subject"],
        produces_savings=bool(raw["produces_savings"]),
        thresholds=MappingProxyType(thresholds),
        savings_formula=raw.get("savings_formula"),
        assumptions=raw.get("assumptions"),
    )
