"""Validated immutable domain data, without HTTP or hosting dependencies.

Pydantic owns shape/type validation. The strict numeric grammar lives only in
parsing.py. Exact values enter these models as Fraction objects, never floats.
"""

from enum import StrEnum
from fractions import Fraction
from math import gcd
from typing import Annotated, Literal, Self

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


class ClassificationKind(StrEnum):
    UNIQUE = "unique"
    INFINITE = "infinite"
    INCONSISTENT = "inconsistent"


class ClassificationResult(DomainModel):
    shape: SystemShape
    arithmetic_mode: ArithmeticMode
    rank_a: Annotated[int, Field(ge=0)]
    rank_augmented: Annotated[int, Field(ge=0)]
    classification: ClassificationKind
    rank_tolerance: Annotated[float, Field(ge=0)] | None
    tolerance_policy: str

    @model_validator(mode="after")
    def validate_ranks(self) -> Self:
        m, n = self.shape.equations, self.shape.unknowns
        if not (
            self.rank_a <= min(m, n)
            and self.rank_a <= self.rank_augmented <= min(m, self.rank_a + 1)
        ):
            raise ValueError("Ranks violate matrix/augmentation bounds.")
        expected = (
            ClassificationKind.INCONSISTENT
            if self.rank_a < self.rank_augmented
            else ClassificationKind.UNIQUE
            if self.rank_a == n
            else ClassificationKind.INFINITE
        )
        if self.classification is not expected:
            raise ValueError("Classification does not agree with ranks.")
        if (self.rank_tolerance is None) != (self.arithmetic_mode is ArithmeticMode.EXACT):
            raise ValueError("Only exact classification omits a floating tolerance.")
        return self


type NumericValue = ExactScalar | FloatScalar
type NumericVector = tuple[NumericValue, ...]
type NumericMatrix = tuple[NumericVector, ...]


class RowOperation(DomainModel):
    index: Annotated[int, Field(ge=0)]
    phase: Literal["forward_elimination", "backward_elimination"]
    operation_type: Literal["row_swap", "row_add_scaled", "row_scale"]
    target_row: Annotated[int, Field(ge=0)]
    source_row: Annotated[int, Field(ge=0)] | None
    pivot_column: Annotated[int, Field(ge=0)]
    factor: NumericValue | None
    matrix_after: NumericMatrix
    explanation: str

    @model_validator(mode="after")
    def validate_operation(self) -> Self:
        needs_source = self.operation_type != "row_scale"
        needs_factor = self.operation_type != "row_swap"
        if needs_source != (self.source_row is not None):
            raise ValueError("Invalid source row for this operation.")
        if needs_factor != (self.factor is not None):
            raise ValueError("Invalid factor for this operation.")
        if self.target_row >= len(self.matrix_after):
            raise ValueError("Target row is outside the trace matrix.")
        if self.source_row is not None and self.source_row >= len(self.matrix_after):
            raise ValueError("Source row is outside the trace matrix.")
        return self


class ParameterTerm(DomainModel):
    parameter: str
    coefficient: NumericValue


class VariableExpression(DomainModel):
    variable: str
    constant: NumericValue
    terms: tuple[ParameterTerm, ...]


class ParametricSolution(DomainModel):
    pivot_variables: tuple[int, ...]
    free_variables: tuple[int, ...]
    expressions: tuple[VariableExpression, ...]


class DirectDiagnostics(DomainModel):
    """Measured on the original system and the returned solution/particular point."""

    residual_inf: NumericValue
    backward_error: NumericValue

    @model_validator(mode="after")
    def validate_nonnegative(self) -> Self:
        if self.residual_inf < 0 or self.backward_error < 0:
            raise ValueError("Residual norm and backward error cannot be negative.")
        return self


