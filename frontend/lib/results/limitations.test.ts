import { describe, expect, it } from "vitest";

import { buildLimitations, LIMITATION_LABELS } from "@/lib/results/limitations";
import { makeEvaluation, makeEvaluationNarrative } from "@/test/fixtures";

// --- Contract-shaped fixtures ---

// --- Limitation labels ---

describe("LIMITATION_LABELS", () => {
  it("carries the exact UI-SPEC copy for each severity row", () => {
    expect(LIMITATION_LABELS).toEqual({
      earlyEnd: "Ended early",
      modelFailure: "Limited model analysis",
      unassessed: "Not assessed",
    });
  });
});

// --- buildLimitations ---

describe("buildLimitations", () => {
  it("maps earlyEndNote to an info limitation", () => {
    const evaluation = makeEvaluation({
      narrative: makeEvaluationNarrative({ earlyEndNote: "Candidate ended the session early." }),
    });
    const result = buildLimitations(evaluation, new Map());

    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({
      kind: "info",
      label: "Ended early",
      text: "Candidate ended the session early.",
    });
  });

  it("maps modelFailureNote to a warning limitation", () => {
    const evaluation = makeEvaluation({
      narrative: makeEvaluationNarrative({
        modelFailureNote: "The grading model returned an incomplete analysis.",
      }),
    });
    const result = buildLimitations(evaluation, new Map());

    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({
      kind: "warning",
      label: "Limited model analysis",
      text: "The grading model returned an incomplete analysis.",
    });
  });

  it("resolves unassessed competency ids to names when known", () => {
    const evaluation = makeEvaluation({
      narrative: makeEvaluationNarrative({ unassessedCompetencyIds: ["id-1", "id-2"] }),
    });
    const labelMap = new Map([
      ["id-1", "System Design"],
      ["id-2", "Communication"],
    ]);
    const result = buildLimitations(evaluation, labelMap);

    expect(result).toEqual([
      {
        kind: "muted",
        label: "Not assessed",
        text: "System Design",
        unresolved: false,
      },
      {
        kind: "muted",
        label: "Not assessed",
        text: "Communication",
        unresolved: false,
      },
    ]);
  });

  it("falls back to the raw id and marks unresolved when a label is unknown", () => {
    const evaluation = makeEvaluation({
      narrative: makeEvaluationNarrative({ unassessedCompetencyIds: ["unknown-id"] }),
    });
    const result = buildLimitations(evaluation, new Map());

    expect(result).toEqual([
      {
        kind: "muted",
        label: "Not assessed",
        text: "unknown-id",
        unresolved: true,
      },
    ]);
  });

  it("returns an empty array when no limitation fields are present", () => {
    const evaluation = makeEvaluation();
    expect(buildLimitations(evaluation, new Map())).toEqual([]);
  });

  it("orders rows as early-end, model-failure, then unassessed", () => {
    const evaluation = makeEvaluation({
      narrative: makeEvaluationNarrative({
        earlyEndNote: "Ended early.",
        modelFailureNote: "Model failed.",
        unassessedCompetencyIds: ["id-1"],
      }),
    });
    const result = buildLimitations(evaluation, new Map([["id-1", "Leadership"]]));

    expect(result).toHaveLength(3);
    expect(result[0].label).toBe("Ended early");
    expect(result[1].label).toBe("Limited model analysis");
    expect(result[2]).toEqual({
      kind: "muted",
      label: "Not assessed",
      text: "Leadership",
      unresolved: false,
    });
  });
});
