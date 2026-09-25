"""Independent mathematical oracles and cross-method invariants."""

from fractions import Fraction

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from solver_core.gauss_jordan import solve_gauss_jordan
from solver_core.gauss_seidel import solve_gauss_seidel
from solver_core.gaussian import solve_gaussian
from solver_core.jacobi import solve_jacobi
from solver_core.models import ArithmeticMode, IterationOptions, IterationStatus, RowPermutation
from solver_core.parsing import parse_system
from solver_core.permutations import apply_row_permutation


@st.composite
def dominant_systems(draw):
    n = draw(st.integers(1, 5))
    entries = draw(st.lists(st.integers(-4, 4), min_size=n * n, max_size=n * n))
    matrix = [entries[i * n : (i + 1) * n] for i in range(n)]
    for i in range(n):
        matrix[i][i] = 2 * sum(abs(v) for j, v in enumerate(matrix[i]) if j != i) + 1
    rhs = draw(st.lists(st.integers(-10, 10), min_size=n, max_size=n))
    return matrix, rhs


def parsed(matrix, rhs, mode=ArithmeticMode.FLOAT64):
    return parse_system([[str(v) for v in row] for row in matrix], [str(v) for v in rhs], mode=mode)


@given(dominant_systems())
@settings(max_examples=40, deadline=None)
def test_all_four_methods_agree_with_independent_numpy_oracle(data):
    matrix, rhs = data
    system = parsed(matrix, rhs)
    before = system.a, system.b
    expected = np.linalg.solve(matrix, rhs)
    for solve in (solve_gaussian, solve_gauss_jordan):
        assert solve(system).solution == pytest.approx(expected, abs=1e-11)
    for solve in (solve_jacobi, solve_gauss_seidel):
        result = solve(system, options=IterationOptions(tolerance=1e-12, max_iterations=200))
        assert result.status is IterationStatus.CONVERGED
        assert result.solution == pytest.approx(expected, abs=1e-10)
        assert all(type(x) is float for step in result.history for x in step.vector)
    assert (system.a, system.b) == before


@given(dominant_systems(), st.integers(-5, 5).filter(lambda v: v != 0))
@settings(max_examples=35, deadline=None)
def test_equation_permutation_and_scaling_preserve_solution(data, scale):
    matrix, rhs = data
    n = len(rhs)
    system = parsed(matrix, rhs)
    expected = np.linalg.solve(matrix, rhs)
    mapping = RowPermutation(order=tuple(reversed(range(n))), purpose="nonzero_diagonal")
    reordered = apply_row_permutation(system, mapping)
    scaled_matrix = [list(row) for row in matrix]
    scaled_rhs = list(rhs)
    scaled_matrix[0] = [value * scale for value in scaled_matrix[0]]
    scaled_rhs[0] *= scale
    for variant in (reordered, parsed(scaled_matrix, scaled_rhs)):
        for solve in (solve_gaussian, solve_gauss_jordan):
            assert solve(variant).solution == pytest.approx(expected, abs=1e-10)
        for solve in (solve_jacobi, solve_gauss_seidel):
            result = solve(variant, options=IterationOptions(tolerance=1e-12, max_iterations=200))
            assert result.status is IterationStatus.CONVERGED
            assert result.solution == pytest.approx(expected, abs=1e-10)


@given(dominant_systems(), st.integers(1, 9))
@settings(max_examples=35, deadline=None)
def test_exact_solutions_satisfy_rational_equations_and_rref(data, denominator):
    matrix, rhs = data
    matrix = [[Fraction(value, denominator) for value in row] for row in matrix]
    rhs = [Fraction(value, denominator + 1) for value in rhs]
    system = parsed(matrix, rhs, ArithmeticMode.EXACT)
    for solve in (solve_gaussian, solve_gauss_jordan):
        result = solve(system)
        assert all(type(x) is Fraction for x in result.solution)
        for row, b in zip(system.a, system.b, strict=True):
            assert sum(a * x for a, x in zip(row, result.solution, strict=True)) == b
        assert result.diagnostics.residual_inf == result.diagnostics.backward_error == 0
        if result.method == "gauss_jordan":
            assert result.pivot_columns == tuple(range(len(rhs)))
            for i, row in enumerate(result.matrix):
                assert row[:-1] == tuple(Fraction(int(i == j)) for j in range(len(rhs)))


@given(st.integers(1, 5), st.integers(-5, 5))
@settings(max_examples=25)
def test_rectangular_rref_parameterization_solves_every_original_equation(n, parameter):
    # n independent rows, n+1 columns, plus a duplicate equation.
    a = [[int(i == j) for j in range(n)] + [i + 1] for i in range(n)]
    b = [2 * i + 1 for i in range(n)]
    system = parsed(a + [a[0]], b + [b[0]], ArithmeticMode.EXACT)
    result = solve_gauss_jordan(system)
    assert result.free_columns == (n,)
    vector = tuple(
        expression.constant + sum(term.coefficient * parameter for term in expression.terms)
        for expression in result.parametric_solution.expressions
    )
    assert all(
        sum(value * x for value, x in zip(row, vector, strict=True)) == rhs
        for row, rhs in zip(system.a, system.b, strict=True)
    )
    for i, pivot in enumerate(result.pivot_columns):
        assert all(result.matrix[j][pivot] == int(i == j) for j in range(n + 1))


@pytest.mark.parametrize("solve", [solve_jacobi, solve_gauss_seidel])
def test_maximum_dimension_converges_and_does_not_use_black_box_solver(solve, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Solver must not call a library solve, determinant, or inverse.")

    for name in ("solve", "inv", "det"):
        monkeypatch.setattr(np.linalg, name, forbidden)
    n = 12
    system = parsed([[20 if i == j else 1 for j in range(n)] for i in range(n)], [31] * n)
    result = solve(system, options=IterationOptions(max_iterations=100))
    assert result.status is IterationStatus.CONVERGED
    assert result.solution == pytest.approx((1.0,) * n, abs=1e-7)


@pytest.mark.parametrize("solve", [solve_jacobi, solve_gauss_seidel])
@pytest.mark.parametrize("scale", [1e-100, 1e-20, 1e10])
def test_uniform_scale_preserves_iteration_stopping(solve, scale):
    baseline = solve(parsed([[4, 1], [2, 3]], [1, 2]))
    scaled = solve(parsed([[4 * scale, scale], [2 * scale, 3 * scale]], [scale, 2 * scale]))
    assert scaled.status == baseline.status
    assert len(scaled.history) == len(baseline.history)
    assert scaled.solution == pytest.approx(baseline.solution, abs=1e-14)
