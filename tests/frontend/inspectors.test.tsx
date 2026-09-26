import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import type { AnalyzeOutcome, SolveOutcome } from "../../lib/api/types";
import { AnalysisPanel } from "../../components/solver/analysis-panel";
import { ResultInspector } from "../../components/solver/result-inspector";
import fixtures from "./fixtures/api.json";

const display = { mode: "decimal" as const, decimal_places: 6 };
test("direct replay starts at original, highlights swaps, and honors boundaries", () => {
  render(<ResultInspector outcome={fixtures.gaussJordan as SolveOutcome} display={display} />);
  expect(screen.getByRole("button", { name: "Previous step" })).toBeDisabled();
  expect(screen.getByText("Original augmented matrix")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Next step" }));
  expect(screen.getByText("Swap equations")).toBeInTheDocument();
  expect(screen.getByRole("rowheader", { name: "1 · target" })).toBeInTheDocument(); expect(screen.getByRole("rowheader", { name: "2 · source" })).toBeInTheDocument();
  expect(document.querySelectorAll(".pivot-column").length).toBeGreaterThan(0);
  fireEvent.click(screen.getByRole("button", { name: "End" }));
  expect(screen.getByRole("button", { name: "Next step" })).toBeDisabled();
  expect(screen.getByText("Scale a pivot row")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Start" }));
  expect(screen.getByText("Original augmented matrix")).toBeInTheDocument();
});
test("Gaussian elimination exposes back substitution", () => {
  render(<ResultInspector outcome={fixtures.gaussian as SolveOutcome} display={display} />);
  expect(screen.getByText("Read the answer by back substitution")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Next step" }));
  expect(screen.getByText("Eliminate a coefficient")).toBeInTheDocument();
});
test("free variables and contradiction witnesses have separate outcomes", () => {
  const { rerender } = render(<ResultInspector outcome={fixtures.infinite as SolveOutcome} display={display} />);
  expect(screen.getByRole("heading", { name: "Parametric solution" })).toBeInTheDocument();
  expect(screen.getByText(/Free variables: x3/)).toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: "Solution vector" })).not.toBeInTheDocument();
  rerender(<ResultInspector outcome={fixtures.inconsistent as SolveOutcome} display={display} />);
  expect(screen.getByRole("heading", { name: "Contradiction witnesses" })).toBeInTheDocument();
  expect(screen.getByText(/No vector satisfies all equations/)).toBeInTheDocument();
});
test.each(["jacobi", "seidel", "limit", "declined", "breakdown", "permuted"] as const)("renders iterative contract %s without pretending failure is a solution", name => {
  render(<ResultInspector outcome={fixtures[name] as SolveOutcome} display={display} />);
  const result = fixtures[name].result;
  if (result.status !== "converged") expect(screen.getByRole("heading", { name: /Last iterate/ })).toBeInTheDocument();
  else expect(screen.getByRole("heading", { name: "Solution vector" })).toBeInTheDocument();
  if (result.history.length) expect(screen.getByRole("img", { name: /Normalized backward error/ })).toBeInTheDocument();
  else expect(screen.getByText("No completed iterations to plot.")).toBeInTheDocument();
  if (name === "permuted") expect(screen.getByText("Equations reordered")).toBeInTheDocument();
});
test("long iteration history is paged without dropping records", () => {
  render(<ResultInspector outcome={fixtures.limit as SolveOutcome} display={display} />);
  expect(screen.getByText("Page 1 of 3 · 60 iterations")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Later iterations" }));
  fireEvent.click(screen.getByRole("button", { name: "Later iterations" }));
  expect(screen.getByText("Page 3 of 3 · 60 iterations")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Later iterations" })).toBeDisabled();
});
test("zero diagnostics produce finite chart coordinates and are labeled", () => {
  render(<ResultInspector outcome={fixtures.zeroStep as SolveOutcome} display={display} />);
  const svg = screen.getByRole("img");
  expect(svg.outerHTML).not.toMatch(/NaN|Infinity/);
  expect(screen.getByText(/Zero values sit at the lower edge/)).toBeInTheDocument();
});
test("exact values retain fractional precision", () => {
  render(<ResultInspector outcome={fixtures.exact as SolveOutcome} display={{ mode: "fraction", decimal_places: 2 }} />);
  expect(screen.getByText("1/10")).toBeInTheDocument(); expect(screen.getByText(/Exact rational arithmetic/)).toBeInTheDocument();
});
test("method incompatibilities and candidate SPD diagnostics are explained", () => {
  const { rerender } = render(<AnalysisPanel analysis={fixtures.analysisInfinite as AnalyzeOutcome} method="gaussian" onSelect={() => {}} />);
  expect(screen.getByRole("radio", { name: /Jacobi/ })).toBeDisabled();
  expect(screen.getAllByText("Iteration requires a square matrix.")).toHaveLength(2);
  rerender(<AnalysisPanel analysis={fixtures.analysisUnique as AnalyzeOutcome} method="gaussian" onSelect={() => {}} />);
  expect(screen.getAllByText(/SPD:.*spectral radius/)).toHaveLength(2);
});
test("top-level numerical limitation is not rendered as a successful solve", () => {
  render(<ResultInspector display={display} outcome={{ status: "numeric_breakdown", request_id: "rank-check", method: "gaussian", arithmetic_mode: "float64", shape: { equations: 2, unknowns: 2 }, error: { code: "rank_uncertain", message: "Use exact mode.", location: [] } }} />);
  expect(screen.getByRole("heading", { name: "Numerical limitation" })).toBeInTheDocument();
  expect(screen.getByText(/Request rank-check/)).toBeInTheDocument();
});
