"""Strict input grammar, bounded exactness, shape validation, and model boundaries."""

import json
import math
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from solver_core.constants import MAX_RATIONAL_BITS, MAX_TOKEN_CHARS
from solver_core.errors import ErrorCode, InputError, ResourceLimitError, SolverError
from solver_core.models import (
    ArithmeticMode,
    DisplaySettings,
    ExactSystem,
    FloatSystem,
    IterationSettings,
    RationalValue,
    SystemTokens,
)
from solver_core.parsing import parse_exact, parse_float, parse_system


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("0", Fraction(0)),
        ("-0", Fraction(0)),
        ("+12", Fraction(12)),
        ("00012", Fraction(12)),
        ("-2", Fraction(-2)),
        ("0.1", Fraction(1, 10)),
        (".125", Fraction(1, 8)),
        ("1.", Fraction(1)),
        ("-.5", Fraction(-1, 2)),
        ("+1.25e+2", Fraction(125)),
        ("2.5e-4", Fraction(1, 4000)),
        ("3E2", Fraction(300)),
        ("1.e2", Fraction(100)),
        ("1/3", Fraction(1, 3)),
        ("-2/4", Fraction(-1, 2)),
        ("2/-4", Fraction(-1, 2)),
        ("-2/-4", Fraction(1, 2)),
        ("1/+2", Fraction(1, 2)),
        ("0/-2", Fraction(0)),
        ("1e-100", Fraction(1, 10**100)),
        ("999e-100", Fraction(999, 10**100)),
        ("1000000000000", Fraction(10**12)),
    ],
)
def test_supported_tokens_are_exact_and_float_conversion_is_unrounded(
    token: str, expected: Fraction
) -> None:
    assert parse_exact(token) == expected
    assert parse_float(token) == float(expected)


@pytest.mark.parametrize(
    "token",
    [
        " ",
        " 1",
        "1 ",
        "1\n",
        "\t1",
        "1\x00",
        "1 2",
        "1 /2",
        "1/ 2",
        "NaN",
        "nan",
        "Inf",
        "Infinity",
        "-Infinity",
        "1+2",
        "2**3",
        "2*3",
        "1//2",
        "1/2/3",
        "1.0/2",
        "1/2.0",
        "1e2/3",
        "x",
        "sqrt(4)",
        "__import__('os').system('echo bad')",
        "[1]",
        "(2)",
        "1j",
        "1,000",
        "1_000",
        "0x10",
        "0b10",
        ".",
        "+",
        "-",
        "--1",
        "1e",
        "1e+",
        "1e1.5",
        "1e2e3",
        "１２",
        "١٢",
        "−1",
        "1\u00a0",
        "1\u200b",
    ],
)
def test_rejects_non_grammar_tokens(token: str) -> None:
    with pytest.raises(InputError) as caught:
        parse_exact(token)
    assert caught.value.code is ErrorCode.INVALID_TOKEN


@pytest.mark.parametrize("token", [None, True, 1, 1.0, float("nan"), b"1", Fraction(1, 3), []])
def test_never_coerces_non_string_tokens(token: object) -> None:
    with pytest.raises(InputError) as caught:
        parse_float(token)
    assert caught.value.code is ErrorCode.TOKEN_TYPE


def test_empty_and_length_limits() -> None:
    with pytest.raises(InputError) as caught:
        parse_exact("")
    assert caught.value.code is ErrorCode.EMPTY_TOKEN
    assert parse_exact("0" * (MAX_TOKEN_CHARS - 1) + "1") == 1
    with pytest.raises(ResourceLimitError) as caught_long:
        parse_exact("0" * MAX_TOKEN_CHARS + "1")
    assert caught_long.value.code is ErrorCode.TOKEN_TOO_LONG


@pytest.mark.parametrize("token", ["1/0", "0/0", "-3/-0", "2/+000"])
def test_zero_denominators_have_a_domain_error(token: str) -> None:
    with pytest.raises(InputError) as caught:
        parse_exact(token)
    assert caught.value.code is ErrorCode.ZERO_DENOMINATOR


