import type { SessionDetail } from "@/types/session";

// Result contract returned by the history API's getReplay (mirrors ApiResult).
type ReplayApiResult = { status: "ok"; data: SessionDetail } | { status: "error"; message: string };

// Minimal shape of the dynamically imported history module the loader needs.
type HistoryModule = {
  getReplay: (sessionId: string) => Promise<ReplayApiResult>;
};

export type ReplayLoadResult = {
  session: SessionDetail | null;
  error: string | null;
};

const DEFAULT_ERROR = "Could not load replay";

/**
 * Loads a replay session, converting import-time failures (e.g. the fail-loud
 * client config guard from ADR-008) and API errors into a renderable error
 * result instead of throwing. This lets the replay page leave the
 * "Loading replay..." branch and render "Could not load replay" (MOCK-05).
 */
export async function loadReplaySession(
  sessionId: string,
  loadHistory: () => Promise<HistoryModule> = () => import("@/lib/api/history"),
): Promise<ReplayLoadResult> {
  try {
    const { getReplay } = await loadHistory();
    const result = await getReplay(sessionId);
    if (result.status === "error") {
      return { session: null, error: result.message };
    }
    return { session: result.data, error: null };
  } catch (err) {
    return {
      session: null,
      error: err instanceof Error ? err.message : DEFAULT_ERROR,
    };
  }
}
