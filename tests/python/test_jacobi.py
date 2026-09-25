import json
import math

import numpy as np
import pytest
from pydantic import ValidationError

from solver_core.errors import ErrorCode, InputError
from solver_core.jacobi import solve_jacobi
from solver_core.models import ArithmeticMode, FloatSystem, IterationOptions, IterationStatus
from solver_core.parsing import parse_system


def test_jacobi_uses_only_previous_vector_and_never_rounds():
    system = parse_system([["4", "1"], ["2", "3"]], ["1", "2"])
    result = solve_jacobi(system, options=IterationOptions(max_iterations=2))
    assert result.history[0].vector == (0.25, 2.0 / 3.0)
    assert result.history[1].vector == ((1.0 - 2.0 / 3.0) / 4.0, 0.5)
    assert result.history[0].vector[1] != round(2.0 / 3.0, 6)
    assert result.status is IterationStatus.MAX_ITERATIONS_REACHED
    assert result.solution is None


def test_converges_before_default_limit_with_original_system_residuals():
    system = parse_system([["4", "1"], ["2", "3"]], ["1", "2"])
    result = solve_jacobi(system)
    assert result.status is IterationStatus.CONVERGED
    assert len(result.history) < 25
    assert result.solution == pytest.approx((0.1, 0.6), abs=1e-8)
    assert result.convergence.spectral.radius == pytest.approx(math.sqrt(1 / 6))
    assert result.convergence.strict_diagonal_dominance
    previous = result.initial_guess
    for record in result.history:
        residual = np.linalg.norm(np.asarray(system.a) @ record.vector - system.b, ord=np.inf)
        denominator = np.linalg.norm(system.a, ord=np.inf) * max(map(abs, record.vector)) + 2
        assert record.residual_inf == pytest.approx(residual, abs=3e-16)
        assert record.backward_error == pytest.approx(residual / denominator, abs=3e-16)
        assert record.delta_inf == max(
            abs(x - y) for x, y in zip(record.vector, previous, strict=True)
        )
        assert record.converged == (
            record.backward_error <= result.options.tolerance
            and record.normalized_step_change <= result.options.tolerance
        )
        previous = record.vector


def test_custom_initial_guess_is_used():
    result = solve_jacobi(
        parse_system([["4", "1"], ["2", "3"]], ["1", "2"]),
        options=IterationOptions(initial_guess=(1.0, 1.0), max_iterations=1),
    )
    assert result.history[0].vector == (0.0, 0.0)
    assert result.history[0].normalized_step_change == 1.0


def test_exact_initial_solution_completes_one_zero_step():
    result = solve_jacobi(
        parse_system([["2"]], ["4"]), options=IterationOptions(initial_guess=(2.0,))
    )
    assert result.status is IterationStatus.CONVERGED
    assert len(result.history) == 1
    assert result.history[0].delta_inf == result.diagnostics.residual_inf == 0.0


def test_small_step_alone_does_not_converge_near_zero():
    system = parse_system([["1", "0.5"], ["0.5", "1"]], ["1e-20", "1e-20"])
    result = solve_jacobi(system, options=IterationOptions(max_iterations=1))
    assert result.history[0].normalized_step_change < result.options.tolerance
    assert result.history[0].backward_error > result.options.tolerance
    assert result.status is IterationStatus.MAX_ITERATIONS_REACHED


def test_zero_residual_alone_does_not_converge_after_large_step():
    result = solve_jacobi(parse_system([["3"]], ["1"]), options=IterationOptions(max_iterations=1))
    assert result.history[0].backward_error == 0.0
    assert result.status is IterationStatus.MAX_ITERATIONS_REACHED


@pytest.mark.parametrize("limit", [None, 1, 37, 500])
def test_iteration_limit_is_honored(limit):
    options = IterationOptions() if limit is None else IterationOptions(max_iterations=limit)
    result = solve_jacobi(
        parse_system([["1", "0.9999"], ["0.9999", "1"]], ["1", "1"]), options=options
    )
    assert result.status is IterationStatus.MAX_ITERATIONS_REACHED
    assert len(result.history) == (25 if limit is None else limit)
    assert result.solution is None
    assert result.last_iterate == result.history[-1].vector


def test_zero_diagonal_is_recovered_by_strict_matching():
    system = parse_system([["0", "4"], ["3", "1"]], ["8", "5"])
    result = solve_jacobi(system)
    assert result.status is IterationStatus.CONVERGED
    assert result.solution == pytest.approx((1.0, 2.0))
    assert result.reordering.permutation.order == (1, 0)
    assert result.reordering.dominance_matching_found is True


