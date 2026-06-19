/**
 * Canonical owner ID source of truth.
 *
 * Owner ID is a client-generated UUID persisted in localStorage under `aq_owner_id`.
 * It scopes sessions, history, and API calls to a single browser.
 *
 * Two accessors:
 * - `getStoredOwnerId()` — read-only, returns "" if absent or unavailable.
 * - `getOrCreateOwnerId()` — lazy-inits on first call, returns UUID always.
 */

const STORAGE_KEY = "aq_owner_id";

/**
 * Read the stored owner ID without creating one.
 * Safe for server-side (returns "") and private browsing.
 */
export function getStoredOwnerId(): string {
  if (typeof globalThis === "undefined" || !("localStorage" in globalThis)) return "";
  try {
    return globalThis.localStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

/**
 * Get or create the owner ID.
 * Creates and persists a new UUID if none exists.
 * Falls back to an ephemeral UUID when localStorage is unavailable.
 */
export function getOrCreateOwnerId(): string {
  if (typeof globalThis === "undefined" || !("localStorage" in globalThis)) {
    return crypto.randomUUID();
  }
  try {
    const stored = globalThis.localStorage.getItem(STORAGE_KEY);
    if (stored) return stored;
    const id = crypto.randomUUID();
    globalThis.localStorage.setItem(STORAGE_KEY, id);
    return id;
  } catch {
    return crypto.randomUUID();
  }
}
