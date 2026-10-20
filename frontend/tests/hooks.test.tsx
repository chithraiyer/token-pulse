import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiGet } from "../src/api/client";
import { useMeta, useTeams, useTotals, useTrends } from "../src/api/hooks";

vi.mock("../src/api/client", () => ({ apiGet: vi.fn() }));

const apiGetMock = vi.mocked(apiGet);

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("api hooks", () => {
  beforeEach(() => {
    apiGetMock.mockReset();
  });

  it("useMeta fetches /api/meta", async () => {
    apiGetMock.mockResolvedValue({ mode: "demo" });
    const { result } = renderHook(() => useMeta(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiGetMock).toHaveBeenCalledWith("/api/meta");
    expect(result.current.data).toEqual({ mode: "demo" });
  });

  it("useTeams fetches /api/teams", async () => {
    apiGetMock.mockResolvedValue([]);
    const { result } = renderHook(() => useTeams(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiGetMock).toHaveBeenCalledWith("/api/teams");
  });

  it("useTotals fetches /api/totals with the date range", async () => {
    apiGetMock.mockResolvedValue({});
    const { result } = renderHook(() => useTotals("2026-09-01", "2026-09-30"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiGetMock).toHaveBeenCalledWith("/api/totals", {
      start: "2026-09-01",
      end: "2026-09-30",
    });
  });

  it("useTrends omits optional params when not provided", async () => {
    apiGetMock.mockResolvedValue({});
    const { result } = renderHook(
      () => useTrends({ scope: "team", metric: "cost", start: "2026-09-01", end: "2026-09-30" }),
      { wrapper },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiGetMock).toHaveBeenCalledWith("/api/trends", {
      scope: "team",
      metric: "cost",
      start: "2026-09-01",
      end: "2026-09-30",
    });
  });

  it("useTrends includes scope_id and by_model when set", async () => {
    apiGetMock.mockResolvedValue({});
    const { result } = renderHook(
      () =>
        useTrends({
          scope: "member",
          metric: "tokens",
          start: "2026-09-01",
          end: "2026-09-30",
          scopeId: "alice",
          byModel: true,
        }),
      { wrapper },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiGetMock).toHaveBeenCalledWith("/api/trends", {
      scope: "member",
      metric: "tokens",
      start: "2026-09-01",
      end: "2026-09-30",
      scope_id: "alice",
      by_model: true,
    });
  });
});
