import type { components, operations } from "../contracts/api.generated";

export type Model<K extends keyof components["schemas"]> = components["schemas"][K];
export type AnalyzeRequest = operations["analyze_system"]["requestBody"]["content"]["application/json"];
export type AnalyzeOutcome = operations["analyze_system"]["responses"][200]["content"]["application/json"];
export type SolveRequest = operations["solve_system"]["requestBody"]["content"]["application/json"];
export type SolveOutcome = operations["solve_system"]["responses"][200]["content"]["application/json"];
export type Method = Model<"Method">;
export type SystemInput = Model<"SystemInput">;
export type Numeric = Model<"NumericValue">;
export type Display = Required<Model<"DisplayPreferences">>;
