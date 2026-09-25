"""A bounded ASCII numeric grammar, parsed exactly before optional float conversion."""

import math
import re
from fractions import Fraction
from typing import Literal, overload

from pydantic import ValidationError

from solver_core.constants import (
    MAX_ABS_EXPONENT,
    MAX_ABS_INPUT,
    MAX_TOKEN_CHARS,
    MIN_NONZERO_INPUT_DENOMINATOR,
)
from solver_core.errors import ErrorCode, ErrorLocation, InputError, ResourceLimitError
from solver_core.models import ArithmeticMode, ExactSystem, FloatSystem, SystemTokens

_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE]([+-]?[0-9]+))?")
_RATIONAL = re.compile(r"([+-]?[0-9]+)/([+-]?[0-9]+)")
_MIN_NONZERO = Fraction(1, MIN_NONZERO_INPUT_DENOMINATOR)


def parse_exact(token: object, *, location: ErrorLocation = ()) -> Fraction:
    """Parse one token without evaluating expressions or passing through float.

    Whitespace (including trailing newlines), underscores, Unicode digits/signs,
    decimal denominators, and expression syntax are intentionally rejected.
    """
    if not isinstance(token, str):
        raise InputError(ErrorCode.TOKEN_TYPE, "Numeric tokens must be strings.", location=location)
    if len(token) > MAX_TOKEN_CHARS:
        raise ResourceLimitError(
            ErrorCode.TOKEN_TOO_LONG,
            f"Numeric tokens may contain at most {MAX_TOKEN_CHARS} characters.",
            location=location,
        )
    if not token:
        raise InputError(ErrorCode.EMPTY_TOKEN, "Numeric cells cannot be empty.", location=location)

    rational = _RATIONAL.fullmatch(token)
    if rational is not None:
        denominator = int(rational.group(2))
        if denominator == 0:
            raise InputError(
                ErrorCode.ZERO_DENOMINATOR, "A denominator cannot be zero.", location=location
            )
        value = Fraction(int(rational.group(1)), denominator)
    else:
        decimal = _DECIMAL.fullmatch(token)
        if decimal is None:
            raise InputError(
                ErrorCode.INVALID_TOKEN,
                "Expected an ASCII integer, decimal, scientific decimal, or integer/integer.",
                location=location,
            )
        exponent = decimal.group(1)
        if exponent is not None and abs(int(exponent)) > MAX_ABS_EXPONENT:
            raise ResourceLimitError(
                ErrorCode.EXPONENT_OUT_OF_RANGE,
                f"The scientific exponent must be between {-MAX_ABS_EXPONENT} and "
                f"{MAX_ABS_EXPONENT}.",
                location=location,
            )
        # Fraction's broader grammar is unreachable until our full-match checks pass.
        value = Fraction(token)

    magnitude = abs(value)
    if magnitude > MAX_ABS_INPUT or (value != 0 and magnitude < _MIN_NONZERO):
        raise InputError(
            ErrorCode.MAGNITUDE_OUT_OF_RANGE,
            "Input must be zero or have magnitude between 1e-100 and 1e12, inclusive.",
            location=location,
        )
    return value


def parse_float(token: object, *, location: ErrorLocation = ()) -> float:
    """Convert once to float64 after exact grammar/range validation; never round."""
    exact = parse_exact(token, location=location)
    value = float(exact)
    if not math.isfinite(value) or (value == 0.0 and exact != 0):
        raise InputError(
            ErrorCode.NON_FINITE_VALUE,
            "Input cannot be represented as a finite nonzero float64 value.",
            location=location,
        )
    return value


def _validate_system(a: object, b: object) -> SystemTokens:
    try:
        return SystemTokens.model_validate({"a": a, "b": b})
    except ValidationError as error:
        issue = error.errors(include_url=False, include_input=False)[0]
        location = issue["loc"]
        cause = issue.get("ctx", {}).get("error")
        if isinstance(cause, InputError):
            raise InputError(cause.code, cause.message, location=location) from None
        if issue["type"] == "string_type":
            raise InputError(
                ErrorCode.TOKEN_TYPE, "Numeric tokens must be strings.", location=location
            ) from None
        if issue["type"] == "string_too_long":
            raise ResourceLimitError(
                ErrorCode.TOKEN_TOO_LONG,
                f"Numeric tokens may contain at most {MAX_TOKEN_CHARS} characters.",
                location=location,
            ) from None
        raise InputError(
            ErrorCode.INVALID_SYSTEM, "Invalid coefficient matrix or RHS.", location=location
        ) from None


@overload
def parse_system(
    a: object, b: object, *, mode: Literal[ArithmeticMode.FLOAT64] = ArithmeticMode.FLOAT64
) -> FloatSystem: ...


@overload
def parse_system(a: object, b: object, *, mode: Literal[ArithmeticMode.EXACT]) -> ExactSystem: ...


@overload
def parse_system(a: object, b: object, *, mode: ArithmeticMode) -> FloatSystem | ExactSystem: ...


def parse_system(
    a: object, b: object, *, mode: ArithmeticMode = ArithmeticMode.FLOAT64
) -> FloatSystem | ExactSystem:
    """Validate shape before parsing up to 12×12 cells and attach error locations."""
    if not isinstance(mode, ArithmeticMode):
        raise InputError(ErrorCode.INVALID_SYSTEM, "Expected an ArithmeticMode enum value.")
    tokens = _validate_system(a, b)
    if mode is ArithmeticMode.EXACT:
        return ExactSystem(
            a=tuple(
                tuple(parse_exact(token, location=("a", i, j)) for j, token in enumerate(row))
                for i, row in enumerate(tokens.a)
            ),
            b=tuple(parse_exact(token, location=("b", i)) for i, token in enumerate(tokens.b)),
        )
    return FloatSystem(
        a=tuple(
            tuple(parse_float(token, location=("a", i, j)) for j, token in enumerate(row))
            for i, row in enumerate(tokens.a)
        ),
        b=tuple(parse_float(token, location=("b", i)) for i, token in enumerate(tokens.b)),
    )
