import type { AnalyzeOutcome, Display, Model, Numeric } from "../api/types";
import { formatValue } from "../solver/format";

export type CompletedSolve = Model<"SolveResponse">;
export type ReportBlock = { kind: "heading" | "text" | "math"; text: string };
export type ReportInput = { outcome: CompletedSolve; display: Display; analysis?: AnalyzeOutcome | null };

/** Key order is stable; numbers and rational integer strings are never rounded. */
export function canonicalJSON(value: unknown): string {
  function ordered(item: unknown): unknown {
    if (Array.isArray(item)) return item.map(ordered);
    if (item !== null && typeof item === "object") return Object.fromEntries(Object.entries(item).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([key, v]) => [key, ordered(v)]));
    return item;
  }
  return JSON.stringify(ordered(value), null, 2) + "\n";
}

export function reportJSON(input: ReportInput): string {
  return canonicalJSON({ export_schema_version: 1, display: input.display, analysis: input.analysis ?? null, outcome: input.outcome });
}

export function escapeTex(text: string): string {
  const substitutions: Record<string, string> = { "\\": "\\textbackslash{}", "{": "\\{", "}": "\\}", "#": "\\#", "$": "\\$", "%": "\\%", "&": "\\&", "_": "\\_", "~": "\\textasciitilde{}", "^": "\\textasciicircum{}", "∞": "$\\infty$", "≈": "$\\approx$", "→": "$\\rightarrow$", "←": "$\\leftarrow$", "−": "-", "–": "--", "—": "---", "ρ": "$\\rho$", "≤": "$\\leq$", "≥": "$\\geq$" };
  return [...text].map(c => substitutions[c] ?? c).join("");
}

export function numberTex(value: Numeric, display: Display): string {
  // Exact values never pass through Number, even when decimal presentation is selected.
  if (typeof value !== "number") return value.denominator === "1" ? value.numerator : `\\frac{${value.numerator}}{${value.denominator}}`;
  const rendered = formatValue(value, display).replaceAll("−", "-").replace(/^≈\s*/, "");
  const scientific = rendered.match(/^(.+)e([+-]?\d+)$/);
  const fraction = rendered.match(/^(-?\d+)\/(\d+)$/);
  return `\\approx ${scientific ? `${scientific[1]}\\times 10^{${Number(scientific[2])}}` : fraction ? `\\frac{${fraction[1]}}{${fraction[2]}}` : rendered}`;
}

export function matrixTex(matrix: Numeric[][], display: Display, augmented = false): string {
  const columns = matrix[0]?.length ?? 0;
  return `\\left[\\begin{array}{${"r".repeat(Math.max(0, columns - (augmented ? 1 : 0)))}${augmented ? "|r" : ""}}${matrix.map(row => row.map(v => numberTex(v, display)).join(" & ")).join(" \\\\ ")}\\end{array}\\right]`;
}

function describe(value: unknown, path = ""): string[] {
  if (value !== null && typeof value === "object" && !Array.isArray(value)) return Object.entries(value).sort(([a], [b]) => a.localeCompare(b, "en")).flatMap(([key, child]) => describe(child, path ? `${path}.${key}` : key));
  return [`${path}: ${Array.isArray(value) ? JSON.stringify(value) : value === null ? "unavailable" : String(value)}`];
}

