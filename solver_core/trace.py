"""Versioned trace serialization preserving full precision and structured rationals."""

from fractions import Fraction
from typing import Literal

from pydantic import Field

from solver_core.constants import MAX_ITERATIONS, MAX_TRACE_VALUE_CHARS
from solver_core.errors import ErrorCode, ResourceLimitError
from solver_core.models import (
    ArithmeticMode,
    DirectResult,
    DomainModel,
    IterationRecord,
    IterativeResult,
    RowOperation,
)


class DirectTrace(DomainModel):
    schema_version: Literal[1] = 1
    kind: Literal["direct"] = "direct"
    method: Literal["gaussian", "gauss_jordan"]
    arithmetic_mode: ArithmeticMode
    operations: tuple[RowOperation, ...]


class IterativeTrace(DomainModel):
    schema_version: Literal[1] = 1
    kind: Literal["iterative"] = "iterative"
    method: Literal["jacobi", "gauss_seidel"]
    arithmetic_mode: Literal[ArithmeticMode.FLOAT64] = ArithmeticMode.FLOAT64
    iterations: tuple[IterationRecord, ...] = Field(max_length=MAX_ITERATIONS)


def build_trace(result: DirectResult | IterativeResult) -> DirectTrace | IterativeTrace:
    """Enforce the same numeric payload budget for standalone traces as for solving."""
    if isinstance(result, DirectResult):
        size = 0
        for operation in result.trace:
            values = [v for row in operation.matrix_after for v in row]
            if operation.factor is not None:
                values.append(operation.factor)
            size += sum(
                len(str(v.numerator)) + len(str(v.denominator))
                if isinstance(v, Fraction)
                else len(repr(v))
                for v in values
            )
        trace: DirectTrace | IterativeTrace = DirectTrace(
            method=result.method, arithmetic_mode=result.arithmetic_mode, operations=result.trace
        )
    else:
        size = sum(
            sum(
                len(repr(v))
                for v in (
                    *record.vector,
                    record.delta_inf,
                    record.normalized_step_change,
                    record.residual_inf,
                    record.backward_error,
                )
            )
            for record in result.history
        )
        trace = IterativeTrace(method=result.method, iterations=result.history)
    if size > MAX_TRACE_VALUE_CHARS:
        raise ResourceLimitError(ErrorCode.TRACE_LIMIT, "Trace exceeds the numeric payload budget.")
    return trace


def serialize_trace(result: DirectResult | IterativeResult) -> str:
    """Numbers remain binary64 or numerator/denominator strings; never formatted HTML."""
    return build_trace(result).model_dump_json()
