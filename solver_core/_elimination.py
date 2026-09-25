"""Shared, handwritten row operations with bounded arithmetic and replayable traces.

This private implementation has no dependency on classification or a web layer.
Exact classification can reuse forward reduction without a circular dependency.
"""

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Literal

from solver_core.constants import MAX_RATIONAL_BITS, MAX_TRACE_VALUE_CHARS
from solver_core.errors import ErrorCode, NumericBreakdownError, ResourceLimitError
from solver_core.models import ExactSystem, FloatSystem, RowOperation
from solver_core.tolerance import TolerancePolicy, tolerance_for

type Scalar = float | Fraction
type Matrix = tuple[tuple[Scalar, ...], ...]
type System = FloatSystem | ExactSystem


def checked(value: Scalar) -> Scalar:
    """Guard every arithmetic intermediate, not just stored row snapshots."""
    if isinstance(value, Fraction):
        if max(value.numerator.bit_length(), value.denominator.bit_length()) > MAX_RATIONAL_BITS:
            raise ResourceLimitError(
                ErrorCode.RATIONAL_GROWTH_LIMIT,
                "Exact arithmetic exceeded 4096 bits; use float64 mode.",
            )
    elif not math.isfinite(value):
        raise NumericBreakdownError(
            ErrorCode.NON_FINITE_VALUE, "A row operation or diagnostic overflowed float64."
        )
    return value


def magnitude(value: Scalar) -> Scalar:
    if isinstance(value, Fraction):
        return abs(value)
    return abs(value)


def add(left: Scalar, right: Scalar) -> Scalar:
    return checked(left + right)


def multiply(left: Scalar, right: Scalar) -> Scalar:
    return checked(left * right)


def divide(left: Scalar, right: Scalar) -> Scalar:
    if right == 0:
        raise NumericBreakdownError(ErrorCode.ZERO_PIVOT, "Unexpected zero pivot during reduction.")
    return checked(left / right)


def total(values: Iterable[Scalar], zero: Scalar) -> Scalar:
    if isinstance(zero, float):
        try:
            return checked(math.fsum(float(checked(value)) for value in values))
        except OverflowError:
            raise NumericBreakdownError(
                ErrorCode.NON_FINITE_VALUE, "A sum overflowed float64."
            ) from None
    result: Scalar = zero
    for value in values:
        result = add(result, value)
    return result


