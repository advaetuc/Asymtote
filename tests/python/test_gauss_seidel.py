import numpy as np
import pytest

from solver_core.errors import InputError
from solver_core.gauss_seidel import solve_gauss_seidel
from solver_core.models import ArithmeticMode, IterationOptions, IterationStatus
from solver_core.parsing import parse_system


def test_sweep_uses_updated_components_immediately_without_rounding():
    result = solve_gauss_seidel(
        parse_system([["4", "1"], ["2", "3"]], ["1", "2"]),
        options=IterationOptions(max_iterations=2),
    )
    assert result.history[0].vector == (0.25, 0.5)
    assert result.history[1].vector == (0.125, 1.75 / 3.0)
    assert result.history[1].vector[1] != round(1.75 / 3, 6)
    assert result.status is IterationStatus.MAX_ITERATIONS_REACHED
    assert result.solution is None


def test_convergent_dominant_system_before_25():
    result = solve_gauss_seidel(parse_system([["4", "1"], ["2", "3"]], ["1", "2"]))
    assert result.status is IterationStatus.CONVERGED
    assert len(result.history) < 25
    assert result.solution == pytest.approx((0.1, 0.6), abs=1e-8)
    assert result.convergence.spectral.radius == pytest.approx(1 / 6)
    assert result.history[-1].normalized_step_change <= result.options.tolerance
    assert result.diagnostics.backward_error <= result.options.tolerance


def test_initial_guess_affects_first_sweep():
    result = solve_gauss_seidel(
        parse_system([["4", "1"], ["2", "3"]], ["1", "2"]),
        options=IterationOptions(initial_guess=(1.0, 1.0), max_iterations=1),
    )
    assert result.history[0].vector == (0.0, 2 / 3)


def test_spd_is_sufficient_for_gauss_seidel_without_dominance():
    system = parse_system(
        [["1", "0.9", "0.9"], ["0.9", "1", "0.9"], ["0.9", "0.9", "1"]], ["1", "2", "3"]
    )
    result = solve_gauss_seidel(system, options=IterationOptions(max_iterations=500))
    assert result.convergence.symmetric_positive_definite is True
    assert not result.convergence.strict_diagonal_dominance
    assert result.convergence.assessment == "sufficient_condition"
    assert result.status is IterationStatus.CONVERGED
    assert result.solution == pytest.approx(np.linalg.solve(system.a, system.b), abs=1e-6)


@pytest.mark.parametrize("limit", [None, 1, 37, 500])
def test_default_and_custom_iteration_limits(limit):
    options = IterationOptions() if limit is None else IterationOptions(max_iterations=limit)
    result = solve_gauss_seidel(
        parse_system([["1", "0.9999"], ["0.9999", "1"]], ["1", "1"]), options=options
    )
    assert result.status is IterationStatus.MAX_ITERATIONS_REACHED
    assert len(result.history) == (25 if limit is None else limit)
    assert result.solution is None


def test_strict_matching_recovers_zero_diagonal():
    result = solve_gauss_seidel(parse_system([["0", "4"], ["3", "1"]], ["8", "5"]))
    assert result.reordering.permutation.order == (1, 0)
    assert result.status is IterationStatus.CONVERGED
    assert result.solution == pytest.approx((1.0, 2.0))


def test_nonzero_fallback_is_explicit_and_does_not_claim_strict_dominance():
    system = parse_system([["0", "1", "1"], ["1", "1", "0"], ["1", "0", "1"]], ["2", "2", "2"])
    with pytest.raises(InputError):
        solve_gauss_seidel(system)
    result = solve_gauss_seidel(
        system,
        options=IterationOptions(
            auto_reorder_for_nonzero_diagonal=True,
            run_despite_convergence_risk=True,
            max_iterations=3,
        ),
    )
    assert result.reordering.dominance_matching_found is False
    assert result.reordering.nonzero_search_attempted
    assert result.reordering.permutation.purpose == "nonzero_diagonal"
    assert not result.convergence.strict_diagonal_dominance
    assert len(result.history) == 3


def test_spectral_radius_at_least_one_requires_opt_in():
    system = parse_system([["1", "2"], ["2", "1"]], ["1", "1"])
    declined = solve_gauss_seidel(
        system, options=IterationOptions(auto_reorder_for_diagonal_dominance=False)
    )
    assert declined.convergence.spectral.radius == pytest.approx(4.0)
    assert declined.status is IterationStatus.CONVERGENCE_RISK_DECLINED
    assert declined.history == ()
    run = solve_gauss_seidel(
        system,
        options=IterationOptions(
            auto_reorder_for_diagonal_dominance=False,
            run_despite_convergence_risk=True,
            max_iterations=3,
        ),
    )
    assert run.status is IterationStatus.MAX_ITERATIONS_REACHED
    assert run.history[0].vector == (1.0, -1.0)
    assert run.history[-1].residual_inf > run.history[0].residual_inf


def test_nonfinite_guard_keeps_complete_history_only():
    result = solve_gauss_seidel(
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
    assert all(np.isfinite(record.vector).all() for record in result.history)


@pytest.mark.parametrize(
    "a,b",
    [
        ([["1", "2"]], ["1"]),
        ([["1", "1"], ["1", "1"]], ["1", "1"]),
        ([["1", "1"], ["1", "1"]], ["1", "2"]),
    ],
)
def test_invalid_system_preconditions(a, b):
    with pytest.raises(InputError):
        solve_gauss_seidel(parse_system(a, b))


def test_exact_mode_and_bad_guess_rejected():
    with pytest.raises(InputError):
        solve_gauss_seidel(parse_system([["1"]], ["1"], mode=ArithmeticMode.EXACT))
    with pytest.raises(InputError):
        solve_gauss_seidel(
            parse_system([["1"]], ["1"]), options=IterationOptions(initial_guess=(0.0, 0.0))
        )
