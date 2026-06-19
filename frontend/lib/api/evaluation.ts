import type { SessionDetail } from "@/types/session";
import { apiCall } from "./client";

export async function getEvaluation(sessionId: string) {
  return apiCall<SessionDetail>(`/api/sessions/${sessionId}/evaluation`);
}
