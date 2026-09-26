# TULYA

Educational linear equation solver. Phase 0 provides the application scaffold.
Phase 1 foundations now include strict numeric parsing, immutable domain models,
resource bounds, and tolerance policy. Gaussian elimination, Gauss-Jordan RREF,
and rank classification are implemented and tested in float64 and exact modes.
Phase 1 now also includes row matching, float64 Jacobi and Gauss-Seidel, convergence
diagnostics, complete traces, and structured report data. Phase 2 adds typed
analysis/solve endpoints, correlated request logs, and generated API contracts.
The interactive solver UI awaits Phase 3.

## Requirements

- Python 3.12.x (`requires-python = "~=3.12.0"`).
- Node 22.23.3 and npm 10.9.9 (`.nvmrc`, `package.json`).
- uv 0.12.19 for the Python lock workflow.

## Windows setup

Run from the repository root with Node 22/npm available on PATH:

```powershell
.\scripts\scaffold.ps1
py -3.12 -m venv .tools\bootstrap
.\.tools\bootstrap\Scripts\python.exe -m pip install uv==0.12.19
$env:Path = "$(Join-Path $PWD '.tools\bootstrap\Scripts');$env:Path"
uv sync --locked
npm ci
```

If using the project-local Node installed during Phase 0 in this workspace:

```powershell
$env:Path = "$(Join-Path $PWD '.tools\node-v22.23.3-win-x64');$env:Path"
```

That ignored tool directory is not part of a clean checkout; install the version
in `.nvmrc` through your normal Node installation workflow on other machines.

For focused development, open two PowerShell terminals with the same environment:

```powershell
# Terminal 1
npm run dev:api
```

```powershell
# Terminal 2
npm run dev
```

Visit `http://localhost:3000`. The development proxy makes
`http://localhost:3000/api/health` reach Python at port 18000 without browser CORS.
The Python health endpoint is also accessible at `http://127.0.0.1:18000/api/health`.

API documentation is at `http://127.0.0.1:18000/api/docs`. See
[API contracts](docs/api-contracts.md) for request examples and outcome handling.
After changing a backend schema, regenerate both committed contract artifacts:

```powershell
npm run contracts:generate
npm run contracts:check
npm run typecheck
```

OpenAPI is generated into `docs/openapi.json`, and `openapi-typescript` generates
`lib/contracts/api.generated.ts`. CI rejects stale artifacts and compiles the
generated types alongside the project. Do not edit generated contracts manually.

Deployment-parity development requires a separately installed, security-reviewed
Vercel CLI and linking the intended Vercel project:

```powershell
npm run dev:integrated
```

The CLI is deliberately outside application dependencies. Version 60.0.1's
transitive security findings must be addressed or an appropriate alternative
version selected during deployment work; no Vercel account was linked here.

## Checks

```powershell
npm run lint:python
npm run typecheck:python
npm run test:python
npm run check
npx playwright install chromium
npm run test:e2e
```

The browser smoke test starts its own frontend and backend; stop other processes
on ports 3000 and 18000 first. It checks the landing page and same-origin health
route. It is a local integration check, not a Vercel preview test.

`.github/workflows/ci.yml` installs locked dependencies, runs Python and frontend
checks, builds Next.js, and runs the Chromium integration smoke test. CI expands
to numerical, contract-generation, and full workflow gates in later phases.

## Dependency maintenance

Use npm only and retain `package-lock.json`. Update exact manifest versions and
regenerate the lock with `npm install`; use `npm ci` for reproducible installs.
Use `uv lock` when editing Python dependencies and `uv sync --locked` otherwise.
Keep `pyproject.toml` authoritative. Vercel installs runtime dependencies from
root Python metadata; the development group is not required by the function.

## Vercel target

One project serves Next.js at `/` and the FastAPI function under `/api/*`.
`vercel.json` selects Next.js and routes the API prefix to `api/index.py`.
The Python entrypoint exposes `app`; there is no persistent backend state.
Use Python 3.12 and Node 22 in project settings. No API keys are required.
Preview deployment and routing verification are deferred to Phase 5; Phase 0
does not claim a deployed or production-ready numerical application.

See [architecture](docs/architecture.md) and [numerical policy](docs/numerical-policy.md).
