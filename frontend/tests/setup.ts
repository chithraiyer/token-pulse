import "@testing-library/jest-dom/vitest";

// Recharts' ResponsiveContainer needs a non-zero size in jsdom. It reads
// clientWidth/clientHeight (and, as a fallback, getBoundingClientRect).
for (const [prop, value] of [
  ["offsetWidth", 800],
  ["offsetHeight", 320],
  ["clientWidth", 800],
  ["clientHeight", 320],
] as const) {
  Object.defineProperty(HTMLElement.prototype, prop, { configurable: true, value });
}

HTMLElement.prototype.getBoundingClientRect = function getBoundingClientRect() {
  return {
    width: 800,
    height: 320,
    top: 0,
    left: 0,
    right: 800,
    bottom: 320,
    x: 0,
    y: 0,
    toJSON() {},
  } as DOMRect;
};

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
