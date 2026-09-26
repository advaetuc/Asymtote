import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { SolverWorkspace } from "../../components/solver/workspace";
import * as api from "../../lib/api/client";
import type { AnalyzeOutcome, SolveOutcome } from "../../lib/api/types";
import fixtures from "./fixtures/api.json";

vi.mock("../../lib/api/client", async importOriginal => {
  const original = await importOriginal<typeof import("../../lib/api/client")>();
  return { ...original, analyzeSystem: vi.fn(), solveSystem: vi.fn() };
});
const analyze = vi.mocked(api.analyzeSystem), solve = vi.mocked(api.solveSystem);
beforeEach(() => { sessionStorage.clear(); analyze.mockReset(); solve.mockReset(); });
afterEach(() => { sessionStorage.clear(); });

function preset(id = "unique") { fireEvent.change(screen.getByLabelText("Explore an example"), { target: { value: id } }); }
async function analyzed(id = "unique", outcome: AnalyzeOutcome = fixtures.analysisUnique as AnalyzeOutcome) {
  analyze.mockResolvedValueOnce(outcome); preset(id); fireEvent.click(screen.getByRole("button", { name: "Analyze system" }));
  await screen.findByRole("heading", { name: "Method settings" });
}

test("dimensions are selected before constructing the 1–12 bounded grid", () => {
  render(<SolverWorkspace />);
  expect(screen.queryByLabelText("Row 1, x1")).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Equations"), { target: { value: "12" } });
  fireEvent.change(screen.getByLabelText("Unknowns"), { target: { value: "12" } });
  fireEvent.click(screen.getByRole("button", { name: "Create matrix" }));
  expect(screen.getByLabelText("Row 12, x12")).toBeInTheDocument();
  expect(screen.getAllByRole("textbox")).toHaveLength(156);
  fireEvent.change(screen.getByLabelText("Unknowns"), { target: { value: "1" } });
  fireEvent.change(screen.getByLabelText("Equations"), { target: { value: "1" } });
  expect(screen.getAllByRole("textbox")).toHaveLength(2);
});

test("incomplete matrix highlights cells and never calls the API", () => {
  render(<SolverWorkspace />); fireEvent.click(screen.getByRole("button", { name: "Create matrix" }));
  fireEvent.change(screen.getByLabelText("Row 1, x1"), { target: { value: "2" } });
  expect(analyze).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Analyze system" }));
  expect(analyze).not.toHaveBeenCalled(); expect(screen.getByRole("alert")).toHaveTextContent(/highlighted/);
  expect(screen.getByLabelText("Row 2, right-hand side")).toHaveAttribute("aria-invalid", "true");
});

test.each(["gaussian", "gauss_jordan", "jacobi", "gauss_seidel"] as const)("completes the %s workflow with typed options", async method => {
  render(<SolverWorkspace />); await analyzed();
  const names = { gaussian: "Gaussian elimination", gauss_jordan: "Gauss–Jordan", jacobi: "Jacobi", gauss_seidel: "Gauss–Seidel" };
  fireEvent.click(screen.getByRole("radio", { name: names[method] }));
  const data = { gaussian: fixtures.gaussian, gauss_jordan: fixtures.gaussJordan, jacobi: fixtures.jacobi, gauss_seidel: fixtures.seidel }[method];
  solve.mockResolvedValueOnce(data as SolveOutcome);
  fireEvent.click(screen.getByRole("button", { name: "Solve system" }));
  await screen.findByRole("heading", { name: /^(Unique solution|Converged)$/ });
  expect(solve.mock.calls[0]![0].method).toBe(method);
  expect(solve.mock.calls[0]![0].system).toEqual({ a: [["4", "1"], ["2", "3"]], b: ["1", "2"] });
  fireEvent.change(screen.getByLabelText("Decimal places"), { target: { value: "2" } });
  expect(solve).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("heading", { name: /^(Unique solution|Converged)$/ })).toBeInTheDocument();
});

test("matrix edits discard old analysis/results and cancel in-flight work", async () => {
  let resolve!: (value: AnalyzeOutcome) => void;
  analyze.mockImplementationOnce(() => new Promise(r => { resolve = r; }));
  render(<SolverWorkspace />); preset(); fireEvent.click(screen.getByRole("button", { name: "Analyze system" }));
  const signal = analyze.mock.calls[0]![1];
  fireEvent.change(screen.getByLabelText("Row 1, x1"), { target: { value: "9" } });
  expect(signal.aborted).toBe(true);
  await act(async () => resolve(fixtures.analysisUnique as AnalyzeOutcome));
  expect(screen.queryByRole("heading", { name: "Method settings" })).not.toBeInTheDocument();
  expect(screen.getByLabelText("Row 1, x1")).toHaveValue("9");
});

