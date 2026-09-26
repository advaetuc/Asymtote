import { useState } from "react";
import type { Display, Model } from "../../lib/api/types";
import { formatValue, metric } from "../../lib/solver/format";

export function ConvergenceChart({ history, tolerance }: { history: Model<"IterationRecord">[]; tolerance: number }) {
  if (!history.length) return <p>No completed iterations to plot.</p>;
  const values = history.flatMap(r => [r.backward_error, r.normalized_step_change]);
  const positive = values.filter(v => v > 0);
  const low = Math.min(-1, Math.floor(Math.log10(Math.min(tolerance, ...positive))) - 1);
  const high = Math.max(0, Math.ceil(Math.log10(Math.max(tolerance, ...positive))));
  const x = (i: number) => 72 + (history.length === 1 ? 245 : i / (history.length - 1) * 490);
  const y = (value: number) => 220 - ((value === 0 ? low : Math.log10(value)) - low) / (high - low) * 190;
  const path = (key: "backward_error" | "normalized_step_change") => history.map((r, i) => `${x(i)},${y(r[key])}`).join(" ");
  return <figure className="convergence-chart"><figcaption>Dual convergence · logarithmic scale</figcaption>
    <svg viewBox="0 0 620 270" role="img" aria-label="Normalized backward error and normalized step change against target tolerance">
      <desc>Both series must reach the target. Exact zero values are drawn at the bottom edge, not replaced in the computation. The table below contains the values.</desc>
      {[0, 0.25, 0.5, 0.75, 1].map(f => { const log = low + (high - low) * f; const lineY = 220 - f * 190; return <g key={f}><line x1="72" x2="562" y1={lineY} y2={lineY} className="chart-grid" /><text x="62" y={lineY + 4} textAnchor="end">10^{log.toFixed(1)}</text></g>; })}
      <line x1="72" x2="562" y1={y(tolerance)} y2={y(tolerance)} className="target-line" />
      <polyline points={path("backward_error")} className="error-series" /><polyline points={path("normalized_step_change")} className="step-series" />
      {history.map((r, i) => <g key={r.index}><circle cx={x(i)} cy={y(r.backward_error)} r="2.5" className="error-point"><title>Iteration {r.index}: backward error {r.backward_error}</title></circle><circle cx={x(i)} cy={y(r.normalized_step_change)} r="2.5" className="step-point"><title>Iteration {r.index}: step change {r.normalized_step_change}</title></circle></g>)}
      <text x="72" y="247">1</text><text x="562" y="247" textAnchor="end">{history.length}</text><text x="317" y="263" textAnchor="middle">Iteration</text>
    </svg><div className="chart-legend"><span className="error-legend">━ Backward error</span><span className="step-legend">┄ Step change</span><span>··· Target {metric(tolerance)}</span></div><p className="muted">Zero values sit at the lower edge. Hover a point for its raw value, or read the accessible history table.</p>
  </figure>;
}

export function IterativeInspector({ result, display }: { result: Model<"IterativeResult">; display: Display }) {
  const [page, setPage] = useState(0);
  const perPage = 25, pages = Math.max(1, Math.ceil(result.history.length / perPage));
  const reordered = result.reordering.permutation.order.some((row, i) => row !== i);
  return <>
    <div className="info-banner"><strong>{reordered ? "Equations reordered" : "Original equation order retained"}</strong><p>Working rows ← original rows: {result.reordering.permutation.order.map((row, i) => `${i + 1} ← ${row + 1}`).join("; ")}. The RHS follows the same mapping; variable order is unchanged.</p><p>Reason: {result.reordering.permutation.purpose.replaceAll("_", " ")}.</p></div>
    <p>{result.convergence.explanation}</p><p>SPD diagnostic: {result.convergence.symmetric_positive_definite === null ? "unavailable" : result.convergence.symmetric_positive_definite ? "yes" : "no"} · actual iteration-matrix spectral radius: {metric(result.convergence.spectral.radius)}</p>
    {result.breakdown_reason && <p className="error-note">{result.breakdown_reason} The last complete finite iteration is preserved.</p>}
    <ConvergenceChart history={result.history} tolerance={result.options.tolerance ?? 1e-8} />
    <h3>Iteration history</h3>
    {!result.history.length ? <p>No iterations were completed. The last iterate is the initial guess.</p> : <>
      <div className="step-controls"><button disabled={!page} onClick={() => setPage(p => p - 1)}>Earlier iterations</button><span>Page {page + 1} of {pages} · {result.history.length} iterations</span><button disabled={page + 1 >= pages} onClick={() => setPage(p => p + 1)}>Later iterations</button></div>
      <div className="table-scroll" tabIndex={0} aria-label="Iteration history scroll area"><table className="numeric-table"><caption>Completed iterations; diagnostics use the original equations</caption><thead><tr><th scope="col">k</th>{result.last_iterate.map((_, i) => <th key={i} scope="col">x<sub>{i + 1}</sub></th>)}<th scope="col">Δ∞</th><th scope="col">Residual ∞</th><th scope="col">Backward error</th><th scope="col">Normalized step</th><th scope="col">Converged</th></tr></thead><tbody>{result.history.slice(page * perPage, (page + 1) * perPage).map(row => <tr key={row.index}><th scope="row">{row.index}</th>{row.vector.map((value, j) => <td key={j} title={String(value)}>{formatValue(value, display)}</td>)}<td title={String(row.delta_inf)}>{metric(row.delta_inf)}</td><td title={String(row.residual_inf)}>{metric(row.residual_inf)}</td><td title={String(row.backward_error)}>{metric(row.backward_error)}</td><td title={String(row.normalized_step_change)}>{metric(row.normalized_step_change)}</td><td>{row.converged ? "Yes · both tests" : "No"}</td></tr>)}</tbody></table></div>
    </>}
  </>;
}
