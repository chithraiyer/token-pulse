import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useTrends } from "../api/hooks";
import { DateRangePicker, type DateRange } from "../components/DateRangePicker";
import { TrendChart } from "../components/TrendChart";
import { ChartSkeleton, EmptyState, ErrorState } from "../components/Skeletons";
import { isoDaysAgo, todayIso } from "../lib/format";

export function MemberDetail() {
  const { memberId = "" } = useParams();
  const [range, setRange] = useState<DateRange>({ start: isoDaysAgo(30), end: todayIso() });
  const [metric, setMetric] = useState<"cost" | "tokens">("cost");
  const [byModel, setByModel] = useState(true);

  const trend = useTrends({
    scope: "member",
    scopeId: memberId,
    metric,
    start: range.start,
    end: range.end,
    byModel,
  });

  return (
    <div className="page">
      <div className="page-head">
        <h1>
          <Link to="/">Team</Link> / {memberId}
        </h1>
        <DateRangePicker value={range} onChange={setRange} />
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>Usage trend</h2>
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
            <label className="by-model">
              <input
                type="checkbox"
                checked={byModel}
                onChange={(e) => setByModel(e.target.checked)}
              />
              by model
            </label>
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
    </div>
  );
}
