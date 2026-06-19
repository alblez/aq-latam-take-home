import { describe, expect, it } from "vitest";

import { beginReplayLoad, finishReplayLoad } from "./replay-page-state";

// MOCK-05 regression for the page-visible UAT failure surface: direct-loading
// /history/{sessionId} must leave the "Loading replay..." branch and enter the
// "Could not load replay" branch when the loader returns an error.

describe("beginReplayLoad", () => {
  it("clears stale session and error and enters loading", () => {
    const stale = {
      loading: false,
      session: { id: "old" } as never,
      error: "previous failure",
    };

    expect(beginReplayLoad(stale)).toEqual({
      loading: true,
      session: null,
      error: null,
    });
  });
});

describe("finishReplayLoad", () => {
  it("exits loading with the error set and session null on failure (UAT surface)", () => {
    const loading = { loading: true, session: null, error: null };

    const next = finishReplayLoad(loading, {
      session: null,
      error: "NEXT_PUBLIC_API_URL is required",
    });

    expect(next).toEqual({
      loading: false,
      session: null,
      error: "NEXT_PUBLIC_API_URL is required",
    });
  });

  it("exits loading with the session set and error null on success", () => {
    const loading = { loading: true, session: null, error: null };
    const detail = { id: "session-1" } as never;

    const next = finishReplayLoad(loading, { session: detail, error: null });

    expect(next).toEqual({ loading: false, session: detail, error: null });
  });
});