/** A common ordered document feeds Markdown, TeX and the complete print view. */
export function reportBlocks({ outcome, display, analysis }: ReportInput): ReportBlock[] {
  const blocks: ReportBlock[] = [];
  const add = (kind: ReportBlock["kind"], text: string) => blocks.push({ kind, text });
  const heading = (text: string) => add("heading", text);
  const text = (value: string) => add("text", value);
  const math = (value: string) => add("math", value);
  const details = (value: unknown) => describe(value).forEach(text);
  const num = (v: Numeric) => numberTex(v, display);
  const vector = (values: Numeric[]) => matrixTex(values.map(v => [v]), display);
  const system = outcome.problem.original_system, result = outcome.result;
  heading("TULYA linear system report");
  text(`Method: ${result.method}. Arithmetic: ${outcome.problem.arithmetic_mode}. Request: ${outcome.request_id}. Solver: ${outcome.report.solver_version}.`);
  text("Exact rationals remain exact in this report regardless of decimal display settings. Floating values are approximations. Presentation rounding does not change computation; JSON retains every returned value.");
  heading("Original system");
  math(matrixTex(system.a.map((row, i) => [...row, system.b[i]!]), display, true));
  system.a.forEach((row, i) => math(`${row.map((v, j) => `\\left(${num(v)}\\right)x_{${j + 1}}`).join(" + ")} = ${num(system.b[i]!)}`));
  heading("Settings"); details({ arithmetic: outcome.problem.arithmetic_mode, exported_display: display, submitted_display: outcome.report.display, options: outcome.report.options });
  heading("Rank and conditioning analysis"); details(result.classification); details({ conditioning: outcome.conditioning, conditioning_arithmetic: outcome.conditioning_arithmetic_mode });
  if (analysis) {
    heading("On-demand analysis");
    if (analysis.status === "numeric_breakdown") text(analysis.error.message);
    else {
      text(`Analysis request: ${analysis.request_id}. Strict diagonal dominance: ${analysis.strict_diagonal_dominance === null ? "unavailable" : analysis.strict_diagonal_dominance ? "yes" : "no"}.`);
      for (const [name, permutation] of [["Strict dominance", analysis.dominance_permutation], ["Non-zero diagonal", analysis.nonzero_permutation]] as const) text(`${name} candidate row order: ${permutation ? permutation.order.map(i => i + 1).join(", ") : "none"}. These are analysis candidates; the applied order is recorded separately.`);
      analysis.methods.forEach(method => { text(`${method.method}: ${method.eligible ? "eligible subject to stated requirements" : "unavailable"}. ${method.reason}`); if (method.convergence) text(`Candidate-order diagnostics: SPD ${method.convergence.symmetric_positive_definite ?? "unavailable"}; spectral radius ${method.convergence.spectral.radius ?? "unavailable"}. ${method.convergence.explanation}`); });
      analysis.warnings.forEach(text);
    }
  }
  heading("Outcome");
  text(`Classification: ${result.classification.classification}.`);
  if ("history" in result) {
    text(`Iteration status: ${result.status}.`);
    text(result.solution ? "Converged solution:" : "Last iterate only; this is not a converged solution:");
    math(`x ${result.solution ? "=" : "\\approx"} ${vector(result.solution ?? result.last_iterate)}`);
    heading("Applied row permutation");
    text(`Working rows receive original rows: ${result.reordering.permutation.order.map((row, i) => `${i + 1} <- ${row + 1}`).join("; ")}. Variable order is unchanged.`);
    details(result.reordering);
    math(matrixTex(result.reordering.permutation.order.map(row => [...system.a[row]!, system.b[row]!]), display, true));
    heading("Convergence diagnostics"); details(result.convergence);
    if (result.breakdown_reason) text(result.breakdown_reason);
    heading("Complete iteration history");
    text("Initial guess:"); math(`x^{(0)} = ${vector(result.initial_guess)}`);
    text("Both normalized backward error and normalized step change must meet the configured tolerance.");
    if (!result.history.length) text("No completed iterations.");
    for (const iteration of result.history) {
      heading(`Iteration ${iteration.index}`); math(`x^{(${iteration.index})} = ${vector(iteration.vector)}`);
      // Diagnostic text uses round-trip numbers, even when vector displays are rounded.
      details({ delta_inf: iteration.delta_inf, residual_inf: iteration.residual_inf, backward_error: iteration.backward_error, normalized_step_change: iteration.normalized_step_change, converged: iteration.converged });
    }
  } else {
    if (result.solution) math(`x = ${vector(result.solution)}`);
    if (result.parametric_solution) {
      heading("Parametric solution");
      text(`Free columns: ${result.free_columns.map(i => i + 1).join(", ")}. All parameters range over the reals.`);
      for (const expression of result.parametric_solution.expressions) math(`\\mathrm{${escapeTex(expression.variable)}} = ${num(expression.constant)}${expression.terms.map(term => ` + \\left(${num(term.coefficient)}\\right)\\mathrm{${escapeTex(term.parameter)}}`).join("")}`);
      text("Residual diagnostics use the particular solution with all parameters equal to zero.");
    }
    if (result.contradictory_rows.length) {
      heading("Contradiction witnesses");
      result.contradictory_rows.forEach(row => { text(`Reduced row ${row + 1}: coefficients are ${result.arithmetic_mode === "exact" ? "exactly zero" : "zero under the backend row tolerance"}, while the right side is nonzero.`); math(matrixTex([result.matrix[row]!], display, true)); });
    }
    heading("Complete elimination trace");
    text("Row numbering in this report is one-based. Each snapshot is the returned state after the operation. Row swaps are the applied equation permutations.");
    if (!result.trace.length) text("No row operations were required.");
    result.trace.forEach((operation, i) => {
      heading(`Step ${i + 1}: ${operation.operation_type}`);
      text(operation.explanation);
      text(`Target row: ${operation.target_row + 1}. Source row: ${operation.source_row === null ? "none" : operation.source_row + 1}. Pivot column: ${operation.pivot_column + 1}.`);
      if (operation.factor !== null) math(`\\text{Factor} = ${num(operation.factor)}`);
      math(matrixTex(operation.matrix_after, display, true));
    });
    heading(`Final ${result.form.toUpperCase()}`); math(matrixTex(result.matrix, display, true));
    details({ pivot_columns_one_based: result.pivot_columns.map(i => i + 1), free_columns_one_based: result.free_columns.map(i => i + 1), row_tolerances: result.row_tolerances });
  }
  heading("Original-system residual diagnostics");
  if (result.diagnostics) { math(`\\lVert Ax-b\\rVert_\\infty = ${num(result.diagnostics.residual_inf)}`); math(`\\eta = ${num(result.diagnostics.backward_error)}`); }
  else text("No candidate with valid residual diagnostics is available.");
  heading("Warnings"); (result.warnings?.length ? result.warnings : ["No additional solver warnings."]).forEach(text);
  return blocks;
}

export function reportMarkdown(input: ReportInput): string {
  return reportBlocks(input).map(block => block.kind === "heading" ? `## ${block.text}` : block.kind === "math" ? `$$\n${block.text}\n$$` : block.text.replace(/[\\`*_{}[\]<>#|]/g, "\\$&")).join("\n\n") + "\n";
}

export function reportLatex(input: ReportInput): string {
  return ["\\documentclass[11pt]{article}", "\\usepackage[T1]{fontenc}", "\\usepackage[utf8]{inputenc}", "\\usepackage{amsmath,amssymb,geometry,graphicx}", "\\geometry{margin=20mm}", "\\setlength{\\emergencystretch}{3em}", "\\begin{document}", ...reportBlocks(input).map(block => block.kind === "heading" ? `\\section*{${escapeTex(block.text)}}` : block.kind === "math" ? `\\begin{center}\\resizebox{\\ifdim\\width>\\linewidth\\linewidth\\else\\width\\fi}{!}{$\\displaystyle ${block.text}$}\\end{center}` : `${escapeTex(block.text)}\\par`), "\\end{document}", ""].join("\n");
}
