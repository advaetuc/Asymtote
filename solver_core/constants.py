"""Central resource limits and numeric policy; display never changes arithmetic."""

from sys import float_info
from typing import Final

MIN_DIMENSION: Final = 1
MAX_EQUATIONS: Final = 12
MAX_UNKNOWNS: Final = 12
MIN_ITERATIONS: Final = 1
MAX_ITERATIONS: Final = 500
DEFAULT_ITERATIONS: Final = 25
MIN_DECIMAL_PLACES: Final = 0
MAX_DECIMAL_PLACES: Final = 12
DEFAULT_DECIMAL_PLACES: Final = 6
MAX_TOKEN_CHARS: Final = 48

# Check exponents before creating a Decimal, Fraction, or power of ten.
MAX_ABS_EXPONENT: Final = 100
MAX_ABS_INPUT: Final = 10**12
MIN_NONZERO_INPUT_DENOMINATOR: Final = 10**100
MIN_NONZERO_INPUT: Final = 1e-100

# Applies to each reduced numerator/denominator, including future intermediates.
MAX_RATIONAL_BITS: Final = 4096
MAX_DISPLAY_DENOMINATOR: Final = 10_000
MIN_ITERATIVE_TOLERANCE: Final = 1e-14
MAX_ITERATIVE_TOLERANCE: Final = 1e-2
DEFAULT_ITERATIVE_TOLERANCE: Final = 1e-8
FLOAT64_EPSILON: Final = float_info.epsilon

# These are versioned numerical decisions, not user-adjustable preferences.
TOLERANCE_POLICY_VERSION: Final = "float64-coefficient-scale-v1"