@pytest.mark.parametrize("token", ["1e101", "1e-101", "0e1000000000", "1e" + "9" * 46])
def test_exponent_limit_is_checked_before_constructing_fraction(
    token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden_fraction(*args: object, **kwargs: object) -> Fraction:
        pytest.fail("Unsafe exponent reached Fraction construction")

    monkeypatch.setattr("solver_core.parsing.Fraction", forbidden_fraction)
    with pytest.raises(ResourceLimitError) as caught:
        parse_exact(token)
    assert caught.value.code is ErrorCode.EXPONENT_OUT_OF_RANGE


@pytest.mark.parametrize("token", ["1000000000001", "-1000000000001", "1e13", "0.1e-100"])
def test_magnitude_limits_are_applied_to_exact_values(token: str) -> None:
    with pytest.raises(InputError) as caught:
        parse_float(token)
    assert caught.value.code is ErrorCode.MAGNITUDE_OUT_OF_RANGE


def test_rounding_cannot_hide_an_out_of_bounds_value() -> None:
    token = "1000000000000.0000000000000001"
    assert float(token) == 1e12
    with pytest.raises(InputError):
        parse_exact(token)


def test_exact_decimal_is_not_created_from_float() -> None:
    assert parse_exact("0.1") == Fraction(1, 10)
    assert parse_exact("0.1") != Fraction(0.1)
    assert parse_float("1/3") != round(1 / 3, 6)
    assert parse_float("1e-100") != 0.0


@pytest.mark.parametrize(("m", "n"), [(1, 1), (1, 12), (12, 1), (12, 12), (2, 3), (3, 2)])
def test_independent_rectangular_dimensions(m: int, n: int) -> None:
    system = parse_system([["1"] * n for _ in range(m)], ["2"] * m)
    assert isinstance(system, FloatSystem)
    assert system.shape.equations == m
    assert system.shape.unknowns == n
    assert system.shape.is_square is (m == n)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ([], []),
        ([[]], ["1"]),
        ([["1"]] * 13, ["1"] * 13),
        ([["1"] * 13], ["1"]),
        ([["1"], ["1", "2"]], ["1", "2"]),
        ([["1"]], []),
        ([["1"]], ["1", "2"]),
        ("1", ["1"]),
        ([["1"]], "1"),
        (["12"], ["1"]),
        ([["1"]], {"b": "1"}),
    ],
)
def test_invalid_shapes_are_controlled_domain_errors(a: object, b: object) -> None:
    with pytest.raises(InputError):
        parse_system(a, b)


def test_unbounded_iterables_are_not_consumed() -> None:
    def hostile_iterator():
        pytest.fail("Untrusted generator was consumed")
        yield ["1"]

    with pytest.raises(InputError):
        parse_system(hostile_iterator(), ["1"])


@pytest.mark.parametrize(
    ("a", "b", "code", "location"),
    [
        ([["1", "1/0"]], ["1"], ErrorCode.ZERO_DENOMINATOR, ("a", 0, 1)),
        ([["1"]], ["NaN"], ErrorCode.INVALID_TOKEN, ("b", 0)),
        ([[1]], ["1"], ErrorCode.TOKEN_TYPE, ("a", 0, 0)),
        ([["1"]], ["0" * 49], ErrorCode.TOKEN_TOO_LONG, ("b", 0)),
        ([["1"]], [""], ErrorCode.EMPTY_TOKEN, ("b", 0)),
    ],
)
def test_system_errors_locate_the_cell(
    a: object, b: object, code: ErrorCode, location: tuple[str | int, ...]
) -> None:
    with pytest.raises(SolverError) as caught:
        parse_system(a, b)
    assert caught.value.code is code
    assert caught.value.location == location