class DirectResult(DomainModel):
    method: Literal["gaussian", "gauss_jordan"]
    arithmetic_mode: ArithmeticMode
    classification: ClassificationResult
    form: Literal["ref", "rref"]
    matrix: NumericMatrix
    pivot_columns: tuple[int, ...]
    free_columns: tuple[int, ...]
    augmented_pivot_columns: tuple[int, ...]
    solution: NumericVector | None
    parametric_solution: ParametricSolution | None
    contradictory_rows: tuple[int, ...]
    row_tolerances: tuple[float, ...] | None
    trace: tuple[RowOperation, ...]
    diagnostics: DirectDiagnostics | None
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_structure(self) -> Self:
        m, n = self.classification.shape.equations, self.classification.shape.unknowns
        if len(self.matrix) != m or any(len(row) != n + 1 for row in self.matrix):
            raise ValueError("Reduced matrix must preserve the augmented input shape.")
        if self.form != ("ref" if self.method == "gaussian" else "rref"):
            raise ValueError("Matrix form does not match the selected method.")
        if tuple(sorted(set(self.augmented_pivot_columns))) != self.augmented_pivot_columns or any(
            column < 0 or column > n for column in self.augmented_pivot_columns
        ):
            raise ValueError("Augmented pivot columns must be sorted, distinct, and in range.")
        if self.pivot_columns != tuple(
            column for column in self.augmented_pivot_columns if column < n
        ):
            raise ValueError("Coefficient pivots must agree with augmented pivots.")
        if self.free_columns != tuple(
            column for column in range(n) if column not in self.pivot_columns
        ):
            raise ValueError("Free columns must complement coefficient pivots.")
        if (
            len(self.pivot_columns) != self.classification.rank_a
            or len(self.augmented_pivot_columns) != self.classification.rank_augmented
        ):
            raise ValueError("Pivot counts must agree with ranks.")
        if self.solution is not None and len(self.solution) != n:
            raise ValueError("Solution length must equal the unknown count.")
        if any(row < 0 or row >= m for row in self.contradictory_rows):
            raise ValueError("Contradiction row is out of range.")
        exact = self.arithmetic_mode is ArithmeticMode.EXACT
        if exact != (self.row_tolerances is None):
            raise ValueError("Only floating results have row tolerance metadata.")
        if self.row_tolerances is not None:
            if len(self.row_tolerances) != m or any(value < 0 for value in self.row_tolerances):
                raise ValueError("Each reduced row requires a nonnegative tolerance.")
        values = [value for row in self.matrix for value in row]
        if self.solution is not None:
            values.extend(self.solution)
        if self.diagnostics is not None:
            values.extend((self.diagnostics.residual_inf, self.diagnostics.backward_error))
        if self.parametric_solution is not None:
            parametric = self.parametric_solution
            if (
                parametric.pivot_variables != self.pivot_columns
                or parametric.free_variables != self.free_columns
                or tuple(expression.variable for expression in parametric.expressions)
                != tuple(f"x{j + 1}" for j in range(n))
            ):
                raise ValueError("Parametric structure must agree with pivots and variable order.")
            parameters = {f"t{k + 1}" for k in range(len(self.free_columns))}
            for expression in parametric.expressions:
                if any(term.parameter not in parameters for term in expression.terms):
                    raise ValueError("Unknown parameter in a variable expression.")
                values.append(expression.constant)
                values.extend(term.coefficient for term in expression.terms)
        for index, step in enumerate(self.trace):
            if (
                step.index != index
                or len(step.matrix_after) != m
                or any(len(row) != n + 1 for row in step.matrix_after)
                or step.pivot_column > n
            ):
                raise ValueError("Trace indices, columns, and shapes must match the result.")
            values.extend(value for row in step.matrix_after for value in row)
            if step.factor is not None:
                values.append(step.factor)
        if any(isinstance(value, Fraction) != exact for value in values):
            raise ValueError("Float and exact values cannot be mixed within one result.")
        return self

    @model_validator(mode="after")
    def validate_outcome(self) -> Self:
        kind = self.classification.classification
        if self.arithmetic_mode is not self.classification.arithmetic_mode:
            raise ValueError("Result and classification arithmetic modes must agree.")
        if kind is ClassificationKind.INCONSISTENT:
            if (
                self.solution is not None
                or self.parametric_solution is not None
                or self.diagnostics is not None
                or not self.contradictory_rows
            ):
                raise ValueError("Inconsistent results require a witness, not a solution.")
        elif self.contradictory_rows or self.diagnostics is None:
            raise ValueError("Consistent results require diagnostics and no contradiction.")
        elif kind is ClassificationKind.UNIQUE:
            if self.solution is None or self.parametric_solution is not None:
                raise ValueError("Unique results require one solution vector.")
        elif self.solution is not None or self.parametric_solution is None:
            raise ValueError("Infinite results require a parametric solution.")
        return self
