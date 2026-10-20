import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatTokens, formatUsdCompact } from "../lib/format";
import type { TrendResponse } from "../api/types";

const COLORS = ["#2563eb", "#d97706", "#059669", "#7c3aed", "#dc2626"];

interface Row {
  date: string;
  [seriesKey: string]: number | string | null;
}

/** Merge the API's per-series points into one row per date for Recharts. */
function toRows(data: TrendResponse): { rows: Row[]; keys: string[]; spikeDates: Set<string> } {
  const keys = data.series.map((s) => s.key);
  const spikeDates = new Set<string>();
  const byDate = new Map<string, Row>();
  for (const s of data.series) {
    for (const p of s.points) {
      const row = byDate.get(p.date) ?? { date: p.date };
      row[s.key] = p.missing ? null : p.value;
      if (p.is_spike) spikeDates.add(p.date);
      byDate.set(p.date, row);
    }
  }
  const rows = [...byDate.values()].sort((a, b) => a.date.localeCompare(b.date));
  return { rows, keys, spikeDates };
}

export function TrendChart({ data }: { data: TrendResponse }) {
  const { rows, keys, spikeDates } = toRows(data);
  const fmt = data.metric === "cost" ? formatUsdCompact : formatTokens;

  return (
    <div className="trend-chart" data-testid="trend-chart" data-spike-days={spikeDates.size}>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={24} />
          <YAxis tickFormatter={(v: number) => fmt(v)} tick={{ fontSize: 11 }} width={64} />
          <Tooltip
            formatter={(v: number) => fmt(v)}
            labelFormatter={(d: string) => (spikeDates.has(d) ? `${d} — spike` : d)}
          />
          {keys.length > 1 && <Legend />}
          {keys.map((k, i) => (
            <Line
              key={k}
              type="monotone"
              dataKey={k}
              name={k === "total" ? (data.metric === "cost" ? "Cost" : "Tokens") : k}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              connectNulls={false}
              dot={(props: { cx?: number; cy?: number; payload?: Row; index?: number }) => {
                const { cx, cy, payload, index } = props;
                const dotKey = `${k}-${payload?.date ?? index}`;
                if (cx == null || cy == null || !payload) return <g key={dotKey} />;
                const isSpike = spikeDates.has(String(payload.date));
                return (
                  <circle
                    key={dotKey}
                    cx={cx}
                    cy={cy}
                    r={isSpike ? 5 : 0}
                    fill="#dc2626"
                    stroke="#fff"
                    strokeWidth={1}
                  />
                );
              }}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
