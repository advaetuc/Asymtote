import type { AnalyzeOutcome, Method, Model } from "../../lib/api/types";
import { metric } from "../../lib/solver/format";
import { METHODS } from "../../lib/solver/presets";

export function Conditioning({ value }: { value: Model<"ConditionDiagnostic"> }) {
  return <div><p>Condition number (float64): <strong>{value.status === "finite" ? metric(value.condition_number) : value.status}</strong></p>
    {value.status === "finite" && <p className="muted">Potential decimal digit loss: ≈ {value.approximate_digit_loss?.toFixed(2)}. This is a conditioning estimate, not an error bound.</p>}</div>;
}

export function AnalysisPanel({ analysis, method, onSelect }: { analysis: AnalyzeOutcome; method: Method; onSelect: (method: Method) => void }) {
  if (analysis.status === "numeric_breakdown") return <section className="panel warning-note" aria-labelledby="analysis-title"><h2 id="analysis-title">Analysis needs attention</h2><p>{analysis.error.message}</p><p>Try exact mode or rescale the equations.</p><small>Request {analysis.request_id}</small></section>;
  const rank = analysis.classification;
  return <section className="panel" aria-labelledby="analysis-title">
    <p className="eyebrow">02 / Understand the system</p><h2 id="analysis-title">{rank.classification === "unique" ? "One solution" : rank.classification === "infinite" ? "A family of solutions" : "No common solution"}</h2>
    <dl className="facts"><div><dt>Rank A / [A | b]</dt><dd>{rank.rank_a} / {rank.rank_augmented}</dd></div><div><dt>Shape</dt><dd>{analysis.shape.equations} × {analysis.shape.unknowns}{analysis.is_square ? " · square" : " · rectangular"}</dd></div><div><dt>Strict diagonal dominance</dt><dd>{analysis.strict_diagonal_dominance === null ? "Not applicable" : analysis.strict_diagonal_dominance ? "Yes" : "No"}</dd></div><div><dt>Rank arithmetic</dt><dd>{rank.arithmetic_mode === "exact" ? "Exact rational" : `Float64 · cutoff ${metric(rank.rank_tolerance)}`}</dd></div></dl>
    <Conditioning value={analysis.conditioning} />
    {analysis.dominance_permutation && <p className="muted">Dominant row order available: {analysis.dominance_permutation.order.map(i => i + 1).join(" → ")}. This changes equations, not variables.</p>}
    {analysis.warnings.map(warning => <p className="warning-note" key={warning}>{warning}</p>)}
    <fieldset className="method-picker"><legend>Choose a method</legend>
      {analysis.methods.map(item => { const info = METHODS[item.method]; return <label key={item.method} className={`method-choice ${method === item.method ? "selected" : ""}`}>
        <span className="method-choice-title"><input type="radio" name="method" aria-label={info.name} aria-describedby={`method-description-${item.method} method-reason-${item.method}`} value={item.method} checked={method === item.method} disabled={!item.eligible} onChange={() => onSelect(item.method)} /><strong>{info.name}</strong><span className="badge">{info.category}</span></span>
        <span id={`method-description-${item.method}`}>{info.description}</span><span className="muted">{info.benefit} {info.limitation}</span>
        <span id={`method-reason-${item.method}`} className={!item.eligible || item.requires_risk_override ? "warning-text" : "muted"}>{item.reason}</span>
        {item.convergence && <span className="diagnostic-line">SPD: {item.convergence.symmetric_positive_definite === null ? "untested" : item.convergence.symmetric_positive_definite ? "yes" : "no"} · spectral radius: {metric(item.convergence.spectral.radius)}{item.requires_row_reordering ? " (candidate row order)" : " (original order)"}</span>}
      </label>; })}
    </fieldset><small className="muted">Analysis request {analysis.request_id}</small>
  </section>;
}
