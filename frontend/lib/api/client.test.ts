import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiCall } from "./client";

// --- fail-loud config guard (MOCK-02) ---

describe("client.ts module-init guard", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("throws when NEXT_PUBLIC_API_URL is unset", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");
    vi.resetModules();
    await expect(import("./client")).rejects.toThrow(/NEXT_PUBLIC_API_URL/);
  });
});

// --- fetch stub helpers ---

function mockFetch(response: { ok: boolean; status: number; json?: () => Promise<unknown> }): void {
  globalThis.fetch = async () =>
    ({
      ok: response.ok,
      status: response.status,
      json: response.json ?? (() => Promise.resolve({})),
    }) as unknown as Response;
}

function mockFetchThrow(error: Error): void {
  globalThis.fetch = async () => {
    throw error;
  };
}

describe("apiCall error handling (D-15: ErrorResponse envelope)", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    // Ensure no localStorage side effects for X-Owner-Id
    Object.defineProperty(globalThis, "localStorage", {
      value: {
        getItem: () => null,
        setItem: () => {},
        removeItem: () => {},
        clear: () => {},
        length: 0,
        key: () => null,
      },
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    Object.defineProperty(globalThis, "localStorage", {
      value: undefined,
      writable: true,
      configurable: true,
    });
  });

  it("2xx response yields { status: 'ok', data }", async () => {
    mockFetch({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: "abc", name: "test" }),
    });
    const result = await apiCall<{ id: string; name: string }>("/test");
    expect(result).toEqual({ status: "ok", data: { id: "abc", name: "test" } });
  });

  it("4xx with valid ErrorResponse envelope extracts code, message, requestId", async () => {
    mockFetch({
      ok: false,
      status: 409,
      json: () =>
        Promise.resolve({
          error: {
            code: "turn_already_submitted",
            message: "Turn was already submitted",
            requestId: "req-123",
          },
        }),
    });
    const result = await apiCall("/test");
    expect(result).toEqual({
      status: "error",
      code: "turn_already_submitted",
      message: "Turn was already submitted",
      requestId: "req-123",
    });
  });

  it("code equals the contract enum value from body.error.code", async () => {
    mockFetch({
      ok: false,
      status: 404,
      json: () =>
        Promise.resolve({
          error: {
            code: "session_not_found",
            message: "Session does not exist",
          },
        }),
    });
    const result = await apiCall("/test");
    expect(result.status).toBe("error");
    if (result.status === "error") {
      expect(result.code).toBe("session_not_found");
    }
  });

  it("non-ok response with non-envelope body yields code: null and HTTP fallback message", async () => {
    mockFetch({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ unexpected: "format" }),
    });
    const result = await apiCall("/test");
    expect(result).toEqual({
      status: "error",
      code: null,
      message: "HTTP 500",
      requestId: null,
    });
  });

  it("non-ok response with invalid JSON yields code: null and HTTP fallback", async () => {
    mockFetch({
      ok: false,
      status: 502,
      json: () => Promise.reject(new Error("invalid json")),
    });
    const result = await apiCall("/test");
    expect(result).toEqual({
      status: "error",
      code: null,
      message: "HTTP 502",
      requestId: null,
    });
  });

  it("network throw yields { status: 'error', code: null, message }", async () => {
    mockFetchThrow(new Error("Failed to fetch"));
    const result = await apiCall("/test");
    expect(result).toEqual({
      status: "error",
      code: null,
      message: "Failed to fetch",
      requestId: null,
    });
  });

  it("error object does NOT include body.error.details (security V7)", async () => {
    mockFetch({
      ok: false,
      status: 422,
      json: () =>
        Promise.resolve({
          error: {
            code: "validation_error",
            message: "Invalid input",
            details: { field: "email", issue: "required" },
            requestId: "req-456",
          },
        }),
    });
    const result = await apiCall("/test");
    expect(result.status).toBe("error");
    if (result.status === "error") {
      expect(result).not.toHaveProperty("details");
      expect(result.code).toBe("validation_error");
      expect(result.message).toBe("Invalid input");
      expect(result.requestId).toBe("req-456");
    }
  });
});
