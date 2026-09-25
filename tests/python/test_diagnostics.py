import numpy as np
import pytest

from solver_core.convergence import convergence_diagnostics, iteration_matrix
from solver_core.diagnostics import condition_diagnostic, float_metrics
from solver_core.errors import InputError
from solver_core.gauss_seidel import solve_gauss_seidel
from solver_core.jacobi import solve_jacobi
from solver_core.models import IterationOptions, IterationStatus
from solver_core.parsing import parse_system
from solver_core.tolerance import tolerance_for


@pytest.mark.parametrize("method", ["jacobi", "gauss_seidel"])
def test_iteration_matrix_matches_reference_splitting(method):
    system = parse_system([["4", "1", "-1"], ["2", "5", "1"], ["1", "-2", "6"]], ["1", "2", "3"])
    a = np.asarray(system.a)
    splitting = np.diag(np.diag(a)) if method == "jacobi" else np.tril(a)
    expected = np.linalg.solve(splitting, -(a - splitting))
    assert iteration_matrix(system, method) == pytest.approx(expected, abs=1e-15)
    assert iteration_matrix(system, method).dtype == np.dtype("float64")


def test_nondominant_nonspd_system_with_small_radius_is_accepted():
    system = parse_system([["1", "2"], ["0.1", "1"]], ["3", "1.1"])
    result = solve_jacobi(system, options=IterationOptions(max_iterations=100))
    assert result.convergence.assessment == "spectral_radius_below_one"
    assert result.convergence.symmetric_positive_definite is False
    assert result.status is IterationStatus.CONVERGED
    assert result.solution == pytest.approx((1, 1), abs=1e-7)


def test_radius_equal_to_one_is_a_risk():
    system = parse_system([["1", "-1"], ["1", "1"]], ["0", "2"])
    for solve in (solve_jacobi, solve_gauss_seidel):
        result = solve(system)
        assert result.convergence.spectral.radius == pytest.approx(1.0)
        assert result.status is IterationStatus.CONVERGENCE_RISK_DECLINED


def test_spd_uses_scale_aware_symmetry_and_cholesky():
    spd = parse_system([["2", "1.0000000000000002"], ["1", "2"]], ["1", "1"])
    diagnostic = convergence_diagnostics(spd, "gauss_seidel")
    assert diagnostic.symmetric_positive_definite is True
    assert diagnostic.symmetry_tolerance == tolerance_for(spd).pivot_abs
    indefinite = parse_system([["1", "2"], ["2", "1"]], ["1", "1"])
    assert convergence_diagnostics(indefinite, "gauss_seidel").symmetric_positive_definite is False


def test_condition_number_is_finite_or_structured_status():
    diagonal = parse_system([["1", "0"], ["0", "100"]], ["1", "1"])
    result = condition_diagnostic(diagonal)
    assert result.status == "finite"
    assert result.condition_number == pytest.approx(100)
    assert result.approximate_digit_loss == pytest.approx(2)
    singular = condition_diagnostic(parse_system([["0", "0"], ["0", "1"]], ["0", "1"]))
    assert singular.status == "singular"
    assert singular.condition_number is singular.approximate_digit_loss is None


def test_library_diagnostic_failure_is_unavailable_not_a_solver_crash(monkeypatch):
    def unavailable(*args, **kwargs):
        raise np.linalg.LinAlgError("simulated failure")

    monkeypatch.setattr(np.linalg, "cond", unavailable)
    monkeypatch.setattr(np.linalg, "eigvals", unavailable)
    # Strict dominance still supplies a sufficient condition.
    result = solve_jacobi(parse_system([["4", "1"], ["2", "3"]], ["1", "2"]))
    assert result.status is IterationStatus.CONVERGED
    assert result.convergence.spectral.status == "unavailable"
    assert result.conditioning.status == "unavailable"
    # Without a sufficient condition, unknown spectral behavior is a risk.
    result = solve_jacobi(parse_system([["1", "2"], ["0.1", "1"]], ["1", "1"]))
    assert result.status is IterationStatus.CONVERGENCE_RISK_DECLINED


def test_nonfinite_library_diagnostics_are_not_serialized(monkeypatch):
    monkeypatch.setattr(np.linalg, "eigvals", lambda *args: np.array([np.nan]))
    monkeypatch.setattr(np.linalg, "cond", lambda *args: np.nan)
    result = solve_jacobi(parse_system([["1"]], ["1"]))
    assert result.convergence.spectral.status == "unavailable"
    assert result.conditioning.status == "unavailable"
    assert "NaN" not in result.model_dump_json()


def test_zero_system_metrics_and_candidate_shape():
    system = parse_system([["0"]], ["0"])
    assert float_metrics(system, (0.0,)).backward_error == 0.0
    with pytest.raises(InputError):
        float_metrics(system, (0.0, 0.0))


@pytest.mark.parametrize("solve", [solve_jacobi, solve_gauss_seidel])
def test_iteration_invariant_failure_is_an_explicit_breakdown(solve, monkeypatch):
    import solver_core._iterative as engine

    monkeypatch.setattr(engine, "_sweep", lambda *args: (1.0, 2.0))
    result = solve(parse_system([["1"]], ["1"]))
    assert result.status is IterationStatus.NUMERIC_BREAKDOWN
    assert result.last_iterate == (0.0,)
    assert result.history == () and result.breakdown_reason
