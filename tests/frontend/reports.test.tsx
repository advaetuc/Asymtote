import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import katex from "katex";
import { canonicalJSON, escapeTex, numberTex, reportBlocks, reportJSON, reportLatex, reportMarkdown, type CompletedSolve, type ReportInput } from "../../lib/reports/render";
import { ReportTools } from "../../components/solver/report-tools";
import fixtures from "./fixtures/api.json";
import geometry from "./fixtures/geometry.json";
const display = { mode: "decimal" as const, decimal_places: 3 };
const input = (outcome: unknown): ReportInput => ({ outcome: outcome as CompletedSolve, display });
afterEach(() => vi.restoreAllMocks());

test("canonical JSON preserves raw values, integer strings and array order deterministically", () => {
  expect(canonicalJSON({ z: [3, 1], a: { z: 2, a: 1 } })).toBe(canonicalJSON({ a: { a: 1, z: 2 }, z: [3, 1] }));
  const parsed = JSON.parse(reportJSON(input(fixtures.exact)));
  expect(parsed.outcome).toEqual(fixtures.exact);
  expect(JSON.parse(reportJSON(input(fixtures.jacobi))).outcome.result.history).toEqual(fixtures.jacobi.result.history);
});
test("exact fractions never pass through floating conversion in text reports", () => {
  expect(numberTex({ numerator: "900719925474099312345", denominator: "7" }, display)).toBe("\\frac{900719925474099312345}{7}");
  expect(numberTex(1 / 3, { mode: "fraction", decimal_places: 6 })).toBe("\\approx \\frac{1}{3}");
  expect(numberTex(1e-20, display)).toContain("10^{-20}");
  expect(reportLatex(input(fixtures.exact))).toContain("\\frac{");
  expect(reportMarkdown(input(fixtures.exact))).toContain("\\frac{");
});
test("reports preserve settings, current display and supplied analysis", () => {
  const document = reportMarkdown({ ...input(fixtures.gaussian), analysis: fixtures.analysisUnique as ReportInput["analysis"] });
  expect(document).toContain("Original system"); expect(document).toContain("exported\\_display.decimal\\_places: 3");
  expect(document).toContain("On-demand analysis"); expect(document).toContain("Rank and conditioning analysis");
  expect(document).toContain("Original-system residual diagnostics");
  expect(document).toContain("Complete elimination trace");
});
test("full direct trace, parametric form and contradiction witnesses are included", () => {
  for (const result of [fixtures.gaussJordan, fixtures.gaussian]) {
    const text = reportMarkdown(input(result));
    expect((text.match(/## Step /g) ?? []).length).toBe(result.result.trace.length);
    expect(text).toContain("Final");
  }
  expect(reportMarkdown(input(fixtures.infinite))).toContain("Parametric solution");
  expect(reportMarkdown(input(fixtures.inconsistent))).toContain("Contradiction witnesses");
});
test("iteration exports include all pages, permutation, initial guess and both tests", () => {
  const text = reportMarkdown(input(fixtures.limit));
  expect((text.match(/## Iteration \d+/g) ?? []).length).toBe(fixtures.limit.result.history.length);
  expect(text).toContain("not a converged solution"); expect(text).toContain("Initial guess");
  expect(text).toContain("normalized\\_step\\_change");
  expect(reportMarkdown(input(fixtures.permuted))).toContain("1 \\<- 2");
  expect(reportMarkdown(input(fixtures.declined))).toContain("No completed iterations");
});
test("TeX text is escaped and the document is standalone", () => {
  expect(escapeTex("a_1 & 50% \\input{x} #$~^")).toBe("a\\_1 \\& 50\\% \\textbackslash{}input\\{x\\} \\#\\$\\textasciitilde{}\\textasciicircum{}");
  const tex = reportLatex(input(fixtures.gaussian));
  expect(tex).toMatch(/^\\documentclass/); expect(tex).toContain("\\begin{document}"); expect(tex).toMatch(/\\end\{document\}\n$/);
});
test.each(Object.entries({ ...fixtures, ...geometry }).filter(([, outcome]) => outcome.status === "completed"))("every generated formula parses in KaTeX: %s", (_, outcome) => {
  for (const block of reportBlocks(input(outcome))) if (block.kind === "math") expect(() => katex.renderToString(block.text, { throwOnError: true, trust: false, strict: "error" })).not.toThrow();
});
test("download triggers use deterministic filenames and surface failures", () => {
  vi.useFakeTimers();
  let filename = "";
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) { filename = this.download; });
  const create = vi.fn(() => "blob:test"); vi.stubGlobal("URL", { createObjectURL: create, revokeObjectURL: vi.fn() });
  render(<ReportTools input={input(fixtures.gaussian)} />);
  fireEvent.click(screen.getByRole("button", { name: "Download JSON" }));
  expect(create).toHaveBeenCalledWith(expect.any(Blob));
  expect(filename).toBe("tulya-gaussian-report.json");
  create.mockImplementationOnce(() => { throw Error("blocked"); });
  fireEvent.click(screen.getByRole("button", { name: "Download Markdown" }));
  expect(screen.getByRole("alert")).toHaveTextContent("could not be downloaded");
  vi.runOnlyPendingTimers(); vi.useRealTimers(); vi.unstubAllGlobals();
});
