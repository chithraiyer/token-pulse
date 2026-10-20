import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  formatPct,
  formatTokens,
  formatUsd,
  formatUsdCompact,
  isoDaysAgo,
  microsToUsd,
  todayIso,
} from "../src/lib/format";

describe("microsToUsd", () => {
  it("converts micro-USD to USD", () => {
    expect(microsToUsd(1_000_000)).toBe(1);
    expect(microsToUsd(2_500_000)).toBe(2.5);
    expect(microsToUsd(0)).toBe(0);
  });
});

describe("formatUsd", () => {
  it("formats as USD currency", () => {
    expect(formatUsd(1_000_000)).toBe("$1.00");
    expect(formatUsd(1_234_560)).toBe("$1.23");
    expect(formatUsd(0)).toBe("$0.00");
  });
});

describe("formatUsdCompact", () => {
  it("uses full currency formatting under $1000", () => {
    expect(formatUsdCompact(999_000_000)).toBe("$999.00");
  });

  it("compacts to a 'k' suffix at or above $1000", () => {
    expect(formatUsdCompact(1_000_000_000)).toBe("$1.0k");
    expect(formatUsdCompact(12_340_000_000)).toBe("$12.3k");
  });

  it("compacts large negative amounts too", () => {
    expect(formatUsdCompact(-5_000_000_000)).toBe("$-5.0k");
  });
});

describe("formatTokens", () => {
  it("renders small counts verbatim", () => {
    expect(formatTokens(0)).toBe("0");
    expect(formatTokens(999)).toBe("999");
  });

  it("compacts thousands with a 'k' suffix", () => {
    expect(formatTokens(1_000)).toBe("1.0k");
    expect(formatTokens(12_345)).toBe("12.3k");
  });

  it("compacts millions with an 'M' suffix", () => {
    expect(formatTokens(1_000_000)).toBe("1.0M");
    expect(formatTokens(9_876_543)).toBe("9.9M");
  });
});

describe("formatPct", () => {
  it("renders an em dash for null", () => {
    expect(formatPct(null)).toBe("—");
  });

  it("prefixes positive values with a plus sign", () => {
    expect(formatPct(12.34)).toBe("+12.3%");
  });

  it("leaves negative values unprefixed", () => {
    expect(formatPct(-5)).toBe("-5.0%");
  });

  it("does not add a plus sign for zero", () => {
    expect(formatPct(0)).toBe("0.0%");
  });
});

describe("date helpers", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-09-18T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("todayIso returns the current UTC date", () => {
    expect(todayIso()).toBe("2026-09-18");
  });

  it("isoDaysAgo subtracts whole days in UTC", () => {
    expect(isoDaysAgo(0)).toBe("2026-09-18");
    expect(isoDaysAgo(1)).toBe("2026-09-17");
    expect(isoDaysAgo(30)).toBe("2026-08-19");
  });
});
