import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiGet } from "../src/api/client";

function jsonResponse(body: unknown, init: { ok?: boolean; status?: number; statusText?: string } = {}) {
  const { ok = true, status = 200, statusText = "OK" } = init;
  return {
    ok,
    status,
    statusText,
    json: () => Promise.resolve(body),
  } as Response;
}

describe("apiGet", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches JSON from the given path", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ hello: "world" }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiGet<{ hello: string }>("/api/meta");

    expect(result).toEqual({ hello: "world" });
    const [url, options] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/api/meta");
    expect(options).toEqual({ headers: { Accept: "application/json" } });
  });

  it("serializes defined params as query string values", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({}));
    vi.stubGlobal("fetch", fetchMock);

    const params = { scope: "team", by_model: true, scope_id: undefined, note: "" } as unknown as Record<
      string,
      string | number | boolean
    >;
    await apiGet("/api/trends", params);

    const [url] = fetchMock.mock.calls[0];
    const parsed = new URL(String(url));
    expect(parsed.searchParams.get("scope")).toBe("team");
    expect(parsed.searchParams.get("by_model")).toBe("true");
    expect(parsed.searchParams.has("scope_id")).toBe(false);
    expect(parsed.searchParams.has("note")).toBe(false);
  });

  it("throws an ApiError with the response's detail message on failure", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ detail: "not found" }, { ok: false, status: 404, statusText: "Not Found" }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const error = await apiGet("/api/missing").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, message: "not found" });
  });

  it("falls back to statusText when the error body isn't JSON", async () => {
    const res = {
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: () => Promise.reject(new Error("not json")),
    } as unknown as Response;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(res));

    const error = await apiGet("/api/broken").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 500, message: "Internal Server Error" });
  });
});
