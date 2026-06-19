import type {
  EndSessionEarlyResponse,
  SessionStateResponse,
  StartSessionResponse,
  SubmitAnswerRequest,
  SubmitAnswerResponse,
} from "@/types/session";
import type { ApiResult } from "./client";
import { apiCall } from "./client";

// ---------------------------------------------------------------------------
// API functions — response types are contract aliases (D-12)
// ---------------------------------------------------------------------------

export async function startSession(sessionId: string): Promise<ApiResult<StartSessionResponse>> {
  return apiCall<StartSessionResponse>(`/api/sessions/${sessionId}/start`, { method: "POST" });
}

export async function submitAnswer(
  sessionId: string,
  body: SubmitAnswerRequest,
): Promise<ApiResult<SubmitAnswerResponse>> {
  return apiCall<SubmitAnswerResponse>(`/api/sessions/${sessionId}/turn`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function endSessionEarly(
  sessionId: string,
): Promise<ApiResult<EndSessionEarlyResponse>> {
  return apiCall<EndSessionEarlyResponse>(`/api/sessions/${sessionId}/end-early`, {
    method: "POST",
  });
}

export async function getSessionState(sessionId: string): Promise<ApiResult<SessionStateResponse>> {
  return apiCall<SessionStateResponse>(`/api/sessions/${sessionId}/state`);
}
