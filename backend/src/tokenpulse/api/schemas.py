"""Pydantic response models. These are the contract in contracts/rest-api.openapi.yaml.

Money fields are integer micro-USD; the frontend formats them for display.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class Meta(BaseModel):
    mode: str
    is_demo_data: bool
    tool_version: str
    pricing_table_versions: list[str]
    rule_catalog_version: str
    retention_days: int
    spike_multiple: str


class MemberOut(BaseModel):
    id: str
    display_name: str
    is_unattributed: bool


class TeamOut(BaseModel):
    id: str
    name: str
    members: list[MemberOut]


class SeriesPointOut(BaseModel):
    date: date
    value: int
    is_spike: bool
    missing: bool


class SeriesOut(BaseModel):
    key: str
    points: list[SeriesPointOut]


class TrendResponse(BaseModel):
    scope: str
    metric: str
    start: date
    end: date
    empty_reason: str | None
    series: list[SeriesOut]


class ScopeTotalsOut(BaseModel):
    scope_id: str
    cost_micros: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    prev_period_delta_pct: float | None


class TotalsResponse(BaseModel):
    start: date
    end: date
    team: ScopeTotalsOut
    members: list[ScopeTotalsOut]


class ErrorOut(BaseModel):
    detail: str
