import type { SessionDetail } from "@/types/session";
import type { ReplayLoadResult } from "./replay-loader";

// Page-visible state for the replay route, mapping directly to page.tsx's
// loading / session / error useState values.
export type ReplayPageState = {
  loading: boolean;
  session: SessionDetail | null;
  error: string | null;
};

/**
 * Start a direct-load: clear any stale session/error from a previous session
 * and enter the loading state, so prior data can never leak into the next load.
 */
export function beginReplayLoad(_previous: ReplayPageState): ReplayPageState {
  return { loading: true, session: null, error: null };
}

/**
 * Finish a direct-load: exit loading and apply the loader result. On failure
 * this sets error with session null so the page renders the existing
 * "Could not load replay" branch instead of staying on "Loading replay..."
 * (MOCK-05).
 */
export function finishReplayLoad(
  _previous: ReplayPageState,
  result: ReplayLoadResult,
): ReplayPageState {
  return { loading: false, session: result.session, error: result.error };
}
