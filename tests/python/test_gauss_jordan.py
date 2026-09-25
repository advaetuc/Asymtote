"""RREF structure, parameter substitution, contradictions, and exact trace fidelity."""

import json
from fractions import Fraction

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from solver_core.gauss_jordan import solve_gauss_jordan
from solver_core.models import ArithmeticMode, ClassificationKind, FloatSystem
from solver_core.parsing import parse_system


@pytest.mark.parametrize("mode", list(ArithmeticMode))
def test_unique_rectangular_rref_and_zero_row(mode) -> None:
    system = parse_system([["0", "2"], ["3", "1"], ["3", "3"]], ["4", "5", "9"], mode=mode)
    result = solve_gauss_jordan(system)
    assert result.form == "rref"
    assert result.solution == (1, 2)
    np.testing.assert_allclose(
        np.array(result.matrix, dtype=float), [[1, 0, 1], [0, 1, 2], [0, 0, 0]], atol=1e-14
    )
    assert result.pivot_columns == (0, 1)
    assert result.diagnostics.residual_inf == 0


@pytest.mark.parametrize("mode", list(ArithmeticMode))
def test_multiple_free_variables_and_leading_free_column(mode) -> None:
    system = parse_system([["0", "2", "1", "0"], ["0", "0", "0", "3"]], ["4", "6"], mode=mode)
    result = solve_gauss_jordan(system)
    assert result.classification.classification is ClassificationKind.INFINITE
    assert result.solution is None
    assert result.pivot_columns == (1, 3)
    assert result.free_columns == (0, 2)
    parametric = result.parametric_solution
    assert parametric is not None
    assert parametric.free_variables == (0, 2)
    assert [expression.variable for expression in parametric.expressions] == [
        "x1",
        "x2",
        "x3",
        "x4",
    ]
    for t1, t2 in ((0, 0), (3, -7), (Fraction(2, 3), Fraction(5, 7))):
        parameters = {"t1": t1, "t2": t2}
        x = [
            expression.constant
            + sum(term.coefficient * parameters[term.parameter] for term in expression.terms)
            for expression in parametric.expressions
        ]
        residuals = [
            sum(a * value for a, value in zip(row, x, strict=True)) - b
            for row, b in zip(system.a, system.b, strict=True)
        ]
        if mode is ArithmeticMode.EXACT:
            assert residuals == [0, 0]
        else:
            np.testing.assert_allclose(np.array(residuals, dtype=float), [0, 0], atol=1e-14)


@pytest.mark.parametrize("mode", list(ArithmeticMode))
@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ([["1", "1"], ["2", "2"]], ["1", "3"], [[1, 1, 0], [0, 0, 1]]),
        ([["0", "0"], ["0", "0"]], ["1", "2"], [[0, 0, 1], [0, 0, 0]]),
        ([["1"], ["1"]], ["1", "2"], [[1, 0], [0, 1]]),
    ],
)
def test_inconsistency_reduces_the_augmented_rhs_pivot(a, b, expected, mode) -> None:
    result = solve_gauss_jordan(parse_system(a, b, mode=mode))
    assert result.classification.classification is ClassificationKind.INCONSISTENT
    assert result.solution is result.parametric_solution is result.diagnostics is None
    np.testing.assert_allclose(np.array(result.matrix, dtype=float), expected, atol=1e-14)
    for row_index in result.contradictory_rows:
        row = result.matrix[row_index]
        threshold = 0 if mode is ArithmeticMode.EXACT else result.row_tolerances[row_index]
        assert all(abs(value) <= threshold for value in row[:-1])
        assert abs(row[-1]) > threshold


@pytest.mark.parametrize("mode", list(ArithmeticMode))
def test_all_zero_system_and_zero_denominator_backward_error(mode) -> None:
    result = solve_gauss_jordan(parse_system([["0", "0"]], ["0"], mode=mode))
    assert result.free_columns == (0, 1)
    assert result.trace == ()
    assert result.parametric_solution is not None
    assert result.diagnostics.residual_inf == result.diagnostics.backward_error == 0


