import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CardsSkeleton, ChartSkeleton, EmptyState, ErrorState } from "../src/components/Skeletons";

describe("ChartSkeleton", () => {
  it("renders a hidden placeholder", () => {
    const { container } = render(<ChartSkeleton />);
    const el = container.querySelector(".skeleton-chart");
    expect(el).toBeInTheDocument();
    expect(el).toHaveAttribute("aria-hidden", "true");
  });
});

describe("CardsSkeleton", () => {
  it("renders four hidden placeholder cards", () => {
    const { container } = render(<CardsSkeleton />);
    expect(container.querySelectorAll(".skeleton-card")).toHaveLength(4);
  });
});

describe("EmptyState", () => {
  it("explains an empty range", () => {
    render(<EmptyState reason="no_data_in_range" />);
    expect(screen.getByRole("status")).toHaveTextContent("No usage recorded in this date range.");
  });

  it("explains insufficient history", () => {
    render(<EmptyState reason="insufficient_history" />);
    expect(screen.getByRole("status")).toHaveTextContent("Not enough history yet for this view.");
  });

  it("falls back to echoing an unrecognized reason", () => {
    render(<EmptyState reason="something_else" />);
    expect(screen.getByRole("status")).toHaveTextContent("something_else");
  });
});

describe("ErrorState", () => {
  it("shows the error message as an alert", () => {
    render(<ErrorState message="network down" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Could not load data: network down");
  });
});
