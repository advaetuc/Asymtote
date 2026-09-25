from fractions import Fraction
from itertools import permutations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from solver_core.errors import InputError
from solver_core.models import ArithmeticMode, RowPermutation
from solver_core.parsing import parse_system
from solver_core.permutations import (
    apply_row_permutation,
    diagonal_dominance,
    find_diagonal_dominance_permutation,
    find_nonzero_diagonal_permutation,
    has_nonzero_diagonal,
)


@pytest.mark.parametrize("mode", list(ArithmeticMode))
def test_dominance_matching_preserves_rhs_and_variables(mode):
    system = parse_system(
        [["1", "8", "1"], ["1", "1", "9"], ["7", "1", "1"]], ["10", "11", "9"], mode=mode
    )
    original = system.a, system.b
    match = find_diagonal_dominance_permutation(system)
    assert match.order == (2, 0, 1)
    reordered = apply_row_permutation(system, match)
    assert diagonal_dominance(reordered) == (True, True)
    assert reordered.a == (system.a[2], system.a[0], system.a[1])
    assert reordered.b == (system.b[2], system.b[0], system.b[1])
    assert (system.a, system.b) == original


def test_nonzero_matching_uses_augmenting_paths_not_greedy_rows():
    # Position zero must relinquish row zero so position one can use it.
    system = parse_system([["1", "1", "0"], ["1", "0", "0"], ["0", "0", "1"]], ["2", "1", "1"])
    assert find_diagonal_dominance_permutation(system) is None
    match = find_nonzero_diagonal_permutation(system)
    assert match.order == (1, 0, 2)
    assert has_nonzero_diagonal(apply_row_permutation(system, match))


def test_no_perfect_matching_even_when_every_column_has_an_edge():
    system = parse_system([["1", "1", "0"], ["0", "0", "1"], ["0", "0", "1"]], ["0", "0", "0"])
    assert find_nonzero_diagonal_permutation(system) is None


def test_strict_dominance_does_not_accept_weak_dominance():
    system = parse_system([["1", "1"], ["1", "1"]], ["0", "0"])
    assert diagonal_dominance(system) == (False, True)
    assert find_diagonal_dominance_permutation(system) is None
    assert find_nonzero_diagonal_permutation(system).order == (0, 1)


def test_float_nonzero_matching_uses_pivot_policy_but_exact_uses_exact_zero():
    a, b = [["1e-20", "0"], ["0", "1"]], ["0", "0"]
    assert find_nonzero_diagonal_permutation(parse_system(a, b)) is None
    exact = parse_system(a, b, mode=ArithmeticMode.EXACT)
    assert find_nonzero_diagonal_permutation(exact).order == (0, 1)
    assert exact.a[0][0] == Fraction(1, 10**20)


@pytest.mark.parametrize("scale", ["1e-100", "1", "1e12"])
def test_nonzero_cutoff_has_no_absolute_one_floor(scale):
    assert has_nonzero_diagonal(parse_system([[scale]], ["0"]))


@pytest.mark.parametrize(
    "utility",
    [
        diagonal_dominance,
        find_diagonal_dominance_permutation,
        find_nonzero_diagonal_permutation,
        has_nonzero_diagonal,
    ],
)
def test_matching_rejects_rectangular_input(utility):
    with pytest.raises(InputError):
        utility(parse_system([["1", "2"]], ["3"]))


@pytest.mark.parametrize("order", [(0, 0), (1, 2), (-1, 0), ()])
def test_invalid_mapping_is_rejected(order):
    with pytest.raises(ValidationError):
        RowPermutation(order=order, purpose="nonzero_diagonal")


def test_apply_rejects_wrong_mapping_length():
    with pytest.raises(InputError):
        apply_row_permutation(
            parse_system([["1"]], ["1"]), RowPermutation(order=(0, 1), purpose="identity")
        )


@given(st.lists(st.integers(-2, 2), min_size=9, max_size=9))
@settings(max_examples=80)
def test_matching_agrees_with_exhaustive_oracle(entries):
    a = [entries[i : i + 3] for i in range(0, 9, 3)]
    system = parse_system([[str(v) for v in row] for row in a], ["0"] * 3)
    for strict in (True, False):

        def eligible(row, col, require_strict=strict):
            return (
                (abs(a[row][col]) > sum(abs(a[row][j]) for j in range(3) if j != col))
                if require_strict
                else a[row][col] != 0
            )

        exists = any(
            all(eligible(order[j], j) for j in range(3)) for order in permutations(range(3))
        )
        find = find_diagonal_dominance_permutation if strict else find_nonzero_diagonal_permutation
        match = find(system)
        assert (match is not None) == exists
        if match is not None:
            assert all(eligible(match.order[j], j) for j in range(3))
