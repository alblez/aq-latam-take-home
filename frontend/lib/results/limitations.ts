import type { Evaluation } from "@/types/evaluation";

// --- Pure helper for degraded-evaluation surfacing ---

/**
 * A single limitation row surfaced in the Evaluation limitations callout.
 *
 * `kind` is a semantic severity token; the component maps it to a Badge variant
 * and adds non-color visual distinctions (D-06).
 */
export type Limitation = {
  kind: "info" | "warning" | "muted";
  label: string;
  text: string;
  unresolved?: boolean;
};

/**
 * Stable labels for the three degraded-evaluation cases.
 *
 * Per UI-SPEC Copywriting Contract: color-coded rows must carry visible text
 * labels; these constants keep the copy centralized and testable.
 */
export const LIMITATION_LABELS = {
  earlyEnd: "Ended early",
  modelFailure: "Limited model analysis",
  unassessed: "Not assessed",
} as const;

/**
 * Builds a severity-ordered list of evaluation limitations.
 *
 * - `earlyEndNote` → info "Ended early"
 * - `modelFailureNote` → warning "Limited model analysis"
 * - `unassessedCompetencyIds` → muted "Not assessed" with resolved name or raw id
 */
export function buildLimitations(
  evaluation: Pick<Evaluation, "narrative">,
  labelMap: Map<string, string>,
): Limitation[] {
  const limitations: Limitation[] = [];
  const { narrative } = evaluation;

  if (narrative.earlyEndNote) {
    limitations.push({
      kind: "info",
      label: LIMITATION_LABELS.earlyEnd,
      text: narrative.earlyEndNote,
    });
  }

  if (narrative.modelFailureNote) {
    limitations.push({
      kind: "warning",
      label: LIMITATION_LABELS.modelFailure,
      text: narrative.modelFailureNote,
    });
  }

  for (const id of narrative.unassessedCompetencyIds) {
    const label = labelMap.get(id);
    limitations.push({
      kind: "muted",
      label: LIMITATION_LABELS.unassessed,
      text: label ?? id,
      unresolved: label === undefined,
    });
  }

  return limitations;
}
