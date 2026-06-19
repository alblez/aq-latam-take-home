import type { Turn } from "@/types/turn";

// --- Pure helpers for evidence chip rendering (EVAL-04) ---

/**
 * Build a lookup map from turn ID to Turn object.
 *
 * Used by NarrativeSection to resolve cited turnIds against known transcript
 * turns before rendering evidence chips. Unknown IDs are never rendered.
 */
export function buildTurnLookup(turns: Turn[]): Map<string, Turn> {
  const map = new Map<string, Turn>();
  for (const turn of turns) {
    map.set(turn.id, turn);
  }
  return map;
}

/**
 * Filter turnIds to only those present in the lookup map.
 *
 * Per D-09/D-11: only render chips for turnIds that match known transcript
 * turns. Unknown/foreign IDs are silently dropped — no disabled/empty UI.
 */
export function getUsableTurnIds(turnIds: string[], lookup: Map<string, Turn>): string[] {
  return turnIds.filter((id) => lookup.has(id));
}

/**
 * Derive visible and accessible label text for an evidence chip.
 *
 * Visible label: "Turn {n}" (1-based display, n = turnIndex + 1)
 * Accessible label: "View evidence: {role} turn {n}" when role is available,
 *   otherwise "View evidence: turn {n}"
 *
 * Per UI-SPEC: chip visible label is "Turn {n}", accessible label includes
 * role metadata when known (D-23).
 */
export function evidenceChipLabel(turn: Turn): { visible: string; accessible: string } {
  const n = turn.turnIndex + 1;
  const visible = `Turn ${n}`;
  const role = turn.role;
  const accessible = role ? `View evidence: ${role} turn ${n}` : `View evidence: turn ${n}`;
  return { visible, accessible };
}
