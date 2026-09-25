# Numerical policy — Phase 1

Implemented: resource constants, Pydantic domain models, strict token parsing,
floating comparison tolerances, rank classification, Gaussian elimination,
Gauss-Jordan reduction, row matching, Jacobi and Gauss-Seidel iteration,
residual/backward-error and convergence diagnostics, trace serialization,
and structured report data.

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
| Cumulative scalar text in direct traces | 1,000,000 characters |

The additional bounds are explicit implementation decisions centralized in
`solver_core/constants.py`, not mathematical limits. They keep parsed values
away from subnormal/overflow ranges and prevent short exponent tokens from
allocating enormous integers. Zero is allowed. Bounds are checked on exact
rationals before float conversion, so rounding cannot hide an out-of-range value.
Both float and exact input modes use the same grammar and magnitude limits.
Exact arithmetic retains the 12-by-12 dimension cap; there is no extra hidden
small-system limit. Arithmetic guards run after every product, division, and
addition, including intermediate products before subtraction and diagnostics.
Each operand is already bounded, so the temporary integer allocation before
the next check is bounded too. Trace snapshots/factors have a cumulative scalar
text budget; exceeding it raises `trace_limit`, rather than returning a silently
truncated trace. JSON structural overhead is additional but bounded by dimensions
and the maximum number of row operations. HTTP payload checks remain an API task.

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
is exactly zero. Rank classification uses this shared cutoff explicitly for both
singular-value comparisons, rather than using independent library defaults.
Comparisons classify `abs(value) <= cutoff` as effectively zero.

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

## Classification and direct row reduction

`classify_system` counts singular values strictly greater than `rank_abs` for A
and [A|b] in float mode. The resulting ranks must satisfy augmentation bounds
and agree with independent handwritten pivot analysis. If they disagree, return
a controlled `rank_uncertain` error recommending rescaling or exact arithmetic.
No rank is silently clamped, and no false mathematical classification is emitted
when the two computations disagree. This safeguard matters near the threshold
and when a large RHS causes augmented SVD roundoff above a coefficient-scale
cutoff. For example, rows `[1,0]`, `[0,1]`, `[1,1]` with RHS `[4e11,4e11,8e11]`
are exactly consistent, but some LAPACK builds report a spurious extra rank.
Exact mode resolves this case; float mode may explicitly report uncertainty.

Exact classification counts pivots in bounded Fraction elimination; it never
calls floating SVD or compares to a floating epsilon.

Gaussian elimination and Gauss-Jordan share `_elimination.py`. Both create an
augmented copy of the immutable input, select the largest-magnitude remaining
pivot in each column, and swap equations without reordering variables. Float
pivot detection uses `max(rank_abs, active_pivot_abs)`; the rank cutoff provides
a floor consistent with classification. Exact pivots use exact zero tests.

Gaussian returns REF and uses pivot-index-aware back substitution. Gauss-Jordan
performs a backward sweep to normalize pivots and eliminate above them. The full
augmented matrix is reduced, including an RHS pivot in inconsistent systems.
Both methods classify rectangular cases. Infinite results have structured
expressions for every variable, with zero-based pivot/free indices and parameters
`t1`, `t2`, etc.; the particular solution sets all parameters to zero. Inconsistent
results contain contradiction row indices and no solution or solution diagnostics.

Every swap, row addition, and normalization has one immutable after-snapshot
and a structured factor/source/target record. Tiny float entries are retained,
including arithmetic cancellation remnants; the returned float matrix is a
numerical REF/RREF under the tolerance metadata, not a symbolic exact matrix.
For comparison of transformed rows, initial row tolerance `rank_abs` propagates:

```text
swap:    swap the row tolerances
scale:   tolerance[row] *= abs(factor)
add:     tolerance[target] += abs(factor) * tolerance[source]
```

These are scale-aware comparison thresholds, not certified error bounds.
Contradiction detection requires effectively zero coefficients and a nonzero
RHS under that row's propagated threshold. Any disagreement with rank
classification produces `rank_uncertain`. Result models validate dimensions,
pivot/free partitions, arithmetic-mode consistency, and outcome invariants.

## Residuals and convergence

For the original input system, report `r = A x - b`, `||r||_infinity`, and
`||r||_infinity / (||A||_infinity ||x||_infinity + ||b||_infinity)`.
Direct methods compute both metrics on the original system, using the unique
solution or the zero-parameter particular solution for infinite cases. Exact
metrics use bounded Fraction arithmetic. Float dot-product sums use `math.fsum`
on unrounded float products. If the denominator is zero, the zero system has
zero residual and backward error is defined as zero. Arithmetic overflow raises
a controlled error; no NaN or Infinity is serialized.

Iterative solvers accept `FloatSystem` only. Exact input requires an explicit
separate parse into float mode; Fraction values never enter an iteration. Python
floats on the supported CPython 3.12 runtime are IEEE binary64, matching NumPy
float64. Jacobi reads only the previous immutable vector; Gauss-Seidel reads its
partially updated buffer. Neither method rounds values or calls a library solver.

