"""Validated immutable domain data, without HTTP or hosting dependencies.

Pydantic owns shape/type validation. The strict numeric grammar lives only in
parsing.py. Exact values enter these models as Fraction objects, never floats.
"""

from enum import StrEnum
from fractions import Fraction
from math import gcd
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    field_serializer,
    field_validator,
    model_validator,
)

from solver_core.constants import (
    DEFAULT_DECIMAL_PLACES,
    DEFAULT_ITERATIONS,
    DEFAULT_ITERATIVE_TOLERANCE,
    MAX_DECIMAL_PLACES,
    MAX_EQUATIONS,
    MAX_ITERATIONS,
    MAX_ITERATIVE_TOLERANCE,
    MAX_RATIONAL_BITS,
    MAX_TOKEN_CHARS,
    MAX_UNKNOWNS,
    MIN_DECIMAL_PLACES,
    MIN_DIMENSION,
    MIN_ITERATIONS,
    MIN_ITERATIVE_TOLERANCE,
)
from solver_core.errors import ErrorCode, InputError, ResourceLimitError


class DomainModel(BaseModel):
    """Reject coercion/extra fields and validate reused model instances."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        extra="forbid",
        validate_default=True,
        revalidate_instances="always",
        allow_inf_nan=False,
    )


class ArithmeticMode(StrEnum):
    FLOAT64 = "float64"
    EXACT = "exact"


class SystemShape(DomainModel):
    equations: Annotated[int, Field(ge=MIN_DIMENSION, le=MAX_EQUATIONS)]
    unknowns: Annotated[int, Field(ge=MIN_DIMENSION, le=MAX_UNKNOWNS)]

    @property
    def is_square(self) -> bool:
        return self.equations == self.unknowns


class RationalValue(DomainModel):
    """Canonical exact rational; JSON integers are strings to prevent JS loss."""

    numerator: int
    denominator: Annotated[int, Field(gt=0)]

    @model_validator(mode="after")
    def validate_canonical_form(self) -> Self:
        if max(self.numerator.bit_length(), self.denominator.bit_length()) > MAX_RATIONAL_BITS:
            raise ResourceLimitError(
                ErrorCode.RATIONAL_GROWTH_LIMIT,
                "Exact arithmetic exceeded its integer-size budget; use float64 mode.",
            )
        if gcd(self.numerator, self.denominator) != 1:
            raise ValueError("Rational values must be reduced with a positive denominator.")
        return self

    @field_serializer("numerator", "denominator", when_used="json")
    def serialize_integer(self, value: int) -> str:
        return str(value)

    @classmethod
    def from_fraction(cls, value: Fraction) -> Self:
        if not isinstance(value, Fraction):
            raise TypeError("Exact values must originate from Fraction, not float.")
        return cls(numerator=value.numerator, denominator=value.denominator)

    def as_fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


def _require_fraction(value: object) -> Fraction:
    if not isinstance(value, Fraction):
        raise ValueError("Expected a Fraction; exact values cannot be coerced from floats.")
    if max(value.numerator.bit_length(), value.denominator.bit_length()) > MAX_RATIONAL_BITS:
        raise ResourceLimitError(
            ErrorCode.RATIONAL_GROWTH_LIMIT,
            "Exact arithmetic exceeded its integer-size budget; use float64 mode.",
        )
    return value


def _require_float(value: object) -> float:
    if type(value) is not float:
        raise ValueError("Expected an already parsed float64 value.")
    return value


type ExactScalar = Annotated[
    Fraction,
    BeforeValidator(_require_fraction),
    PlainSerializer(RationalValue.from_fraction, return_type=RationalValue, when_used="json"),
]
type FloatScalar = Annotated[float, BeforeValidator(_require_float), Field(allow_inf_nan=False)]
type Token = Annotated[str, Field(strict=True, max_length=MAX_TOKEN_CHARS)]


def _bounded_sequence(value: object, maximum: int) -> tuple[object, ...]:
    # Do not consume generators or arbitrary iterables from an untrusted boundary.
    if not isinstance(value, (list, tuple)):
        raise InputError(ErrorCode.INVALID_SYSTEM, "Expected a list or tuple.")
    if not MIN_DIMENSION <= len(value) <= maximum:
        raise InputError(
            ErrorCode.DIMENSION_OUT_OF_RANGE,
            f"Sequence length must be between {MIN_DIMENSION} and {maximum}.",
        )
    return tuple(value)


class _LinearSystem[ScalarT](DomainModel):
    a: tuple[tuple[ScalarT, ...], ...]
    b: tuple[ScalarT, ...]

    @field_validator("a", mode="before")
    @classmethod
    def freeze_matrix(cls, value: object) -> tuple[tuple[object, ...], ...]:
        rows = _bounded_sequence(value, MAX_EQUATIONS)
        return tuple(_bounded_sequence(row, MAX_UNKNOWNS) for row in rows)

    @field_validator("b", mode="before")
    @classmethod
    def freeze_rhs(cls, value: object) -> tuple[object, ...]:
        return _bounded_sequence(value, MAX_EQUATIONS)

    @model_validator(mode="after")
    def validate_shape(self) -> Self:
        if any(len(row) != len(self.a[0]) for row in self.a):
            raise InputError(
                ErrorCode.INVALID_SYSTEM, "All coefficient rows must have equal length."
            )
        if len(self.b) != len(self.a):
            raise InputError(ErrorCode.INVALID_SYSTEM, "RHS length must equal the equation count.")
        return self

    @property
    def shape(self) -> SystemShape:
        return SystemShape(equations=len(self.a), unknowns=len(self.a[0]))


class SystemTokens(_LinearSystem[Token]):
    """Preserve the user's spelling; numeric grammar is validated by the parser."""


class FloatSystem(_LinearSystem[FloatScalar]):
    """Finite binary64 coefficients and RHS; no rounding or mutable arrays."""


class ExactSystem(_LinearSystem[ExactScalar]):
    """Exact coefficients with bounded integer growth and structured JSON output."""


class IterationSettings(DomainModel):
    tolerance: Annotated[float, Field(ge=MIN_ITERATIVE_TOLERANCE, le=MAX_ITERATIVE_TOLERANCE)] = (
        DEFAULT_ITERATIVE_TOLERANCE
    )
    max_iterations: Annotated[int, Field(ge=MIN_ITERATIONS, le=MAX_ITERATIONS)] = DEFAULT_ITERATIONS


class DisplaySettings(DomainModel):
    decimal_places: Annotated[int, Field(ge=MIN_DECIMAL_PLACES, le=MAX_DECIMAL_PLACES)] = (
        DEFAULT_DECIMAL_PLACES
    )
