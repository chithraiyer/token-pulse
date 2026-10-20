import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DateRangePicker } from "../src/components/DateRangePicker";

describe("DateRangePicker", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-09-18T00:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("calls onChange with a computed range when a preset is clicked", () => {
    const onChange = vi.fn();
    render(<DateRangePicker value={{ start: "2026-08-01", end: "2026-09-01" }} onChange={onChange} />);

    fireEvent.click(screen.getByText("14d"));

    expect(onChange).toHaveBeenCalledWith({ start: "2026-09-04", end: "2026-09-18" });
  });

  it("updates the start date when the 'from' input changes", () => {
    const onChange = vi.fn();
    render(<DateRangePicker value={{ start: "2026-08-01", end: "2026-09-01" }} onChange={onChange} />);

    fireEvent.change(screen.getByLabelText("From"), { target: { value: "2026-08-15" } });

    expect(onChange).toHaveBeenCalledWith({ start: "2026-08-15", end: "2026-09-01" });
  });

  it("updates the end date when the 'to' input changes", () => {
    const onChange = vi.fn();
    render(<DateRangePicker value={{ start: "2026-08-01", end: "2026-09-01" }} onChange={onChange} />);

    fireEvent.change(screen.getByLabelText("To"), { target: { value: "2026-09-10" } });

    expect(onChange).toHaveBeenCalledWith({ start: "2026-08-01", end: "2026-09-10" });
  });

  it("caps the 'to' input at today", () => {
    render(<DateRangePicker value={{ start: "2026-08-01", end: "2026-09-01" }} onChange={vi.fn()} />);
    expect(screen.getByLabelText("To")).toHaveAttribute("max", "2026-09-18");
  });
});
