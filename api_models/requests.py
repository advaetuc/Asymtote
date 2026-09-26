"""Strict JSON contracts; numeric text is validated by the core's single grammar."""

from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from solver_core.constants import (
    DEFAULT_DECIMAL_PLACES,
    DEFAULT_ITERATIONS,
    DEFAULT_ITERATIVE_TOLERANCE,
    MAX_DECIMAL_PLACES,
    MAX_EQUATIONS,
    MAX_ITERATIONS,
    MAX_ITERATIVE_TOLERANCE,
    MAX_TOKEN_CHARS,
    MAX_UNKNOWNS,
    MIN_DECIMAL_PLACES,
    MIN_ITERATIONS,
    MIN_ITERATIVE_TOLERANCE,
)
from solver_core.parsing import parse_exact


class APIModel(BaseModel):
    model_config = ConfigDict(
        strict=True, extra="forbid", frozen=True, allow_inf_nan=False, validate_default=True
    )


def validated_token(value: str) -> str:
    parse_exact(value)
    return value


type NumericToken = Annotated[
    str, Field(min_length=1, max_length=MAX_TOKEN_CHARS), AfterValidator(validated_token)
]
type InputRow = Annotated[list[NumericToken], Field(min_length=1, max_length=MAX_UNKNOWNS)]
type Method = Literal["gaussian", "gauss_jordan", "jacobi", "gauss_seidel"]


class SystemInput(APIModel):
    a: Annotated[list[InputRow], Field(min_length=1, max_length=MAX_EQUATIONS)]
    b: Annotated[list[NumericToken], Field(min_length=1, max_length=MAX_EQUATIONS)]

    @model_validator(mode="after")
    def rectangular(self) -> Self:
        if any(len(row) != len(self.a[0]) for row in self.a) or len(self.b) != len(self.a):
            raise ValueError("Coefficient rows and RHS must have consistent dimensions.")
        return self


class DisplayPreferences(APIModel):
    mode: Literal["decimal", "fraction"] = "decimal"
    decimal_places: Annotated[int, Field(ge=MIN_DECIMAL_PLACES, le=MAX_DECIMAL_PLACES)] = (
        DEFAULT_DECIMAL_PLACES
    )


class AnalyzeRequest(APIModel):
    system: SystemInput
    arithmetic_mode: Literal["float64", "exact"] = "float64"


class DirectOptions(APIModel):
    arithmetic_mode: Literal["float64", "exact"] = "float64"


class IterativeOptions(APIModel):
    initial_guess: (
        Annotated[list[NumericToken], Field(min_length=1, max_length=MAX_UNKNOWNS)] | None
    ) = None
    tolerance: Annotated[float, Field(ge=MIN_ITERATIVE_TOLERANCE, le=MAX_ITERATIVE_TOLERANCE)] = (
        DEFAULT_ITERATIVE_TOLERANCE
    )
    max_iterations: Annotated[int, Field(ge=MIN_ITERATIONS, le=MAX_ITERATIONS)] = DEFAULT_ITERATIONS
    auto_reorder_for_diagonal_dominance: bool = True
    auto_reorder_for_nonzero_diagonal: bool = False
    run_despite_convergence_risk: bool = False


class DirectSolveRequest(APIModel):
    system: SystemInput
    method: Literal["gaussian", "gauss_jordan"]
    options: DirectOptions = Field(default_factory=DirectOptions)
    display: DisplayPreferences = Field(default_factory=DisplayPreferences)


class IterativeSolveRequest(APIModel):
    system: SystemInput
    method: Literal["jacobi", "gauss_seidel"]
    options: IterativeOptions = Field(default_factory=IterativeOptions)
    display: DisplayPreferences = Field(default_factory=DisplayPreferences)

    @model_validator(mode="after")
    def initial_length(self) -> Self:
        if self.options.initial_guess is not None and len(self.options.initial_guess) != len(
            self.system.a[0]
        ):
            raise ValueError("Initial guess length must equal the unknown count.")
        return self


type SolveRequest = Annotated[
    DirectSolveRequest | IterativeSolveRequest, Field(discriminator="method")
]
