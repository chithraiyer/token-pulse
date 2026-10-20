import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TrendChart } from "../src/components/TrendChart";
import { EmptyState } from "../src/components/Skeletons";
import type { TrendResponse } from "../src/api/types";

function trend(overrides: Partial<TrendResponse> = {}): TrendResponse {
  return {
    scope: "team",
    metric: "cost",
    start: "2026-09-01",
    end: "2026-09-04",
    empty_reason: null,
    series: [
      {
        key: "total",
        points: [
          { date: "2026-09-01", value: 1_000_000, is_spike: false, missing: false },
          { date: "2026-09-02", value: 9_000_000, is_spike: true, missing: false },
          { date: "2026-09-03", value: 0, is_spike: false, missing: true },
          { date: "2026-09-04", value: 1_200_000, is_spike: false, missing: false },
        ],
      },
    ],
    ...overrides,
  };
}

describe("TrendChart", () => {
  it("renders and marks spike days", () => {
    render(<TrendChart data={trend()} />);
    const chart = screen.getByTestId("trend-chart");
    expect(chart).toBeInTheDocument();
    expect(chart).toHaveAttribute("data-spike-days", "1");
  });

  it("reports zero spike days when none are flagged", () => {
    const data = trend();
    data.series[0].points = data.series[0].points.map((p) => ({ ...p, is_spike: false }));
    render(<TrendChart data={data} />);
    expect(screen.getByTestId("trend-chart")).toHaveAttribute("data-spike-days", "0");
  });

  it("renders per-model series keys", () => {
    const data = trend({
      series: [
        {
          key: "claude-opus-4",
          points: [{ date: "2026-09-01", value: 5, is_spike: false, missing: false }],
        },
        {
          key: "claude-sonnet-4",
          points: [{ date: "2026-09-01", value: 3, is_spike: false, missing: false }],
        },
      ],
    });
    render(<TrendChart data={data} />);
    expect(screen.getByText("claude-opus-4")).toBeInTheDocument();
    expect(screen.getByText("claude-sonnet-4")).toBeInTheDocument();
  });
});

describe("EmptyState", () => {
  it("explains an empty range", () => {
    render(<EmptyState reason="no_data_in_range" />);
    expect(screen.getByRole("status")).toHaveTextContent("No usage recorded");
  });
});
