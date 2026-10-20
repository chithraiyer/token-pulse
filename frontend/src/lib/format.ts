// Display helpers. Money arrives from the API as integer micro-USD (1e-6 USD).

const USD = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export function microsToUsd(micros: number): number {
  return micros / 1_000_000;
}

export function formatUsd(micros: number): string {
  return USD.format(microsToUsd(micros));
}

export function formatUsdCompact(micros: number): string {
  const usd = microsToUsd(micros);
  if (Math.abs(usd) >= 1000) {
    return `$${(usd / 1000).toFixed(1)}k`;
  }
  return USD.format(usd);
}

export function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

export function formatPct(pct: number | null): string {
  if (pct === null) return "—";
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

export function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - days);
  return d.toISOString().slice(0, 10);
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}
