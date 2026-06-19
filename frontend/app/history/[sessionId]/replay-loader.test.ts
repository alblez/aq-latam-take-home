import { describe, expect, it } from "vitest";

import { loadReplaySession } from "./replay-loader";

// MOCK-05 regression: replay direct-load must convert import-time and API
// failures into a renderable error result instead of throwing, so the page can
// leave "Loading replay..." and show "Could not load replay".

describe("loadReplaySession", () => {
  it("returns { session: null, error } when the history module import rejects", async () => {
    const loadHistory = () => Promise.reject(new Error("NEXT_PUBLIC_API_URL is required"));

    const result = await loadReplaySession("session-1", loadHistory);

    expect(result).toEqual({
      session: null,
      error: "NEXT_PUBLIC_API_URL is required",
    });
  });

  it("returns { session: null, error } when getReplay resolves an error result", async () => {
    const loadHistory = () =>
      Promise.resolve({
        getReplay: () =>
          Promise.resolve({
            status: "error" as const,
            code: null,
            message: "Backend unavailable",
          }),
      });

    const result = await loadReplaySession("session-1", loadHistory);

    expect(result).toEqual({ session: null, error: "Backend unavailable" });
  });

  it("returns { session, error: null } when getReplay resolves ok", async () => {
    const detail = { session: { id: "session-1" } } as never;
    const loadHistory = () =>
      Promise.resolve({
        getReplay: () => Promise.resolve({ status: "ok" as const, data: detail }),
      });

    const result = await loadReplaySession("session-1", loadHistory);

    expect(result).toEqual({ session: detail, error: null });
  });

  it("falls back to 'Could not load replay' when a non-Error value is thrown", async () => {
    const loadHistory = () => Promise.reject("boom");

    const result = await loadReplaySession("session-1", loadHistory);

    expect(result).toEqual({ session: null, error: "Could not load replay" });
  });
});
