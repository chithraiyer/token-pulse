import { useState } from "react";
import { Link } from "react-router-dom";

import { useTeams, useTotals, useTrends } from "../api/hooks";
import { DateRangePicker, type DateRange } from "../components/DateRangePicker";
import { TotalsCards } from "../components/TotalsCards";
import { TrendChart } from "../components/TrendChart";
import { CardsSkeleton, ChartSkeleton, EmptyState, ErrorState } from "../components/Skeletons";
import { formatUsd, isoDaysAgo, todayIso } from "../lib/format";

export function Overview() {
  const [range, setRange] = useState<DateRange>({ start: isoDaysAgo(30), end: todayIso() });
  const [metric, setMetric] = useState<"cost" | "tokens">("cost");

  const totals = useTotals(range.start, range.end);
  const trend = useTrends({ scope: "team", metric, start: range.start, end: range.end });
  const teams = useTeams();

  return (
    <div className="page">
      <div className="page-head">
        <h1>Team overview</h1>
        <DateRangePicker value={range} onChange={setRange} />
      </div>

      {totals.isLoading ? (
        <CardsSkeleton />
      ) : totals.isError ? (
        <ErrorState message={String(totals.error)} />
      ) : totals.data ? (
        <TotalsCards team={totals.data.team} />
      ) : null}

      <div className="panel">
        <div className="panel-head">
          <h2>Trend</h2>
          <div className="toggle">
            <button
              type="button"
              className={metric === "cost" ? "active" : ""}
              onClick={() => setMetric("cost")}
            >
              Cost
            </button>
            <button
              type="button"
              className={metric === "tokens" ? "active" : ""}
              onClick={() => setMetric("tokens")}
            >
              Tokens
            </button>
          </div>
        </div>
        {trend.isLoading ? (
          <ChartSkeleton />
        ) : trend.isError ? (
          <ErrorState message={String(trend.error)} />
        ) : trend.data?.empty_reason ? (
          <EmptyState reason={trend.data.empty_reason} />
        ) : trend.data ? (
          <TrendChart data={trend.data} />
        ) : null}
      </div>

      <div className="panel">
        <h2>Members</h2>
        {totals.data && teams.data ? (
          <table className="member-table">
            <thead>
              <tr>
                <th>Member</th>
                <th>Team</th>
                <th className="num">Cost</th>
                <th className="num">Δ prior</th>
              </tr>
            </thead>
            <tbody>
              {totals.data.members.map((m) => {
                const team = teams.data.find((t) => t.members.some((x) => x.id === m.scope_id));
                return (
                  <tr key={m.scope_id}>
                    <td>
                      <Link to={`/members/${m.scope_id}`}>{m.scope_id}</Link>
                    </td>
                    <td>{team?.name ?? "—"}</td>
                    <td className="num">{formatUsd(m.cost_micros)}</td>
                    <td className="num">
                      {m.prev_period_delta_pct === null
                        ? "—"
                        : `${m.prev_period_delta_pct > 0 ? "+" : ""}${m.prev_period_delta_pct.toFixed(1)}%`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <CardsSkeleton />
        )}
      </div>
    </div>
  );
}
