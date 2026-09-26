# Phase 3 — Frontend solver workflow

Implemented for the user verification gate on 2026-09-26.

## Acceptance criteria

- Typed same-origin analyze/solve client uses the generated contract, schema-based
  runtime validation, correlation IDs, cancellation, stale-response protection,
  and distinct mathematical/validation/server/network/protocol outcomes.
- Editable rectangular coefficient matrices support 1–12 equations and unknowns,
  arrow and Tab navigation, rectangular paste, resizing, and inline cell errors.
  Six presets cover unique, infinite, inconsistent, ill-conditioned,
  permutation-recoverable, and convergence-risk examples.
- On-demand analysis shows ranks, classification, conditioning, diagonal dominance,
  method-specific SPD/spectral diagnostics, and method eligibility reasons.
- Controls cover exact/float arithmetic, decimal/fraction display and precision,
  initial guesses, tolerance, iteration limits, row-reordering strategies, and
  explicit risk consent. The browser preserves full-precision returned values.
- Direct replay identifies pivots, source/target rows, swaps, scaling, elimination,
  free-variable forms, contradiction witnesses, and Gaussian back substitution.
- Iterative inspection shows the applied permutation, all completed iterations
  through pagination, both convergence metrics and target, and original-system
  residual/backward error. Non-convergence is never labeled a solution.
- `/learn` explains the classifications and methods. Responsive layouts, explicit
  labels, keyboard controls, live request status, and result focus support access.

## Verification

| Check | Result |
| --- | --- |
| Vitest unit/component tests | 86 passed across 6 files |
| TypeScript and Next.js route generation | Passed |
| ESLint, zero warnings | Passed |
| Next.js production build | Passed |
| OpenAPI and generated TypeScript freshness | Passed |
| Python numerical/API regression suite | 429 passed |

Frontend fixtures contain 17 real responses produced by the local FastAPI
TestClient. Tests cover all four method workflows, replay boundaries, exact large
rationals, contradictory/parametric results, iteration outcomes, pagination, risk
consent, local/server validation, cancellation, stale requests, and draft recovery.
Live browser verification exercised preset loading, analysis, Gaussian solving and
operation replay, and Jacobi convergence against the backend on port 18000.
The matrix controls and converged iterative result were also reviewed at a
390-pixel viewport; the page had no horizontal overflow and the chart fit its panel.

## Review and next phase

Run the backend with `npm run dev:api` and frontend with `npm run dev`, then open
`http://localhost:3000/solve`. Report downloads, geometric visualizations, and the
expanded Playwright workflow suite are deferred to Phase 4. No deployment was
performed and no new dependencies were added. Phase 3 awaits user verification.