def test_failed_dominance_search_preserves_order_and_declines_risk():
    system = parse_system(
        [["1", "0.9", "0.9"], ["0.9", "1", "0.9"], ["0.9", "0.9", "1"]], ["1", "1", "1"]
    )
    result = solve_jacobi(system)
    assert result.convergence.symmetric_positive_definite is True
    assert result.convergence.spectral.radius == pytest.approx(1.8)
    assert result.reordering.dominance_matching_found is False
    assert result.reordering.permutation.order == (0, 1, 2)
    assert result.status is IterationStatus.CONVERGENCE_RISK_DECLINED
    assert result.history == () and result.solution is None


def test_risk_override_runs_actual_trace_even_at_an_unstable_fixed_point():
    system = parse_system([["1", "2"], ["2", "1"]], ["3", "3"])
    result = solve_jacobi(
        system,
        options=IterationOptions(
            auto_reorder_for_diagonal_dominance=False,
            run_despite_convergence_risk=True,
            initial_guess=(1.0, 1.0),
        ),
    )
    assert result.convergence.spectral.radius >= 1.0
    assert result.status is IterationStatus.CONVERGED
    assert result.solution == (1.0, 1.0)


def test_divergence_overflow_preserves_last_complete_finite_trace():
    result = solve_jacobi(
        parse_system([["1", "100"], ["100", "1"]], ["1", "1"]),
        options=IterationOptions(
            max_iterations=500,
            auto_reorder_for_diagonal_dominance=False,
            run_despite_convergence_risk=True,
        ),
    )
    assert result.status is IterationStatus.NUMERIC_BREAKDOWN
    assert 1 < len(result.history) < 500
    assert result.last_iterate == result.history[-1].vector
    assert result.breakdown_reason
    assert result.solution is None
    json.loads(result.model_dump_json(), parse_constant=lambda v: pytest.fail(v))


def test_initial_residual_overflow_has_no_fabricated_record():
    result = solve_jacobi(
        parse_system([["2"]], ["1"]), options=IterationOptions(initial_guess=(1e308,))
    )
    assert result.status is IterationStatus.NUMERIC_BREAKDOWN
    assert result.history == () and result.diagnostics is None
    assert result.last_iterate == (1e308,)


def test_nonfinite_first_iterate_is_not_stored():
    result = solve_jacobi(FloatSystem(a=((1e-100,),), b=(1e308,)))
    assert result.status is IterationStatus.NUMERIC_BREAKDOWN
    assert result.history == () and result.last_iterate == (0.0,)


@pytest.mark.parametrize(
    "a,b",
    [
        ([["1", "2"]], ["1"]),
        ([["1", "1"], ["1", "1"]], ["1", "1"]),
        ([["1", "1"], ["1", "1"]], ["1", "2"]),
    ],
)
def test_invalid_mathematical_preconditions(a, b):
    with pytest.raises(InputError):
        solve_jacobi(parse_system(a, b))


def test_no_implicit_exact_to_float_conversion():
    with pytest.raises(InputError):
        solve_jacobi(parse_system([["1"]], ["1"], mode=ArithmeticMode.EXACT))


def test_guess_length_and_disabled_reordering():
    with pytest.raises(InputError):
        solve_jacobi(
            parse_system([["1"]], ["1"]), options=IterationOptions(initial_guess=(0.0, 0.0))
        )
    with pytest.raises(InputError) as error:
        solve_jacobi(
            parse_system([["0", "1"], ["1", "0"]], ["1", "1"]),
            options=IterationOptions(auto_reorder_for_diagonal_dominance=False),
        )
    assert error.value.code is ErrorCode.ZERO_PIVOT


@pytest.mark.parametrize(
    "options",
    [
        {"tolerance": float("nan")},
        {"tolerance": float("inf")},
        {"tolerance": 1e-15},
        {"tolerance": 0.1},
        {"max_iterations": 0},
        {"max_iterations": 501},
        {"max_iterations": True},
        {"initial_guess": (float("inf"),)},
        {"initial_guess": (0,)},
        {"initial_guess": ()},
        {"initial_guess": (0.0,) * 13},
    ],
)
def test_invalid_options_rejected(options):
    with pytest.raises(ValidationError):
        IterationOptions(**options)
