"""Independent rank/classification fixtures and exact/float boundary cases."""

from fractions import Fraction

import numpy as np
import pytest

from solver_core.classification import classify_system
from solver_core.constants import MAX_RATIONAL_BITS
from solver_core.errors import ErrorCode, NumericBreakdownError, ResourceLimitError
from solver_core.models import ArithmeticMode, ClassificationKind, ExactSystem, FloatSystem
from solver_core.parsing import parse_system
from solver_core.tolerance import tolerance_for


@pytest.mark.parametrize("mode", list(ArithmeticMode))
@pytest.mark.parametrize(
    ("a", "b", "ranks", "kind"),
    [
        ([["2"]], ["4"], (1, 1), "unique"),
        ([["0"]], ["0"], (0, 0), "infinite"),
        ([["0"]], ["1"], (0, 1), "inconsistent"),
        ([["1", "2"], ["2", "4"]], ["3", "6"], (1, 1), "infinite"),
        ([["1", "2"], ["2", "4"]], ["3", "7"], (1, 2), "inconsistent"),
        ([["1", "0"], ["0", "1"], ["1", "1"]], ["2", "3", "5"], (2, 2), "unique"),
        ([["1", "0"], ["0", "1"], ["1", "1"]], ["2", "3", "6"], (2, 3), "inconsistent"),
        ([["1", "2", "3"], ["0", "1", "1"]], ["4", "2"], (2, 2), "infinite"),
        ([["0", "0"], ["0", "0"]], ["0", "2"], (0, 1), "inconsistent"),
        ([["0", "1", "0"], ["0", "0", "0"]], ["2", "0"], (1, 1), "infinite"),
    ],
)
def test_classification_of_square_and_rectangular_systems(a, b, ranks, kind, mode) -> None:
    system = parse_system(a, b, mode=mode)
    original = system.model_dump()
    result = classify_system(system)
    assert (result.rank_a, result.rank_augmented) == ranks
    assert result.classification.value == kind
    assert result.arithmetic_mode is mode
    assert system.model_dump() == original
    if mode is ArithmeticMode.EXACT:
        assert result.rank_tolerance is None
    else:
        assert result.rank_tolerance == tolerance_for(system).rank_abs


def test_effective_float_rank_is_distinct_from_exact_rank() -> None:
    a, b = [["1", "0"], ["0", "1e-100"]], ["1", "0"]
    floating = classify_system(parse_system(a, b))
    exact = classify_system(parse_system(a, b, mode=ArithmeticMode.EXACT))
    assert floating.classification is ClassificationKind.INFINITE
    assert exact.classification is ClassificationKind.UNIQUE


def test_tolerance_is_shared_and_equality_is_not_a_nonzero_singular_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline = parse_system([["1", "0"], ["0", "1"]], ["0", "0"])
    cutoff = tolerance_for(baseline).rank_abs
    system = FloatSystem(a=((1.0, 0.0), (0.0, cutoff)), b=(0.0, 0.0))
    calls = []

    def singular_values(matrix, *, compute_uv):
        calls.append(matrix.shape)
        assert compute_uv is False
        return np.array([1.0, cutoff])

    monkeypatch.setattr(np.linalg, "svd", singular_values)
    result = classify_system(system)
    assert calls == [(2, 2), (2, 3)]
    assert result.rank_a == result.rank_augmented == 1
    assert result.rank_tolerance == cutoff


def test_exact_rank_does_not_call_floating_linear_algebra(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args, **kwargs):
        pytest.fail("Exact classification called floating SVD")

    monkeypatch.setattr(np.linalg, "svd", forbidden)
    result = classify_system(parse_system([["1/3", "1/7"]], ["1/11"], mode=ArithmeticMode.EXACT))
    assert result.rank_a == result.rank_augmented == 1


def test_exact_classification_enforces_intermediate_growth() -> None:
    huge = Fraction(2 ** (MAX_RATIONAL_BITS - 1))
    system = ExactSystem(a=((huge, Fraction(1)), (Fraction(1), huge)), b=(Fraction(0), Fraction(0)))
    with pytest.raises(ResourceLimitError) as caught:
        classify_system(system)
    assert caught.value.code is ErrorCode.RATIONAL_GROWTH_LIMIT


def test_failed_svd_is_a_controlled_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args, **kwargs):
        raise np.linalg.LinAlgError("internal library detail")

    monkeypatch.setattr(np.linalg, "svd", fail)
    with pytest.raises(NumericBreakdownError) as caught:
        classify_system(parse_system([["1"]], ["2"]))
    assert caught.value.code is ErrorCode.RANK_UNCERTAIN
    assert "internal library detail" not in str(caught.value)


def test_nonfinite_svd_output_is_not_serialized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(np.linalg, "svd", lambda *args, **kwargs: np.array([np.inf]))
    with pytest.raises(NumericBreakdownError) as caught:
        classify_system(parse_system([["1"]], ["2"]))
    assert caught.value.code is ErrorCode.NON_FINITE_VALUE


def test_incoherent_rank_estimates_are_not_silently_repaired(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = iter([np.array([1.0, 1.0]), np.array([1.0, 0.0])])
    monkeypatch.setattr(np.linalg, "svd", lambda *args, **kwargs: next(values))
    with pytest.raises(NumericBreakdownError) as caught:
        classify_system(parse_system([["1", "0"], ["0", "1"]], ["0", "0"]))
    assert caught.value.code is ErrorCode.RANK_UNCERTAIN


def test_large_rhs_roundoff_cannot_publish_a_false_inconsistent_classification() -> None:
    a = [["1", "0"], ["0", "1"], ["1", "1"]]
    b = ["400000000000", "400000000000", "800000000000"]
    # Different LAPACK builds may resolve the tiny augmented singular value
    # differently. A correct unique result or an explicit uncertainty is safe.
    try:
        result = classify_system(parse_system(a, b))
    except NumericBreakdownError as error:
        assert error.code is ErrorCode.RANK_UNCERTAIN
    else:
        assert result.classification is ClassificationKind.UNIQUE
    exact = classify_system(parse_system(a, b, mode=ArithmeticMode.EXACT))
    assert exact.classification is ClassificationKind.UNIQUE
