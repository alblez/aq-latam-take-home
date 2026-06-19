import type { components } from "@/types/api/contract";
import type { SessionDetail, SessionSummary } from "@/types/session";
import { apiCall } from "./client";

// ---------------------------------------------------------------------------
// getHistory — no params (owner via X-Owner-Id header, HIST-02/D-13)
// Unwraps { sessions } wrapper per contract HistoryResponse shape.
// ---------------------------------------------------------------------------
export async function getHistory() {
  const result = await apiCall<components["schemas"]["HistoryResponse"]>("/api/history");
  if (result.status === "error") {
    return result;
  }
  const sessions: SessionSummary[] = Array.isArray(result.data.sessions)
    ? result.data.sessions
    : [];
  return { status: "ok" as const, data: sessions };
}

export async function getReplay(sessionId: string) {
  return apiCall<SessionDetail>(`/api/sessions/${sessionId}/replay`);
}
