# Augmentr

[GitHub repository](https://github.com/advaetuc/Augmentr) ·
[Live demo](https://augmentr.vercel.app) (new domain; activation and verification pending rebrand Gate 5).

An educational linear-equation solver built with Next.js 16, React 19,
TypeScript, FastAPI, and Python 3.12. Gaussian and Gauss–Jordan methods support
bounded exact rational arithmetic and float64 partial pivoting. Jacobi and
Gauss–Seidel use unrounded float64 iteration with residual and step-change tests.

The workspace supports 1–12 equations and unknowns, rank and conditioning
analysis, explicit row reordering, replayable traces, deterministic report
exports, printable KaTeX reports, and lazy interactive 2D/3D geometry.
No account, database, API key, background worker, or application WebSocket is required.

## Windows setup

Install Python 3.12, Node 22.23.3, npm 10.9.9, and uv 0.12.19. From the repository root:

```powershell
py -3.12 -m venv .tools\bootstrap
.\.tools\bootstrap\Scripts\python.exe -m pip install uv==0.12.19
$env:Path = "$PWD\.tools\bootstrap\Scripts;$env:Path"
uv sync --locked
npm ci
```

This workspace also has an ignored local Node installation. If needed:

```powershell
$env:Path = "$PWD\.tools\node-v22.23.3-win-x64;$env:Path"
$env:UV_CACHE_DIR = "$PWD\.tools\uv-cache"
```

In separate terminals, run `npm run dev:api` and `npm run dev`. Open
`http://localhost:3000`. The local `/api/*` proxy reaches FastAPI on
`127.0.0.1:18000`; there is no browser CORS configuration. Interactive API docs
are available locally at `http://127.0.0.1:18000/api/docs`.

## Release verification

```powershell
npm run lint:python
npm run typecheck:python
npm run test:python
npm run contracts:check
npm run audit:runtime
npm audit --audit-level=high
# Build a production frontend with a LOCAL integration proxy.
$env:AUGMENTR_LOCAL_API_PROXY = "1"
npm run check
npx playwright install chromium
$env:E2E_PRODUCTION = "1"
$env:E2E_REUSE_SERVERS = "0"
npm run test:e2e
Remove-Item Env:AUGMENTR_LOCAL_API_PROXY, Env:E2E_PRODUCTION, Env:E2E_REUSE_SERVERS
```

Stop development servers before requiring fresh test servers. Playwright owns
ports 3000 and 18000 and fails on collisions; it never silently changes ports.
For this workspace's existing browser cache, set
`$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\.tools\browsers"` before installing or testing.
For development-mode tests, omit `E2E_PRODUCTION`; healthy existing Augmentr servers
can be reused when `E2E_REUSE_SERVERS` is not `0`. A health preflight checks both
backend and frontend API routes.

CI installs locked dependencies, checks Python lint/types/tests, frontend
lint/types/unit tests, generated contracts, runtime size, dependency audit,
production build, and desktop/mobile Playwright workflows plus accessibility
and CSP checks. Browser failure artifacts are retained for seven days. The
workflow does not deploy. Branch protection must require its `quality` job.

## Contracts and dependency maintenance

FastAPI/Pydantic owns `docs/openapi.json`. Run `npm run contracts:generate` after
schema changes, then `npm run contracts:check`. The client imports the generated
`lib/contracts/api.generated.ts`; do not hand-edit it. Mathematical outcomes
use HTTP 200, validation failures 422, browser origin failures 403, reception
timeouts 408, computation deadlines 504, and unexpected failures generic 500.
Each response carries `X-Request-ID`.

Retain `package-lock.json` and `uv.lock`. Direct dependencies have exact pins.
Use `npm ci` and `uv sync --locked` for reproducible installs. Runtime Python
dependencies are only FastAPI, Pydantic, NumPy, and required transitive packages.
A second `requirements.txt` is unnecessary: Vercel supports the root
`pyproject.toml` and `uv.lock`.

## Deployment

One Vercel project serves Next.js and the thin `api/index.py` FastAPI function.
Production rewrites belong to `vercel.json`; Vercel builds always disable the
local backend proxy. No environment secrets are required. See `.env.example`
and the [deployment runbook](docs/deployment.md) for configuration, preview
verification, production promotion, logs, and rollback.

**No external deployment has been performed.** Preview validation and production
promotion require the owner's manual authorization. Local production E2E tests
cannot establish that Vercel's built artifact and routing work remotely.

See [architecture](docs/architecture.md), [numerical policy](docs/numerical-policy.md),
[API contracts](docs/api-contracts.md), and [Phase 5 verification](docs/phase-5-completion-report.md).
