import type { Evaluation, EvaluationNarrative } from "@/types/evaluation";

// --- Pure helpers for evaluation verdict rendering ---

/**
 * Maps contract `overallVerdict` enum values to human-readable labels.
 *
 * Per UI-SPEC Copywriting Contract: verdict badge labels must be stable strings
 * so reviewers can distinguish `insufficient_signal` from a low numeric score.
 */
export const VERDICT_LABELS: Record<EvaluationNarrative["overallVerdict"], string> = {
  strong: "Strong",
  mixed: "Mixed",
  needs_improvement: "Needs improvement",
  insufficient_signal: "Insufficient signal",
};

/** Returns the display label for a contract `overallVerdict` value. */
export function verdictLabel(verdict: EvaluationNarrative["overallVerdict"]): string {
  return VERDICT_LABELS[verdict];
}

/**
 * Strict null-score predicate.
 *
 * A score of `0` is a real score, not insufficient signal — Pitfall 1. Never
 * use `?? 0` or `||` fallbacks here.
 */
export function isInsufficientSignal(evaluation: Pick<Evaluation, "overallScore">): boolean {
  return evaluation.overallScore === null;
}

/**
 * Maps a contract verdict to a Badge variant.
 *
 * Badge variants are constrained to `default | accent | success | warning | muted`;
 * this helper never returns `"info"`.
 */
export function verdictBadgeVariant(
  verdict: EvaluationNarrative["overallVerdict"],
): "muted" | "success" | "warning" {
  switch (verdict) {
    case "insufficient_signal":
      return "muted";
    case "strong":
      return "success";
    case "mixed":
    case "needs_improvement":
      return "warning";
  }
}
