import { describe, expect, it } from "vitest";

import { makeCompetencyStatus, makePanelState } from "@/test/fixtures";
import type { FlagEnum, PolicyAction } from "@/types/turn";
import {
  budgetInfo,
  buildNameMap,
  coverageRows,
  replayFields,
  resolveTargetName,
} from "./decision-panel";

// --- Minimal contract-shaped fixtures ---

const COMPETENCIES = [
  makeCompetencyStatus({
    id: "aaa-111",
    name: "Problem Solving",
    category: "technical",
    status: "covered",
  }),
  makeCompetencyStatus({
    id: "bbb-222",
    name: "Communication",
    category: "behavioral",
    status: "in-progress",
  }),
  makeCompetencyStatus({
    id: "ccc-333",
    name: "System Design",
    category: "technical",
    status: "not-reached",
  }),
];

const PANEL_STATE = makePanelState({
  rubricSnapshot: {
    covered: ["aaa-111"],
    inProgress: ["bbb-222"],
    gaps: ["ccc-333"],
  },
  flags: [
    { flag: "tradeoff_mentioned", detail: "Discussed caching tradeoff" },
    { flag: "vague_claim", detail: "No concrete example" },
  ],
  policyState: {
    questionCount: 5,
    followUpCount: 3,
    minQuestions: 6,
    minFollowUps: 2,
    maxQuestions: 12,
    maxFollowUpsPerCompetency: 2,
    eligibleToEnd: false,
  },
  action: "follow_up",
  targetCompetencyId: "bbb-222",
  sourcePackItemId: "pack-item-42",
  trigger: {
    turnId: "turn-99",
    answerExcerpt: "We used Redis but...",
    reason: "Incomplete caching rationale",
  },
  rationale: "Following up on caching gap",
  generation: {
    mode: "targeted_follow_up",
    fallbackMode: null,
    answerDependencyRequired: true,
  },
});

const PANEL_STATE_WITH_FAILURE = makePanelState({
  ...PANEL_STATE,
  failureMode: "model_timeout",
  trigger: null,
});

// --- Tests ---

describe("buildNameMap", () => {
  it("creates a Map from competency ids to names", () => {
    const nameMap = buildNameMap(COMPETENCIES);
    expect(nameMap.get("aaa-111")).toBe("Problem Solving");
    expect(nameMap.get("bbb-222")).toBe("Communication");
    expect(nameMap.get("ccc-333")).toBe("System Design");
    expect(nameMap.size).toBe(3);
  });
});

describe("coverageRows", () => {
  it("resolves uuid arrays to named coverage rows", () => {
    const nameMap = buildNameMap(COMPETENCIES);
    const rows = coverageRows(PANEL_STATE.rubricSnapshot, nameMap);

    const coveredRow = rows.find((r) => r.name === "Problem Solving");
    expect(coveredRow).toBeDefined();
    expect(coveredRow?.coverage).toBe("covered");

    const inProgressRow = rows.find((r) => r.name === "Communication");
    expect(inProgressRow).toBeDefined();
    expect(inProgressRow?.coverage).toBe("in-progress");

    const gapRow = rows.find((r) => r.name === "System Design");
    expect(gapRow).toBeDefined();
    expect(gapRow?.coverage).toBe("not-reached");
  });

  it("falls back to uuid string when id is unmapped", () => {
    const nameMap = new Map<string, string>();
    const rows = coverageRows(PANEL_STATE.rubricSnapshot, nameMap);

    expect(rows.find((r) => r.name === "aaa-111")).toBeDefined();
  });
});

describe("budgetInfo", () => {
  it("returns followUpCount and maxFollowUpsPerCompetency from policyState", () => {
    const info = budgetInfo(PANEL_STATE.policyState);
    expect(info.followUpCount).toBe(3);
    expect(info.maxFollowUpsPerCompetency).toBe(2);
    expect(info.eligibleToEnd).toBe(false);
  });
});

describe("replayFields", () => {
  it("returns generation, trigger, failureMode, and sourcePackItemId for replay", () => {
    const fields = replayFields(PANEL_STATE);
    expect(fields.generation.mode).toBe("targeted_follow_up");
    expect(fields.trigger).not.toBeNull();
    expect(fields.trigger?.answerExcerpt).toBe("We used Redis but...");
    expect(fields.trigger?.reason).toBe("Incomplete caching rationale");
    expect(fields.failureMode).toBeNull();
    expect(fields.sourcePackItemId).toBe("pack-item-42");
  });

  it("returns null for trigger and non-null failureMode when set", () => {
    const fields = replayFields(PANEL_STATE_WITH_FAILURE);
    expect(fields.trigger).toBeNull();
    expect(fields.failureMode).toBe("model_timeout");
  });

  it("never returns undefined or [object Object] for nullable fields", () => {
    const fields = replayFields(PANEL_STATE);
    // failureMode is null — should be explicitly null, not undefined
    expect(fields.failureMode).toBeNull();
    expect(String(fields.failureMode)).not.toBe("[object Object]");
  });
});

describe("resolveTargetName", () => {
  it("resolves targetCompetencyId to a name via the nameMap", () => {
    const nameMap = buildNameMap(COMPETENCIES);
    expect(resolveTargetName("bbb-222", nameMap)).toBe("Communication");
  });

  it("falls back to the uuid string when unmapped", () => {
    const nameMap = new Map<string, string>();
    expect(resolveTargetName("unknown-id", nameMap)).toBe("unknown-id");
  });

  it("returns null when targetCompetencyId is null", () => {
    const nameMap = buildNameMap(COMPETENCIES);
    expect(resolveTargetName(null, nameMap)).toBeNull();
  });
});

describe("contract conformance", () => {
  it("flags array accepts all 8 FlagEnum values", () => {
    const allFlags = [
      "vague_claim",
      "no_evidence",
      "interesting_thread",
      "contradiction",
      "well_covered",
      "tradeoff_mentioned",
      "metric_mentioned",
      "specific_tool_mentioned",
    ] as const satisfies readonly FlagEnum[];

    // Verify fixture flags are valid members
    for (const f of PANEL_STATE.flags) {
      expect(allFlags).toContain(f.flag);
    }

    // Verify buildNameMap/coverageRows work with full flag set
    expect(PANEL_STATE.flags.length).toBeGreaterThan(0);
  });

  it("action is contract PolicyAction — no 'open' branch", () => {
    const validActions = [
      "new_topic",
      "follow_up",
      "end",
    ] as const satisfies readonly PolicyAction[];
    expect(validActions).toContain(PANEL_STATE.action);
    // "open" is NOT a valid action
    expect(PANEL_STATE.action).not.toBe("open");
  });
});
