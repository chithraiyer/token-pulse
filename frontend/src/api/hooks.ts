import { useQuery } from "@tanstack/react-query";

import { apiGet } from "./client";
import type { Meta, TeamOut, TotalsResponse, TrendResponse } from "./types";

export function useMeta() {
  return useQuery({ queryKey: ["meta"], queryFn: () => apiGet<Meta>("/api/meta") });
}

export function useTeams() {
  return useQuery({ queryKey: ["teams"], queryFn: () => apiGet<TeamOut[]>("/api/teams") });
}

interface TrendArgs {
  scope: "team" | "member";
  metric: "cost" | "tokens";
  start: string;
  end: string;
  scopeId?: string;
  byModel?: boolean;
}

export function useTrends(a: TrendArgs) {
  return useQuery({
    queryKey: ["trends", a],
    queryFn: () =>
      apiGet<TrendResponse>("/api/trends", {
        scope: a.scope,
        metric: a.metric,
        start: a.start,
        end: a.end,
        ...(a.scopeId ? { scope_id: a.scopeId } : {}),
        ...(a.byModel ? { by_model: true } : {}),
      }),
  });
}

export function useTotals(start: string, end: string) {
  return useQuery({
    queryKey: ["totals", start, end],
    queryFn: () => apiGet<TotalsResponse>("/api/totals", { start, end }),
  });
}
