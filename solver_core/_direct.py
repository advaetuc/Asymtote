"""Shared result assembly, back substitution, and original-system residuals."""

from typing import Literal

from solver_core._elimination import (
    Reduction,
    Scalar,
    System,
    add,
    checked,
    divide,
    forward_reduce,
    multiply,
    reduce_above_pivots,
    total,
)
from solver_core.classification import classify_system
from solver_core.diagnostics import solution_diagnostics
from solver_core.errors import ErrorCode, NumericBreakdownError
from solver_core.models import (
    ClassificationKind,
    DirectResult,
    ParameterTerm,
    ParametricSolution,
    VariableExpression,
)


def _back_substitute(work: Reduction, free_column: int | None = None) -> tuple[Scalar, ...]:
    """Use pivot-column indices, including when free columns precede pivots."""
    vector = [work.zero] * work.unknowns
    if free_column is not None:
        vector[free_column] = work.one
    for row in reversed(range(len(work.pivots))):
        column = work.pivots[row]
        rhs = work.matrix[row][-1] if free_column is None else work.zero
        contribution = total(
            (
                multiply(value, vector[j])
                for j, value in enumerate(work.matrix[row][:-1])
                if j != column
            ),
            work.zero,
        )
        vector[column] = divide(add(rhs, checked(-contribution)), work.matrix[row][column])
    return tuple(vector)


def solve_direct(system: System, *, method: Literal["gaussian", "gauss_jordan"]) -> DirectResult:
    classification = classify_system(system)
    work = forward_reduce(system)
    pivots = tuple(column for column in work.pivots if column < work.unknowns)
    free = tuple(column for column in range(work.unknowns) if column not in pivots)
    if len(pivots) != classification.rank_a or len(work.pivots) != classification.rank_augmented:
        raise NumericBreakdownError(
            ErrorCode.RANK_UNCERTAIN,
            "Singular-value rank and elimination pivots disagree at the numerical cutoff; "
            "rescale the input or use exact mode.",
        )
    if method == "gauss_jordan":
        reduce_above_pivots(work)
    contradictions = work.contradictory_rows()
    inconsistent = classification.classification is ClassificationKind.INCONSISTENT
    if bool(contradictions) != inconsistent:
        raise NumericBreakdownError(
            ErrorCode.RANK_UNCERTAIN,
            "Rank classification and reduced-row consistency disagree; use exact mode.",
        )

    solution = None
    parametric = None
    diagnostics = None
    if not inconsistent:
        particular = _back_substitute(work)
        diagnostics = solution_diagnostics(system, particular)
        if not free:
            solution = particular
        else:
            basis = tuple(_back_substitute(work, column) for column in free)
            parametric = ParametricSolution(
                pivot_variables=pivots,
                free_variables=free,
                expressions=tuple(
                    VariableExpression(
                        variable=f"x{j + 1}",
                        constant=particular[j],
                        terms=tuple(
                            ParameterTerm(parameter=f"t{k + 1}", coefficient=vector[j])
                            for k, vector in enumerate(basis)
                            if vector[j] != 0
                        ),
                    )
                    for j in range(work.unknowns)
                ),
            )
    warnings = (
        ("Classification and reduced form use floating tolerances; tiny entries remain unrounded.",)
        if work.policy is not None
        else ()
    )
    return DirectResult(
        method=method,
        arithmetic_mode=classification.arithmetic_mode,
        classification=classification,
        form="ref" if method == "gaussian" else "rref",
        matrix=work.snapshot(),
        pivot_columns=pivots,
        free_columns=free,
        augmented_pivot_columns=tuple(work.pivots),
        solution=solution,
        parametric_solution=parametric,
        contradictory_rows=contradictions,
        row_tolerances=tuple(work.row_tolerances) if work.policy is not None else None,
        trace=tuple(work.trace),
        diagnostics=diagnostics,
        warnings=warnings,
    )
