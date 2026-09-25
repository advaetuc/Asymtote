# Phase 1 completion — numerical core

Implemented the final approved Phase 1 batch. The numerical core is ready for
user verification before Phase 2 API work.

## Delivered modules

| File | Responsibility |
| --- | --- |
| `solver_core/permutations.py` | Bipartite strict-dominance and non-zero-diagonal matching; explicit equation mappings |
| `solver_core/jacobi.py` | Jacobi public entry point |
| `solver_core/gauss_seidel.py` | Gauss-Seidel public entry point |
| `solver_core/_iterative.py` | Preconditions, accepted reordering, handwritten sweeps, risk policy, finite-history retention |
| `solver_core/convergence.py` | Separate iteration matrices, spectral radius, dominance/SPD assessment, dual stopping tests |
| `solver_core/diagnostics.py` | Shared original-system residuals/backward error, finite conditioning diagnostics |
| `solver_core/trace.py` | Complete versioned JSON traces with bounded payloads and exact rational preservation |
| `solver_core/report.py` | Immutable report data containing the original system, result, and display settings |
| `solver_core/models.py` | Validated options, row metadata, diagnostics, iteration records, and outcomes |

Direct solvers now reuse `diagnostics.py`; their numerical behavior and exact
arithmetic remain covered by all existing tests. No new runtime dependencies
were introduced.

## Numerical behavior verified

- Jacobi reads only the previous vector; Gauss-Seidel uses newly updated entries.
- Every iteration uses unrounded binary64 values, including residual computation.
- Convergence requires both normalized backward error and normalized step change
  at or below the requested tolerance.
- Iteration limits default to 25 and are capped at 500. A last iterate is not
  labeled a solution on budget exhaustion or numerical breakdown.
- Strict dominance uses bipartite matching. Non-zero-diagonal fallback is a
  separate explicit option, and equation mappings also move the RHS.
- SPD is a sufficient-condition diagnostic for Gauss-Seidel, not Jacobi.
  Method-specific spectral radii determine additional convergence assessments.
- Convergence risk is declined by default. An explicit override permits bounded
  execution, whose outcome follows the actual trace.
- Numerical breakdown preserves the last complete finite iteration. No partial
  sweep, NaN, or Infinity is serialized.
- Exact direct solutions satisfy their original rational equations. Iterative
  methods reject exact input instead of silently converting it.
- Equation permutations and non-zero row scaling preserve solutions in generated
  test systems; generated results agree with independent NumPy oracles.
- Rectangular direct classification, parametric solutions, and RREF invariants
  remain valid. Maximum 12-by-12 iterative systems are covered.
- Trace/report serialization preserves full precision and structured exact
  rationals, independently of display decimal places.

## Verification results

Executed on the project's Python 3.12 environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
```

Results: **324 tests passed**, Ruff lint/format checks passed, and strict mypy
passed for **23 source files**. This adds 105 test cases, including Hypothesis
properties with multiple generated examples, to the previous 219 passing tests.
The core contains no FastAPI or API-layer imports. Frontend code and dependencies
were unchanged; frontend checks were not rerun for this Python-only batch.

## Calling the new core

```python
from solver_core.jacobi import solve_jacobi
from solver_core.models import IterationOptions
from solver_core.parsing import parse_system
from solver_core.report import build_report, serialize_report
from solver_core.trace import serialize_trace

system = parse_system([["4", "1"], ["2", "3"]], ["1", "2"])
result = solve_jacobi(
    system,
    options=IterationOptions(
        initial_guess=(0.0, 0.0),
        tolerance=1e-8,
        max_iterations=25,
        auto_reorder_for_diagonal_dominance=True,
        auto_reorder_for_nonzero_diagonal=False,
        run_despite_convergence_risk=False,
    ),
)
trace_json = serialize_trace(result)
report_json = serialize_report(build_report(system, result))
```

`solve_gauss_seidel` accepts the same options. `last_iterate` is always available;
`solution` is populated only for `converged`. See `docs/numerical-policy.md` for
the formulas, precondition errors, risk semantics, and breakdown behavior.

Phase 1 delivers report data, as specified in Section 23. Markdown/LaTeX rendering
and downloads belong to Phase 4. Solver HTTP routes and generated contracts are
the next Phase 2 work and await user verification and approval.
