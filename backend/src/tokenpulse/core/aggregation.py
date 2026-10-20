"""Pure rollups over usage points: daily trend series and period totals.

Deterministic: inputs are sorted by ``(member_id, date, model)`` before use, every day in
the requested window is emitted (gaps flagged, not dropped), and all arithmetic is
integer micro-USD / integer tokens (constitution Principle V).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

from tokenpulse.core.money import pct_change

Metric = Literal["cost", "tokens"]
Scope = Literal["team", "member"]


@dataclass(frozen=True)
class UsagePoint:
    member_id: str
    team_id: str
    date: date
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost_micros: int

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_write_tokens
        )


@dataclass(frozen=True)
class SeriesPoint:
    date: date
    value: int
    missing: bool


@dataclass(frozen=True)
class Series:
    key: str  # "total" or a model id
    points: list[SeriesPoint]


@dataclass(frozen=True)
class ScopeTotals:
    scope_id: str
    cost_micros: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    prev_period_delta_pct: float | None


@dataclass(frozen=True)
class PeriodTotals:
    team: ScopeTotals
    members: list[ScopeTotals] = field(default_factory=list)


def _sorted(points: Iterable[UsagePoint]) -> list[UsagePoint]:
    return sorted(points, key=lambda p: (p.member_id, p.date, p.model))


def _in_scope(p: UsagePoint, scope: Scope, scope_id: str | None) -> bool:
    if scope_id is None:
        return True
    return (p.member_id if scope == "member" else p.team_id) == scope_id


def _days(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _value(p: UsagePoint, metric: Metric) -> int:
    return p.cost_micros if metric == "cost" else p.total_tokens


def daily_series(
    points: Sequence[UsagePoint],
    *,
    scope: Scope,
    scope_id: str | None,
    metric: Metric,
    start: date,
    end: date,
    by_model: bool = False,
) -> list[Series]:
    """One :class:`Series` per key (``"total"`` unless ``by_model``), covering every day."""
    relevant = [p for p in _sorted(points) if _in_scope(p, scope, scope_id)]
    days = _days(start, end)

    # key -> {day -> (summed value, saw_any_record)}
    buckets: dict[str, dict[date, tuple[int, bool]]] = {}
    keys_order: list[str] = []
    for p in relevant:
        if not (start <= p.date <= end):
            continue
        key = p.model if by_model else "total"
        if key not in buckets:
            buckets[key] = {}
            keys_order.append(key)
        prev_val, _ = buckets[key].get(p.date, (0, False))
        buckets[key][p.date] = (prev_val + _value(p, metric), True)

    if not by_model and "total" not in buckets:
        buckets["total"] = {}
        keys_order.append("total")

    result: list[Series] = []
    for key in sorted(keys_order):
        day_map = buckets[key]
        pts = []
        for d in days:
            value, seen = day_map.get(d, (0, False))
            pts.append(SeriesPoint(date=d, value=value, missing=not seen))
        result.append(Series(key=key, points=pts))
    return result


def _accumulate(points: Iterable[UsagePoint], start: date, end: date) -> dict[str, list[int]]:
    """member_id -> [cost, input, output, cache_read, cache_write] over [start, end]."""
    acc: dict[str, list[int]] = {}
    for p in points:
        if not (start <= p.date <= end):
            continue
        row = acc.setdefault(p.member_id, [0, 0, 0, 0, 0])
        row[0] += p.cost_micros
        row[1] += p.input_tokens
        row[2] += p.output_tokens
        row[3] += p.cache_read_tokens
        row[4] += p.cache_write_tokens
    return acc


def period_totals(
    points: Sequence[UsagePoint],
    *,
    start: date,
    end: date,
) -> PeriodTotals:
    """Per-member and team totals for ``[start, end]`` plus period-over-period delta.

    The comparison window is the immediately preceding window of equal length.
    """
    ordered = _sorted(points)
    window_len = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=window_len - 1)

    cur = _accumulate(ordered, start, end)
    prev = _accumulate(ordered, prev_start, prev_end)

    members: list[ScopeTotals] = []
    for member_id in sorted(cur):
        c = cur[member_id]
        prev_cost = prev.get(member_id, [0])[0]
        members.append(
            ScopeTotals(
                scope_id=member_id,
                cost_micros=c[0],
                input_tokens=c[1],
                output_tokens=c[2],
                cache_read_tokens=c[3],
                cache_write_tokens=c[4],
                prev_period_delta_pct=pct_change(prev_cost, c[0]),
            )
        )

    team_cost = sum(m.cost_micros for m in members)
    team_prev_cost = sum(v[0] for v in prev.values())
    team = ScopeTotals(
        scope_id="team",
        cost_micros=team_cost,
        input_tokens=sum(m.input_tokens for m in members),
        output_tokens=sum(m.output_tokens for m in members),
        cache_read_tokens=sum(m.cache_read_tokens for m in members),
        cache_write_tokens=sum(m.cache_write_tokens for m in members),
        prev_period_delta_pct=pct_change(team_prev_cost, team_cost),
    )
    return PeriodTotals(team=team, members=members)
