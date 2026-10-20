"""US2 — end-to-end aggregation over seeded demo data."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from tokenpulse.core.aggregation import period_totals
from tokenpulse.reads import usage_points


def test_invariant_holds_over_full_history(seeded_db: Session) -> None:
    points = usage_points(seeded_db, date(2026, 6, 1), date(2026, 9, 7))
    totals = period_totals(points, start=date(2026, 6, 10), end=date(2026, 9, 7))
    assert totals.team.cost_micros == sum(m.cost_micros for m in totals.members)
    assert totals.team.cost_micros > 0
    assert {m.scope_id for m in totals.members} == {
        "alice", "bob", "carol", "dave", "erin", "frank",
    }


def test_prev_period_delta_is_computed(seeded_db: Session) -> None:
    points = usage_points(seeded_db, date(2026, 6, 1), date(2026, 9, 7))
    totals = period_totals(points, start=date(2026, 8, 25), end=date(2026, 9, 7))
    # dave is the steady-high-volume member; his week-over-fortnight change should be modest.
    dave = next(m for m in totals.members if m.scope_id == "dave")
    assert dave.prev_period_delta_pct is not None
    assert abs(dave.prev_period_delta_pct) < 60