test("canceling solve keeps input/configuration and ignores a late response", async () => {
  render(<SolverWorkspace />); await analyzed();
  let resolve!: (value: SolveOutcome) => void;
  solve.mockImplementationOnce(() => new Promise(r => { resolve = r; }));
  fireEvent.click(screen.getByRole("button", { name: "Solve system" }));
  expect(screen.getByRole("button", { name: "Solve system" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Cancel request" }));
  expect(solve.mock.calls[0]![1].aborted).toBe(true);
  await act(async () => resolve(fixtures.gaussian as SolveOutcome));
  expect(screen.queryByRole("heading", { name: "Unique solution" })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Solve system" })).toBeEnabled();
});

test("changing arithmetic invalidates analysis and exact requests stay direct", async () => {
  render(<SolverWorkspace />); await analyzed();
  fireEvent.click(screen.getByRole("radio", { name: "Jacobi" }));
  fireEvent.change(screen.getByLabelText("Arithmetic"), { target: { value: "exact" } });
  expect(screen.queryByRole("heading", { name: "Method settings" })).not.toBeInTheDocument();
  analyze.mockResolvedValueOnce(fixtures.analysisExact as AnalyzeOutcome);
  fireEvent.click(screen.getByRole("button", { name: "Analyze system" }));
  await screen.findByRole("heading", { name: "Method settings" });
  expect(analyze.mock.lastCall![0].arithmetic_mode).toBe("exact");
  expect(screen.getByRole("radio", { name: "Jacobi" })).toBeDisabled();
  solve.mockResolvedValueOnce(fixtures.exact as SolveOutcome);
  fireEvent.click(screen.getByRole("button", { name: "Solve system" }));
  await screen.findByRole("heading", { name: "Unique solution" });
  expect(solve.mock.lastCall![0].options).toEqual({ arithmetic_mode: "exact" });
});

test("explicit risk consent and reordering options are sent only when selected", async () => {
  render(<SolverWorkspace />); await analyzed("divergent", fixtures.analysisRisk as AnalyzeOutcome);
  expect(screen.getByRole("checkbox", { name: /Run even/ })).not.toBeChecked();
  expect(screen.getByRole("checkbox", { name: /Seek strict/ })).not.toBeChecked();
  fireEvent.click(screen.getByRole("checkbox", { name: /Run even/ }));
  fireEvent.click(screen.getByRole("checkbox", { name: /Allow non-zero/ }));
  fireEvent.change(screen.getByLabelText("Maximum iterations"), { target: { value: "500" } });
  solve.mockResolvedValueOnce(fixtures.breakdown as SolveOutcome);
  fireEvent.click(screen.getByRole("button", { name: "Solve system" }));
  await screen.findByRole("heading", { name: "Numerical breakdown" });
  expect(solve.mock.lastCall![0].options).toMatchObject({ run_despite_convergence_risk: true, auto_reorder_for_nonzero_diagonal: true, auto_reorder_for_diagonal_dominance: false, max_iterations: 500 });
});

test("invalid method options prevent solving and explain the bounds", async () => {
  render(<SolverWorkspace />); await analyzed(); fireEvent.click(screen.getByRole("radio", { name: "Jacobi" }));
  fireEvent.change(screen.getByLabelText("Tolerance"), { target: { value: "NaN" } });
  fireEvent.change(screen.getByLabelText("Maximum iterations"), { target: { value: "501" } });
  expect(screen.getByRole("button", { name: "Solve system" })).toBeDisabled();
  expect(screen.getByText(/Tolerance must be between/)).toBeInTheDocument();
});

test("API cell errors map to inputs, keep correlation ID, and can be retried", async () => {
  analyze.mockRejectedValueOnce(new api.ApiError("Request validation failed.", "http", "validation-id", 422, [{ code: "magnitude_out_of_range", message: "Out of range", location: ["body", "system", "a", 0, 1] }]));
  render(<SolverWorkspace />); preset(); fireEvent.click(screen.getByRole("button", { name: "Analyze system" }));
  await screen.findByRole("heading", { name: "Check your input" });
  expect(screen.getByLabelText("Row 1, x2")).toHaveAccessibleDescription("Out of range");
  expect(screen.getByText("Request validation-id")).toBeInTheDocument();
  analyze.mockResolvedValueOnce(fixtures.analysisUnique as AnalyzeOutcome);
  fireEvent.click(screen.getByRole("button", { name: "Retry request" }));
  await screen.findByRole("heading", { name: "Method settings" });
});

test.each(["http", "network"] as const)("%s errors remain separate from mathematical outcomes", async kind => {
  analyze.mockRejectedValueOnce(new api.ApiError("Please retry.", kind, "retry-id", kind === "http" ? 500 : undefined));
  render(<SolverWorkspace />); preset(); fireEvent.click(screen.getByRole("button", { name: "Analyze system" }));
  await screen.findByRole("heading", { name: kind === "http" ? "The solver encountered an error" : "Request could not be completed" });
  expect(screen.getByText("Request retry-id")).toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: "Unique solution" })).not.toBeInTheDocument();
});

test("drafts restore compatible data, never old results", async () => {
  const { unmount } = render(<SolverWorkspace />); preset("infinite");
  await waitFor(() => expect(sessionStorage.getItem("tulya.draft.v1")).toContain('"3","4"'));
  unmount(); render(<SolverWorkspace />);
  expect(screen.getByLabelText("Row 1, x3")).toHaveValue("1");
  expect(screen.queryByRole("heading", { name: "Method settings" })).not.toBeInTheDocument();
});
