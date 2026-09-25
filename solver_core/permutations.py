"""Bounded bipartite row matching; column/variable order is never changed."""

from fractions import Fraction
from typing import overload

from solver_core._elimination import System, magnitude, total
from solver_core.errors import ErrorCode, InputError
from solver_core.models import ExactSystem, FloatSystem, RowPermutation
from solver_core.tolerance import tolerance_for


def require_square(system: System) -> int:
    if not system.shape.is_square:
        raise InputError(ErrorCode.INVALID_SYSTEM, "This operation requires a square matrix.")
    return system.shape.unknowns


def diagonal_dominance(system: System) -> tuple[bool, bool]:
    """Return (strict, weak); strict means every row satisfies a strict inequality."""
    n = require_square(system)
    zero = Fraction(0) if isinstance(system, ExactSystem) else 0.0
    margins = [
        (
            magnitude(system.a[i][i]),
            total((magnitude(system.a[i][j]) for j in range(n) if j != i), zero),
        )
        for i in range(n)
    ]
    return all(d > rest for d, rest in margins), all(d >= rest for d, rest in margins)


def has_nonzero_diagonal(system: System) -> bool:
    n = require_square(system)
    cutoff = tolerance_for(system).pivot_abs if isinstance(system, FloatSystem) else 0
    return all(magnitude(system.a[i][i]) > cutoff for i in range(n))


def _perfect_matching(edges: tuple[tuple[int, ...], ...]) -> tuple[int, ...] | None:
    """Augmenting paths, O(n^3), including reassignment of earlier matches."""
    n = len(edges)
    if all(i in edges[i] for i in range(n)):
        return tuple(range(n))
    position_for_row = [-1] * n

    def augment(position: int, visited: set[int]) -> bool:
        for row in edges[position]:
            if row in visited:
                continue
            visited.add(row)
            previous = position_for_row[row]
            if previous == -1 or augment(previous, visited):
                position_for_row[row] = position
                return True
        return False

    for position in range(n):
        if not augment(position, set()):
            return None
    order = [-1] * n
    for row, position in enumerate(position_for_row):
        order[position] = row
    return tuple(order)


def find_diagonal_dominance_permutation(system: System) -> RowPermutation | None:
    n = require_square(system)
    zero = Fraction(0) if isinstance(system, ExactSystem) else 0.0
    edges = tuple(
        tuple(
            row
            for row in range(n)
            if magnitude(system.a[row][column])
            > total((magnitude(system.a[row][j]) for j in range(n) if j != column), zero)
        )
        for column in range(n)
    )
    order = _perfect_matching(edges)
    return (
        None if order is None else RowPermutation(order=order, purpose="strict_diagonal_dominance")
    )


def find_nonzero_diagonal_permutation(system: System) -> RowPermutation | None:
    n = require_square(system)
    cutoff = tolerance_for(system).pivot_abs if isinstance(system, FloatSystem) else 0
    edges = tuple(
        tuple(row for row in range(n) if magnitude(system.a[row][column]) > cutoff)
        for column in range(n)
    )
    order = _perfect_matching(edges)
    return None if order is None else RowPermutation(order=order, purpose="nonzero_diagonal")


@overload
def apply_row_permutation(system: FloatSystem, permutation: RowPermutation) -> FloatSystem: ...


@overload
def apply_row_permutation(system: ExactSystem, permutation: RowPermutation) -> ExactSystem: ...


def apply_row_permutation(system: System, permutation: RowPermutation) -> System:
    if len(permutation.order) != system.shape.equations:
        raise InputError(ErrorCode.INVALID_SYSTEM, "Row mapping must match the equation count.")
    if isinstance(system, FloatSystem):
        return FloatSystem(
            a=tuple(system.a[i] for i in permutation.order),
            b=tuple(system.b[i] for i in permutation.order),
        )
    return ExactSystem(
        a=tuple(system.a[i] for i in permutation.order),
        b=tuple(system.b[i] for i in permutation.order),
    )
