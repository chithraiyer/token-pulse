"""Test-first for aggregation rollups (constitution Principle III / V).

Covers per-member / per-team / per-model series, missing-vs-zero days, period totals,
period-over-period delta, and the team == Σ members invariant (FR-017).
"""

from __future__ import annotations

from datetime import date

import pytest

from tokenpulse.core.aggregation import UsagePoint, daily_series, period_totals


def _pt(member: str, team: str, d: str, model: str, cost: int, inp: int = 0, out: int = 0) -> UsagePoint:
    return UsagePoint(
        member_id=member,
        team_id=team,
        date=date.fromisoformat(d),
        model=model,
        input_tokens=inp,
        output_tokens=out,
        cache_read_tokens=0,
        cache_write_tokens=0,
        cost_micros=cost,
    )


@pytest.fixture
def points() -> list[UsagePoint]:
    return [
        _pt("alice", "platform", "2026-09-01", "claude-sonnet-4", 1_000_000, inp=100, out=50),
        _pt("alice", "platform", "2026-09-01", "claude-opus-4", 2_000_000, inp=10, out=5),
        _pt("alice", "platform", "2026-09-03", "claude-sonnet-4", 500_000, inp=40, out=20),
        _pt("bob", "platform", "2026-09-02", "claude-haiku-4", 250_000, inp=30, out=10),
        _pt("bob", "platform", "2026-09-03", "claude-haiku-4", 0, inp=0, out=0),  # genuine zero
    ]


class TestDailySeries:
    def test_team_total_series_fills_every_day_and_marks_gaps(self, points: list[UsagePoint]) -> None:
        series = daily_series(
            points, scope="team", scope_id="platform", metric="cost",
            start=date(2026, 9, 1), end=date(2026, 9, 4),
        )
        assert len(series) == 1
        pts = {p.date.isoformat(): p for p in series[0].points}
        assert pts["2026-09-01"].value == 3_000_000
        assert pts["2026-09-02"].value == 250_000
        assert pts["2026-09-03"].value == 500_000  # alice 500k + bob 0
        assert pts["2026-09-03"].missing is False   # bob had a (zero) record
        assert pts["2026-09-04"].value == 0
        assert pts["2026-09-04"].missing is True    # nobody had a record

    def test_member_series_by_model(self, points: list[UsagePoint]) -> None:
        series = daily_series(
            points, scope="member", scope_id="alice", metric="cost",
            start=date(2026, 9, 1), end=date(2026, 9, 3), by_model=True,
        )
        keys = {s.key for s in series}
        assert keys == {"claude-sonnet-4", "claude-opus-4"}
        opus = next(s for s in series if s.key == "claude-opus-4")
        by_day = {p.date.isoformat(): p for p in opus.points}
        assert by_day["2026-09-01"].value == 2_000_000
        assert by_day["2026-09-02"].missing is True
        assert by_day["2026-09-03"].missing is True

    def test_tokens_metric_sums_all_token_classes(self, points: list[UsagePoint]) -> None:
        series = daily_series(
            points, scope="member", scope_id="alice", metric="tokens",
            start=date(2026, 9, 1), end=date(2026, 9, 1),
        )
        # day 1: (100+50) + (10+5) = 165
        assert series[0].points[0].value == 165

    def test_all_teams_aggregate_when_scope_id_none(self, points: list[UsagePoint]) -> None:
        series = daily_series(
            points, scope="team", scope_id=None, metric="cost",
            start=date(2026, 9, 1), end=date(2026, 9, 3),
        )
        total = sum(p.value for p in series[0].points)
        assert total == 3_750_000

    def test_output_is_sorted_by_date(self, points: list[UsagePoint]) -> None:
        series = daily_series(
            points, scope="team", scope_id="platform", metric="cost",
            start=date(2026, 9, 1), end=date(2026, 9, 4),
        )
        dates = [p.date for p in series[0].points]
        assert dates == sorted(dates)


class TestPeriodTotals:
    def test_team_equals_sum_of_members(self, points: list[UsagePoint]) -> None:
        totals = period_totals(points, start=date(2026, 9, 1), end=date(2026, 9, 4))
        assert totals.team.cost_micros == sum(m.cost_micros for m in totals.members)
        assert totals.team.cost_micros == 3_750_000

    def test_members_sorted_by_id(self, points: list[UsagePoint]) -> None:
        totals = period_totals(points, start=date(2026, 9, 1), end=date(2026, 9, 4))
        assert [m.scope_id for m in totals.members] == ["alice", "bob"]

    def test_prev_period_delta_pct(self) -> None:
        pts = [
            _pt("alice", "p", "2026-09-01", "m", 100),  # prev window 08-30..08-31 -> nothing
            _pt("alice", "p", "2026-08-31", "m", 50),
        ]
        # current window 09-01..09-01 (len 1) -> prev window 08-31..08-31
        totals = period_totals(pts, start=date(2026, 9, 1), end=date(2026, 9, 1))
        alice = totals.members[0]
        assert alice.cost_micros == 100
        assert alice.prev_period_delta_pct == pytest.approx(100.0)  # 50 -> 100

    def test_prev_period_delta_none_when_no_prior_data(self, points: list[UsagePoint]) -> None:
        totals = period_totals(points, start=date(2026, 9, 1), end=date(2026, 9, 4))
        assert totals.team.prev_period_delta_pct is None

    def test_empty_input(self) -> None:
        totals = period_totals([], start=date(2026, 9, 1), end=date(2026, 9, 4))
        assert totals.team.cost_micros == 0
        assert totals.members == []
