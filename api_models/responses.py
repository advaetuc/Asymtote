"""Typed public outcomes. Numerical values retain the core's serialization policy."""

from typing import Annotated, Literal

from pydantic import ConfigDict, Field

from api_models.requests import DirectOptions, DisplayPreferences, IterativeOptions, Method
from solver_core.models import (
    ArithmeticMode,
    ClassificationResult,
    ConditionDiagnostic,
    ConvergenceDiagnostics,
    DirectResult,
    DomainModel,
    ExactSystem,
    FloatSystem,
    IterativeResult,
    RowPermutation,
    SystemShape,
)


class APIResponse(DomainModel):
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)


class Issue(APIResponse):
    code: str
    message: str
    location: tuple[str | int, ...] = ()


class ErrorResponse(APIResponse):
    status: Literal["error"] = "error"
    request_id: str
    error: Issue
    details: tuple[Issue, ...] = ()


class NumericalFailure(APIResponse):
    """A controlled numerical limitation, without an invented classification or solution."""

    status: Literal["numeric_breakdown"] = "numeric_breakdown"
    request_id: str
    method: Method | None
    arithmetic_mode: ArithmeticMode
    shape: SystemShape
    error: Issue


class MethodEligibility(APIResponse):
    """Eligible means available subject to the stated reordering and risk requirements."""

    method: Method
    eligible: bool
    code: Literal[
        "available",
        "requires_square",
        "requires_unique",
        "requires_float64",
        "unsafe_diagonal",
        "requires_row_reordering",
        "convergence_risk",
        "numeric_breakdown",
    ]
    reason: str
    requires_row_reordering: bool = False
    requires_risk_override: bool = False
    row_permutation: RowPermutation | None = None
    convergence: ConvergenceDiagnostics | None = None


class AnalyzeResponse(APIResponse):
    status: Literal["analyzed"] = "analyzed"
    request_id: str
    shape: SystemShape
    is_square: bool
    classification: ClassificationResult
    conditioning: ConditionDiagnostic
    conditioning_arithmetic_mode: Literal["float64"] = "float64"
    strict_diagonal_dominance: bool | None
    dominance_permutation: RowPermutation | None
    nonzero_permutation: RowPermutation | None
    methods: tuple[MethodEligibility, ...]
    warnings: tuple[str, ...] = ()


class ProblemMetadata(APIResponse):
    shape: SystemShape
    is_square: bool
    arithmetic_mode: ArithmeticMode
    original_system: FloatSystem | ExactSystem


class ReportMetadata(APIResponse):
    """Use problem + result + this metadata; traces are never duplicated."""

    schema_version: Literal[1] = 1
    solver_version: Literal["0.1.0"] = "0.1.0"
    method: Method
    options: DirectOptions | IterativeOptions
    display: DisplayPreferences
    fraction_values: Literal["exact", "approximate"]


class SolveResponse(APIResponse):
    """Completed means the computation returned a result, not that it converged.

    Inspect result.classification for direct methods and result.status for iteration.
    Conditioning always estimates the original coefficient matrix in float64.
    """

    status: Literal["completed"] = "completed"
    request_id: str
    problem: ProblemMetadata
    result: Annotated[DirectResult | IterativeResult, Field(discriminator="method")]
    conditioning: ConditionDiagnostic
    conditioning_arithmetic_mode: Literal["float64"] = "float64"
    report: ReportMetadata


type AnalyzeOutcome = Annotated[AnalyzeResponse | NumericalFailure, Field(discriminator="status")]
type SolveOutcome = Annotated[SolveResponse | NumericalFailure, Field(discriminator="status")]
