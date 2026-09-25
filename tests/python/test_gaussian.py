"""Gaussian elimination, original-system diagnostics, traces, and property oracles."""

import json
from fractions import Fraction

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from solver_core.constants import MAX_RATIONAL_BITS
from solver_core.errors import ErrorCode, NumericBreakdownError, ResourceLimitError
from solver_core.gaussian import solve_gaussian
from solver_core.models import ArithmeticMode, ClassificationKind, ExactSystem, FloatSystem
from solver_core.parsing import parse_system


@pytest.mark.parametrize("mode", list(ArithmeticMode))
@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ([["2", "1"], ["1", "-1"]], ["5", "1"], (2, 1)),
        ([["0", "2"], ["1", "1"]], ["4", "3"], (1, 2)),
        ([["1", "1", "0"], ["1", "1", "1"], ["0", "1", "1"]], ["3", "6", "5"], (1, 2, 3)),
        ([["1e-20", "1"], ["1", "1"]], ["1", "2"], None),
        ([["1", "0"], ["0", "1"], ["2", "3"]], ["2", "3", "13"], (2, 3)),
        ([["0.1", "0"], ["0", "1/3"]], ["0.3", "2/3"], (3, 2)),
        ([["1e-100"]], ["1e12"], (10**112,)),
    ],
)
def test_unique_systems_with_first_and_later_pivot_swaps(a, b, expected, mode) -> None:
    system = parse_system(a, b, mode=mode)
    before = system.model_dump()
    result = solve_gaussian(system)
    assert result.classification.classification is ClassificationKind.UNIQUE
    assert result.solution is not None
    assert result.form == "ref"
    assert result.free_columns == ()
    assert result.parametric_solution is None
    assert result.diagnostics is not None
    if mode is ArithmeticMode.EXACT:
        assert all(isinstance(value, Fraction) for value in result.solution)
        for row, rhs in zip(system.a, system.b, strict=True):
            assert sum(a * x for a, x in zip(row, result.solution, strict=True)) == rhs
        assert result.diagnostics.residual_inf == 0
        assert result.diagnostics.backward_error == 0
    else:
        oracle = np.linalg.solve(
            np.array(system.a[: len(result.solution)]), np.array(system.b[: len(result.solution)])
        )
        np.testing.assert_allclose(result.solution, oracle, rtol=1e-12, atol=1e-12)
        assert result.diagnostics.backward_error < 1e-14
    if expected is not None:
        if mode is ArithmeticMode.EXACT:
            assert result.solution == expected
        else:
            np.testing.assert_allclose(
                np.array(result.solution, dtype=float), np.array(expected, dtype=float), rtol=1e-12
            )
    assert system.model_dump() == before


def test_partial_pivoting_selects_largest_magnitude() -> None:
    result = solve_gaussian(parse_system([["1", "2"], ["-5", "1"]], ["3", "-4"]))
    first = result.trace[0]
    assert first.operation_type == "row_swap"
    assert (first.target_row, first.source_row) == (0, 1)
    later = solve_gaussian(
        parse_system([["1", "1", "0"], ["1", "1", "1"], ["0", "1", "1"]], ["3", "6", "5"])
    )
    assert any(step.operation_type == "row_swap" and step.target_row == 1 for step in later.trace)


@pytest.mark.parametrize("mode", list(ArithmeticMode))
def test_singular_infinite_and_inconsistent_results_are_not_solutions(mode) -> None:
    infinite = solve_gaussian(parse_system([["1", "2"], ["2", "4"]], ["3", "6"], mode=mode))
    assert infinite.classification.classification is ClassificationKind.INFINITE
    assert infinite.solution is None
    assert infinite.parametric_solution is not None
    inconsistent = solve_gaussian(parse_system([["1", "2"], ["2", "4"]], ["3", "7"], mode=mode))
    assert inconsistent.classification.classification is ClassificationKind.INCONSISTENT
    assert (
        inconsistent.solution
        is inconsistent.parametric_solution
        is inconsistent.diagnostics
        is None
    )
    assert inconsistent.contradictory_rows


@pytest.mark.parametrize("mode", list(ArithmeticMode))
def test_trace_replays_without_hidden_row_edits(mode) -> None:
    system = parse_system([["0.1", "2"], ["3", "4"]], ["5", "6"], mode=mode)
    result = solve_gaussian(system)
    matrix = [list(row) + [rhs] for row, rhs in zip(system.a, system.b, strict=True)]
    for index, step in enumerate(result.trace):
        assert step.index == index
        if step.operation_type == "row_swap":
            matrix[step.target_row], matrix[step.source_row] = (
                matrix[step.source_row],
                matrix[step.target_row],
            )
        else:
            assert step.operation_type == "row_add_scaled"
            matrix[step.target_row] = [
                a + step.factor * b
                for a, b in zip(matrix[step.target_row], matrix[step.source_row], strict=True)
            ]
        assert tuple(tuple(row) for row in matrix) == step.matrix_after
    assert tuple(tuple(row) for row in matrix) == result.matrix
    json.dumps(json.loads(result.model_dump_json()), allow_nan=False)


