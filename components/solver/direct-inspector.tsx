import { useState } from "react";
import type { Display, Model } from "../../lib/api/types";
import { formatValue, isZero, rawValue } from "../../lib/solver/format";
import { NumericMatrix } from "./numeric-matrix";

export function DirectInspector({ result, original, display }: { result: Model<"DirectResult">; original: Model<"ProblemMetadata">["original_system"]; display: Display }) {
  const [step, setStep] = useState(0);
  const operation = result.trace[step - 1];
  const matrix = operation?.matrix_after ?? original.a.map((row, i) => [...row, original.b[i]!]);
  const titles = { row_swap: "Swap equations", row_scale: "Scale a pivot row", row_add_scaled: "Eliminate a coefficient" };
  return <>
    {result.parametric_solution && <section aria-labelledby="family-title"><h3 id="family-title">Parametric solution</h3><p>Free variables: {result.free_columns.map(i => `x${i + 1}`).join(", ")}. Each parameter may take any real value.</p><ul className="formula-list">{result.parametric_solution.expressions.map(expression => <li key={expression.variable}><code>{expression.variable} = {formatValue(expression.constant, display)}{expression.terms.map(term => ` + (${formatValue(term.coefficient, display)}) ${term.parameter}`).join("")}</code></li>)}</ul></section>}
    {!!result.contradictory_rows.length && <section className="error-note"><h3>Contradiction witnesses</h3>{result.contradictory_rows.map(row => <p key={row}>Reduced row {row + 1}: coefficient entries are {result.arithmetic_mode === "exact" ? "exactly zero" : "zero under the row tolerance"}, but the RHS is <strong title={rawValue(result.matrix[row]!.at(-1)!)}>{formatValue(result.matrix[row]!.at(-1)!, display)}</strong>. No vector satisfies all equations.</p>)}</section>}
    {result.diagnostics && result.parametric_solution && <p className="muted">Residual diagnostics use the particular solution with all parameters set to zero.</p>}
    <section aria-labelledby="replay-title"><h3 id="replay-title">Row-operation replay</h3><p className="muted">Start with [A | b]. Each snapshot is the backend’s full-precision state after one operation. Pivot columns are marked; source and target rows are labeled.</p>
      <div className="step-controls"><button onClick={() => setStep(0)} disabled={!step}>Start</button><button onClick={() => setStep(s => s - 1)} disabled={!step}>Previous step</button><output aria-live="polite">Step {step} of {result.trace.length}</output><button onClick={() => setStep(s => s + 1)} disabled={step === result.trace.length}>Next step</button><button onClick={() => setStep(result.trace.length)} disabled={step === result.trace.length}>End</button></div>
      <label className="step-slider">Replay position<input type="range" min={0} max={result.trace.length} value={step} onChange={e => setStep(Number(e.target.value))} /></label>
      <div className="operation-summary" aria-live="polite"><strong>{operation ? titles[operation.operation_type] : "Original augmented matrix"}</strong>{operation && <><p>{operation.explanation}</p><p>Pivot column: {operation.pivot_column === original.a[0]!.length ? "RHS (contradiction pivot)" : `x${operation.pivot_column + 1}`} · target row {operation.target_row + 1}{operation.source_row === null ? "" : ` · source row ${operation.source_row + 1}`}{operation.factor == null ? "" : ` · factor ${formatValue(operation.factor, display)}`}</p></>}</div>
      <NumericMatrix matrix={matrix} display={display} active={operation} caption={step ? `After operation ${step}` : "Original system"} />
      <p className="muted">Final {result.form.toUpperCase()} coefficient pivots: {result.pivot_columns.map(i => `x${i + 1}`).join(", ") || "none"}. Free columns: {result.free_columns.map(i => `x${i + 1}`).join(", ") || "none"}.</p>
      {result.method === "gaussian" && result.solution && <details><summary>Read the answer by back substitution</summary><p>Work upward from the last pivot. For each row, subtract the contributions of already known variables and divide by the pivot coefficient.</p><ol>{[...result.pivot_columns].reverse().map((column, k) => {
        const row = result.matrix[result.pivot_columns.length - 1 - k]!;
        const contributions = row.slice(0, -1).flatMap((v, j) => j !== column && !isZero(v) ? [`(${formatValue(v, display)})(${formatValue(result.solution![j]!, display)})`] : []);
        return <li key={column}><code>x{column + 1} = ({formatValue(row.at(-1)!, display)}{contributions.map(v => ` − ${v}`).join("")}) / ({formatValue(row[column]!, display)}) = {formatValue(result.solution![column]!, display)}</code></li>;
      })}</ol></details>}
    </section>
  </>;
}
