import { describe, expect, it } from "vitest";

import { makeTurn } from "@/test/fixtures";
import type { Turn } from "@/types/turn";

import { buildTurnLookup, evidenceChipLabel, getUsableTurnIds } from "./evidence";

// --- Fixtures ---

const turns: Turn[] = [
  makeTurn({ id: "t1", role: "interviewer", turnIndex: 0 }),
  makeTurn({ id: "t2", role: "candidate", turnIndex: 1 }),
  makeTurn({ id: "t3", role: "interviewer", turnIndex: 2 }),
];

// --- buildTurnLookup ---

describe("buildTurnLookup", () => {
  it("returns a Map keyed by turn.id", () => {
    const lookup = buildTurnLookup(turns);
    expect(lookup).toBeInstanceOf(Map);
    expect(lookup.size).toBe(3);
    expect(lookup.get("t1")?.id).toBe("t1");
    expect(lookup.get("t2")?.id).toBe("t2");
    expect(lookup.get("t3")?.id).toBe("t3");
  });

  it("returns empty map for empty input", () => {
    const lookup = buildTurnLookup([]);
    expect(lookup.size).toBe(0);
  });
});

// --- getUsableTurnIds ---

describe("getUsableTurnIds", () => {
  const lookup = buildTurnLookup(turns);

  it("filters out unknown ids, keeps known ones", () => {
    expect(getUsableTurnIds(["t1", "tX"], lookup)).toEqual(["t1"]);
  });

  it("returns empty array when input is empty", () => {
    expect(getUsableTurnIds([], lookup)).toEqual([]);
  });

  it("returns empty array when no ids match", () => {
    expect(getUsableTurnIds(["tX", "tY"], lookup)).toEqual([]);
  });

  it("keeps order of provided ids", () => {
    expect(getUsableTurnIds(["t3", "t1"], lookup)).toEqual(["t3", "t1"]);
  });

  it("returns all ids when all match", () => {
    expect(getUsableTurnIds(["t1", "t2", "t3"], lookup)).toEqual(["t1", "t2", "t3"]);
  });
});

// --- evidenceChipLabel ---

describe("evidenceChipLabel", () => {
  it("visible part is 'Turn N' where N = turnIndex + 1", () => {
    const turn = makeTurn({ turnIndex: 4 });
    expect(evidenceChipLabel(turn).visible).toBe("Turn 5");
  });

  it("visible part is 'Turn 1' for turnIndex 0", () => {
    const turn = makeTurn({ turnIndex: 0 });
    expect(evidenceChipLabel(turn).visible).toBe("Turn 1");
  });

  it("accessible label includes role and turn number for candidate", () => {
    const turn = makeTurn({ role: "candidate", turnIndex: 4 });
    expect(evidenceChipLabel(turn).accessible).toBe("View evidence: candidate turn 5");
  });

  it("accessible label includes role and turn number for interviewer", () => {
    const turn = makeTurn({ role: "interviewer", turnIndex: 0 });
    expect(evidenceChipLabel(turn).accessible).toBe("View evidence: interviewer turn 1");
  });

  it("accessible label uses generic form when role is undefined", () => {
    const turn = makeTurn({ turnIndex: 3 });
    // Override role to undefined by casting — simulating missing role
    const turnNoRole = { ...turn, role: undefined as unknown as Turn["role"] };
    expect(evidenceChipLabel(turnNoRole).accessible).toBe("View evidence: turn 4");
  });
});
