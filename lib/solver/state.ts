import type { AnalyzeOutcome, Display, Method, Model, SolveOutcome, SolveRequest, SystemInput } from "../api/types";
import type { ApiError } from "../api/client";
import { resizeSystem } from "./grid";

export type Stage = "DIMENSIONS" | "MATRIX_INPUT" | "ANALYZING" | "METHOD_SELECTION" | "METHOD_CONFIGURATION" | "SOLVING" | "RESULTS";
export type Draft = {
  system: SystemInput; method: Method; mode: Model<"ArithmeticMode">; display: Display;
  guess: string[]; tolerance: string; maxIterations: string; dominance: boolean; nonzero: boolean; risk: boolean;
};
export type State = { stage: Stage; draft: Draft; analysis: AnalyzeOutcome | null; outcome: SolveOutcome | null; error: ApiError | null; restored: boolean };
export const initialDraft: Draft = { system: { a: [["", ""], ["", ""]], b: ["", ""] }, method: "gaussian", mode: "float64", display: { mode: "decimal", decimal_places: 6 }, guess: ["0", "0"], tolerance: "1e-8", maxIterations: "25", dominance: true, nonzero: false, risk: false };
export const initialState: State = { stage: "DIMENSIONS", draft: initialDraft, analysis: null, outcome: null, error: null, restored: false };
export type Action =
  | { type: "RESTORE"; draft: Draft | null }
  | { type: "EDIT"; patch: Partial<Draft>; invalidateAnalysis?: boolean }
  | { type: "RESIZE"; m: number; n: number }
  | { type: "PRESET"; draft: Draft }
  | { type: "STAGE"; stage: Stage }
  | { type: "ANALYZED"; outcome: AnalyzeOutcome }
  | { type: "SOLVED"; outcome: SolveOutcome }
  | { type: "FAILED"; error: ApiError; stage: Stage }
  | { type: "CANCEL"; stage: Stage };

export function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "RESTORE": return { ...initialState, draft: action.draft ?? initialDraft, restored: true, stage: action.draft ? "MATRIX_INPUT" : "DIMENSIONS" };
    case "EDIT": {
      const displayOnly = Object.keys(action.patch).every(k => k === "display");
      return { ...state, draft: { ...state.draft, ...action.patch }, error: null,
        analysis: action.invalidateAnalysis ? null : state.analysis,
        outcome: displayOnly ? state.outcome : null,
        stage: displayOnly ? state.stage : action.invalidateAnalysis ? "MATRIX_INPUT" : "METHOD_CONFIGURATION" };
    }
    case "RESIZE": return { ...state, stage: "MATRIX_INPUT", analysis: null, outcome: null, error: null,
      draft: { ...state.draft, system: resizeSystem(state.draft.system, action.m, action.n), guess: Array.from({ length: action.n }, (_, i) => state.draft.guess[i] ?? "0") } };
    case "PRESET": return { ...state, draft: action.draft, stage: "MATRIX_INPUT", analysis: null, outcome: null, error: null };
    case "STAGE": return { ...state, stage: action.stage, error: null };
    case "ANALYZED": return { ...state, analysis: action.outcome, stage: "METHOD_SELECTION", error: null };
    case "SOLVED": return { ...state, outcome: action.outcome, stage: "RESULTS", error: null };
    case "FAILED": return { ...state, stage: action.stage, error: action.error };
    case "CANCEL": return { ...state, stage: action.stage, error: null };
  }
}

export function solveRequest(draft: Draft): SolveRequest {
  if (draft.method === "gaussian" || draft.method === "gauss_jordan") return {
    method: draft.method, system: draft.system, options: { arithmetic_mode: draft.mode }, display: draft.display,
  };
  return { method: draft.method, system: draft.system, display: draft.display,
    options: { initial_guess: draft.guess, tolerance: Number(draft.tolerance), max_iterations: Number(draft.maxIterations),
      auto_reorder_for_diagonal_dominance: draft.dominance, auto_reorder_for_nonzero_diagonal: draft.nonzero, run_despite_convergence_risk: draft.risk } };
}
