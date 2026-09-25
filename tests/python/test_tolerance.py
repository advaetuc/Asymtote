"""Numerically meaningful policy checks before classification is implemented."""

import math
from fractions import Fraction

import numpy as np
import pytest

from solver_core.constants import FLOAT64_EPSILON
from solver_core.errors import InputError, NumericBreakdownError
from solver_core.models import FloatSystem
from solver_core.parsing import parse_system
from solver_core.tolerance import is_effectively_zero, tolerance_for


def test_rank_cutoff_is_shared_and_rhs_does_not_erase_coefficient_scale() -> None:
    small_rhs = parse_system([["1", "0"], ["0", "1"]], ["1", "1"])
    large_rhs = parse_system([["1", "0"], ["0", "1"]], ["1e12", "1e12"])
    policy = tolerance_for(large_rhs)
    assert policy.rank_abs == tolerance_for(small_rhs).rank_abs == FLOAT64_EPSILON * 3
    a = np.asarray(large_rhs.a)
    augmented = np.column_stack((a, large_rhs.b))
    assert np.linalg.matrix_rank(a, tol=policy.rank_abs) == 2
    assert np.linalg.matrix_rank(augmented, tol=policy.rank_abs) == 2


@pytest.mark.parametrize("scale", [1e-80, 1e-20, 1.0, 1e10])
def test_uniform_scaling_changes_cutoffs_without_changing_pivot_decisions(scale: float) -> None:
    system = FloatSystem(a=((4.0 * scale, scale), (2.0 * scale, 3.0 * scale)), b=(scale, scale))
    policy = tolerance_for(system)
    baseline = tolerance_for(parse_system([["4", "1"], ["2", "3"]], ["1", "1"]))
    assert policy.rank_abs == pytest.approx(baseline.rank_abs * scale, rel=1e-14, abs=0)
    assert policy.pivot_abs == pytest.approx(baseline.pivot_abs * scale, rel=1e-14, abs=0)
    assert not is_effectively_zero(scale, tolerance=policy.pivot_abs)


def test_zero_system_and_rhs_fallback_are_explicit() -> None:
    zero = tolerance_for(parse_system([["0", "0"]], ["0"]))
    assert zero.rank_abs == zero.pivot_abs == 0.0
    assert is_effectively_zero(0.0, tolerance=zero.rank_abs)
    assert not is_effectively_zero(1e-100, tolerance=zero.rank_abs)
    inconsistent = tolerance_for(parse_system([["0", "0"]], ["1e-100"]))
    assert inconsistent.coefficient_scale == 0
    assert inconsistent.rank_scale == 1e-100
    assert 0 < inconsistent.rank_abs < 1e-100


def test_comparisons_and_growth_detection_do_not_mutate_inputs() -> None:
    system = parse_system([["1e-100", "0"], ["0", "1"]], ["0", "0"])
    before = system.model_dump()
    policy = tolerance_for(system)
    assert is_effectively_zero(system.a[0][0], tolerance=policy.pivot_abs)
    assert system.model_dump() == before
    assert system.a[0][0] == float(Fraction(1, 10**100))
    assert policy.pivot_threshold([0.0, 0.5]) == policy.pivot_abs
    assert policy.pivot_threshold([1e10, 0.0]) > policy.pivot_abs


def test_epsilon_and_cutoff_boundary() -> None:
    assert FLOAT64_EPSILON == np.finfo(np.float64).eps
    cutoff = tolerance_for(parse_system([["1"]], ["1"])).rank_abs
    assert is_effectively_zero(cutoff, tolerance=cutoff)
    assert is_effectively_zero(-cutoff, tolerance=cutoff)
    assert not is_effectively_zero(math.nextafter(cutoff, math.inf), tolerance=cutoff)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_nonfinite_diagnostics_fail_explicitly(value: float) -> None:
    with pytest.raises(NumericBreakdownError):
        is_effectively_zero(value, tolerance=0.0)
    with pytest.raises(NumericBreakdownError):
        tolerance_for(parse_system([["1"]], ["1"])).pivot_threshold([value])


@pytest.mark.parametrize("value", [-1.0, math.inf, math.nan])
def test_invalid_tolerances_are_rejected(value: float) -> None:
    with pytest.raises(InputError):
        is_effectively_zero(0.0, tolerance=value)


def test_overflow_and_invalid_column_lengths_are_controlled() -> None:
    with pytest.raises(NumericBreakdownError):
        tolerance_for(FloatSystem(a=((1e308, 1e308),), b=(0.0,)))
    policy = tolerance_for(parse_system([["1"]], ["1"]))
    for column in ([], [1.0, 2.0]):
        with pytest.raises(InputError):
            policy.pivot_threshold(column)
