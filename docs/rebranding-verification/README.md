# Augmentr

A linear system solver that shows its work. Enter an augmented matrix from 1×1 to 12×12, pick a method, and get back the full derivation — every row operation or iteration, the residual and backward error, rank and conditioning, and a 2D/3D visualization where the dimensions allow it — not just an answer.

**Live:** [augmentr.vercel.app](https://augmentr.vercel.app)
<!-- Update the badge URLs below to the renamed repo once Gate 4 of the rebrand is complete -->
<!-- ![CI](https://github.com/advaetuc/Augmentr/actions/workflows/quality.yml/badge.svg) -->
<!-- ![License](https://img.shields.io/github/license/advaetuc/Augmentr) -->

---

## What it does

Four solver methods, each with its own eligibility check against whatever matrix you enter:

| Method | Category | Notes |
|---|---|---|
| Gaussian elimination | Direct | Partial pivoting, row-echelon form, back-substitution. Exact rational or float64 arithmetic. |
| Gauss–Jordan elimination | Direct | Reduced row-echelon form, including the parametric form for infinite-solution systems. |
| Jacobi iteration | Iterative | Configurable initial guess, tolerance, and iteration budget (default 25, capped at 500). |
| Gauss–Seidel iteration | Iterative | Same controls as Jacobi; optional row reordering for diagonal dominance, always shown explicitly. |

Every solve returns a full classification (unique / infinite / inconsistent), rank and condition-number diagnostics, and — for iterative methods — an explicit non-converged state that is never mislabeled as a solution.

## Tech stack

- **Frontend:** Next.js (App Router, Turbopack) + TypeScript + Tailwind CSS. KaTeX for formula rendering, lazy-loaded Plotly.js (strict CSP-compliant distribution) for 2D/3D geometry.
- **Backend:** FastAPI + Pydantic + NumPy, Python 3.12, deployed as a single ASGI serverless function on Vercel. `fractions.Fraction` powers the bounded exact-rational direct-method mode.
- **Contracts:** FastAPI/Pydantic is the single source of truth. `docs/openapi.json` is generated from it and `lib/contracts/api.generated.ts` is generated from that — CI fails if either drifts from the backend schema.
- **One deployment, two runtimes:** Next.js serves `/`, FastAPI serves everything under `/api/*`, same Vercel project, same origin — no separate API host, no permissive CORS.

See [`docs/architecture.md`](docs/architecture.md) for the full picture and [`docs/decisions.md`](docs/decisions.md) for why it's built this way instead of the alternatives that were considered and rejected.

## Local development

Prerequisites: Python 3.12 (pinned via `.python-version`), [`uv`](https://docs.astral.sh/uv/), Node 22.x.

```bash
# Backend
uv sync
uv run uvicorn api.index:app --reload --port 18000

# Frontend (separate terminal)
npm install
npm run dev
```

Next.js proxies `/api/*` to `127.0.0.1:18000` locally. Set `AUGMENTR_LOCAL_API_PROXY=1` to enable this rewrite in a local production build (`npm run build && npm start`); it's automatically disabled whenever the `VERCEL` platform environment variable is present, along with the interactive Swagger UI routes (`/docs`, `/api/docs`).

## Testing

```bash
uv run pytest          # unit, property-based, concurrency, and API tests
uv run ruff check .
uv run mypy --strict .
npm run test            # Vitest unit/component tests
npm run test:e2e        # Playwright, desktop Chromium + mobile Pixel 7
npm run contracts:check # fails if generated TS types have drifted from the OpenAPI schema
```

See [`docs/deployment.md`](docs/deployment.md) for the remote verification suite that runs against the live deployment.

## Deployment

Single Vercel project, `vercel.json` routes `/api/:path*` to `api/index.py` (`app = create_app()`, 15s max duration). Full details, including the resource/numeric bounds the backend enforces and the rollback procedure, are in [`docs/deployment.md`](docs/deployment.md).

## Project layout

```
api/                 ASGI entrypoint (api/index.py)
api_models/           request/response schemas, services, errors, observability
solver_core/          portable numerical engine — zero Vercel coupling
app/                   Next.js routes: /, /learn, /solve
components/            matrix editor, method selector, results panels
lib/contracts/         generated TypeScript types from the OpenAPI schema
docs/                  architecture, decisions, deployment, and build history
scripts/               OpenAPI export, remote preview verification
```

## Contributing

Open an issue or PR. `npm run contracts:check`, `ruff`, `mypy --strict`, and the full test suite listed above all run in CI and are required to merge.

## License

<!-- Fill in once confirmed -->
