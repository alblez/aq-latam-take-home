import { describe, expect, it } from "vitest";

import {
  isInsufficientSignal,
  VERDICT_LABELS,
  verdictBadgeVariant,
  verdictLabel,
} from "@/lib/results/verdict";
import { makeEvaluation } from "@/test/fixtures";
import type { EvaluationNarrative } from "@/types/evaluation";

// --- Contract-shaped fixtures ---

const nullScoreEvaluation = makeEvaluation({ overallScore: null });

const zeroScoreEvaluation = makeEvaluation({ overallScore: 0 });

const numericScoreEvaluation = makeEvaluation({ overallScore: 72 });

// --- Verdict labels ---

describe("VERDICT_LABELS", () => {
  it("maps every contract verdict to the UI-SPEC copy", () => {
    expect(VERDICT_LABELS).toEqual({
      strong: "Strong",
      mixed: "Mixed",
      needs_improvement: "Needs improvement",
      insufficient_signal: "Insufficient signal",
    });
  });
});

describe("verdictLabel", () => {
  it.each([
    ["strong", "Strong"],
    ["mixed", "Mixed"],
    ["needs_improvement", "Needs improvement"],
    ["insufficient_signal", "Insufficient signal"],
  ] as [
    EvaluationNarrative["overallVerdict"],
    string,
  ][])("returns %s → %s", (verdict, expected) => {
    expect(verdictLabel(verdict)).toBe(expected);
  });
});

// --- Null-score predicate ---

describe("isInsufficientSignal", () => {
  it("returns true when overallScore is null", () => {
    expect(isInsufficientSignal(nullScoreEvaluation)).toBe(true);
  });

  it("returns false when overallScore is 0", () => {
    expect(isInsufficientSignal(zeroScoreEvaluation)).toBe(false);
  });

  it("returns false when overallScore is a positive number", () => {
    expect(isInsufficientSignal(numericScoreEvaluation)).toBe(false);
  });
});

// --- Badge severity ---

describe("verdictBadgeVariant", () => {
  it.each([
    ["insufficient_signal", "muted"],
    ["strong", "success"],
    ["mixed", "warning"],
    ["needs_improvement", "warning"],
  ] as [
    EvaluationNarrative["overallVerdict"],
    "muted" | "success" | "warning",
  ][])("returns %s → %s", (verdict, expected) => {
    expect(verdictBadgeVariant(verdict)).toBe(expected);
  });
});
