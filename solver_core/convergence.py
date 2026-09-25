"""Method-specific stationary iteration diagnostics, separate from observed progress."""

import math
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from solver_core.diagnostics import finite_float
from solver_core.errors import ErrorCode, InputError
from solver_core.models import (
    ConvergenceDiagnostics,
    FloatSystem,
    FloatVector,
    IterationMetrics,
    IterationRecord,
    IterativeMethod,
    SpectralDiagnostic,
)
from solver_core.permutations import diagonal_dominance, has_nonzero_diagonal, require_square
from solver_core.tolerance import tolerance_for


def iteration_matrix(system: FloatSystem, method: IterativeMethod) -> NDArray[np.float64]:
    """Build Jacobi T=-D^-1(L+U) or GS T=-(D+L)^-1 U without an inverse."""
    n = require_square(system)
    if not has_nonzero_diagonal(system):
        raise InputError(ErrorCode.ZERO_PIVOT, "Iteration requires a safe non-zero diagonal.")
    if method not in ("jacobi", "gauss_seidel"):
        raise InputError(ErrorCode.INVALID_SYSTEM, "Unknown iterative method.")
    a = np.asarray(system.a, dtype=np.float64)
    result = np.zeros((n, n), dtype=np.float64)
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        if method == "jacobi":
            for i in range(n):
                for j in range(n):
                    if i != j:
                        result[i, j] = -a[i, j] / a[i, i]
        else:
            # Solve one triangular system per upper-triangular column.
            for j in range(n):
                for i in range(n):
                    rhs = -float(a[i, j]) if j > i else 0.0
                    contribution = math.fsum(
                        finite_float(float(a[i, k]) * float(result[k, j])) for k in range(i)
                    )
                    result[i, j] = finite_float((rhs - contribution) / float(a[i, i]))
    return result


def spectral_diagnostic(system: FloatSystem, method: IterativeMethod) -> SpectralDiagnostic:
    from solver_core.errors import NumericBreakdownError

    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            matrix = iteration_matrix(system, method)
            eigenvalues = np.linalg.eigvals(matrix)
            radius = float(np.max(np.abs(eigenvalues)))
        if not math.isfinite(radius):
            return SpectralDiagnostic(status="unavailable")
        return SpectralDiagnostic(status="computed", radius=radius)
    except (np.linalg.LinAlgError, FloatingPointError, OverflowError, NumericBreakdownError):
        return SpectralDiagnostic(status="unavailable")


def convergence_diagnostics(system: FloatSystem, method: IterativeMethod) -> ConvergenceDiagnostics:
    strict, weak = diagonal_dominance(system)
    symmetry_tolerance = tolerance_for(system).pivot_abs
    a = np.asarray(system.a, dtype=np.float64)
    spd: bool | None = False
    try:
        with np.errstate(over="raise", invalid="raise"):
            if float(np.max(np.abs(a - a.T))) <= symmetry_tolerance:
                # Cholesky reads one triangle; explicitly use the symmetric part.
                np.linalg.cholesky(0.5 * a + 0.5 * a.T)
                spd = True
    except np.linalg.LinAlgError:
        spd = False
    except (FloatingPointError, OverflowError):
        spd = None
    spectral = spectral_diagnostic(system, method)
    sufficient = strict or (method == "gauss_seidel" and spd is True)
    assessment: Literal["sufficient_condition", "spectral_radius_below_one", "convergence_risk"]
    # Conflicting numerical evidence is a risk, never a promised convergence.
    if spectral.radius is not None and spectral.radius >= 1.0:
        assessment = "convergence_risk"
        explanation = "Computed spectral radius is at least one; convergence is not guaranteed."
    elif sufficient:
        assessment = "sufficient_condition"
        explanation = (
            "Strict row diagonal dominance is a sufficient convergence condition."
            if strict
            else "Symmetry within tolerance and Cholesky success indicate SPD, a "
            "sufficient Gauss-Seidel condition. This is a floating diagnostic."
        )
    elif spectral.radius is not None:
        assessment = "spectral_radius_below_one"
        explanation = "Computed method-specific spectral radius is below one."
    else:
        assessment = "convergence_risk"
        explanation = "Spectral radius is unavailable and no sufficient condition was established."
    return ConvergenceDiagnostics(
        method=method,
        strict_diagonal_dominance=strict,
        weak_diagonal_dominance=weak,
        symmetric_positive_definite=spd,
        symmetry_tolerance=symmetry_tolerance,
        spectral=spectral,
        assessment=assessment,
        explanation=explanation,
    )


def iteration_record(
    index: int,
    previous: FloatVector,
    vector: FloatVector,
    metrics: IterationMetrics,
    tolerance: float,
) -> IterationRecord:
    delta = max(abs(finite_float(x - old)) for x, old in zip(vector, previous, strict=True))
    normalized = finite_float(delta / max(1.0, max(abs(x) for x in vector)))
    return IterationRecord(
        index=index,
        vector=vector,
        delta_inf=delta,
        normalized_step_change=normalized,
        residual_inf=metrics.residual_inf,
        backward_error=metrics.backward_error,
        converged=metrics.backward_error <= tolerance and normalized <= tolerance,
    )
