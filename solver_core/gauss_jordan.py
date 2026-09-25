"""Gauss-Jordan reduction, free-variable structure, and contradictory-row witnesses."""

from solver_core._direct import solve_direct
from solver_core.models import DirectResult, ExactSystem, FloatSystem


def solve_gauss_jordan(system: FloatSystem | ExactSystem) -> DirectResult:
    """Return augmented RREF and a unique, parametric, or inconsistent outcome."""
    return solve_direct(system, method="gauss_jordan")
