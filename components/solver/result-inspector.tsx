import type { AnalyzeOutcome, Display, SolveOutcome } from "../../lib/api/types";
import { formatValue, rawValue } from "../../lib/solver/format";
import { METHODS } from "../../lib/solver/presets";
import { Conditioning } from "./analysis-panel";
import { DirectInspector } from "./direct-inspector";
import { IterativeInspector } from "./iterative-inspector";
import { GeometryPanel } from "./geometry-panel";
import { ReportTools } from "./report-tools";
import { APPROXIMATE_FRACTION_COPY } from "../site-copy";

const statuses = { converged: "Converged", max_iterations_reached: "Iteration limit reached", numeric_breakdown: "Numerical breakdown", convergence_risk_declined: "Convergence risk declined" };
export function ResultInspector({ outcome, display, analysis }: { outcome: SolveOutcome; display: Display; analysis?: AnalyzeOutcome | null }) {
  if (outcome.status === "numeric_breakdown") return <section className="panel error-note" aria-labelledby="result-title"><h2 id="result-title" tabIndex={-1}>Numerical limitation</h2><p>{outcome.error.message}</p><p>Try rescaling or exact direct arithmetic to obtain a reliable result.</p><small>Request {outcome.request_id}</small></section>;
  const result = outcome.result, iterative = "history" in result;
  const heading = iterative ? statuses[result.status] : result.classification.classification === "unique" ? "Unique solution" : result.classification.classification === "infinite" ? "Infinitely many solutions" : "Inconsistent system";
  const vector = iterative ? result.solution ?? result.last_iterate : result.solution;
  const exact = outcome.problem.arithmetic_mode === "exact";
  const rank = result.classification, unknowns = outcome.problem.shape.unknowns;
  return <section className="panel result-panel" aria-labelledby="result-title"><p className="eyebrow">04 / Inspect the reasoning</p><h2 id="result-title" tabIndex={-1}>Answer</h2><p>The solution, parametric form, or reason none exists.</p><h3>{heading}</h3><p>{METHODS[result.method].name} · {exact ? "Exact rational arithmetic" : "Float64 arithmetic"}</p>
    {rank.classification === "inconsistent" && <p>No values satisfy every equation at once — the augmented matrix&apos;s rank ({rank.rank_augmented}) is higher than the coefficient matrix&apos;s rank ({rank.rank_a}). This is a valid mathematical outcome, not an error.</p>}
    {rank.classification === "infinite" && <p>Rank falls short of the unknown count by {unknowns - rank.rank_a} — {unknowns - rank.rank_a} free parameter(s) describe the full solution set below.</p>}
    {!iterative && result.method === "gaussian" && rank.classification === "infinite" && <p>This system doesn&apos;t have a unique solution — rank(A) is {rank.rank_a}, short of the {unknowns} unknowns. See Steps for where elimination stalls, or switch to Gauss–Jordan for the full parametric solution set.</p>}
    {iterative && result.status === "max_iterations_reached" && <p>{METHODS[result.method].name} didn&apos;t converge within {result.options.max_iterations ?? 25} iterations (tolerance {result.options.tolerance ?? 1e-8} not met). This is not a solution — see Diagnostics for the spectral radius and residual trend.</p>}
    <p className="muted">{exact ? "Fractions are exact. Rounded decimal displays carry ≈." : "Values are floating approximations. Display precision never changes the computation; fraction displays carry ≈."} Hover a number to read its stored value.</p>
    {vector && <div className="answer-block"><h3>{iterative && !result.solution ? "Last iterate — not a converged solution" : "Solution vector"}</h3><dl className="solution-vector">{vector.map((value, i) => <div key={i}><dt>x<sub>{i + 1}</sub></dt><dd title={`${iterative && display.mode === "fraction" ? `${APPROXIMATE_FRACTION_COPY} Stored value: ` : ""}${rawValue(value)}`}>{formatValue(value, display)}</dd></div>)}</dl></div>}
    {(result.warnings ?? []).map(warning => <p className="warning-note" key={warning}>{warning}</p>)}
    <details open><summary>Steps</summary><p>Every row operation (direct methods) or iteration (iterative methods), in order.</p>{iterative ? <IterativeInspector key={outcome.request_id} result={result} display={display} /> : <DirectInspector key={outcome.request_id} result={result} original={outcome.problem.original_system} display={display} />}</details>
    <section className="diagnostics-panel" aria-labelledby="residual-title"><h3 id="residual-title">Diagnostics</h3><p>Rank, condition number, residual, backward error, and any row reordering that was applied.</p>{iterative && <p>Iteration-matrix spectral radius: {result.convergence.spectral.radius ?? "unavailable"}. See the iteration history in Steps for the residual trend and applied row order.</p>}{result.diagnostics ? <dl className="facts"><div><dt>Residual ‖Ax − b‖∞</dt><dd title={rawValue(result.diagnostics.residual_inf)}>{formatValue(result.diagnostics.residual_inf, display)}</dd></div><div><dt>Normalized backward error</dt><dd title={rawValue(result.diagnostics.backward_error)}>{formatValue(result.diagnostics.backward_error, display)}</dd></div></dl> : <p>No candidate with valid residual diagnostics is available for this outcome.</p>}<Conditioning value={outcome.conditioning} /></section>
    <GeometryPanel key={`geometry-${outcome.request_id}`} outcome={outcome} />
    <ReportTools input={{ outcome, display, analysis }} />
    <small className="muted">Request {outcome.request_id} · Solver {outcome.report.solver_version}</small>
  </section>;
}
