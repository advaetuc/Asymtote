"""Shared bounded binary64 iteration engine; no display formatting enters arithmetic."""

import math

from solver_core.classification import classify_system
from solver_core.convergence import convergence_diagnostics, iteration_record
from solver_core.diagnostics import condition_diagnostic, finite_float, float_metrics
from solver_core.errors import ErrorCode, InputError, SolverError
from solver_core.models import (
    ClassificationKind,
    FloatSystem,
    FloatVector,
    IterationMetrics,
    IterationOptions,
    IterationRecord,
    IterationStatus,
    IterativeMethod,
    IterativeResult,
    ReorderingDiagnostics,
    RowPermutation,
)
from solver_core.permutations import (
    apply_row_permutation,
    diagonal_dominance,
    find_diagonal_dominance_permutation,
    find_nonzero_diagonal_permutation,
    has_nonzero_diagonal,
    require_square,
)


def _reorder(
    system: FloatSystem, options: IterationOptions
) -> tuple[FloatSystem, ReorderingDiagnostics]:
    permutation = RowPermutation(order=tuple(range(len(system.a))), purpose="identity")
    searched = options.auto_reorder_for_diagonal_dominance and not diagonal_dominance(system)[0]
    found: bool | None = None
    if searched:
        match = find_diagonal_dominance_permutation(system)
        found = match is not None
        if match is not None:
            permutation = match
    working = apply_row_permutation(system, permutation)
    fallback = options.auto_reorder_for_nonzero_diagonal and not has_nonzero_diagonal(working)
    if fallback:
        match = find_nonzero_diagonal_permutation(system)
        if match is not None:
            permutation = match
            working = apply_row_permutation(system, permutation)
    if not has_nonzero_diagonal(working):
        raise InputError(
            ErrorCode.ZERO_PIVOT,
            "No safe diagonal is available under the accepted row-reordering options.",
        )
    return working, ReorderingDiagnostics(
        permutation=permutation,
        dominance_search_attempted=searched,
        dominance_matching_found=found,
        nonzero_search_attempted=fallback,
    )


def _sweep(system: FloatSystem, previous: FloatVector, method: IterativeMethod) -> FloatVector:
    # Python float is IEEE binary64 on the supported CPython 3.12 runtime.
    # A distinct buffer enforces Jacobi's old-vector-only dependency graph.
    next_vector = list(previous)
    for i, row in enumerate(system.a):
        source = previous if method == "jacobi" else next_vector
        contribution = math.fsum(
            finite_float(value * source[j]) for j, value in enumerate(row) if j != i
        )
        numerator = finite_float(system.b[i] - contribution)
        next_vector[i] = finite_float(numerator / row[i])
    return tuple(next_vector)


def solve_iterative(
    system: FloatSystem,
    *,
    method: IterativeMethod,
    options: IterationOptions | None = None,
) -> IterativeResult:
    if not isinstance(system, FloatSystem):
        raise InputError(
            ErrorCode.INVALID_SYSTEM, "Iterative solvers require parsed float64 input."
        )
    if method not in ("jacobi", "gauss_seidel"):
        raise InputError(ErrorCode.INVALID_SYSTEM, "Unknown iterative method.")
    options = IterationOptions() if options is None else IterationOptions.model_validate(options)
    n = require_square(system)
    initial = options.initial_guess if options.initial_guess is not None else (0.0,) * n
    if len(initial) != n:
        raise InputError(
            ErrorCode.INVALID_SYSTEM, "Initial guess length must equal the unknown count."
        )
    classification = classify_system(system)
    if classification.classification is not ClassificationKind.UNIQUE:
        raise InputError(
            ErrorCode.INVALID_SYSTEM, "Iteration requires a uniquely classified system."
        )
    working, reordering = _reorder(system, options)
    convergence = convergence_diagnostics(working, method)
    conditioning = condition_diagnostic(system)
    warnings: list[str] = []
    if reordering.dominance_matching_found is False:
        warnings.append("No strict diagonal-dominance row matching exists.")
    risk = convergence.assessment == "convergence_risk"
    if risk:
        warnings.append(convergence.explanation)
    if conditioning.status != "finite":
        warnings.append("A finite condition-number diagnostic is unavailable.")
    history: list[IterationRecord] = []
    vector = initial
    metrics: IterationMetrics | None = None
    reason = None
    status = IterationStatus.MAX_ITERATIONS_REACHED
    try:
        metrics = float_metrics(system, initial)
        if risk and not options.run_despite_convergence_risk:
            status = IterationStatus.CONVERGENCE_RISK_DECLINED
        else:
            for index in range(1, options.max_iterations + 1):
                candidate = _sweep(working, vector, method)
                candidate_metrics = float_metrics(system, candidate)
                record = iteration_record(
                    index, vector, candidate, candidate_metrics, options.tolerance
                )
                # Commit only a complete, finite iteration; partial sweeps are not history.
                history.append(record)
                vector, metrics = candidate, candidate_metrics
                if record.converged:
                    status = IterationStatus.CONVERGED
                    break
    except (ArithmeticError, ValueError) as exc:
        status = IterationStatus.NUMERIC_BREAKDOWN
        reason = (
            exc.message
            if isinstance(exc, SolverError)
            else "Iteration failed a finite-arithmetic, shape, or trace invariant."
        )
    return IterativeResult(
        method=method,
        classification=classification,
        options=options,
        initial_guess=initial,
        reordering=reordering,
        convergence=convergence,
        conditioning=conditioning,
        status=status,
        last_iterate=vector,
        solution=vector if status is IterationStatus.CONVERGED else None,
        history=tuple(history),
        diagnostics=metrics,
        breakdown_reason=reason,
        warnings=tuple(warnings),
    )
