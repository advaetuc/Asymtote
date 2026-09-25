"""Transport-independent failures with stable codes and coefficient locations."""

from enum import StrEnum

type ErrorLocation = tuple[str | int, ...]


class ErrorCode(StrEnum):
    TOKEN_TYPE = "token_type"
    EMPTY_TOKEN = "empty_token"
    TOKEN_TOO_LONG = "token_too_long"
    INVALID_TOKEN = "invalid_token"
    ZERO_DENOMINATOR = "zero_denominator"
    EXPONENT_OUT_OF_RANGE = "exponent_out_of_range"
    MAGNITUDE_OUT_OF_RANGE = "magnitude_out_of_range"
    INVALID_SYSTEM = "invalid_system"
    DIMENSION_OUT_OF_RANGE = "dimension_out_of_range"
    RATIONAL_GROWTH_LIMIT = "rational_growth_limit"
    NON_FINITE_VALUE = "non_finite_value"
    INVALID_TOLERANCE = "invalid_tolerance"
    RANK_UNCERTAIN = "rank_uncertain"
    ZERO_PIVOT = "zero_pivot"
    TRACE_LIMIT = "trace_limit"


class SolverError(ValueError):
    """Safe domain error; messages deliberately do not contain raw user input."""

    def __init__(self, code: ErrorCode, message: str, *, location: ErrorLocation = ()) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.location = location


class InputError(SolverError):
    """Invalid numeric syntax, shape, or input value."""


class ResourceLimitError(SolverError):
    """An explicit resource budget was exceeded."""


class NumericBreakdownError(SolverError):
    """An internal arithmetic operation cannot produce finite diagnostics."""