def test_residual_and_backward_error_use_original_system() -> None:
    system = parse_system([["3", "7"], ["11", "2"]], ["1", "5"])
    result = solve_gaussian(system)
    a, b, x = np.array(system.a), np.array(system.b), np.array(result.solution)
    expected_residual = np.linalg.norm(a @ x - b, ord=np.inf)
    denominator = np.linalg.norm(a, ord=np.inf) * np.linalg.norm(x, ord=np.inf) + np.linalg.norm(
        b, ord=np.inf
    )
    assert result.diagnostics.residual_inf == pytest.approx(expected_residual, abs=1e-15)
    assert result.diagnostics.backward_error == pytest.approx(
        expected_residual / denominator, abs=1e-16
    )


def test_no_library_solver_inverse_or_determinant_path(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args, **kwargs):
        pytest.fail("An educational solve delegated to a prohibited library operation")

    for name in ("solve", "inv", "det", "lstsq", "pinv"):
        monkeypatch.setattr(np.linalg, name, forbidden)
    result = solve_gaussian(parse_system([["2", "1"], ["1", "-1"]], ["5", "1"]))
    assert result.solution == (2.0, 1.0)


def test_growth_and_float_overflow_are_controlled() -> None:
    huge = Fraction(2 ** (MAX_RATIONAL_BITS - 1))
    with pytest.raises(ResourceLimitError):
        solve_gaussian(
            ExactSystem(a=((huge, Fraction(1)), (Fraction(1), huge)), b=(Fraction(0), Fraction(0)))
        )
    with pytest.raises(NumericBreakdownError) as caught:
        solve_gaussian(FloatSystem(a=((1e-300,),), b=(1e308,)))
    assert caught.value.code is ErrorCode.NON_FINITE_VALUE


def test_near_cutoff_disagreement_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force an external SVD result that disagrees with stable elimination.
    monkeypatch.setattr(np.linalg, "svd", lambda *args, **kwargs: np.array([1.0, 0.0]))
    with pytest.raises(NumericBreakdownError) as caught:
        solve_gaussian(parse_system([["1", "0"], ["0", "1"]], ["0", "0"]))
    assert caught.value.code is ErrorCode.RANK_UNCERTAIN


@given(
    st.lists(st.integers(-8, 8), min_size=9, max_size=9),
    st.lists(st.integers(-9, 9), min_size=3, max_size=3),
)
def test_generated_diagonally_dominant_systems_match_oracle_and_exact_solution(
    values, expected
) -> None:
    a = [values[i : i + 3] for i in range(0, 9, 3)]
    for i, row in enumerate(a):
        row[i] = sum(abs(row[j]) for j in range(3) if j != i) + 1
    b = [sum(coefficient * x for coefficient, x in zip(row, expected, strict=True)) for row in a]
    tokens = [[str(value) for value in row] for row in a]
    rhs = list(map(str, b))
    floating = solve_gaussian(parse_system(tokens, rhs))
    exact = solve_gaussian(parse_system(tokens, rhs, mode=ArithmeticMode.EXACT))
    np.testing.assert_allclose(floating.solution, np.linalg.solve(a, b), rtol=1e-12, atol=1e-12)
    assert exact.solution == tuple(expected)
    permuted = solve_gaussian(parse_system(tokens[::-1], rhs[::-1], mode=ArithmeticMode.EXACT))
    assert permuted.solution == exact.solution


@pytest.mark.parametrize("factor", ["1e-80", "1e-10", "1", "1e10"])
def test_uniform_scaling_preserves_float_solution(factor: str) -> None:
    scale = float(factor)
    result = solve_gaussian(
        FloatSystem(a=((2 * scale, scale), (scale, -scale)), b=(5 * scale, scale))
    )
    np.testing.assert_allclose(result.solution, [2, 1], rtol=1e-12, atol=1e-12)


def test_trace_budget_is_controlled_without_returning_a_truncated_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("solver_core._elimination.MAX_TRACE_VALUE_CHARS", 1)
    with pytest.raises(ResourceLimitError) as caught:
        solve_gaussian(parse_system([["0", "1"], ["1", "0"]], ["1", "2"]))
    assert caught.value.code is ErrorCode.TRACE_LIMIT


def test_gaussian_back_substitution_handles_leading_free_variables() -> None:
    system = parse_system([["0", "2", "1"]], ["4"], mode=ArithmeticMode.EXACT)
    result = solve_gaussian(system)
    assert result.pivot_columns == (1,)
    assert result.free_columns == (0, 2)
    parameters = {"t1": Fraction(3, 7), "t2": Fraction(-1, 11)}
    vector = [
        expr.constant + sum(term.coefficient * parameters[term.parameter] for term in expr.terms)
        for expr in result.parametric_solution.expressions
    ]
    assert sum(a * x for a, x in zip(system.a[0], vector, strict=True)) == 4


def test_output_schema_rejects_mixed_arithmetic_and_wrong_shapes() -> None:
    from pydantic import ValidationError

    from solver_core.models import DirectResult

    result = solve_gaussian(parse_system([["1"]], ["2"]))
    payload = result.model_dump()
    payload["solution"] = (Fraction(2),)
    with pytest.raises(ValidationError):
        DirectResult.model_validate(payload)
    payload = result.model_dump()
    payload["matrix"] = ((1.0,),)
    with pytest.raises(ValidationError):
        DirectResult.model_validate(payload)
