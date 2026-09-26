import type { Numeric } from "../api/types";
import type { CompletedSolve } from "../reports/render";

export type Point = number[];
export type Shape = { name: string; kind: "line" | "plane" | "point" | "trajectory"; points: Point[]; color: string };
export type Geometry = { dimension: 2 | 3; bound: number; shapes: Shape[]; notes: string[]; classification: string };
export const GEOMETRY_LIMIT = 1e6;
const colors = ["#00d5ee", "#f4bf62", "#ba9cff"];

/** Rendering conversion only. Backend classification is never recomputed here. */
export function approximate(value: Numeric): number {
  if (typeof value === "number") return value;
  // Scale integer strings independently to avoid Infinity / Infinity for large fractions.
  const sign = value.numerator.startsWith("-") ? -1 : 1;
  const n = value.numerator.replace(/^-/, ""), d = value.denominator;
  return sign * (Number(n.slice(0, 16)) / Number(d.slice(0, 16))) * 10 ** (Math.max(0, n.length - 16) - Math.max(0, d.length - 16));
}
const dot = (a: Point, b: Point) => a.reduce((s, v, i) => s + v * b[i]!, 0);
const subtract = (a: Point, b: Point) => a.map((v, i) => v - b[i]!);
const cross = (a: Point, b: Point) => [a[1]! * b[2]! - a[2]! * b[1]!, a[2]! * b[0]! - a[0]! * b[2]!, a[0]! * b[1]! - a[1]! * b[0]!];

/** Intersect a line/plane with a bounded square/cube. No slopes or division by tiny chosen axes. */
export function equationSection(coefficients: Point, rhs: number, bound: number): Point[] {
  const scale = Math.max(...coefficients.map(Math.abs));
  if (!scale || !Number.isFinite(scale)) return [];
  const a = coefficients.map(v => v / scale), b = rhs / scale, n = a.length;
  if (!Number.isFinite(b)) return [];
  const vertices = Array.from({ length: 2 ** n }, (_, mask) => a.map((_, axis) => mask & (1 << axis) ? bound : -bound));
  const points: Point[] = [];
  const add = (p: Point) => { if (p.every(Number.isFinite) && !points.some(q => Math.max(...subtract(p, q).map(Math.abs)) < bound * 1e-10)) points.push(p); };
  vertices.forEach((v, mask) => a.forEach((_, axis) => {
    if (mask & (1 << axis)) return;
    const w = vertices[mask | (1 << axis)]!, f = dot(a, v) - b, g = dot(a, w) - b;
    if (f === 0) add(v);
    if (g === 0) add(w);
    if ((f < 0 && g > 0) || (f > 0 && g < 0)) { const t = f / (f - g); add(v.map((value, j) => value + t * (w[j]! - value))); }
  }));
  if (n === 3 && points.length > 2) {
    const center = a.map((_, i) => points.reduce((sum, p) => sum + p[i]!, 0) / points.length);
    const u = subtract(points[0]!, center), v = cross(a, u);
    points.sort((p, q) => Math.atan2(dot(subtract(p, center), v), dot(subtract(p, center), u)) - Math.atan2(dot(subtract(q, center), v), dot(subtract(q, center), u)));
  }
  return points;
}

export function parametricLine(origin: Point, direction: Point, bound: number): Point[] {
  let low = -Infinity, high = Infinity;
  for (let i = 0; i < origin.length; i++) {
    const d = direction[i]!, p = origin[i]!;
    if (d === 0) { if (Math.abs(p) > bound) return []; continue; }
    const ends = [(-bound - p) / d, (bound - p) / d].sort((a, b) => a - b);
    low = Math.max(low, ends[0]!); high = Math.min(high, ends[1]!);
  }
  if (!Number.isFinite(low) || !Number.isFinite(high) || low > high) return [];
  return [low, high].map(t => origin.map((v, i) => v + t * direction[i]!));
}

export function deriveGeometry(outcome: CompletedSolve): Geometry | null {
  const { a: source, b: rhs } = outcome.problem.original_system;
  const n = source[0]!.length;
  if (source.length !== n || (n !== 2 && n !== 3)) return null;
  const a = source.map(row => row.map(approximate)), b = rhs.map(approximate), result = outcome.result;
  const solution = result.solution?.map(approximate);
  const intercepts = a.flatMap((row, i) => row.flatMap(v => v ? [Math.abs(b[i]! / v)] : []));
  const finite = [...(solution ?? []), ...intercepts].map(Math.abs).filter(v => Number.isFinite(v) && v <= GEOMETRY_LIMIT);
  const bound = Math.min(GEOMETRY_LIMIT, Math.max(5, ...finite.map(v => v * 1.4)));
  const geometry: Geometry = { dimension: n, bound, shapes: [], notes: ["Geometry is an approximate, bounded illustration. The backend rank classification is authoritative; nearly coincident objects may overlap visually."], classification: result.classification.classification };
  a.forEach((row, i) => {
    if (row.every(v => v === 0)) { geometry.notes.push(`Equation ${i + 1}: ${b[i] === 0 ? "0 = 0 imposes no geometric restriction" : "0 equals a nonzero RHS: no points satisfy this equation"}.`); return; }
    const points = equationSection(row, b[i]!, bound);
    if (!points.length) geometry.notes.push(`Equation ${i + 1} lies outside the displayed window or cannot be represented at this plotting precision.`);
    else geometry.shapes.push({ name: `Equation ${i + 1}`, kind: n === 2 ? "line" : "plane", points, color: colors[i]! });
  });
  if (solution) {
    if (solution.every(v => Number.isFinite(v) && Math.abs(v) <= bound)) geometry.shapes.push({ name: "history" in result ? "Converged approximation" : "Solution", kind: "point", points: [solution], color: "#e8f7f9" });
    else geometry.notes.push("The returned solution is outside the bounded plot window.");
  }
  if ("history" in result) {
    const trajectory = [result.initial_guess, ...result.history.map(row => row.vector)];
    geometry.shapes.push({ name: "Iteration trajectory (initial guess first)", kind: "trajectory", points: trajectory, color: "#ee79b9" });
    if (trajectory.some(p => p.some(v => Math.abs(v) > bound))) geometry.notes.push("Trajectory segments outside the displayed window are clipped; the complete history remains in the table and exports.");
  } else if (result.parametric_solution) {
    const family = result.parametric_solution;
    const parameters = [...new Set(family.expressions.flatMap(e => e.terms.map(t => t.parameter)))];
    const origin = family.expressions.map(e => approximate(e.constant));
    if (parameters.length === 1) {
      const direction = family.expressions.map(e => e.terms.filter(t => t.parameter === parameters[0]).reduce((s, t) => s + approximate(t.coefficient), 0));
      const points = parametricLine(origin, direction, bound);
      if (points.length) geometry.shapes.push({ name: "Solution family", kind: "line", points, color: "#e8f7f9" });
      else geometry.notes.push("The solution family is outside this bounded window.");
    }
    geometry.notes.push(`The solution family has ${family.free_variables.length} free parameter(s). ${family.free_variables.length === n ? "Every point satisfies the system." : n === 3 && family.free_variables.length === 2 ? "The shared solution set is a plane, not a single line." : "Coincident constraints are distinguished using the equation legend."}`);
  }
  if (geometry.classification === "inconsistent") geometry.notes.push("There is no common intersection. In 3D, inconsistent planes need not be pairwise parallel.");
  return geometry;
}
