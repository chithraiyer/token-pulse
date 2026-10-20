import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useMeta } from "../src/api/hooks";
import { DemoBanner } from "../src/components/DemoBanner";
import type { Meta } from "../src/api/types";

vi.mock("../src/api/hooks", () => ({ useMeta: vi.fn() }));

const useMetaMock = vi.mocked(useMeta);

function meta(overrides: Partial<Meta> = {}): Meta {
  return {
    mode: "demo",
    is_demo_data: true,
    tool_version: "1.0.0",
    pricing_table_versions: ["2026-01"],
    rule_catalog_version: "1",
    retention_days: 90,
    spike_multiple: "3x",
    ...overrides,
  };
}

function metaQuery(data: Meta | undefined): ReturnType<typeof useMeta> {
  return { data } as unknown as ReturnType<typeof useMeta>;
}

describe("DemoBanner", () => {
  it("renders nothing while meta is loading", () => {
    useMetaMock.mockReturnValue(metaQuery(undefined));
    const { container } = render(<DemoBanner />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when the data is not synthetic", () => {
    useMetaMock.mockReturnValue(metaQuery(meta({ is_demo_data: false })));
    const { container } = render(<DemoBanner />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the demo notice with mode, rules, and pricing versions", () => {
    useMetaMock.mockReturnValue(metaQuery(meta()));
    render(<DemoBanner />);
    const banner = screen.getByRole("status");
    expect(banner).toHaveTextContent("Synthetic demo data — not real usage.");
    expect(banner).toHaveTextContent("demo");
    expect(banner).toHaveTextContent("1");
    expect(banner).toHaveTextContent("2026-01");
  });
});
