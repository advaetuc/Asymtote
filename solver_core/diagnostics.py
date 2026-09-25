"""Original-system residuals and finite, JSON-safe conditioning diagnostics."""

import math
from fractions import Fraction

import numpy as np

from solver_core._elimination import (
    Matrix,
    Scalar,
    System,
    add,
    divide,
    magnitude,
    multiply,
    total,
)
from solver_core.errors import ErrorCode, InputError, NumericBreakdownError
from solver_core.models import (
    ConditionDiagnostic,
    DirectDiagnostics,
    ExactSystem,
    FloatSystem,
    FloatVector,
    IterationMetrics,
)


def solution_diagnostics(system: System, vector: tuple[Scalar, ...]) -> DirectDiagnostics:
    if len(vector) != system.shape.unknowns:
        raise InputError(ErrorCode.INVALID_SYSTEM, "Candidate length must match the unknown count.")
    exact = isinstance(system, ExactSystem)
    if any((not isinstance(v, Fraction)) if exact else type(v) is not float for v in vector):
        raise InputError(ErrorCode.INVALID_SYSTEM, "Candidate arithmetic must match the system.")
    zero: Scalar = Fraction(0) if exact else 0.0
    coefficients: Matrix = system.a
    rhs_values: tuple[Scalar, ...] = system.b
    residual = tuple(
        add(total((multiply(a, x) for a, x in zip(row, vector, strict=True)), zero), -b)
        for row, b in zip(coefficients, rhs_values, strict=True)
    )
    residual_inf = max(magnitude(value) for value in residual)
    norm_a = max(total((magnitude(value) for value in row), zero) for row in coefficients)
    norm_x = max(magnitude(value) for value in vector)
    norm_b = max(magnitude(value) for value in rhs_values)
    denominator = add(multiply(norm_a, norm_x), norm_b)
    # The only zero-denominator case is a zero residual for the zero system.
    backward_error = zero if denominator == 0 else divide(residual_inf, denominator)
    return DirectDiagnostics(residual_inf=residual_inf, backward_error=backward_error)


def float_metrics(system: FloatSystem, vector: FloatVector) -> IterationMetrics:
    metrics = solution_diagnostics(system, vector)
    return IterationMetrics(
        residual_inf=float(metrics.residual_inf), backward_error=float(metrics.backward_error)
    )


def finite_float(value: float) -> float:
    if not math.isfinite(value):
        raise NumericBreakdownError(
            ErrorCode.NON_FINITE_VALUE, "Iteration arithmetic overflowed float64."
        )
    return value


def condition_diagnostic(system: FloatSystem) -> ConditionDiagnostic:
    """2-norm condition number; digit loss is an estimate, never an error bound."""
    try:
        with np.errstate(over="raise", invalid="raise", divide="ignore"):
            kappa = float(np.linalg.cond(np.asarray(system.a, dtype=np.float64)))
    except (np.linalg.LinAlgError, FloatingPointError, OverflowError):
        return ConditionDiagnostic(status="unavailable")
    if math.isinf(kappa):
        return ConditionDiagnostic(status="singular")
    if not math.isfinite(kappa) or kappa < 1.0:
        return ConditionDiagnostic(status="unavailable")
    return ConditionDiagnostic(
        status="finite", condition_number=kappa, approximate_digit_loss=max(0.0, math.log10(kappa))
    )
