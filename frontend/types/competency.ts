import type { components } from "@/types/api/contract";

// --- Pure alias into generated contract (D-14) ---

export type CompetencyStatus = components["schemas"]["CompetencyStatus"];

// --- Frontend-local view type (no contract counterpart) ---

/** UI label vocabulary for competency coverage; values aligned to contract status enum */
export type CompetencyCoverage = "covered" | "in-progress" | "not-reached";
