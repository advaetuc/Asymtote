"""Versioned float64 comparison policy; functions never mutate solver state."""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from solver_core.constants import FLOAT64_EPSILON, TOLERANCE_POLICY_VERSION
from solver_core.errors import ErrorCode, InputError, NumericBreakdownError
from solver_core.models import FloatSystem


def _finite(value: float) -> None:
    if not math.isfinite(value):
        raise NumericBreakdownError(ErrorCode.NON_FINITE_VALUE, "Expected finite arithmetic data.")


def _scaled_cutoff(dimension: int, scale: float) -> float:
    # Multiplication in this order avoids an unnecessary large intermediate.
    cutoff = (FLOAT64_EPSILON * dimension) * scale
    _finite(cutoff)
    return cutoff


@dataclass(frozen=True, slots=True)
class TolerancePolicy:
    """Create via tolerance_for; reuse rank_abs for BOTH A and [A|b].

    Scale is ||A||∞, or ||b||∞ only when A is identically zero. This avoids
    discarding coefficient pivots solely because the RHS has a larger scale.
    """

    equations: int
    unknowns: int
    coefficient_scale: float
    rank_scale: float
    rank_abs: float
    pivot_abs: float
    version: str = TOLERANCE_POLICY_VERSION

    def pivot_threshold(self, active_column: Sequence[float]) -> float:
        """Account for elimination growth without lowering the original safety floor."""
        if len(active_column) == 0 or len(active_column) > self.equations:
            raise InputError(ErrorCode.INVALID_SYSTEM, "Invalid active-column length.")
        for value in active_column:
            _finite(value)
        scale = max(self.coefficient_scale, max(abs(value) for value in active_column))
        return _scaled_cutoff(max(self.equations, self.unknowns), scale)


def tolerance_for(system: FloatSystem) -> TolerancePolicy:
    """Use one absolute rank cutoff, including the augmented column dimension."""
    try:
        coefficient_scale = max(math.fsum(abs(value) for value in row) for row in system.a)
    except OverflowError:
        raise NumericBreakdownError(
            ErrorCode.NON_FINITE_VALUE, "The coefficient norm overflowed float64."
        ) from None
    _finite(coefficient_scale)
    rank_scale = coefficient_scale or max(abs(value) for value in system.b)
    m, n = system.shape.equations, system.shape.unknowns
    return TolerancePolicy(
        equations=m,
        unknowns=n,
        coefficient_scale=coefficient_scale,
        rank_scale=rank_scale,
        rank_abs=_scaled_cutoff(max(m, n + 1), rank_scale),
        pivot_abs=_scaled_cutoff(max(m, n), coefficient_scale),
    )


def is_effectively_zero(value: float, *, tolerance: float) -> bool:
    """Compare only; equality with the cutoff counts as zero."""
    _finite(value)
    if not math.isfinite(tolerance) or tolerance < 0:
        raise InputError(ErrorCode.INVALID_TOLERANCE, "Tolerance must be finite and nonnegative.")
    return abs(value) <= tolerance
