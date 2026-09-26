import type { Draft } from "../../lib/solver/state";
import { tokenIssue } from "../../lib/solver/grid";

export function configurationIssues(draft: Draft): string[] {
  if (draft.method === "gaussian" || draft.method === "gauss_jordan") return [];
  const issues: string[] = [];
  if (!draft.tolerance.trim() || !Number.isFinite(Number(draft.tolerance)) || Number(draft.tolerance) < 1e-14 || Number(draft.tolerance) > 1e-2) issues.push("Tolerance must be between 1e-14 and 1e-2.");
  if (!/^\d+$/.test(draft.maxIterations) || Number(draft.maxIterations) < 1 || Number(draft.maxIterations) > 500) issues.push("Maximum iterations must be a whole number from 1 to 500.");
  if (draft.guess.some(v => tokenIssue(v))) issues.push("Correct the initial guess entries.");
  return issues;
}

export function Configuration({ draft, onChange }: { draft: Draft; onChange: (patch: Partial<Draft>) => void }) {
  const iterative = draft.method === "jacobi" || draft.method === "gauss_seidel";
  return <section className="panel" aria-labelledby="config-title"><p className="eyebrow">03 / Choose the calculation</p><h2 id="config-title">Method settings</h2>
    {!iterative && <p>Direct methods find the solution structure by row reduction. Select float64 or exact rational arithmetic above the matrix.</p>}
    {iterative && <>
      <p className="muted">Iterations use unrounded float64 values. A solution is reported only when both backward error and normalized step change meet the tolerance.</p>
      <fieldset><legend>Initial guess</legend><div className="guess-grid">{draft.guess.map((value, i) => <label key={i}>x<sub>{i + 1}</sub><input aria-label={`Initial guess x${i + 1}`} value={value} aria-invalid={!!tokenIssue(value)} onChange={event => onChange({ guess: draft.guess.map((v, j) => j === i ? event.target.value : v) })} />{tokenIssue(value) && <small className="error-note">{tokenIssue(value)}</small>}</label>)}</div></fieldset>
      <div className="control-row"><label>Tolerance<input value={draft.tolerance} aria-invalid={configurationIssues(draft).some(v => v.startsWith("Tolerance"))} onChange={e => onChange({ tolerance: e.target.value })} /></label><label>Maximum iterations<input inputMode="numeric" value={draft.maxIterations} aria-invalid={configurationIssues(draft).some(v => v.startsWith("Maximum"))} onChange={e => onChange({ maxIterations: e.target.value })} /></label></div>
      <label className="check-line"><input type="checkbox" checked={draft.dominance} onChange={e => onChange({ dominance: e.target.checked })} />Seek strict diagonal dominance by reordering rows</label>
      <label className="check-line"><input type="checkbox" checked={draft.nonzero} onChange={e => onChange({ nonzero: e.target.checked })} />Allow non-zero diagonal fallback</label>
      <p className="muted">Fallback can make division possible; it does not guarantee convergence. Diagnostics from analysis describe the indicated candidate row order. The solve response evaluates your chosen settings.</p>
      <label className="check-line risk-control"><input type="checkbox" checked={draft.risk} onChange={e => onChange({ risk: e.target.checked })} />Run even if convergence is not guaranteed</label>
      <p className="muted">Leave this off to let the solver decline a risky iteration safely.</p>
      {configurationIssues(draft).map(issue => <p className="error-note" key={issue}>{issue}</p>)}
    </>}
  </section>;
}
