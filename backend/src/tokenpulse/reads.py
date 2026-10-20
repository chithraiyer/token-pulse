"""Non-core read helpers: pull stored rows and hand pure ``UsagePoint`` lists to
``tokenpulse.core``. No aggregation logic lives here.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from tokenpulse.core.aggregation import UsagePoint
from tokenpulse.db.models import Member, ReportRun, SpikeFlag, UsageRecord


def usage_points(session: Session, start: date, end: date) -> list[UsagePoint]:
    rows = session.execute(
        select(UsageRecord, Member.team_id)
        .join(Member, Member.id == UsageRecord.member_id)
        .where(UsageRecord.date >= start, UsageRecord.date <= end)
        .order_by(UsageRecord.member_id, UsageRecord.date, UsageRecord.model)
    ).all()
    return [
        UsagePoint(
            member_id=rec.member_id,
            team_id=team_id,
            date=rec.date,
            model=rec.model,
            input_tokens=rec.input_tokens,
            output_tokens=rec.output_tokens,
            cache_read_tokens=rec.cache_read_tokens,
            cache_write_tokens=rec.cache_write_tokens,
            cost_micros=rec.cost_micros,
        )
        for rec, team_id in rows
    ]


def latest_report_run_id(session: Session) -> int | None:
    return session.scalars(
        select(ReportRun.id).order_by(ReportRun.id.desc()).limit(1)
    ).first()


def spike_dates_by_member(session: Session, report_run_id: int | None) -> dict[str, set[date]]:
    """member_id -> set of flagged dates for the given report run (empty until US3)."""
    if report_run_id is None:
        return {}
    out: dict[str, set[date]] = {}
    for member_id, day in session.execute(
        select(SpikeFlag.member_id, SpikeFlag.date).where(
            SpikeFlag.report_run_id == report_run_id
        )
    ).all():
        out.setdefault(member_id, set()).add(day)
    return out
