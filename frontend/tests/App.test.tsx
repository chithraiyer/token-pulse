import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { useMeta } from "../src/api/hooks";
import { useTeams, useTotals, useTrends } from "../src/api/hooks";
import type { Meta } from "../src/api/types";

vi.mock("../src/api/hooks", () => ({
  useMeta: vi.fn(),
  useTeams: vi.fn(),
  useTotals: vi.fn(),
  useTrends: vi.fn(),
}));

const useMetaMock = vi.mocked(useMeta);
const useTeamsMock = vi.mocked(useTeams);
const useTotalsMock = vi.mocked(useTotals);
const useTrendsMock = vi.mocked(useTrends);

function idleQuery<T>(): T {
  return { isLoading: true, isError: false, data: undefined, error: undefined } as unknown as T;
}

function meta(overrides: Partial<Meta> = {}): Meta {
  return {
    mode: "demo",
    is_demo_data: true,
    tool_version: "1.2.3",
    pricing_table_versions: ["2026-01"],
    rule_catalog_version: "1",
    retention_days: 90,
    spike_multiple: "3x",
    ...overrides,
  };
}

function renderApp(initialPath = "/") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <App />
    </MemoryRouter>,
  );
}

describe("App", () => {
  beforeEach(() => {
    useTeamsMock.mockReturnValue(idleQuery());
    useTotalsMock.mockReturnValue(idleQuery());
    useTrendsMock.mockReturnValue(idleQuery());
  });

  it("shows the demo banner when meta reports synthetic data", () => {
    useMetaMock.mockReturnValue({ data: meta() } as unknown as ReturnType<typeof useMeta>);
    renderApp();
    expect(screen.getByRole("status")).toHaveTextContent("Synthetic demo data");
  });

  it("hides the demo banner and renders the footer once meta is real", () => {
    useMetaMock.mockReturnValue({ data: meta({ is_demo_data: false }) } as unknown as ReturnType<
      typeof useMeta
    >);
    renderApp();
    expect(screen.queryByText(/Synthetic demo data/)).not.toBeInTheDocument();
    expect(screen.getByText(/TokenPulse v1\.2\.3/)).toBeInTheDocument();
    expect(screen.getByText(/spike ×3x/)).toBeInTheDocument();
    expect(screen.getByText(/retention 90d/)).toBeInTheDocument();
  });

  it("renders the overview route at /", () => {
    useMetaMock.mockReturnValue({ data: meta({ is_demo_data: false }) } as unknown as ReturnType<
      typeof useMeta
    >);
    renderApp("/");
    expect(screen.getByRole("heading", { name: "Team overview" })).toBeInTheDocument();
  });

  it("renders the member detail route at /members/:memberId", () => {
    useMetaMock.mockReturnValue({ data: meta({ is_demo_data: false }) } as unknown as ReturnType<
      typeof useMeta
    >);
    renderApp("/members/alice");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Team / alice");
  });
});
