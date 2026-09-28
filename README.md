# Augmentr

A linear system solver that shows its work. Enter an augmented matrix from 1×1 to 12×12, pick a method, and get back the full derivation — every row operation or iteration, the residual and backward error, rank and conditioning, and a 2D/3D visualization where the dimensions allow it — not just an answer.

**Live:** [augmentr-solvr.vercel.app](https://augmentr-solvr.vercel.app)

[![CI](https://github.com/advaetuc/Augmentr/actions/workflows/ci.yml/badge.svg)](https://github.com/advaetuc/Augmentr/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Repository:** [advaetuc/Augmentr](https://github.com/advaetuc/Augmentr)

---

## What it does

Four solver methods, each with its own eligibility check against whatever matrix you enter:

| Method | Category | Notes |
|---|---|---|
| Gaussian elimination | Direct | Partial pivoting, row-echelon form, back-substitution. Exact rational or float64 arithmetic. |
| Gauss–Jordan elimination | Direct | Reduced row-echelon form, including the parametric form for infinite-solution systems. |
| Jacobi iteration | Iterative | Configurable initial guess, tolerance, and iteration budget (default 25, capped at 500). |
| Gauss–Seidel iteration | Iterative | Same controls as Jacobi; optional row reordering for diagonal dominance, always shown explicitly. |

Analysis reports classification (unique / infinite / inconsistent), rank and condition-number diagnostics. Solves return structured mathematical outcomes, including explicit non-convergence and numerical-breakdown states that are never mislabeled as solutions.

## Tech stack

- **Frontend:** Next.js 16 (App Router, Turbopack) + TypeScript + Tailwind CSS. KaTeX for formula rendering, lazy-loaded Plotly.js (strict CSP-compliant distribution) for 2D/3D geometry.
- **Backend:** FastAPI + Pydantic + NumPy, Python 3.12, deployed as a single ASGI serverless function on Vercel. `fractions.Fraction` powers the bounded exact-rational direct-method mode.
- **Contracts:** FastAPI/Pydantic is the single source of truth. `docs/openapi.json` is generated from it and `lib/contracts/api.generated.ts` is generated from that — CI fails if either drifts from the backend schema.
- **One deployment, two runtimes:** Next.js serves `/`, FastAPI serves everything under `/api/*`, same Vercel project, same origin — no separate API host, no permissive CORS.

See [`docs/architecture.md`](docs/architecture.md) for the full picture and [`docs/decisions.md`](docs/decisions.md) for why it's built this way instead of the alternatives that were considered and rejected.

## Local development

Prerequisites: Python 3.12 (pinned via `.python-version`), [`uv`](https://docs.astral.sh/uv/) (CI pins 0.12.19), Node 22.x and npm 10.x. Run from the repository root; its local directory name can remain `TULYA`.

```powershell
# Install the locked dependencies once.
uv sync --locked
npm ci

# Backend terminal: 127.0.0.1:18000
npm run dev:api

# Frontend in a separate terminal: http://localhost:3000
npm run dev
```

Next.js automatically proxies `/api/*` to `127.0.0.1:18000` in local development. For a local production build, keep the backend running and set the proxy flag **before building**:

```powershell
$env:AUGMENTR_LOCAL_API_PROXY = "1"
npm run build
npm start
```

The `VERCEL` platform environment variable disables the localhost rewrite. FastAPI's interactive `/api/docs` is disabled on Vercel; `/docs` is not configured. `/api/openapi.json` remains available.

## Testing

```powershell
npm run test:python      # pytest: unit, property-based, concurrency, and API tests
npm run lint:python      # ruff
npm run typecheck:python  # mypy --strict
npm run check             # frontend lint, types, Vitest unit/component tests, and a production build
npm run test:e2e          # local Playwright, desktop Chromium + mobile Pixel 7
npm run contracts:check   # fails if generated TS types have drifted from the OpenAPI schema
npm run audit:runtime     # measures the installed Python runtime closure against a 200 MB budget
```

Install the local browser once with `npx playwright install chromium`. For production CSP coverage, build with the proxy flag above, set `$env:E2E_PRODUCTION = "1"` and `$env:E2E_REUSE_SERVERS = "0"`, stop manually started servers on ports 3000/18000, and run the E2E suite so it manages both servers. The runtime audit measures local dependencies, not the deployed Vercel artifact.

See [`docs/deployment.md`](docs/deployment.md) for the remote verification suite that runs against the live deployment.

## Deployment

Single Vercel project, `vercel.json` routes `/api/:path*` to `api/index.py` (`app = create_app()`, 15s max duration). Full details, including the resource/numeric bounds the backend enforces and the rollback procedure, are in [`docs/deployment.md`](docs/deployment.md).

## Project layout

```
api/                 ASGI entrypoint (api/index.py)
api_models/          request/response schemas
api_app/             application factory, services, errors, observability
solver_core/          portable numerical engine — zero Vercel coupling
app/                   Next.js routes: /, /learn, /solve
components/            matrix editor, method selector, results panels
lib/contracts/         generated TypeScript types from the OpenAPI schema
docs/                  architecture, decisions, deployment, and build history
scripts/               OpenAPI export, remote preview verification
```

## Contributing

Open an issue or PR. The `quality` job in [ci.yml](.github/workflows/ci.yml) runs contract freshness, Python and frontend lint/types/tests, the production build, dependency audits, and local Playwright including axe/CSP checks. Require a successful run before merging; repository branch-protection settings are owner-managed. Current follow-up work is tracked in [docs/backlog.md](docs/backlog.md), and release evidence in [docs/rebrand-summary-report.md](docs/rebrand-summary-report.md) and [docs/history](docs/history/).

## License

MIT © 2026 advaetuc. See [LICENSE](LICENSE).
