# Phase 2 API contracts

The authoritative contract is generated from FastAPI/Pydantic into
[`openapi.json`](openapi.json). The frontend imports generated types from
`lib/contracts/api.generated.ts`; there is no second handwritten interface layer.
Local base URL: `http://127.0.0.1:18000`. Interactive documentation: `/api/docs`.

## Input conventions

Coefficient, RHS, and initial-guess entries are **strings**, including integers,
decimals, scientific notation, and integer/integer fractions. The core's strict
parser validates every token; expressions, whitespace, non-finite values, and
numeric JSON coefficients are rejected. Existing magnitude, exponent, and
48-character token limits apply. Matrices have 1–12 rows and 1–12 columns, with
a matching RHS length. Unknown request fields are rejected.

The HTTP body limit is 65,536 bytes, enforced on received bytes before JSON
decoding, including chunked requests. Exceeding it returns a structured 422.

## Analyze

`POST /api/v1/analyze`:

```json
{
  "system": {"a": [["4", "1"], ["2", "3"]], "b": ["1", "2"]},
  "arithmetic_mode": "float64"
}
```

`arithmetic_mode` defaults to `float64`; `exact` uses rational classification.
The successful `analyzed` envelope includes:

- `request_id`, shape, and square flag;
- rank and classification with tolerance metadata;
- condition-number status and approximate digit loss;
- original strict-dominance status (`null` for rectangular matrices);
- strict-dominance and non-zero-diagonal row-permutation candidates;
- eligibility and an explanation for every method;
- diagnostic warnings.

Conditioning is always a float64 estimate, including when ranks are exact. It is
labeled with `conditioning_arithmetic_mode`. A non-finite estimate becomes a
structured `singular` or `unavailable` diagnostic.

`eligible: true` means a method can run **subject to** its explicit requirements.
Check `requires_row_reordering` and `requires_risk_override`. A row candidate
identifies its `purpose`; enable the corresponding solve option to accept it.
`order[j]` is the original equation moved to row j; variables never move.
An exact analysis marks iterative methods `requires_float64`; request a float64
analysis to assess their numerical preconditions.

## Solve

`POST /api/v1/solve`, direct example:

```json
{
  "system": {"a": [["4", "1"], ["2", "3"]], "b": ["1", "2"]},
  "method": "gauss_jordan",
  "options": {"arithmetic_mode": "exact"},
  "display": {"mode": "fraction", "decimal_places": 6}
}
```

Direct methods are `gaussian` and `gauss_jordan`. Their only option is
`arithmetic_mode`, defaulting to `float64`. Iterative fields are rejected.

Iterative example:

```json
{
  "system": {"a": [["4", "1"], ["2", "3"]], "b": ["1", "2"]},
  "method": "jacobi",
  "options": {
    "initial_guess": ["0", "0"],
    "tolerance": 1e-8,
    "max_iterations": 25,
    "auto_reorder_for_diagonal_dominance": true,
    "auto_reorder_for_nonzero_diagonal": false,
    "run_despite_convergence_risk": false
  },
  "display": {"mode": "decimal", "decimal_places": 6}
}
```

`gauss_seidel` uses the same options. Omitting options uses the displayed defaults
and a zero initial guess. A guess, when supplied, must have exactly n tokens.
Iterations use float64 only; an `arithmetic_mode` option is rejected. Tolerance
must be finite and between 1e-14 and 1e-2; the iteration budget is 1–500.
Display preferences never round internal arithmetic or raw response values.

The `completed` envelope contains:

| Field | Meaning |
| --- | --- |
| `request_id` | Correlates response and logs |
| `problem` | Original parsed system, dimensions, and arithmetic mode |
| `result` | The complete core direct or iterative result, discriminated by method |
| `conditioning` | Float64 estimate for the original coefficient matrix |
| `conditioning_arithmetic_mode` | Always `float64`, independent of exact solving |
| `report` | Version, method, accepted options, and separate display preferences |

`completed` means the computation produced a structured result. It does **not**
mean a unique solution exists or that iteration converged. For direct methods,
read `result.classification.classification`; for iteration, read `result.status`.
Direct traces are in `result.trace`; iteration records are in `result.history`.
Residuals are measured on the original system. Applied iteration row mappings
are in `result.reordering`. Gaussian/Gauss-Jordan row swaps are in their trace.

Infinite systems have a structured `parametric_solution`. Inconsistent systems
have contradiction rows and no solution. Non-converged iterations have a
`last_iterate`, available diagnostics/history, and `solution: null`. The statuses
are `converged`, `max_iterations_reached`, `convergence_risk_declined`, and
`numeric_breakdown`. Actual iteration history governs the outcome even when
diagnostics predict risk.

Exact values use `{"numerator": "1", "denominator": "10"}`. Integer strings
preserve precision beyond JavaScript's safe integer range. Float values remain
unrounded JSON numbers. `report.fraction_values` distinguishes exact values from
approximate fraction display. Combine `problem`, `result`, and `report` for later
report rendering; trace snapshots are not repeated in report metadata.

## Outcomes and errors

| HTTP | Payload | Interpretation |
| --- | --- | --- |
| 200 | `analyzed` | Classification and eligibility available |
| 200 | `completed` | Full solver result, including inconsistency or non-convergence |
| 200 | `numeric_breakdown` | Controlled numerical limitation before a full result could be produced |
| 422 | `error` | Invalid shape/token/options, ineligible method, or resource-policy violation |
| 500 | `error` with `internal_error` | Unexpected failure; generic message and correlation ID |

A top-level `numeric_breakdown` includes shape, arithmetic mode, optional selected
method, and a stable domain error code such as `rank_uncertain`. No classification
or successful solution is fabricated. If iteration began and failed, its regular
result instead retains the last complete finite history. Rational growth or trace
resource exhaustion returns a controlled 422, with a safe remediation message.

Errors contain `request_id`, an `error` object (`code`, `message`, `location`), and
`details`. Request validation includes up to 32 field issues with locations;
rejected values and exception internals are excluded. Unknown routes and wrong
HTTP methods also receive this error envelope with their normal 404/405 status.

## Correlation and logs

Clients may send `X-Request-ID` containing 1–64 ASCII letters, digits, underscores,
or hyphens. Otherwise a new UUID hex ID is generated. Every HTTP response includes
the final ID in that header; analysis, solve, and error bodies also contain it.

One JSON event is emitted through `tulya.requests` per request, including ID,
known route, HTTP method, selected solver, validated dimensions, elapsed
milliseconds, HTTP status, numerical outcome, and warning/error codes. Unexpected
failures include the exception type, but no message, traceback, or raw input.
Unknown paths are logged as `<unmatched>` to avoid storing arbitrary path data.
Fields unavailable during request validation are `null`. There is no persistence
of matrices or results.

## Contract workflow

```powershell
npm run contracts:generate
npm run contracts:check
npm run typecheck
```

The first command exports OpenAPI and runs the pinned `openapi-typescript`.
The second verifies both artifacts without changing them; CI fails if either is
stale. Generation preserves optional request defaults. Response defaults are
included in the serialized contract. Files use LF endings for reproducible
Windows/Linux checks. `scripts/export_openapi.py --output <path> --check` supports
checking another target and works independently of the current directory.

Phase 2 delivers the API and contracts. The interactive UI remains Phase 3;
Markdown/LaTeX report rendering remains Phase 4.
