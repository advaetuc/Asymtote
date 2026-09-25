# Numerical policy — Phase 1 foundations

Implemented: resource constants, Pydantic domain models, strict token parsing,
and floating comparison tolerances. Classification, solution algorithms,
residual diagnostics, and iteration stopping are not implemented yet.

## Fixed specification limits

| Setting | Value |
| --- | --- |
| Minimum equations / unknowns | 1 |
| Maximum equations | 12 |
| Maximum unknowns | 12 |
| Default iteration budget | 25 |
| Maximum iteration budget | 500 |
| Display decimal places | 0–12 |
| Maximum numeric token length | 48 characters |
| Maximum absolute input value | 10^12, inclusive |
| Minimum nonzero absolute input value | 10^-100, inclusive |
| Scientific exponent | -100 through +100, inclusive |
| Reduced rational numerator / denominator | At most 4,096 bits each |
| Approximate display denominator cap | 10,000 |
| Iterative tolerance bounds | 10^-14 through 10^-2, inclusive |
| Default iterative tolerance | 10^-8 |
| Default decimal places | 6 |

The additional bounds are explicit implementation decisions centralized in
`solver_core/constants.py`, not mathematical limits. They keep parsed values
away from subnormal/overflow ranges and prevent short exponent tokens from
allocating enormous integers. Zero is allowed. Bounds are checked on exact
rationals before float conversion, so rounding cannot hide an out-of-range value.
Both float and exact input modes use the same grammar and magnitude limits.
Exact arithmetic retains the 12-by-12 dimension cap; there is no extra hidden
small-system limit. Future row-operation code must enforce the rational-growth
guard after every operation, not only when assembling the final output.

Equation and unknown counts remain independent. Direct methods support
rectangular systems. Iterative methods require square systems classified unique
and a valid nonzero diagonal after any user-authorized reordering.

## Float64 and tolerances

Compute iterates and row operations in full float64 precision. Decimal places
affect rendering only. Never replace small stored entries with zero for display.

`solver_core/tolerance.py` implements policy `float64-coefficient-scale-v1`.
Python's binary64 epsilon is `2^-52`, verified against NumPy float64 in tests.
For m equations and n unknowns:

```text
coefficient_scale = max_i sum_j abs(A[i,j])       # ||A|| infinity
rank_scale = coefficient_scale if nonzero, else max_i abs(b[i])
rank_abs = epsilon * max(m, n + 1) * rank_scale
pivot_abs = epsilon * max(m, n) * coefficient_scale
active_pivot_abs = epsilon * max(m, n) *
                   max(coefficient_scale, max(abs(active_column)))
```

The rank cutoff is one shared absolute threshold for both A and [A|b], including
the augmented dimension. A large RHS alone does not enlarge it when A is
nonzero. If A is zero, the RHS supplies the scale; if both are zero, the cutoff
is exactly zero. Future rank classification must pass this shared cutoff
explicitly to both singular-value comparisons, rather than using independent
library defaults. Comparisons classify `abs(value) <= cutoff` as effectively zero.

The active-column pivot threshold accounts for elimination growth without
lowering the original coefficient-scale floor. Norm overflow and non-finite
values produce controlled numerical-breakdown errors. These functions compare
values without modifying coefficients. Uniform scaling scales the cutoffs;
there is no absolute `max(1, matrix_norm)` floor. Strongly uneven scaling can
still make small pivots numerically insignificant: this is a floating numerical
rank policy, not a claim about exact symbolic rank.

User tolerance controls iterative convergence, never internal pivot safety.
Direct float methods require partial pivoting, rank-based classification, and
no matrix inverse. Exact arithmetic uses exact zero comparisons.

## Residuals and convergence

For the original input system, report `r = A x - b`, `||r||_infinity`, and
`||r||_infinity / (||A||_infinity ||x||_infinity + ||b||_infinity)`.
Define zero-denominator behavior explicitly; prevent NaN/Infinity in JSON.
Stopping must require small normalized residual and complementary normalized
step change. Budget exhaustion and numerical breakdown are explicit outcomes,
not successful solutions. Use separate Jacobi and Gauss-Seidel iteration matrices.

## Strict parsing and exact arithmetic

`parse_exact` validates text and constructs Fraction directly. `parse_float`
performs one final float conversion and verifies finite representation without
rounding. `parse_system` validates dimensions before parsing cells and adds
zero-based error locations such as `("a", 1, 2)` or `("b", 0)`.

The full-match ASCII grammar is:

```text
decimal:  [+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?
rational: [+-]?[0-9]+/[+-]?[0-9]+
```

Leading zeros, `.5`, `1.`, signs on either integer in a fraction, and uppercase
E are accepted. Whitespace is rejected, including leading/trailing spaces,
internal spaces, and trailing newlines. There is no implicit trimming.
Unicode digits/signs, underscores, identifiers, expressions, decimal
denominators, NaN, infinity, complex numbers, and non-string cells are rejected.
Exponent limits are checked before Fraction construction, including zero
mantissas. Exact zero canonicalizes to 0/1 (including negative zero input).

`SystemTokens` preserves the original spelling but validates only shape, string
types, and length. `parse_system` is the numeric trust boundary. Pydantic models
forbid extra fields/coercion, validate defaults and reused instances, and freeze
matrix data as nested tuples. Lists/tuples are copied; generators are rejected
before consumption. FloatSystem and ExactSystem hold already parsed/internal
values, so they do not reapply user magnitude limits to solver intermediates.

ExactSystem contains Fraction objects. Its JSON export represents each as
`{"numerator": "...", "denominator": "..."}`: decimal strings prevent JavaScript
integer precision loss. RationalValue requires canonical reduced integers and a
positive denominator. This is an output representation; strict domain
constructors require parsed integers/Fractions, not these JSON strings.
Do not use Pydantic `model_construct` or unvalidated `model_copy(update=...)` on
untrusted values. API-specific request/response models remain a Phase 2 concern.

Iterative fraction display must be approximate and marked `≈`; its implementation
comes later. The chosen iterative tolerance range/default are validated now;
residual zero-denominator behavior and normalized-step stopping formulas still
need implementation and tests before iterative solvers are accepted.
