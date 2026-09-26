import type { Display, Model } from "../../lib/api/types";
import { formatValue, rawValue } from "../../lib/solver/format";

export function NumericMatrix({ matrix, display, active, caption }: { matrix: Model<"NumericMatrix">; display: Display; active?: Model<"RowOperation">; caption: string }) {
  const n = (matrix[0]?.length ?? 1) - 1;
  return <div className="table-scroll" tabIndex={0} aria-label={caption}><table className="numeric-table"><caption>{caption}</caption><thead><tr><th scope="col">Row</th>{Array.from({ length: n }, (_, j) => <th scope="col" key={j}>x<sub>{j + 1}</sub></th>)}<th scope="col" className="rhs-cell">RHS</th></tr></thead>
    <tbody>{matrix.map((row, i) => <tr key={i} className={active?.target_row === i ? "target-row" : active?.source_row === i ? "source-row" : undefined}><th scope="row">{i + 1}{active?.target_row === i ? " · target" : active?.source_row === i ? " · source" : ""}</th>{row.map((value, j) => <td key={j} title={rawValue(value)} className={`${j === n ? "rhs-cell " : ""}${active?.pivot_column === j ? "pivot-column" : ""}`}>{formatValue(value, display)}{active?.pivot_column === j && <span className="sr-only"> pivot column</span>}</td>)}</tr>)}</tbody></table></div>;
}
