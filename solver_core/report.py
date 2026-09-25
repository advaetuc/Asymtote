"""Immutable report data for later Markdown/LaTeX renderers; no TeX execution."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from solver_core.models import (
    ArithmeticMode,
    DirectResult,
    DisplaySettings,
    DomainModel,
    ExactSystem,
    FloatSystem,
    IterativeResult,
)
from solver_core.trace import build_trace


class SolverReport(DomainModel):
    """One raw result owns its trace; renderers generate display strings on demand.

    Iterative results carry the accepted options and original-to-working row map.
    Direct results carry classification, pivots, solution/parameters, and row operations.
    The original immutable system remains available for independent verification.
    """

    schema_version: Literal[1] = 1
    original_system: FloatSystem | ExactSystem
    result: Annotated[DirectResult | IterativeResult, Field(discriminator="method")]
    display: DisplaySettings = Field(default_factory=DisplaySettings)

    @model_validator(mode="after")
    def validate_source(self) -> Self:
        if self.original_system.shape != self.result.classification.shape:
            raise ValueError("Report source and result shapes must agree.")
        exact = isinstance(self.original_system, ExactSystem)
        if exact != (self.result.arithmetic_mode is ArithmeticMode.EXACT):
            raise ValueError("Report source and result arithmetic modes must agree.")
        build_trace(self.result)
        return self


def build_report(
    system: FloatSystem | ExactSystem,
    result: DirectResult | IterativeResult,
    *,
    display: DisplaySettings | None = None,
) -> SolverReport:
    return SolverReport(
        original_system=system,
        result=result,
        display=DisplaySettings() if display is None else display,
    )


def serialize_report(report: SolverReport) -> str:
    """Complete report data, with no display rounding and no duplicate trace snapshots."""
    return report.model_dump_json()
