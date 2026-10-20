import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useTrends } from "../src/api/hooks";
import { MemberDetail } from "../src/pages/MemberDetail";
import type { TrendResponse } from "../src/api/types";

vi.mock("../src/api/hooks", () => ({ useTrends: vi.fn() }));

const useTrendsMock = vi.mocked(useTrends);

function query(overrides: Partial<ReturnType<typeof useTrends>> = {}): ReturnType<typeof useTrends> {
  return {
    isLoading: false,
    isError: false,
    data: undefined,
    error: undefined,
    ...overrides,
  } as unknown as ReturnType<typeof useTrends>;
}

const trend: TrendResponse = {
  scope: "member",
  metric: "cost",
  start: "2026-09-01",
  end: "2026-09-30",
  empty_reason: null,
  series: [{ key: "total", points: [{ date: "2026-09-01", value: 1, is_spike: false, missing: false }] }],
};

function renderMemberDetail(memberId = "alice") {
  return render(
    <MemoryRouter initialEntries={[`/members/${memberId}`]}>
      <Routes>
        <Route path="/members/:memberId" element={<MemberDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("MemberDetail", () => {
  beforeEach(() => {
    useTrendsMock.mockReturnValue(query({ data: trend }));
  });

  it("shows the member id from the route in the heading", () => {
    renderMemberDetail("alice");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Team / alice");
  });

  it("links back to the team overview", () => {
    renderMemberDetail("alice");
    expect(screen.getByRole("link", { name: "Team" })).toHaveAttribute("href", "/");
  });

  it("shows a chart skeleton while loading", () => {
    useTrendsMock.mockReturnValue(query({ isLoading: true }));
    const { container } = renderMemberDetail();
    expect(container.querySelector(".skeleton-chart")).toBeInTheDocument();
  });

  it("shows an error state on failure", () => {
    useTrendsMock.mockReturnValue(query({ isError: true, error: new Error("network down") }));
    renderMemberDetail();
    expect(screen.getByRole("alert")).toHaveTextContent("network down");
  });

  it("shows an empty state when there's no data", () => {
    useTrendsMock.mockReturnValue(query({ data: { ...trend, empty_reason: "insufficient_history" } }));
    renderMemberDetail();
    expect(screen.getByRole("status")).toHaveTextContent("Not enough history yet for this view.");
  });

  it("renders the trend chart once data is loaded", () => {
    renderMemberDetail();
    expect(screen.getByTestId("trend-chart")).toBeInTheDocument();
  });

  it("defaults to by-model on and can be toggled off", () => {
    renderMemberDetail();
    const checkbox = screen.getByRole("checkbox", { name: "by model" });
    expect(checkbox).toBeChecked();
    fireEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });
});
