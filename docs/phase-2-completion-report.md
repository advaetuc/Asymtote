# Phase 2 completion — API contracts

The approved API-contract phase is implemented and ready for verification.

## Delivered

| File | Responsibility |
| --- | --- |
| `api_models/requests.py` | Strict token-based system input, method-specific options, display preferences, discriminated solve requests |
| `api_models/responses.py` | Typed analysis, eligibility, solver/report metadata, controlled numerical outcomes, and errors |
| `api_app/__init__.py` | Factory with health, analyze, and solve endpoints and stable OpenAPI operation IDs |
| `api_app/services.py` | Request-to-core adaptation, eligibility, direct/iterative dispatch, and response assembly |
| `api_app/errors.py` | Safe structured validation, policy, and HTTP errors |
| `api_app/observability.py` | Bounded body intake, correlation IDs, generic unexpected-error handling, and one structured request log |
| `scripts/export_openapi.py` | Deterministic schema export and non-mutating stale check |
| `docs/openapi.json` | Generated OpenAPI contract |
| `lib/contracts/api.generated.ts` | Generated frontend types from the pinned openapi-typescript |
| `tests/python/test_api.py` | 105 API cases covering contracts, mathematical outcomes, failures, concurrency, privacy, limits, and schema generation |
| `tests/contracts/api-contracts.ts` | Compile-time request/output narrowing and invalid-contract checks |
| `docs/api-contracts.md` | Request examples, response semantics, logging, and contract workflow |

`api/index.py` remains the existing thin `app = create_app()` entrypoint. The
numerical core and dependency versions were unchanged. Package scripts and CI
now verify that OpenAPI and TypeScript artifacts are current. Generated files
use explicit LF endings for consistent Windows and Linux comparisons.

## Acceptance criteria met

- `POST /api/v1/analyze` returns shape, classification/ranks, conditioning,
  dominance, row-permutation candidates, and method eligibility with reasons.
- `POST /api/v1/solve` supports all four methods, exact direct arithmetic,
  full traces, original-system residual diagnostics, accepted row mappings,
  and report metadata. It preserves the distinction between exact and approximate
  fraction display.
- Inconsistent/infinite systems and iteration non-convergence are valid HTTP 200
  outcomes. Controlled rank uncertainty has its own HTTP 200 numerical-failure
  envelope. Input/precondition/resource failures return structured 422 errors.
  Unexpected exceptions and invalid server responses become generic 500s.
- Error payloads and logs exclude rejected values and exception messages. Every
  response carries a correlation ID. Logs contain only request metadata, outcome,
  duration, and diagnostic codes, with isolated context under concurrency.
- Body size is bounded before JSON parsing, including requests without a
  Content-Length header. Core limits and grammar remain authoritative.
- Public responses have typed models with forbidden extra properties; no public
  arbitrary dictionary result fields were introduced.
- Generated frontend types compile, including optional defaults, method-specific
  options, outcome discrimination, and exact integer strings.
- OpenAPI export matches the live application schema; stale-check tests verify
  failure without silently overwriting artifacts. CI checks both generated files.

## Verification

| Check | Result |
| --- | --- |
| Complete Python suite | **429 passed**, including all previous 324 tests and 105 new API tests |
| Ruff lint and formatting | Passed |
| Strict mypy | Passed for 28 source files |
| TypeScript compilation / Next.js route typing | Passed |
| Frontend ESLint | Passed |
| OpenAPI and generated TypeScript freshness | Passed |
| Live local Uvicorn on `127.0.0.1:18000` | Health, analyze, and Jacobi solve returned successful responses with correlation IDs |
| Temporary smoke-test process cleanup | Server stopped after verification |

Commands used for the repeatable checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
npm run contracts:check
npm run typecheck
npm run lint
```

The frontend runtime/UI did not change; a production frontend build and browser
workflow tests were not rerun for this phase. The live smoke test exercised the
actual local backend on the specified Windows port. No deployment was performed.

Phase 2 stops here for user verification. The next approved stage would be
Phase 3: the interactive frontend solver workflow.
