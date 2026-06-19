import { getStoredOwnerId } from "@/lib/owner-id";
import type { components } from "@/types/api/contract";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_URL) {
  throw new Error(
    "NEXT_PUBLIC_API_URL is required. Set it in frontend/.env.local (e.g. http://localhost:8000). " +
      "There is no mock fallback — the frontend always talks to the live backend (ADR-008).",
  );
}

// --- Typed error code from contract ErrorResponse envelope ---

/** 9-value error code enum derived from the contract ErrorResponse schema. */
export type ErrorCode = components["schemas"]["ErrorResponse"]["error"]["code"];

export type ApiResult<T> =
  | { status: "ok"; data: T }
  | { status: "error"; code: ErrorCode | null; message: string; requestId?: string | null };

export async function apiCall<T>(path: string, options: RequestInit = {}): Promise<ApiResult<T>> {
  const ownerId = getStoredOwnerId();

  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-Owner-Id": ownerId,
        ...options.headers,
      },
    });
    if (!res.ok) {
      const body = (await res.json().catch(() => null)) as
        | components["schemas"]["ErrorResponse"]
        | null;
      const env = body?.error;
      return {
        status: "error",
        code: env?.code ?? null,
        message: env?.message ?? `HTTP ${res.status}`,
        requestId: env?.requestId ?? null,
      };
    }
    return { status: "ok", data: (await res.json()) as T };
  } catch (err) {
    return {
      status: "error",
      code: null,
      message: err instanceof Error ? err.message : "Network error",
      requestId: null,
    };
  }
}
