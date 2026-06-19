import type { CompetencyStatus } from "@/types/competency";
import type { Evaluation, EvaluationNarrative } from "@/types/evaluation";
import type { PanelState, TerminalPanelState, Turn } from "@/types/turn";

// --- Shared contract-typed test fixtures (D-10) ---
// Return types alias @/types/* -> components["schemas"][...] so tsc rejects drift.

export function makeCompetencyStatus(overrides: Partial<CompetencyStatus> = {}): CompetencyStatus {
  return {
    id: "c1",
    name: "System Design",
    category: "technical",
    status: "not-reached",
    ...overrides,
  };
}

export function makePanelState(overrides: Partial<PanelState> = {}): PanelState {
  return {
    rubricSnapshot: { covered: [], inProgress: [], gaps: ["c1"] },
    flags: [],
    policyState: {
      questionCount: 1,
      followUpCount: 0,
      minQuestions: 6,
      minFollowUps: 2,
      maxQuestions: 12,
      maxFollowUpsPerCompetency: 2,
      eligibleToEnd: false,
    },
    action: "new_topic",
    targetCompetencyId: "c1",
    sourcePackItemId: "pack1",
    trigger: null,
    rationale: "Opening question",
    generation: { mode: "pack_seed", answerDependencyRequired: false },
    failureMode: null,
    ...overrides,
  };
}

export function makeTerminalPanelState(
  overrides: Partial<TerminalPanelState> = {},
): TerminalPanelState {
  return {
    ...makePanelState(),
    action: "end",
    generation: { mode: "terminal", answerDependencyRequired: false },
    completionReason: "all_competencies_covered",
    endedBy: "controller",
    uncoveredCompetencyIds: [],
    ...overrides,
  };
}

export function makeTurn(overrides: Partial<Turn> = {}): Turn {
  return {
    id: "t-default",
    role: "candidate",
    turnIndex: 0,
    competencyId: "comp-1",
    content: "Hello",
    ...overrides,
  };
}

export function makeEvaluationNarrative(
  overrides: Partial<EvaluationNarrative> = {},
): EvaluationNarrative {
  return {
    summary: "Test summary",
    overallVerdict: "mixed",
    strengths: [],
    concerns: [],
    unassessedCompetencyIds: [],
    earlyEndNote: null,
    modelFailureNote: null,
    ...overrides,
  };
}

export function makeEvaluation(overrides: Partial<Evaluation> = {}): Evaluation {
  return {
    overallScore: null,
    scoreScale: { min: 1, max: 10 },
    competencyScores: [],
    narrative: makeEvaluationNarrative(),
    ...overrides,
  };
}
