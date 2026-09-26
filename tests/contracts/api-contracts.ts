// Compile-time checks against generated contracts, without handwritten API interfaces.
import type { components, operations } from "../../lib/contracts/api.generated";

type SolveRequest = operations["solve_system"]["requestBody"]["content"]["application/json"];
type SolveOutcome = operations["solve_system"]["responses"][200]["content"]["application/json"];
type AnalyzeRequest = operations["analyze_system"]["requestBody"]["content"]["application/json"];

const system = { a: [["4", "1"], ["2", "3"]], b: ["1", "2"] };

export const defaultAnalysis = { system } satisfies AnalyzeRequest;
export const defaultDirect = { system, method: "gaussian" } satisfies SolveRequest;
export const exactDirect = {
  system, method: "gauss_jordan", options: { arithmetic_mode: "exact" },
} satisfies SolveRequest;
export const iterative = {
  system, method: "jacobi", options: { initial_guess: ["0", "1/3"], max_iterations: 100 },
} satisfies SolveRequest;

// @ts-expect-error Coefficients must remain string tokens at the JSON boundary.
export const invalidToken: components["schemas"]["NumericToken"] = 1;
// @ts-expect-error Iterative requests cannot request exact arithmetic.
export const invalidOptions: components["schemas"]["IterativeOptions"] = { arithmetic_mode: "exact" };
// @ts-expect-error Large exact integers are decimal strings on the wire.
export const invalidRational: components["schemas"]["RationalValue"] = { numerator: 1, denominator: 3 };

export function describeOutcome(outcome: SolveOutcome): string {
  if (outcome.status === "numeric_breakdown") {
    return outcome.error.code;
  }
  const result = outcome.result;
  if (result.method === "jacobi" || result.method === "gauss_seidel") {
    return `${result.status}: ${result.history.length} iterations`;
  }
  return result.classification.classification;
}
