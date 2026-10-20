import { formatPct, formatTokens, formatUsd } from "../lib/format";
import type { ScopeTotalsOut } from "../api/types";

export function TotalsCards({ team }: { team: ScopeTotalsOut }) {
  const cards = [
    { label: "Total cost", value: formatUsd(team.cost_micros), delta: team.prev_period_delta_pct },
    { label: "Input tokens", value: formatTokens(team.input_tokens), delta: null },
    { label: "Output tokens", value: formatTokens(team.output_tokens), delta: null },
    {
      label: "Cache reads",
      value: formatTokens(team.cache_read_tokens),
      delta: null,
    },
  ];
  return (
    <div className="cards">
      {cards.map((c) => (
        <div key={c.label} className="card">
          <div className="card-label">{c.label}</div>
          <div className="card-value">{c.value}</div>
          {c.delta !== null && (
            <div className={`card-delta ${c.delta > 0 ? "up" : "down"}`}>
              {formatPct(c.delta)} vs prior period
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
