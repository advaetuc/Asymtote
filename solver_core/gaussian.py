"""Gaussian elimination with partial pivoting and pivot-aware back substitution."""

from solver_core._direct import solve_direct
from solver_core.models import DirectResult, ExactSystem, FloatSystem


def solve_gaussian(system: FloatSystem | ExactSystem) -> DirectResult:
    """Solve/classify a rectangular system, preserving input and every row operation."""
    return solve_direct(system, method="gaussian")