def test_exact_fraction_trace_replay_and_json_serialization() -> None:
    system = parse_system(
        [["0", "1/3"], ["2/7", "1/11"]], ["1/5", "2/13"], mode=ArithmeticMode.EXACT
    )
    before = system.model_dump()
    result = solve_gauss_jordan(system)
    matrix = [list(row) + [b] for row, b in zip(system.a, system.b, strict=True)]
    for step in result.trace:
        i, j = step.target_row, step.source_row
        if step.operation_type == "row_swap":
            matrix[i], matrix[j] = matrix[j], matrix[i]
        elif step.operation_type == "row_scale":
            matrix[i] = [value * step.factor for value in matrix[i]]
        else:
            matrix[i] = [a + step.factor * b for a, b in zip(matrix[i], matrix[j], strict=True)]
        assert tuple(tuple(row) for row in matrix) == step.matrix_after
    assert tuple(tuple(row) for row in matrix) == result.matrix
    assert system.model_dump() == before
    payload = json.loads(result.model_dump_json())
    assert all(set(value) == {"numerator", "denominator"} for value in payload["solution"])
    assert isinstance(payload["solution"][0]["numerator"], str)
    json.dumps(payload, allow_nan=False)


def test_float_skipped_entries_are_not_silently_zeroed() -> None:
    result = solve_gauss_jordan(parse_system([["1e-100", "1"]], ["1"]))
    assert result.pivot_columns == (1,)
    assert result.matrix[0][0] == 1e-100
    assert result.parametric_solution is not None


@pytest.mark.parametrize("scale", [1e-80, 1.0, 1e10])
def test_row_tolerances_follow_normalization(scale: float) -> None:
    system = FloatSystem(a=((scale, scale), (2 * scale, 2 * scale)), b=(scale, 3 * scale))
    result = solve_gauss_jordan(system)
    assert result.contradictory_rows == (1,)
    assert result.row_tolerances[1] < 1e-12


def test_jordan_does_not_call_a_library_solver(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args, **kwargs):
        pytest.fail("Gauss-Jordan used a library solve/inverse")

    for name in ("solve", "inv", "det", "lstsq", "pinv"):
        monkeypatch.setattr(np.linalg, name, forbidden)
    result = solve_gauss_jordan(parse_system([["2", "1"], ["1", "-1"]], ["5", "1"]))
    np.testing.assert_allclose(result.solution, [2, 1], atol=1e-14)


@given(st.lists(st.integers(-5, 5), min_size=6, max_size=6), st.integers(-7, 7), st.integers(-7, 7))
def test_generated_exact_rectangular_rref_structure_and_parametric_solution(values, p, q) -> None:
    # Guaranteed rank two with one free variable, independent of chosen integers.
    a = [
        [1, 0, values[0]],
        [0, 1, values[1]],
        [values[2], values[3], values[2] * values[0] + values[3] * values[1]],
    ]
    b = [p, q, values[2] * p + values[3] * q]
    system = parse_system(
        [[str(value) for value in row] for row in a], list(map(str, b)), mode=ArithmeticMode.EXACT
    )
    result = solve_gauss_jordan(system)
    assert result.pivot_columns == (0, 1)
    assert result.free_columns == (2,)
    assert result.matrix == ((1, 0, values[0], p), (0, 1, values[1], q), (0, 0, 0, 0))
    parametric = result.parametric_solution
    for parameter in (-3, 0, 4):
        x = [
            expr.constant + sum(term.coefficient * parameter for term in expr.terms)
            for expr in parametric.expressions
        ]
        assert [sum(aij * xj for aij, xj in zip(row, x, strict=True)) for row in system.a] == list(
            system.b
        )


@pytest.mark.parametrize("mode", list(ArithmeticMode))
def test_full_twelve_by_twelve_system(mode) -> None:
    a = [[25 if i == j else (i + j) % 3 - 1 for j in range(12)] for i in range(12)]
    expected = list(range(-6, 6))
    b = [sum(aij * xj for aij, xj in zip(row, expected, strict=True)) for row in a]
    system = parse_system(
        [[str(value) for value in row] for row in a], list(map(str, b)), mode=mode
    )
    result = solve_gauss_jordan(system)
    np.testing.assert_allclose(np.array(result.solution, dtype=float), expected, atol=1e-12)
    np.testing.assert_allclose(np.array(result.matrix, dtype=float)[:, :12], np.eye(12), atol=1e-12)
    if mode is ArithmeticMode.EXACT:
        assert result.solution == tuple(expected)
    else:
        np.testing.assert_allclose(result.solution, np.linalg.solve(a, b), atol=1e-12)
