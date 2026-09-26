import type { Model, SystemInput } from "../api/types";

export type CellErrors = Record<string, string>;
export const cellKey = (row: number, column: number) => `${row}:${column}`;

export function resizeSystem(system: SystemInput, m: number, n: number): SystemInput {
  return { a: Array.from({ length: m }, (_, i) => Array.from({ length: n }, (_, j) => system.a[i]?.[j] ?? "")),
    b: Array.from({ length: m }, (_, i) => system.b[i] ?? "") };
}

export function tokenIssue(token: string): string | undefined {
  if (!token) return "Enter a number.";
  if (token.length > 48) return "Use at most 48 characters.";
  const rational = /^([+-]?\d+)\/([+-]?\d+)$/.exec(token);
  if (rational) return BigInt(rational[2]!) === BigInt(0) ? "A denominator cannot be zero." : undefined;
  const decimal = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE]([+-]?\d+))?$/.exec(token);
  if (!decimal) return "Use an integer, decimal, scientific number, or fraction such as 2/3.";
  if (decimal[1] && Math.abs(Number(decimal[1])) > 100) return "Use an exponent from −100 to 100.";
  return undefined; // The backend owns exact magnitude/rank policy, avoiding JS rounding decisions.
}

export function validateGrid(system: SystemInput): CellErrors {
  const errors: CellErrors = {};
  system.a.forEach((row, i) => [...row, system.b[i]!].forEach((v, j) => {
    const issue = tokenIssue(v);
    if (issue) errors[cellKey(i, j)] = issue;
  }));
  return errors;
}

export function serverCellErrors(issues: Model<"Issue">[], n: number): CellErrors {
  const errors: CellErrors = {};
  for (const issue of issues) {
    const path = issue.location;
    const start = path.indexOf("system");
    const field = path[start + 1];
    const row = path[start + 2];
    const column = field === "b" ? n : path[start + 3];
    if (start >= 0 && (field === "a" || field === "b") && typeof row === "number" && typeof column === "number")
      errors[cellKey(row, column)] = issue.message;
  }
  return errors;
}

export function pasteBlock(system: SystemInput, text: string, row: number, column: number): SystemInput {
  const block = text.trim().split(/\r?\n/).map(line => line.trim().split(/\t| +/));
  const width = block[0]?.length ?? 0;
  if (!width || block.some(line => line.length !== width)) throw new Error("Paste a rectangular block of cells.");
  const n = system.a[0]!.length;
  if (row + block.length > system.a.length || column + width > n + 1) throw new Error("The pasted block does not fit. Increase dimensions or choose an earlier cell.");
  const a = system.a.map(r => [...r]); const b = [...system.b];
  block.forEach((line, i) => line.forEach((value, j) => {
    if (column + j === n) b[row + i] = value;
    else a[row + i]![column + j] = value;
  }));
  return { a, b };
}
