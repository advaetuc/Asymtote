import { afterEach, expect, test, vi } from "vitest";
import { formatValue } from "../../lib/solver/format";
import { initialDraft, initialState, reducer, solveRequest } from "../../lib/solver/state";
import { DRAFT_KEY, loadDraft, saveDraft } from "../../lib/solver/storage";
import type { AnalyzeOutcome, SolveOutcome } from "../../lib/api/types";
import fixtures from "./fixtures/api.json";

afterEach(() => { sessionStorage.clear(); vi.restoreAllMocks(); });
test("data changes invalidate derived results; display changes do not", () => {
  const ready = { ...initialState, analysis: fixtures.analysisUnique as AnalyzeOutcome, outcome: fixtures.gaussian as SolveOutcome, stage: "RESULTS" as const };
  const edited = reducer(ready, { type: "EDIT", patch: { mode: "exact" }, invalidateAnalysis: true });
  expect(edited.analysis).toBeNull(); expect(edited.outcome).toBeNull(); expect(edited.stage).toBe("MATRIX_INPUT");
  const displayed = reducer(ready, { type: "EDIT", patch: { display: { mode: "fraction", decimal_places: 12 } } });
  expect(displayed.outcome).toBe(ready.outcome); expect(displayed.analysis).toBe(ready.analysis);
  const configured = reducer(ready, { type: "EDIT", patch: { tolerance: "1e-10" } });
  expect(configured.outcome).toBeNull(); expect(configured.analysis).toBe(ready.analysis);
});
test("resizing also updates initial guess and clears stale outcomes", () => {
  const state = reducer(initialState, { type: "RESIZE", m: 12, n: 12 });
  expect(state.draft.system.a).toHaveLength(12); expect(state.draft.guess).toHaveLength(12);
  expect(state.stage).toBe("MATRIX_INPUT");
});
test("request builder keeps direct and iterative options separate", () => {
  const direct = solveRequest({ ...initialDraft, mode: "exact" });
  expect(direct.options).toEqual({ arithmetic_mode: "exact" });
  const iterative = solveRequest({ ...initialDraft, method: "jacobi", guess: ["1/3", "0"] });
  expect(iterative.options).not.toHaveProperty("arithmetic_mode"); expect(iterative.options).toHaveProperty("initial_guess", ["1/3", "0"]);
});
test("draft storage validates dimensions and renews risk consent", () => {
  saveDraft({ ...initialDraft, risk: true }); expect(loadDraft()).toEqual({ ...initialDraft, risk: false });
  sessionStorage.setItem(DRAFT_KEY, "{invalid"); expect(loadDraft()).toBeNull();
  sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ ...initialDraft, guess: [] })); expect(loadDraft()).toBeNull();
  sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ ...initialDraft, system: { a: [["1"], ["2", "3"]], b: ["1", "2"] } })); expect(loadDraft()).toBeNull();
});
test("blocked session storage does not prevent use", () => {
  vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
  expect(loadDraft()).toBeNull(); expect(() => saveDraft(initialDraft)).not.toThrow();
});
test("exact decimal display never converts large integers through Number", () => {
  expect(formatValue({ numerator: "9007199254740993", denominator: "1" }, { mode: "decimal", decimal_places: 2 })).toBe("9007199254740993.00");
  expect(formatValue({ numerator: "1", denominator: "3" }, { mode: "decimal", decimal_places: 6 })).toBe("≈ 0.333333");
  expect(formatValue({ numerator: "-2", denominator: "3" }, { mode: "decimal", decimal_places: 2 })).toBe("≈ −0.67");
});
test("exact fractions and approximate fraction displays stay distinct", () => {
  expect(formatValue({ numerator: "1", denominator: "3" }, { mode: "fraction", decimal_places: 6 })).toBe("1/3");
  expect(formatValue(1/3, { mode: "fraction", decimal_places: 6 })).toBe("≈ 1/3");
  expect(formatValue(1e-15, { mode: "decimal", decimal_places: 6 })).toContain("e-15");
  expect(formatValue(0, { mode: "fraction", decimal_places: 6 })).toBe("≈ 0");
});
