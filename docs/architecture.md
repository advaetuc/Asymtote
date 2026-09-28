# Architecture

## Deployment topology

Augmentr is a single Vercel project combining a Next.js frontend and a Python/FastAPI backend, deployed together rather than as two separately hosted services.

- **Routing:** `vercel.json` maps `/api/:path*` to a single ASGI serverless entrypoint, `api/index.py` (`app = create_app()`), with a 15-second max duration.
- **Local vs. remote proxy:** Local development runs FastAPI/Uvicorn on `127.0.0.1:18000` (`npm run dev:api`), proxied through Next.js. Local production E2E builds enable the port-18000 rewrite via `AUGMENTR_LOCAL_API_PROXY=1`. The presence of the `VERCEL` platform environment variable disables localhost rewrites and FastAPI’s interactive `/api/docs`; `/docs` is not configured. The production `/api/:path*` Vercel rewrite remains active.
- **Why one project instead of a separate API host:** avoids a second hostname, avoids `Access-Control-Allow-Origin: *`, and lets the same-origin Fetch Metadata guard (`Sec-Fetch-Site` + `Origin` validation) protect all browser traffic while still allowing no-`Origin` CLI access. See [`decisions.md`](decisions.md) for the full reasoning and the alternative (Reflex + WebSocket state) that was considered and rejected.

## Backend

- **Runtime:** Python 3.12, pinned via `.python-version`, `pyproject.toml`, and `uv.lock`. FastAPI, Pydantic, and NumPy are the only direct production dependencies, alongside their required transitive dependencies — no SciPy, no database, no queue.
- **Numerical core (`solver_core/`):** Portable, with zero Vercel coupling, so it can move to a container host without rewriting anything numerical. Implements:
  - Exact rational arithmetic (`fractions.Fraction`) for a bounded direct-method mode, and float64 for everything else — computation precision and display precision are kept as separate concerns; a `≈` marker distinguishes an approximate display fraction from an exact result.
  - Scale-aware tolerances for pivot detection, zero tests, residual evaluation, and rank calculation — never a single hardcoded epsilon threshold.
  - Rank-based singularity/consistency classification (not determinant equality): `rank(A) == rank([A|b]) == n` → unique solution; `rank(A) == rank([A|b]) < n` → infinitely many; `rank(A) < rank([A|b])` → inconsistent.
  - Partial pivoting by default for all floating-point elimination; the system never computes `A⁻¹` to solve.
  - Row-permutation search for diagonal dominance, solved as a bipartite matching problem between rows and diagonal positions — the original equation order is always shown alongside any reordering, and only rows (not variables) are ever reordered.
