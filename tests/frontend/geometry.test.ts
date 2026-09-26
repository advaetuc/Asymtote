import { expect, test } from "vitest";
import { approximate, deriveGeometry, equationSection, GEOMETRY_LIMIT, parametricLine } from "../../lib/geometry/derive";
import type { CompletedSolve } from "../../lib/reports/render";
import fixtures from "./fixtures/api.json";
import geometry from "./fixtures/geometry.json";
const derive = (value: unknown) => deriveGeometry(value as CompletedSolve)!;

test("vertical/horizontal lines, cube-aligned planes and empty sections stay bounded", () => {
  expect(equationSection([1, 0], 2, 5)).toEqual([[2, -5], [2, 5]]);
  expect(equationSection([0, 1], -3, 5)).toEqual([[-5, -3], [5, -3]]);
  expect(equationSection([1, 0, 0], 2, 5)).toHaveLength(4);
  expect(equationSection([1, 0], 20, 5)).toEqual([]);
  expect(equationSection([0, 0], 0, 5)).toEqual([]);
});
test.each([[1,2,3], [0,1,-2], [1e-100,1e100,0], [1,0,0]])("plane vertices satisfy the original equation: %j", (...a) => {
  const coefficients = a as number[];
  const points = equationSection(coefficients, 1, 5);
  expect(points.length).toBeGreaterThanOrEqual(3);
  for (const p of points) {
    expect(p.every(v => Number.isFinite(v) && Math.abs(v) <= 5)).toBe(true);
    const lhs = coefficients.reduce((sum, v, i) => sum + v * p[i]!, 0);
    // Severe scale separation can lose an intercept at plotting precision.
    expect(Math.abs(lhs - 1) / Math.max(1, ...coefficients.map(Math.abs))).toBeLessThan(1e-12);
  }
});
test("rational rendering handles huge matching integer strings without NaN", () => {
  expect(approximate({ numerator: "1" + "0".repeat(400), denominator: "2" + "0".repeat(400) })).toBe(0.5);
  expect(approximate({ numerator: "-1", denominator: "4" })).toBe(-0.25);
});
test("classification comes from the contract, with no invented intersection for inconsistency", () => {
  const g = derive(fixtures.inconsistent);
  expect(g.classification).toBe("inconsistent"); expect(g.shapes.filter(s => s.kind === "point")).toHaveLength(0);
  expect(g.shapes.filter(s => s.kind === "line")).toHaveLength(2);
  expect(g.notes.join(" ")).toContain("no common intersection");
});
test("3D unique, line, plane, full-space and empty systems are distinguished", () => {
  expect(derive(geometry.unique3d).shapes.find(s => s.kind === "point")?.points[0]).toEqual([1,2,3]);
  const line = derive(geometry.line3d).shapes.find(s => s.name === "Solution family")!;
  expect(line.points).toHaveLength(2);
  line.points.forEach(p => { expect(p[0]! + p[1]!).toBeCloseTo(2); expect(p[1]! + p[2]!).toBeCloseTo(3); });
  expect(derive(geometry.plane3d).notes.join(" ")).toContain("a plane, not a single line");
  expect(derive(geometry.space3d).notes.join(" ")).toContain("Every point");
  expect(derive(geometry.empty3d).notes.join(" ")).toContain("no points satisfy");
  expect(derive(geometry.inconsistent3d).classification).toBe("inconsistent");
  expect(derive(geometry.coincident2d).shapes.filter(s => s.name === "Solution family")).toHaveLength(1);
});
test("trajectory preserves initial guess and every completed iteration without mutation", () => {
  const original = JSON.stringify(fixtures.jacobi);
  const path = derive(fixtures.jacobi).shapes.find(s => s.kind === "trajectory")!;
  expect(path.points[0]).toEqual(fixtures.jacobi.result.initial_guess);
  expect(path.points.slice(1)).toEqual(fixtures.jacobi.result.history.map(r => r.vector));
  expect(JSON.stringify(fixtures.jacobi)).toBe(original);
});
test("unsupported dimensions are explicit and oversized views stay bounded", () => {
  expect(deriveGeometry(fixtures.infinite as CompletedSolve)).toBeNull();
  const huge = structuredClone(fixtures.gaussian) as CompletedSolve;
  huge.problem.original_system.b = [1e12, 1e12];
  expect(derive(huge).bound).toBeLessThanOrEqual(GEOMETRY_LIMIT);
  expect(parametricLine([20,0], [0,1], 5)).toEqual([]);
});
