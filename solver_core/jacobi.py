"""Jacobi iteration with an independent old-vector buffer and dual stopping tests."""

from solver_core._iterative import solve_iterative
from solver_core.models import FloatSystem, IterationOptions, IterativeResult


def solve_jacobi(
    system: FloatSystem, *, options: IterationOptions | None = None
) -> IterativeResult:
    return solve_iterative(system, method="jacobi", options=options)
