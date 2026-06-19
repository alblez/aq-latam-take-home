import type { Job } from "@/types/job";
import type { Session } from "@/types/session";
import { apiCall } from "./client";

// ---------------------------------------------------------------------------
// API base resolution (server-side fetchJobs uses raw fetch with revalidation;
// createSession uses apiCall which owns its own API_URL)
// ---------------------------------------------------------------------------
const API_URL = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL;
if (!API_URL) {
  throw new Error("API_URL/NEXT_PUBLIC_API_URL is required (ADR-008). No mock fallback.");
}

// Revalidation interval for job list (seconds)
const JOBS_REVALIDATE_SECONDS = 60;

// ---------------------------------------------------------------------------
// Result types
// ---------------------------------------------------------------------------
export type FetchJobsResult =
  | { status: "ok"; jobs: Job[] }
  | { status: "empty"; jobs: [] }
  | { status: "error"; message: string };

export type CreateSessionResult =
  | { status: "ok"; session: Session }
  | { status: "error"; message: string };

// ---------------------------------------------------------------------------
// fetchJobs — Server Component data source
// ---------------------------------------------------------------------------
async function fetchJobs(): Promise<FetchJobsResult> {
  try {
    const res = await fetch(`${API_URL}/api/jobs`, {
      next: { revalidate: JOBS_REVALIDATE_SECONDS },
    });

    if (!res.ok) {
      return {
        status: "error",
        message: `Failed to load positions (HTTP ${res.status}).`,
      };
    }

    const data: { jobs: Job[] } = await res.json();

    if (!Array.isArray(data.jobs) || data.jobs.length === 0) {
      return { status: "empty", jobs: [] };
    }

    return { status: "ok", jobs: data.jobs };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unable to reach the server.";
    return { status: "error", message };
  }
}

// ---------------------------------------------------------------------------
// fetchJobsWithState — Dev helper for forced states via query param
// ---------------------------------------------------------------------------
export async function fetchJobsWithState(state?: string): Promise<FetchJobsResult> {
  if (process.env.NODE_ENV !== "production" && state) {
    if (state === "empty") {
      return { status: "empty", jobs: [] };
    }
    if (state === "error") {
      return { status: "error", message: "Unable to reach the server." };
    }
  }
  return fetchJobs();
}

// ---------------------------------------------------------------------------
// createSession — Client-side: POST to backend via apiCall (SESS-01)
//
// Owner flows via the X-Owner-Id header that apiCall injects — no ownerId in
// body or params. Body contains only { jobId } per contract CreateSessionRequest.
// ---------------------------------------------------------------------------
export async function createSession(jobId: string): Promise<CreateSessionResult> {
  const result = await apiCall<Session>("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ jobId }),
  });

  if (result.status === "error") {
    return { status: "error", message: result.message };
  }
  return { status: "ok", session: result.data };
}
