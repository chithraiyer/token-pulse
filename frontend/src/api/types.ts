// Mirrors backend/src/tokenpulse/api/schemas.py and contracts/rest-api.openapi.yaml.

export interface Meta {
  mode: string;
  is_demo_data: boolean;
  tool_version: string;
  pricing_table_versions: string[];
  rule_catalog_version: string;
  retention_days: number;
  spike_multiple: string;
}

export interface MemberOut {
  id: string;
  display_name: string;
  is_unattributed: boolean;
}

export interface TeamOut {
  id: string;
  name: string;
  members: MemberOut[];
}

export interface SeriesPointOut {
  date: string;
  value: number;
  is_spike: boolean;
  missing: boolean;
}

export interface SeriesOut {
  key: string;
  points: SeriesPointOut[];
}

export interface TrendResponse {
  scope: "team" | "member";
  metric: "cost" | "tokens";
  start: string;
  end: string;
  empty_reason: null | "no_data_in_range" | "insufficient_history";
  series: SeriesOut[];
}

export interface ScopeTotalsOut {
  scope_id: string;
  cost_micros: number;
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cache_write_tokens: number;
  prev_period_delta_pct: number | null;
}

export interface TotalsResponse {
  start: string;
  end: string;
  team: ScopeTotalsOut;
  members: ScopeTotalsOut[];
}