Every complete iteration records the vector, residual norm, backward error,
step norm, normalized step, and convergence boolean:

```text
delta_inf = max_i abs(x_new[i] - x_old[i])
normalized_step_change = delta_inf / max(1, max_i abs(x_new[i]))
converged = backward_error <= tolerance AND normalized_step_change <= tolerance
```

The denominator floor applies only to step normalization, never matrix pivot
tests. It gives an absolute step test near the zero vector. The residual test
still prevents a tiny step with a large relative residual from claiming success.
At least one sweep is performed, including when the initial guess is already a
solution. Default initial guess is zero, tolerance is 1e-8, and budget is 25.
The existing tolerance and iteration caps are enforced by `IterationOptions`.

Only `converged` populates `solution`. Budget exhaustion returns
`max_iterations_reached`, with a `last_iterate` and its diagnostics. Arithmetic
overflow in a product, sum, vector update, norm, or backward-error denominator,
and violations of iteration shape/trace invariants, return `numeric_breakdown`.
The last complete finite record is preserved; a partial sweep or a candidate
whose diagnostics failed is discarded. If the initial residual cannot be
computed, history is empty and diagnostics are absent. No NaN/Infinity enters
serialized output. Invalid preconditions (non-square/non-unique systems,
wrong initial length, or an unsafe diagonal) raise domain errors before iteration.

## Row matching and iteration risk

`permutations.py` uses augmenting-path bipartite matching, bounded by O(n^3),
with positions on one side and equation rows on the other. For strict matching,
an edge exists exactly when `abs(A[row,j]) > sum(k != j, abs(A[row,k]))`.
Weak dominance does not satisfy this test. Float sums use `math.fsum`; exact
systems use bounded rational sums. For non-zero matching, float edges require
`abs(A[row,j]) > pivot_abs`; exact edges require an exactly nonzero coefficient.
There is no permutation enumeration or column reordering.

`RowPermutation.order[j]` identifies the original equation moved to working row
j. The same map moves the RHS. The source model remains immutable. Identity is
preferred when it already satisfies the matching criterion.

By default, `auto_reorder_for_diagonal_dominance=True` searches only when the
current matrix is not strictly dominant. Failure preserves the original order.
The separate `auto_reorder_for_nonzero_diagonal=False` option explicitly permits
fallback matching if a safe diagonal is still missing. A non-zero match does not
imply dominance or convergence. Search outcomes and the accepted permutation are
stored in the result.

`convergence.py` builds Jacobi's `-D^-1(L+U)` by row division and Gauss-Seidel's
`-(D+L)^-1 U` by handwritten forward substitution. It never constructs an inverse.
NumPy eigenvalues provide a method-specific spectral-radius diagnostic.
Symmetry is tested with absolute cutoff `pivot_abs`; Cholesky is applied to the
symmetric part `(A/2 + A.T/2)` to avoid relying on just one triangle. This is a
floating SPD diagnostic, not a symbolic proof. SPD supports Gauss-Seidel; it is
not treated as sufficient for Jacobi.

Strict row dominance, the Gauss-Seidel SPD diagnostic, or a computed spectral
radius below one allows execution. A computed radius at least one, conflicting
numerical evidence, or unavailable spectral information with no sufficient
condition is treated as convergence risk. The default result is
`convergence_risk_declined`. `run_despite_convergence_risk=True` allows a bounded
run whose status follows the actual trace. A particular initial guess may still
converge even when convergence from all initial guesses is not guaranteed.

## Conditioning, traces, and report data

`condition_diagnostic` uses NumPy's 2-norm condition number on the original float
coefficient matrix. Finite values include `max(0, log10(kappa))` as approximate
potential decimal digit loss, not a universal error bound or a bad-condition
threshold. Infinite condition values yield structured `singular` status;
failed/NaN computations yield `unavailable`, with no non-finite JSON number.
Spectral failures likewise produce `unavailable` without fabricating a radius.

`trace.py` emits version-1 direct and iterative trace envelopes. Exact entries
retain structured numerator/denominator decimal strings. Float values serialize
at full precision; display settings never affect raw data. Iteration histories
contain at most 500 records of at most 12 values plus four scalar metrics, which
stay below the existing million-character numeric budget. Standalone trace
serialization also enforces that budget and never silently truncates.

`report.py` assembles version-1 immutable report data: the original system,
validated result (including options, accepted row order, classification,
solution or parametric outcome, diagnostics, warnings, and trace), and separate
display settings. It checks shape and arithmetic-mode compatibility; callers
must pair a result with the system that produced it. The result owns the single
trace copy. Markdown/LaTeX rendering and user-facing exports belong to Phase 4.

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
normalized-step stopping formulas and iterative diagnostic integration still
need implementation and tests before iterative solvers are accepted.
