import type { components } from "@/types/api/contract";

// --- Pure aliases into generated contract (D-14) ---

export type Turn = components["schemas"]["Turn"];
export type Flag = components["schemas"]["Flag"];
export type PanelState = components["schemas"]["PanelState"];
export type TerminalPanelState = components["schemas"]["TerminalPanelState"];
export type PolicyAction = components["schemas"]["PolicyAction"];

/** 8-value flag enum derived from contract Flag shape (D-11, backlog #12) */
export type FlagEnum = Flag["flag"];
