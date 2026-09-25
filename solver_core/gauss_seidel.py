"""Gauss-Seidel iteration using updated components immediately within each sweep."""

from solver_core._iterative import solve_iterative
from solver_core.models import FloatSystem, IterationOptions, IterativeResult


def solve_gauss_seidel(
    system: FloatSystem,
    *,
    options: IterationOptions | None = None,
) -> IterativeResult:
    return solve_iterative(system, method="gauss_seidel", options=options)
