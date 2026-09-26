import type { Method, SystemInput } from "../api/types";

export const METHODS: Record<Method, { name: string; category: string; description: string; benefit: string; limitation: string }> = {
  gaussian: { name: "Gaussian elimination", category: "Direct", description: "Eliminate below each pivot, then back-substitute to recover the variables.", benefit: "Works with rectangular systems and exact fractions.", limitation: "A numerical pivot may be uncertain near the rank cutoff." },
  gauss_jordan: { name: "Gauss–Jordan", category: "Direct", description: "Reduce above and below pivots to reveal the full solution structure.", benefit: "Makes free variables and contradictions visible.", limitation: "More row operations than Gaussian elimination." },
  jacobi: { name: "Jacobi", category: "Iterative", description: "Compute every new component from the previous vector only.", benefit: "Easy to follow and update components independently.", limitation: "Requires a square, unique system and safe diagonal; convergence depends on the iteration matrix." },
  gauss_seidel: { name: "Gauss–Seidel", category: "Iterative", description: "Use each newly updated component immediately within the same sweep.", benefit: "SPD matrices give a sufficient convergence condition.", limitation: "Requires a square, unique system and safe diagonal; it is not always faster than Jacobi." },
};
export const PRESETS: { id: string; name: string; note: string; system: SystemInput; method: Method; reorder?: boolean }[] = [
  { id: "planes", name: "3D · three planes meet", note: "Three independent planes meet at (1, 2, 3).", system: { a: [["4", "1", "0"], ["1", "4", "1"], ["0", "1", "4"]], b: ["6", "12", "14"] }, method: "gauss_jordan" },
  { id: "line3d", name: "3D · a line of solutions", note: "Two independent constraints leave a line of common intersections.", system: { a: [["1", "1", "0"], ["0", "1", "1"], ["1", "2", "1"]], b: ["2", "3", "5"] }, method: "gauss_jordan" },
  { id: "coincident", name: "2D · coincident lines", note: "Both equations describe the same line; every point on it is a solution.", system: { a: [["1", "1"], ["2", "2"]], b: ["2", "4"] }, method: "gauss_jordan" },
  { id: "unique", name: "Unique · a gentle start", note: "Two independent equations; the solution is x₁ = 0.1, x₂ = 0.6.", system: { a: [["4", "1"], ["2", "3"]], b: ["1", "2"] }, method: "gaussian" },
  { id: "infinite", name: "Infinite · a free variable", note: "Two equations, three unknowns. Explore a family of solutions.", system: { a: [["1", "1", "1"], ["0", "1", "2"]], b: ["3", "4"] }, method: "gauss_jordan" },
  { id: "inconsistent", name: "Inconsistent · a contradiction", note: "The same left side cannot equal both 2 and 3.", system: { a: [["1", "1"], ["1", "1"]], b: ["2", "3"] }, method: "gauss_jordan" },
  { id: "ill", name: "Ill-conditioned · close equations", note: "Nearly dependent rows amplify input changes. Compare float and exact modes.", system: { a: [["1", "1"], ["1", "1.0000000001"]], b: ["2", "2.0000000001"] }, method: "gaussian" },
  { id: "permutation", name: "Reordering · recover the diagonal", note: "Swap the equations to obtain a safe, strictly dominant diagonal.", system: { a: [["0", "4"], ["3", "1"]], b: ["8", "5"] }, method: "jacobi" },
  { id: "divergent", name: "Non-convergent · inspect the risk", note: "With reordering off and a zero start, this iteration diverges. An explicit risk override is required to run it.", system: { a: [["1", "2"], ["2", "1"]], b: ["1", "1"] }, method: "jacobi", reorder: false },
];
