import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TotalsCards } from "../src/components/TotalsCards";
import type { ScopeTotalsOut } from "../src/api/types";

function totals(overrides: Partial<ScopeTotalsOut> = {}): ScopeTotalsOut {
  return {
    scope_id: "team",
    cost_micros: 12_340_000,
    input_tokens: 1_500_000,
    output_tokens: 250_000,
    cache_read_tokens: 4_000,
    cache_write_tokens: 1_000,
    prev_period_delta_pct: 8.2,
    ...overrides,
  };
}

describe("TotalsCards", () => {
  it("renders formatted values for each card", () => {
    render(<TotalsCards team={totals()} />);
    expect(screen.getByText("Total cost")).toBeInTheDocument();
    expect(screen.getByText("$12.34")).toBeInTheDocument();
    expect(screen.getByText("Input tokens")).toBeInTheDocument();
    expect(screen.getByText("1.5M")).toBeInTheDocument();
    expect(screen.getByText("Output tokens")).toBeInTheDocument();
    expect(screen.getByText("250.0k")).toBeInTheDocument();
    expect(screen.getByText("Cache reads")).toBeInTheDocument();
    expect(screen.getByText("4.0k")).toBeInTheDocument();
  });

  it("marks a positive delta as up", () => {
    render(<TotalsCards team={totals({ prev_period_delta_pct: 8.2 })} />);
    const delta = screen.getByText("+8.2% vs prior period");
    expect(delta).toHaveClass("up");
  });

  it("marks a negative delta as down", () => {
    render(<TotalsCards team={totals({ prev_period_delta_pct: -3.5 })} />);
    const delta = screen.getByText("-3.5% vs prior period");
    expect(delta).toHaveClass("down");
  });

  it("omits the delta line for token cards, which have none", () => {
    render(<TotalsCards team={totals()} />);
    expect(screen.queryAllByText(/vs prior period/)).toHaveLength(1);
  });
});
