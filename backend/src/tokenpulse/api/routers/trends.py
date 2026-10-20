"""/api/trends and /api/totals — the dashboard's trend lines and period totals."""

from __future__ import annotations

from datetime import date, timedelta
from typing import cast

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from tokenpulse.api.deps import get_session
from tokenpulse.api.schemas import (
    ScopeTotalsOut,
    SeriesOut,
    SeriesPointOut,
    TotalsResponse,
    TrendResponse,
)
from tokenpulse.core.aggregation import (
    Metric,
    ScopeTotals,
    daily_series,
    period_totals,
)
from tokenpulse.core.aggregation import Scope as AggScope
from tokenpulse.reads import latest_report_run_id, spike_dates_by_member, usage_points

router = APIRouter(prefix="/api", tags=["trends"])


@router.get("/trends", response_model=TrendResponse)
def read_trends(
    session: Session = Depends(get_session),
    scope: str = Query(..., pattern="^(team|member)$"),
    metric: str = Query(..., pattern="^(cost|tokens)$"),
    start: date = Query(...),
    end: date = Query(...),
    scope_id: str | None = Query(None),
    by_model: bool = Query(False),
) -> TrendResponse:
    if end < start:
        raise ValueError("end must not be before start")

    points = usage_points(session, start, end)
    series = daily_series(
        points,
        scope=cast(AggScope, scope),
        scope_id=scope_id,
        metric=cast(Metric, metric),
        start=start,
        end=end,
        by_model=by_model,
    )

    run_id = latest_report_run_id(session)
    flagged = spike_dates_by_member(session, run_id)
    # A day is a spike on a series if any in-scope member is flagged that day.
    spike_days: set[date] = set()
    for member_id, days in flagged.items():
        if scope == "member" and scope_id not in (None, member_id):
            continue
        spike_days |= days

    empty_reason = None if points else "no_data_in_range"

    return TrendResponse(
        scope=scope,
        metric=metric,
        start=start,
        end=end,
        empty_reason=empty_reason,
        series=[
            SeriesOut(
                key=s.key,
                points=[
                    SeriesPointOut(
                        date=p.date, value=p.value,
                        is_spike=(metric == "cost" and p.date in spike_days and not p.missing),
                        missing=p.missing,
                    )
                    for p in s.points
                ],
            )
            for s in series
        ],
    )


@router.get("/totals", response_model=TotalsResponse)
def read_totals(
    session: Session = Depends(get_session),
    start: date = Query(...),
    end: date = Query(...),
) -> TotalsResponse:
    if end < start:
        raise ValueError("end must not be before start")

    # Load the prior window too so period-over-period change can be computed.
    window_len = (end - start).days + 1
    load_start = start - timedelta(days=window_len)
    totals = period_totals(usage_points(session, load_start, end), start=start, end=end)

    def out(t: ScopeTotals) -> ScopeTotalsOut:
        return ScopeTotalsOut(
            scope_id=t.scope_id,
            cost_micros=t.cost_micros,
            input_tokens=t.input_tokens,
            output_tokens=t.output_tokens,
            cache_read_tokens=t.cache_read_tokens,
            cache_write_tokens=t.cache_write_tokens,
            prev_period_delta_pct=t.prev_period_delta_pct,
        )

    return TotalsResponse(
        start=start, end=end, team=out(totals.team), members=[out(m) for m in totals.members]
    )
