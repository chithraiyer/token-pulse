"""Runtime settings, loaded from a TOML file.

Relative paths in the file resolve against the file's own directory. Secrets are read
from the environment only, never from the file and never logged (constitution Section 2).
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

Mode = Literal["demo", "live"]

DEFAULT_CONFIG_NAMES = ("tokenpulse.toml", "tokenpulse.demo.toml")


@dataclass(frozen=True)
class Settings:
    mode: Mode
    database_path: Path
    db_key_env: str
    retention_days: int
    pricing_dir: Path
    schema_dir: Path
    rules_catalog: Path
    spike_multiple_override: Decimal | None
    demo_seed: int
    demo_days: int
    demo_members: int

    @classmethod
    def load(cls, path: str | Path | None = None) -> Settings:
        cfg_path = _resolve_config_path(path)
        raw: dict[str, Any] = {}
        root = Path.cwd()
        if cfg_path is not None:
            raw = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
            root = cfg_path.parent

        pricing = raw.get("pricing", {})
        rules = raw.get("rules", {})
        spike = raw.get("spike", {})
        demo = raw.get("demo", {})

        def rel(value: str) -> Path:
            p = Path(value)
            return p if p.is_absolute() else (root / p)

        override = spike.get("multiple") or None
        return cls(
            mode=raw.get("mode", "demo"),
            database_path=rel(raw.get("database_path", "tokenpulse.db")),
            db_key_env=raw.get("db_key_env", "TOKENPULSE_DB_KEY"),
            retention_days=int(raw.get("retention_days", 90)),
            pricing_dir=rel(pricing.get("dir", "config/pricing")),
            schema_dir=rel(pricing.get("schema_dir", "config/schemas")),
            rules_catalog=rel(rules.get("catalog", "config/rules/catalog-v1.yaml")),
            spike_multiple_override=Decimal(str(override)) if override else None,
            demo_seed=int(demo.get("seed", 20260907)),
            demo_days=int(demo.get("days", 90)),
            demo_members=int(demo.get("members", 6)),
        )

    @property
    def is_demo(self) -> bool:
        return self.mode == "demo"

    def database_url(self) -> str:
        if self.mode == "live":
            # SQLCipher-encrypted store lands in US5 (T092); guard until then.
            raise NotImplementedError(
                "live mode (encrypted store + Admin API ingestion) is delivered in US5"
            )
        return f"sqlite:///{self.database_path}"

    def admin_api_key(self) -> str:  # pragma: no cover - exercised in US5
        key = os.environ.get("TOKENPULSE_ADMIN_API_KEY")
        if not key:
            raise RuntimeError("TOKENPULSE_ADMIN_API_KEY is required for live mode")
        return key


def _resolve_config_path(path: str | Path | None) -> Path | None:
    if path is not None:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"config file not found: {p}")
        return p
    for name in DEFAULT_CONFIG_NAMES:
        candidate = Path.cwd() / name
        if candidate.exists():
            return candidate
    return None
