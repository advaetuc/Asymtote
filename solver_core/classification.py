"""Rank-based classification for rectangular float64 and exact rational systems."""

import numpy as np

from solver_core._elimination import forward_reduce
from solver_core.errors import ErrorCode, NumericBreakdownError
from solver_core.models import (
    ArithmeticMode,
    ClassificationKind,
    ClassificationResult,
    ExactSystem,
    FloatSystem,
)
from solver_core.tolerance import tolerance_for


def classify_system(system: FloatSystem | ExactSystem) -> ClassificationResult:
    """Return unique, infinite, or inconsistent using rank(A) and rank([A|b])."""
    if isinstance(system, ExactSystem):
        reduced = forward_reduce(system, record_trace=False)
        rank_a = sum(column < system.shape.unknowns for column in reduced.pivots)
        rank_augmented = len(reduced.pivots)
        mode = ArithmeticMode.EXACT
        cutoff = None
        policy_version = "exact-rational-v1"
    else:
        policy = tolerance_for(system)
        a = np.asarray(system.a, dtype=np.float64)
        augmented = np.column_stack((a, np.asarray(system.b, dtype=np.float64)))
        try:
            singular_a = np.linalg.svd(a, compute_uv=False)
            singular_augmented = np.linalg.svd(augmented, compute_uv=False)
        except np.linalg.LinAlgError:
            raise NumericBreakdownError(
                ErrorCode.RANK_UNCERTAIN, "Singular-value analysis failed to converge."
            ) from None
        if not (np.isfinite(singular_a).all() and np.isfinite(singular_augmented).all()):
            raise NumericBreakdownError(ErrorCode.NON_FINITE_VALUE, "Non-finite singular values.")
        rank_a = int(np.count_nonzero(singular_a > policy.rank_abs))
        rank_augmented = int(np.count_nonzero(singular_augmented > policy.rank_abs))
        if not rank_a <= rank_augmented <= rank_a + 1:
            raise NumericBreakdownError(
                ErrorCode.RANK_UNCERTAIN,
                "Numerical rank estimates disagree; rescale the input or use exact mode.",
            )
        # A coefficient-derived shared cutoff can be below the rounding noise of
        # SVD([A|b]) when b is much larger than A. Never publish a classification
        # contradicted by pivot analysis (including a false extra augmented rank).
        reduced = forward_reduce(system, record_trace=False)
        pivot_rank_a = sum(column < system.shape.unknowns for column in reduced.pivots)
        if (pivot_rank_a, len(reduced.pivots)) != (rank_a, rank_augmented):
            raise NumericBreakdownError(
                ErrorCode.RANK_UNCERTAIN,
                "Singular-value and pivot rank estimates disagree at this scale; "
                "rescale the input or use exact mode.",
            )
        mode = ArithmeticMode.FLOAT64
        cutoff = policy.rank_abs
        policy_version = policy.version

    kind = (
        ClassificationKind.INCONSISTENT
        if rank_a < rank_augmented
        else ClassificationKind.UNIQUE
        if rank_a == system.shape.unknowns
        else ClassificationKind.INFINITE
    )
    return ClassificationResult(
        shape=system.shape,
        arithmetic_mode=mode,
        rank_a=rank_a,
        rank_augmented=rank_augmented,
        classification=kind,
        rank_tolerance=cutoff,
        tolerance_policy=policy_version,
    )