@dataclass(slots=True)
class Reduction:
    matrix: list[list[Scalar]]
    unknowns: int
    zero: Scalar
    one: Scalar
    policy: TolerancePolicy | None
    record_trace: bool
    pivots: list[int] = field(default_factory=list)
    trace: list[RowOperation] = field(default_factory=list)
    # Per-row absolute zero cutoffs transformed with the row operations. They
    # are comparison metadata, not mathematical error bounds or matrix entries.
    row_tolerances: list[float] = field(default_factory=list)
    trace_value_chars: int = 0

    def snapshot(self) -> Matrix:
        return tuple(tuple(row) for row in self.matrix)

    def record(
        self,
        operation: Literal["row_swap", "row_add_scaled", "row_scale"],
        target: int,
        source: int | None,
        column: int,
        factor: Scalar | None,
        phase: Literal["forward_elimination", "backward_elimination"],
    ) -> None:
        if not self.record_trace:
            return

        def text_size(value: Scalar) -> int:
            if isinstance(value, Fraction):
                return len(str(value.numerator)) + len(str(value.denominator))
            return len(repr(value))

        added_chars = sum(text_size(value) for row in self.matrix for value in row)
        if factor is not None:
            added_chars += text_size(factor)
        if self.trace_value_chars + added_chars > MAX_TRACE_VALUE_CHARS:
            raise ResourceLimitError(
                ErrorCode.TRACE_LIMIT,
                "Full row-operation trace exceeded its budget; "
                "use a smaller system or float64 mode.",
            )
        self.trace_value_chars += added_chars
        if operation == "row_swap":
            explanation = f"Swap rows {target + 1} and {source + 1 if source is not None else 0}."
        elif operation == "row_scale":
            explanation = f"Scale row {target + 1} to normalize its pivot in column {column + 1}."
        else:
            explanation = (
                f"Add the recorded multiple of row {source + 1 if source is not None else 0} "
                f"to row {target + 1} to eliminate column {column + 1}."
            )
        self.trace.append(
            RowOperation(
                index=len(self.trace),
                phase=phase,
                operation_type=operation,
                target_row=target,
                source_row=source,
                pivot_column=column,
                factor=factor,
                matrix_after=self.snapshot(),
                explanation=explanation,
            )
        )

    def swap(self, target: int, source: int, column: int) -> None:
        self.matrix[target], self.matrix[source] = self.matrix[source], self.matrix[target]
        if self.policy is not None:
            self.row_tolerances[target], self.row_tolerances[source] = (
                self.row_tolerances[source],
                self.row_tolerances[target],
            )
        self.record("row_swap", target, source, column, None, "forward_elimination")

    def add_row(
        self,
        target: int,
        source: int,
        column: int,
        factor: Scalar,
        phase: Literal["forward_elimination", "backward_elimination"],
    ) -> None:
        self.matrix[target] = [
            add(value, multiply(factor, other))
            for value, other in zip(self.matrix[target], self.matrix[source], strict=True)
        ]
        if self.policy is not None:
            self.row_tolerances[target] = float(
                checked(
                    self.row_tolerances[target] + abs(float(factor)) * self.row_tolerances[source]
                )
            )
        self.record("row_add_scaled", target, source, column, factor, phase)

    def scale_row(self, row: int, column: int, factor: Scalar) -> None:
        self.matrix[row] = [multiply(value, factor) for value in self.matrix[row]]
        if self.policy is not None:
            self.row_tolerances[row] = float(checked(self.row_tolerances[row] * abs(float(factor))))
        self.record("row_scale", row, None, column, factor, "backward_elimination")

    def contradictory_rows(self) -> tuple[int, ...]:
        def zero(value: Scalar, row: int) -> bool:
            if self.policy is None:
                return value == 0
            return magnitude(value) <= self.row_tolerances[row]

        return tuple(
            i
            for i, row in enumerate(self.matrix)
            if all(zero(value, i) for value in row[:-1]) and not zero(row[-1], i)
        )


def forward_reduce(system: System, *, record_trace: bool = True) -> Reduction:
    """Row-echelon form of the full augmented matrix; no variable permutation."""
    exact = isinstance(system, ExactSystem)
    policy = None if isinstance(system, ExactSystem) else tolerance_for(system)
    coefficients: Matrix = system.a
    rhs_values: tuple[Scalar, ...] = system.b
    work = Reduction(
        matrix=[list(row) + [rhs] for row, rhs in zip(coefficients, rhs_values, strict=True)],
        unknowns=system.shape.unknowns,
        zero=Fraction(0) if exact else 0.0,
        one=Fraction(1) if exact else 1.0,
        policy=policy,
        record_trace=record_trace,
        row_tolerances=[] if policy is None else [policy.rank_abs] * system.shape.equations,
    )
    for column in range(work.unknowns + 1):
        target = len(work.pivots)
        if target == len(work.matrix):
            break
        # Mandatory partial pivoting for float; also deterministic in exact mode.
        source = max(
            range(target, len(work.matrix)), key=lambda i: magnitude(work.matrix[i][column])
        )
        candidate = work.matrix[source][column]
        cutoff = 0.0
        if policy is not None:
            cutoff = max(
                policy.rank_abs,
                policy.pivot_threshold(
                    [float(work.matrix[i][column]) for i in range(target, len(work.matrix))]
                ),
            )
        if magnitude(candidate) <= cutoff:
            continue
        if source != target:
            work.swap(target, source, column)
        work.pivots.append(column)
        for row in range(target + 1, len(work.matrix)):
            if work.matrix[row][column] == 0:
                continue
            factor = checked(-divide(work.matrix[row][column], work.matrix[target][column]))
            work.add_row(row, target, column, factor, "forward_elimination")
    return work


def reduce_above_pivots(work: Reduction) -> None:
    """Complete augmented RREF, including an RHS pivot for inconsistent systems."""
    for row in reversed(range(len(work.pivots))):
        column = work.pivots[row]
        pivot = work.matrix[row][column]
        if pivot != work.one:
            work.scale_row(row, column, divide(work.one, pivot))
        for target in range(row):
            if work.matrix[target][column] == 0:
                continue
            factor = checked(-divide(work.matrix[target][column], work.matrix[row][column]))
            work.add_row(target, row, column, factor, "backward_elimination")
