import type { UseQueryResult } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useTeams, useTotals, useTrends } from "../src/api/hooks";
import { Overview } from "../src/pages/Overview";
import type { TeamOut, TotalsResponse, TrendResponse } from "../src/api/types";

vi.mock("../src/api/hooks", () => ({
  useTeams: vi.fn(),
  useTotals: vi.fn(),
  useTrends: vi.fn(),
}));

const useTeamsMock = vi.mocked(useTeams);
const useTotalsMock = vi.mocked(useTotals);
const useTrendsMock = vi.mocked(useTrends);

type Query<T> = { isLoading: boolean; isError: boolean; data?: T; error?: unknown };

function query<T>(overrides: Partial<Query<T>> = {}): UseQueryResult<T, Error> {
  return {
    isLoading: false,
    isError: false,
    data: undefined,
    error: undefined,
    ...overrides,
  } as unknown as UseQueryResult<T, Error>;
}

const totals: TotalsResponse = {
  start: "2026-09-01",
  end: "2026-09-30",
  team: {
    scope_id: "team",
    cost_micros: 10_000_000,
    input_tokens: 1_000,
    output_tokens: 500,
    cache_read_tokens: 0,
    cache_write_tokens: 0,
    prev_period_delta_pct: 5,
  },
  members: [
    {
      scope_id: "alice",
      cost_micros: 4_000_000,
      input_tokens: 400,
      output_tokens: 200,
      cache_read_tokens: 0,
      cache_write_tokens: 0,
      prev_period_delta_pct: -2,
    },
  ],
};

const teams: TeamOut[] = [
  { id: "t1", name: "Platform", members: [{ id: "alice", display_name: "Alice", is_unattributed: false }] },
];

const trend: TrendResponse = {
  scope: "team",
  metric: "cost",
  start: "2026-09-01",
  end: "2026-09-30",
  empty_reason: null,
  series: [{ key: "total", points: [{ date: "2026-09-01", value: 1, is_spike: false, missing: false }] }],
};

function renderOverview() {
  return render(
    <MemoryRouter>
      <Overview />
    </MemoryRouter>,
  );
}

describe("Overview", () => {
  beforeEach(() => {
    useTeamsMock.mockReturnValue(query<TeamOut[]>({ data: teams }));
    useTotalsMock.mockReturnValue(query<TotalsResponse>({ data: totals }));
    useTrendsMock.mockReturnValue(query<TrendResponse>({ data: trend }));
  });

  it("shows skeletons while totals and trend are loading", () => {
    useTotalsMock.mockReturnValue(query<TotalsResponse>({ isLoading: true }));
    useTrendsMock.mockReturnValue(query<TrendResponse>({ isLoading: true }));
    const { container } = renderOverview();
    expect(container.querySelectorAll(".skeleton-card").length).toBeGreaterThan(0);
    expect(container.querySelector(".skeleton-chart")).toBeInTheDocument();
  });

  it("shows an error state when totals fail to load", () => {
    useTotalsMock.mockReturnValue(query<TotalsResponse>({ isError: true, error: new Error("boom") }));
    renderOverview();
    expect(screen.getByRole("alert")).toHaveTextContent("boom");
  });

  it("shows an empty state when the trend has no data", () => {
    useTrendsMock.mockReturnValue(
      query<TrendResponse>({ data: { ...trend, empty_reason: "no_data_in_range" } }),
    );
    renderOverview();
    expect(screen.getByRole("status")).toHaveTextContent("No usage recorded in this date range.");
  });

  it("renders totals cards and the trend chart once loaded", () => {
    renderOverview();
    expect(screen.getByText("Total cost")).toBeInTheDocument();
    expect(screen.getByTestId("trend-chart")).toBeInTheDocument();
  });

  it("renders a member row linking to the member's detail page with its team", () => {
    renderOverview();
    const link = screen.getByRole("link", { name: "alice" });
    expect(link).toHaveAttribute("href", "/members/alice");
    expect(screen.getByText("Platform")).toBeInTheDocument();
    expect(screen.getByText("$4.00")).toBeInTheDocument();
    expect(screen.getByText("-2.0%")).toBeInTheDocument();
  });

  it("shows an em dash for a member with no prior-period delta", () => {
    useTotalsMock.mockReturnValue(
      query<TotalsResponse>({
        data: {
          ...totals,
          members: [{ ...totals.members[0], prev_period_delta_pct: null }],
        },
      }),
    );
    renderOverview();
    expect(screen.getByRole("cell", { name: "—" })).toBeInTheDocument();
  });

  it("toggles the active metric button between cost and tokens", () => {
    renderOverview();
    const costBtn = screen.getByRole("button", { name: "Cost" });
    const tokensBtn = screen.getByRole("button", { name: "Tokens" });
    expect(costBtn).toHaveClass("active");
    expect(tokensBtn).not.toHaveClass("active");

    fireEvent.click(tokensBtn);

    expect(tokensBtn).toHaveClass("active");
    expect(costBtn).not.toHaveClass("active");
  });
});