def test_input_spelling_and_nested_immutability() -> None:
    a, b = [["+01.00", "1/3"]], ["2"]
    tokens = SystemTokens.model_validate({"a": a, "b": b})
    exact = parse_system(a, b, mode=ArithmeticMode.EXACT)
    a[0][0] = "99"
    b[0] = "99"
    assert tokens.a == (("+01.00", "1/3"),)
    assert exact.a == ((Fraction(1), Fraction(1, 3)),)
    assert exact.b == (Fraction(2),)
    with pytest.raises(ValidationError):
        tokens.a = (("2",),)
    with pytest.raises(TypeError):
        exact.a[0][0] = Fraction(2)  # type: ignore[index]


def test_models_forbid_extra_fields_and_numeric_coercion() -> None:
    with pytest.raises(ValidationError):
        SystemTokens.model_validate({"a": [["1"]], "b": ["2"], "extra": True})
    for value in (0.1, "1/10", 1, True):
        with pytest.raises(ValidationError):
            ExactSystem.model_validate({"a": [[value]], "b": [Fraction(1)]})
    for value in ("1", 1, True, math.inf, math.nan):
        with pytest.raises(ValidationError):
            FloatSystem.model_validate({"a": [[value]], "b": [1.0]})


def test_exact_growth_limit_and_canonical_rationals() -> None:
    permitted = Fraction(2 ** (MAX_RATIONAL_BITS - 1), 1)
    assert RationalValue.from_fraction(permitted).as_fraction() == permitted
    with pytest.raises(ValidationError):
        RationalValue.from_fraction(Fraction(2**MAX_RATIONAL_BITS, 1))
    with pytest.raises(ValidationError):
        ExactSystem(a=((Fraction(1, 2**MAX_RATIONAL_BITS),),), b=(Fraction(1),))
    for numerator, denominator in ((2, 4), (0, 2), (1, 0), (1, -2)):
        with pytest.raises(ValidationError):
            RationalValue(numerator=numerator, denominator=denominator)


def test_exact_json_preserves_integers_above_javascript_safe_range() -> None:
    system = parse_system([["9007199254740993/10000000000"]], ["1/3"], mode=ArithmeticMode.EXACT)
    assert system.b == (Fraction(1, 3),)
    payload = json.loads(system.model_dump_json())
    assert payload["a"][0][0] == {"numerator": "9007199254740993", "denominator": "10000000000"}
    assert payload["b"][0] == {"numerator": "1", "denominator": "3"}


def test_settings_validate_defaults_limits_and_types() -> None:
    assert IterationSettings().max_iterations == 25
    assert IterationSettings().tolerance == 1e-8
    assert DisplaySettings().decimal_places == 6
    for value in (0, 501, True, "25"):
        with pytest.raises(ValidationError):
            IterationSettings.model_validate({"max_iterations": value})
    for value in (0.0, 1e-15, 0.1, math.nan, math.inf, "1e-8", True):
        with pytest.raises(ValidationError):
            IterationSettings.model_validate({"tolerance": value})
    for value in (-1, 13, True, "6"):
        with pytest.raises(ValidationError):
            DisplaySettings.model_validate({"decimal_places": value})


@given(st.integers(-(10**10), 10**10), st.integers(1, 10**10))
def test_rational_property_matches_independent_integer_construction(
    numerator: int, denominator: int
) -> None:
    token = f"{numerator}/{denominator}"
    expected = Fraction(numerator, denominator)
    assert parse_exact(token) == expected
    assert parse_float(token) == float(expected)


@given(st.integers(-(10**6), 10**6), st.integers(0, 12))
def test_scientific_property_preserves_exact_decimal_value(coefficient: int, places: int) -> None:
    assert parse_exact(f"{coefficient}e-{places}") == Fraction(coefficient, 10**places)


@given(st.text(max_size=60))
def test_arbitrary_text_either_parses_finitely_or_raises_a_domain_error(token: str) -> None:
    try:
        value = parse_float(token)
    except SolverError:
        return
    assert math.isfinite(value)
    assert abs(value) <= 1e12
