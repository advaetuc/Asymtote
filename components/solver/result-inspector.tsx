import type { AnalyzeOutcome, Display, SolveOutcome } from "../../lib/api/types";
import { formatValue, rawValue } from "../../lib/solver/format";
import { METHODS } from "../../lib/solver/presets";
import { Conditioning } from "./analysis-panel";
import { DirectInspector } from "./direct-inspector";
import { IterativeInspector } from "./iterative-inspector";
import { GeometryPanel } from "./geometry-panel";
import { ReportTools } from "./report-tools";

const statuses = { converged: "Converged", max_iterations_reached: "Iteration limit reached", numeric_breakdown: "Numerical breakdown", convergence_risk_declined: "Convergence risk declined" };
export function ResultInspector({ outcome, display, analysis }: { outcome: SolveOutcome; display: Display; analysis?: AnalyzeOutcome | null }) {
  if (outcome.status === "numeric_breakdown") return <section className="panel error-note" aria-labelledby="result-title"><h2 id="result-title" tabIndex={-1}>Numerical limitation</h2><p>{outcome.error.message}</p><p>Try rescaling or exact direct arithmetic to obtain a reliable result.</p><small>Request {outcome.request_id}</small></section>;
  const result = outcome.result, iterative = "history" in result;
  const heading = iterative ? statuses[result.status] : result.classification.classification === "unique" ? "Unique solution" : result.classification.classification === "infinite" ? "Infinitely many solutions" : "Inconsistent system";
  const vector = iterative ? result.solution ?? result.last_iterate : result.solution;
  const exact = outcome.problem.arithmetic_mode === "exact";
  return <section className="panel result-panel" aria-labelledby="result-title"><p className="eyebrow">04 / Inspect the reasoning</p><h2 id="result-title" tabIndex={-1}>{heading}</h2><p>{METHODS[result.method].name} · {exact ? "Exact rational arithmetic" : "Float64 arithmetic"}</p>
    <p className="muted">{exact ? "Fractions are exact. Rounded decimal displays carry ≈." : "Values are floating approximations. Display precision never changes the computation; fraction displays carry ≈."} Hover a number to read its stored value.</p>
    {vector && <div className="answer-block"><h3>{iterative && !result.solution ? "Last iterate — not a converged solution" : "Solution vector"}</h3><dl className="solution-vector">{vector.map((value, i) => <div key={i}><dt>x<sub>{i + 1}</sub></dt><dd title={rawValue(value)}>{formatValue(value, display)}</dd></div>)}</dl></div>}
    {(result.warnings ?? []).map(warning => <p className="warning-note" key={warning}>{warning}</p>)}
    <details open><summary>Steps &amp; explanation</summary>{iterative ? <IterativeInspector key={outcome.request_id} result={result} display={display} /> : <DirectInspector key={outcome.request_id} result={result} original={outcome.problem.original_system} display={display} />}</details>
    <section className="diagnostics-panel" aria-labelledby="residual-title"><h3 id="residual-title">Original-system diagnostics</h3>{result.diagnostics ? <dl className="facts"><div><dt>Residual ‖Ax − b‖∞</dt><dd title={rawValue(result.diagnostics.residual_inf)}>{formatValue(result.diagnostics.residual_inf, display)}</dd></div><div><dt>Normalized backward error</dt><dd title={rawValue(result.diagnostics.backward_error)}>{formatValue(result.diagnostics.backward_error, display)}</dd></div></dl> : <p>No candidate with valid residual diagnostics is available for this outcome.</p>}<Conditioning value={outcome.conditioning} /></section>
    <GeometryPanel key={`geometry-${outcome.request_id}`} outcome={outcome} />
    <ReportTools input={{ outcome, display, analysis }} />
    <small className="muted">Request {outcome.request_id} · Solver {outcome.report.solver_version}</small>
  </section>;
}
