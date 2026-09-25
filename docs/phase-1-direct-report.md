# Phase 1 — classification and direct solvers

Implemented in the TULYA workspace, stopping before equation matching and
iterative methods, as requested.

## Entry points

- `solver_core.classification.classify_system(system)`
- `solver_core.gaussian.solve_gaussian(system)`
- `solver_core.gauss_jordan.solve_gauss_jordan(system)`

Each accepts an immutable FloatSystem or ExactSystem produced by `parse_system`.
Classification returns typed ranks, arithmetic mode, classification, dimensions,
and tolerance metadata. Solvers return typed DirectResult values; mathematical
inconsistency is a result, not an exception. Numerical ambiguity and resource
exhaustion are controlled domain errors.

```python
from solver_core.gaussian import solve_gaussian
from solver_core.gauss_jordan import solve_gauss_jordan
from solver_core.models import ArithmeticMode
from solver_core.parsing import parse_system

system = parse_system([["2", "1"], ["1", "-1"]], ["5", "1"], mode=ArithmeticMode.EXACT)
gaussian = solve_gaussian(system)
jordan = solve_gauss_jordan(system)
assert gaussian.solution == jordan.solution == (2, 1)
```

## Acceptance evidence

- 219 Python tests pass, including existing parser, policy, and health checks.
- Ruff lint and formatting pass; strict mypy passes across 15 source files.
- Rectangular unique, infinite, and inconsistent systems are covered.
- First-pivot and later-pivot swaps, uniform scaling, and tiny pivots are covered.
- Exact solutions satisfy original equations without floating conversion.
- Generated well-conditioned float solves agree with NumPy's independent solver.
- Parametric solutions are verified by substitution, including leading free columns.
- Full augmented RREF includes normalized contradictory RHS pivots.
- Tests replay row-operation traces and check original input remains unchanged.
- Tests exercise integer-growth, trace-size, non-finite, and rank-disagreement errors.
- Tests cover full 12-by-12 systems in both arithmetic modes.
- Tests prohibit library solve, inverse, pseudoinverse, least-squares, and determinant
  paths in educational solver execution.

The public solver modules use shared private implementation files instead of
duplicating elimination logic. Domain result/trace models were added to models.py;
this is necessary supporting work for the requested educational outputs. No new
dependency was installed.

## Numerical boundaries

Float ranks use the existing coefficient-scale cutoff with
[NumPy's singular-value interface](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html).
Pivot analysis cross-checks those ranks before a classification is published.
Very uneven scales or values close to the cutoff can produce `rank_uncertain`;
use exact mode or explicitly rescale inputs. This prevents false inconsistent
classifications caused by augmented-matrix roundoff. Tiny matrix values are
never erased for presentation.

Exact arithmetic has a 4,096-bit per-integer budget. Full traces have a cumulative
one-million-character scalar-value budget; exceeding either fails explicitly
without truncating a result. Numerators/denominators serialize as decimal strings
inside structured rational objects to preserve browser-side integer precision.

Condition-number diagnostics, iterative methods, API integration, and UI/report
work remain subsequent phases. Frontend tests/build were not rerun because this
batch changes only Python and documentation. No commit, push, or deployment was
performed. Next verification gate: `solver_core/permutations.py` and its tests.
