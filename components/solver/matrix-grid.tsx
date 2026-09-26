import { useRef, useState } from "react";
import type { SystemInput } from "../../lib/api/types";
import { cellKey, pasteBlock, type CellErrors } from "../../lib/solver/grid";

export function MatrixGrid({ system, onChange, errors }: { system: SystemInput; onChange: (system: SystemInput) => void; errors: CellErrors }) {
  const cells = useRef<Record<string, HTMLInputElement | null>>({});
  const [pasteError, setPasteError] = useState("");
  const n = system.a[0]!.length;
  function change(row: number, column: number, value: string) {
    const a = system.a.map(r => [...r]), b = [...system.b];
    if (column === n) b[row] = value; else a[row]![column] = value;
    onChange({ a, b });
  }
  return <div>
    <p id="matrix-help" className="muted">Enter numbers or fractions such as 2/3. Arrow keys move between cells; Tab follows row order. Paste a rectangular block of tab- or space-separated values, including the final RHS column.</p>
    <div className="table-scroll" tabIndex={0} aria-label="Augmented matrix scroll area">
      <table className="matrix-editor"><caption className="sr-only">Coefficient matrix and right-hand side</caption>
        <thead><tr><th scope="col">Equation</th>{Array.from({ length: n }, (_, j) => <th scope="col" key={j}>x<sub>{j + 1}</sub></th>)}<th scope="col" className="rhs-cell">RHS</th></tr></thead>
        <tbody>{system.a.map((row, i) => <tr key={i}><th scope="row">{i + 1}</th>{[...row, system.b[i]!].map((value, j) => {
          const key = cellKey(i, j), error = errors[key];
          return <td key={j} className={j === n ? "rhs-cell" : undefined}>
            <input ref={node => { cells.current[key] = node; }} value={value} aria-label={`Row ${i + 1}, ${j === n ? "right-hand side" : `x${j + 1}`}`} aria-invalid={!!error}
              aria-describedby={error ? `error-${i}-${j}` : "matrix-help"} autoComplete="off" spellCheck={false}
              onChange={event => { setPasteError(""); change(i, j, event.target.value); }}
              onKeyDown={event => {
                if (event.altKey || event.ctrlKey || event.metaKey) return;
                const move = { ArrowUp: [i - 1, j], ArrowDown: [i + 1, j], ArrowLeft: [i, j - 1], ArrowRight: [i, j + 1] }[event.key];
                if (move) { event.preventDefault(); cells.current[cellKey(move[0]!, move[1]!)]?.focus(); }
              }}
              onPaste={event => {
                const text = event.clipboardData.getData("text");
                if (!/[\t\n ]/.test(text.trim())) return;
                event.preventDefault();
                try { const next = pasteBlock(system, text, i, j); setPasteError(""); onChange(next); }
                catch (error) { setPasteError(error instanceof Error ? error.message : "Unable to paste this block."); }
              }} />
            {error && <span className="cell-error" id={`error-${i}-${j}`}>{error}</span>}
          </td>;
        })}</tr>)}</tbody>
      </table>
    </div>
    {pasteError && <p role="alert" className="error-note">{pasteError}</p>}
  </div>;
}
