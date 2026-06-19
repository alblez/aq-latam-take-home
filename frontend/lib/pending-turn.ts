/**
 * Pending-turn localStorage persistence for crash-recovery idempotency.
 *
 * Persists the turn payload (including the once-generated `clientTurnId`) to
 * localStorage before a POST, and clears it when the answer lands. Recovery
 * reads the stored record and re-submits with the same `clientTurnId`.
 *
 * Key format: `aq_pending_turn_<sessionId>` (mirrors `aq_owner_id` convention).
 * This file does NOT generate `clientTurnId` — that happens once in the room
 * component when the candidate presses Done (D-05).
 */

import type { components } from "@/types/api/contract";

// --- Types ---

/** Derived from the contract Turn.inputMode (never hand-typed "voice" | "text"). */
export type InputMode = NonNullable<components["schemas"]["Turn"]["inputMode"]>;

export interface PendingTurn {
  clientTurnId: string;
  answerText: string;
  inputMode: InputMode;
  audioDurationMs?: number;
}

// --- Key helper ---

function storageKey(sessionId: string): string {
  return `aq_pending_turn_${sessionId}`;
}

// --- SSR-safe guard ---

function hasLocalStorage(): boolean {
  return typeof globalThis !== "undefined" && "localStorage" in globalThis;
}

// --- Accessors ---

/**
 * Persist pending-turn record before POST.
 * No-op if localStorage is unavailable (SSR, private browsing quota).
 */
export function writePendingTurn(sessionId: string, record: PendingTurn): void {
  if (!hasLocalStorage()) return;
  try {
    globalThis.localStorage.setItem(storageKey(sessionId), JSON.stringify(record));
  } catch {
    // Quota or security error — silent no-op (availability > crash).
  }
}

/**
 * Read the pending-turn record for a session.
 * Returns `null` when absent, malformed, or localStorage is unavailable.
 */
export function readPendingTurn(sessionId: string): PendingTurn | null {
  if (!hasLocalStorage()) return null;
  try {
    const raw = globalThis.localStorage.getItem(storageKey(sessionId));
    if (!raw) return null;
    return JSON.parse(raw) as PendingTurn;
  } catch {
    return null;
  }
}

/**
 * Clear the pending-turn record (answer landed / session ended).
 * No-op if absent or localStorage is unavailable.
 */
export function clearPendingTurn(sessionId: string): void {
  if (!hasLocalStorage()) return;
  try {
    globalThis.localStorage.removeItem(storageKey(sessionId));
  } catch {
    // Silent no-op.
  }
}