- **API layer (`api_models/`, `api_app/`):** `requests.py`, `responses.py`, `services.py`, `errors.py`, `observability.py`. Enforces token grammar, rejects unknown request properties, attaches an `X-Request-ID` correlation header, logs one structured JSON event per request, and applies cooperative timeouts.
- **Cold start / bundle:** earlier platform verification reported a 32.5 MB function, a 1.07s cold start, and a ~111ms warm 12×12 Gaussian solve. These are historical observations, not current-build size guarantees or latency targets; see [platform evidence](preview-verification/platform-evidence.json) and the accepted visibility limit in [D11](decisions.md#d11--accepted-platform-artifact-visibility-limit).

## Frontend

- **Framework:** Next.js 16 (App Router, Turbopack) with TypeScript and Tailwind CSS.
- **Routes:** `/` (landing), `/learn` (method primer), `/solve` (the entire stateful solver workspace — matrix entry, method selection, configuration, and results all live in one client workflow to avoid route-level state synchronization).
- **Solver workflow state machine:** explicit states, not a bag of booleans —
  `DIMENSIONS → MATRIX_INPUT → ANALYZING → METHOD_SELECTION → METHOD_CONFIGURATION → SOLVING → RESULTS`, with support for moving back to an earlier stage without losing compatible data. Draft state persists to `sessionStorage` only — nothing solver-related is stored server-side.
- **Rendering:** KaTeX for formula rendering and print/report views; lazy-loaded Plotly.js (strict distribution; historical Phase 5 measurement: ~4.95 MB raw / ~1.5 MB gzip) for CSP-compliant 2D/3D WebGL geometry — 2D for square 2×2 systems, 3D for square 3×3 systems, degenerate cases get an algebraic explanation instead of invented geometry. The iterative-method convergence/residual chart renders in the Steps panel alongside the iteration table, not in Visualize.
- **Design system:** Swiss/International Typographic Style grid discipline (strong grid, flush-left text, controlled asymmetry) combined with restrained glassmorphism (low-opacity surfaces, subtle backdrop blur, thin borders) for major panels only. The implemented font stack is Arial/Helvetica/sans-serif for body text and Cascadia Code/SFMono-Regular/Consolas/monospace for code and numeric tokens; the proposed Space Grotesk/Inter fonts have not been introduced.

## API surface

- `GET /api/health` — health probe.
- `GET /api/openapi.json` — live JSON OpenAPI schema.
- `POST /api/v1/analyze` — matrix shape, numerical rank, system classification, condition number, diagonal dominance, SPD/spectral properties, and per-method eligibility with diagnostic reasons.
- `POST /api/v1/solve` — discriminated-union endpoint executing the selected method: full elimination snapshots or iteration histories, applied row permutations, solution vectors / parametric free-variable forms / contradiction witnesses, and residual/backward-error diagnostics against the original (unreduced) system.

## Contract pipeline

FastAPI/Pydantic is the single source of truth for the API schema — never maintain two manually duplicated type systems.

```
create_app()  →  scripts/export_openapi.py  →  docs/openapi.json  →  openapi-typescript  →  lib/contracts/api.generated.ts
```

`npm run contracts:check` runs in CI and fails the build if the generated TypeScript types have drifted from the current backend schema.

## Testing & audit surface

Counts below are the most recently confirmed figures (post-rebrand regression coverage), not a fixed target — they grow as gates and features add cases. Treat the latest completion/verification report as ground truth over this table.

| Suite | Count (as of last confirmation) |
|---|---|
| Python (pytest: unit, property-based, concurrency, API) | 472 |
| Vitest (unit/component) | 139 |
| Playwright, local E2E (desktop Chromium + mobile Pixel 7) | 46 |
| Playwright, remote E2E | 48 |
| Remote HTTP verification | 70 requests / 718 assertions (two independent passes) |
| `@axe-core/playwright` WCAG A/AA accessibility checks | included in the E2E suites, 0 violations |
| `ruff`, `mypy --strict` (30 source files), `npm run audit:runtime` | clean / under the 200 MB runtime-closure budget |

## Non-negotiable resource and numeric bounds

- Request body: 65,536 bytes, enforced before JSON parsing (including chunked transfers — 65,537 bytes is verified to fail with HTTP 422).
- Matrix dimensions: 1 to 12 equations/unknowns. Iterative iteration cap: 500. Token length: ≤48 characters. Exact rational intermediates: ≤4096 bits.
- Timeouts: 5s body reception (HTTP 408), 5s cooperative numerical budget (checked during elimination and iterative sweeps), 10s whole-request deadline (HTTP 504), 15s Vercel platform ceiling.
- `vercel.json`'s `functions["api/index.py"].excludeFiles` glob must stay ≤256 characters (currently a regression-tested brace-expansion string).
- Runtime closure must stay under 200 MB (`npm run audit:runtime`); the earlier dashboard reported 32.5 MB, while the local dependency audit measured about 49.5 MiB. These are different measurements, not proof of the current deployed artifact’s exact contents.
- Application logs and error responses never contain matrix coefficients, rejected input tokens, unknown validation field names, query strings, or stack traces.

## Current identity and release evidence

The repository is [advaetuc/Augmentr](https://github.com/advaetuc/Augmentr), and production is [augmentr-solvr.vercel.app](https://augmentr-solvr.vercel.app). The local `TULYA` path is intentionally retained. The browser draft key `tulya.draft.v1` and Python request logger `tulya.requests` remain compatibility identifiers; the latter is not client storage.

The guard compares request metadata and the current request host; it has no domain allowlist. Production CSP uses `connect-src 'self'` and `frame-ancestors 'none'`. There is no configured `metadataBase`, absolute canonical URL, sitemap, or robots URL to rename. See [decisions](decisions.md) for the precise Origin fallback and inline-style exception.

[Numerical policy](numerical-policy.md) describes the tolerance rules. [Release summary](rebrand-summary-report.md) distinguishes fresh local checks from the earlier remote verification. The [history index](history/README.md) preserves phase and rebrand provenance; [backlog](backlog.md) tracks operational follow-ups.
