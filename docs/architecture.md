# TULYA architecture — Phase 0

The authoritative specification is `production_system_architecture_prompt.md`,
baseline 2026-09-25. The user's explicit phase gate takes precedence over the
document's instruction to continue directly into numerical implementation.

## Repository audit

The initial repository contained `.gitattributes`, a Node-oriented `.gitignore`,
a one-heading README, local VS Code settings, and an untracked Python environment.
There was no application, dependency manifest, lockfile, Next.js configuration,
Vercel configuration, or prototype architecture to preserve or remove.

The existing `venv` uses Python 3.12.0 and initially contained pip 23.2.1 only.
The agent shell exposed Node 24.19.0 without npm. A checksum-verified local Node
22.23.3 / npm 10.9.9 toolchain is used for this scaffold; `.tools` is ignored.
The existing environment and editor settings are preserved.

## Boundaries and dependency graph

Browser → Next.js → same-origin HTTP `/api/*` → `api/index.py` → `api_app`.
In Phase 2, the application layer will call `solver_core`; the core must never
import FastAPI or hosting code. Pydantic HTTP schemas belong in `api_models`.
The extra `api_app` package implements the factory suggested in Section 11.1
and keeps the Vercel entrypoint thin.

Implementation order after Phase 0:

1. Limits and safe token parser.
2. Domain models and centralized tolerance policy.
3. Rank classification and direct float/exact methods.
4. Row matching, iterative methods, convergence diagnostics, traces, report data.
5. Pydantic API contracts and generated TypeScript definitions.
6. Frontend workflow, then lazy visualization and report export.
7. Integration, accessibility, security, and deployment verification.

Inputs remain strings until Python parses them. The browser may validate input
shape for usability; numerical decisions remain authoritative in Python.
No application WebSockets, database, Redis, background queue, or agent runtime.
Next.js development hot reload is framework tooling, not an application protocol.

## Dependency decisions

All direct package versions are exact and checked against npm/PyPI on 2026-09-25.
The complete resolved dependency graphs are recorded in `package-lock.json` and
`uv.lock`. Python runtime dependencies are FastAPI, Pydantic, and NumPy only.
Uvicorn, Hypothesis, HTTPX2, pytest, Ruff, and mypy are development dependencies.
Starlette 1.7 deprecates its HTTPX fallback; HTTPX2 2.13.1 is pinned for TestClient
after verifying the installed library and the package's official PyPI metadata.
The build backend is Hatchling. TypeScript remains 5.9.3 even though a newer
major exists. Node remains 22.x. React and React DOM share the same release.
Plotly is installed but not imported by any landing-page module.

ESLint 9.39.5 is retained because the current Next.js React, import, and
accessibility plugins declare compatibility with ESLint 9 but not 10. npm marks
the 9.x line unsupported; reassess this development-tool constraint when those
plugins support 10. No forced peer-dependency installation is used.

The Vercel CLI is external deployment tooling, not a project dependency. The
trial of CLI 60.0.1 introduced 29 audit findings (including a critical tar
dependency), all through its dependency graph, so it was removed before delivery.
Choose and audit the deployment CLI during the Phase 5 preview work. The optional
`dev:integrated` command expects a separately installed `vercel` executable.

## Hosting adjustment

The current [Vercel file-based Python documentation](https://vercel.com/docs/functions/runtimes/python/api-directory)
maps `api/index.py` to `/api`; it does not promise that every `/api/*` route
automatically reaches that function. The scaffold therefore sets the Next.js
framework explicitly and supplies one API-prefix rewrite to `/api`.
This is a justified configuration addition to the specification's preference
for auto-detection. It avoids adopting the separately documented beta Services
architecture. Actual Vercel behavior must be checked in the Phase 5 preview.

For focused local development, Next.js proxies `/api/*` to Uvicorn on port 18000.
Port 8000 could not be bound on the current Windows host even outside the
sandbox; port 18000 was verified available and is used consistently in scripts.
This proxy is disabled under Vercel and in production builds. `vercel dev` is
also available for deployment-parity testing after the project is linked.
No deployment has been performed in Phase 0.

## Phase boundary

Phase 0 supplies a working landing page, typed health endpoint, tooling, and CI
skeleton. Empty directories are recreated by `scripts/scaffold.ps1`; they do not
contain dummy future implementations. Numerical algorithms, solve/analyze
endpoints, complete product routes, OpenAPI generation, custom fonts, and
deployment hardening belong to their later phases.

## Phase 1 foundation update

The first approved part of Phase 1 implements constants, domain errors,
Pydantic domain models, strict parsing, and centralized comparison tolerances.
Following the user's explicit request, the core uses Pydantic for immutable,
validated domain values instead of limiting models to standard dataclasses.
It remains independent of FastAPI, HTTP, and Vercel. Input models preserve token
strings; parsed models use float or Fraction explicitly. No solver methods or
classification implementation have been added at this verification gate.

The next approved batch adds `classify_system`, `solve_gaussian`, and
`solve_gauss_jordan`, plus their unit/property tests. `_elimination.py` owns
handwritten guarded row operations; `_direct.py` assembles solutions, parametric
expressions, traces, and original-system residual diagnostics. Classification
depends on the reduction primitive, never on a public solver, avoiding circular
dependencies. No API or frontend changes are part of this batch.

## Phase 1 completion

`permutations.py` supplies independent bipartite matching utilities for strict
dominance and safe non-zero diagonals. `diagnostics.py` owns original-system
residual metrics for direct and iterative solvers, plus float conditioning.
`convergence.py` supplies method-specific iteration matrices, spectral and SPD
diagnostics, and the dual stopping test. `_iterative.py` manages preconditions,
accepted row reordering, guarded sweeps, risk consent, and bounded histories;
`jacobi.py` and `gauss_seidel.py` expose the public solver entry points.

All results and trace records are immutable Pydantic domain models. `trace.py`
serializes complete versioned numerical records, and `report.py` combines a
source system and result without duplicating trace snapshots. The numerical core
imports neither FastAPI nor API models. It accepts typed values and reports
transport-independent errors. The future Phase 2 boundary will parse user tokens,
map domain outcomes to HTTP contracts, and generate frontend types. Phase 4 will
render report data into Markdown and LaTeX. No solver HTTP routes were added here.

## Phase 2 API boundary

`api/index.py` remains the thin application-factory entrypoint. `api_app` composes
the health, analyze, and solve routes. Synchronous numerical handlers run through
FastAPI's worker-thread dispatch. `services.py` adapts validated string-token
requests to the independent numerical core. Mathematical classifications and
iteration outcomes stay in typed HTTP 200 results; invalid input and resource
policies use 422, and unexpected failures use a generic 500 envelope.

`api_models/requests.py` discriminates solve requests by method and delegates all
numeric grammar checks to the existing parser. `responses.py` reuses core result
models for full traces and structured exact values. Problem metadata holds the
original system; report metadata adds options and display preferences without
duplicating the result's trace. Exact classification and floating conditioning
are explicitly distinguished.

Pure ASGI middleware bounds request bodies before JSON parsing, assigns or
validates a correlation ID, attaches it to every HTTP response, and emits one
JSON metadata event per request. It also catches unexpected exceptions before
response transmission. Matrices, vectors, rejected token values, and exception
messages are excluded from those logs. Context is stored per request, not in
shared solver state.

FastAPI/Pydantic owns the contract. `scripts/export_openapi.py` writes deterministic
OpenAPI; the pinned `openapi-typescript` creates the TypeScript contract. Check
modes fail without modifying stale files, and CI runs both checks. Type-level
examples in `tests/contracts/api-contracts.ts` verify default options, method
discrimination, exact integer strings, and outcome narrowing. Generated files
use LF endings on Windows and Linux for reproducible comparisons.

The local backend and Next.js development proxy continue to use port 18000.
No frontend workflow or deployment work is included in Phase 2.

## Phase 3 frontend workflow

Server-rendered route shells compose the client solver workspace. Its reducer
tracks dimensions, matrix input, analysis, method selection/configuration, solve,
and results. AbortController and request sequence ownership prevent canceled or
superseded responses from changing the current draft. Session storage retains
validated drafts within a tab; convergence-risk consent is reset on restoration.

`lib/api` derives HTTP types exclusively from `api.generated.ts`. Runtime response
validation follows the generated OpenAPI schemas. Mathematical HTTP 200 outcomes
remain distinct from validation, server, network, and protocol failures. Correlation
IDs accompany requests and remain visible in diagnostics and error messages.

The browser validates token syntax for feedback while preserving strings for the
backend's authoritative parsing, magnitude checks, and numerical decisions.
Direct inspectors replay returned snapshots; iterative inspectors plot returned
backward error and normalized step change. Formatting never alters these values.
Exact rational formatting uses BigInt, including decimal rounding, and approximate
fraction displays are explicitly marked. A lightweight SVG convergence chart avoids
loading Plotly; geometric plots and report downloads remain Phase 4 work.

## Phase 4 reporting and geometric views

`lib/reports/render.ts` builds one deterministic document from the generated
solve/analysis contracts. Markdown, standalone LaTeX source, and the KaTeX print
view share this ordered content. JSON exports sort object keys while retaining
array order, every returned float, and exact numerator/denominator strings. The
current display preference is stored separately from the submitted preference.
All elimination snapshots or completed iterations are exported, independent of
the inspector's selected step or history page. Backend data is never mutated.

`lib/geometry/derive.ts` converts values only for approximate plotting. It clips
equations against a bounded square or cube; it never computes ranks or replaces
the backend solution. Solution-family lines derive from returned parametric
expressions. Zero equations, full-space families, coincident planes, inconsistent
systems, and off-window values receive explicit explanations. Per the Phase 4
user request, geometry is limited to exactly 2 × 2 or 3 × 3 systems.

The client-only geometric component loads on expansion. Only Plotly core and the
scatter, scatter3d, and mesh3d modules are registered. Every effect owns a separate
DOM plot element, so a late completion after React Strict Mode cleanup cannot
erase its successor. Resize observers and plots are released on unmount. The
existing SVG convergence chart remains lightweight and independent of Plotly.

KaTeX is loaded with the printable report; all formulas are application-generated
and rendered with trust disabled. Print CSS isolates the complete report from
interactive controls. No server-side TeX compiler or reporting endpoint was added.

Playwright now runs the workflow suite on desktop and mobile Chromium. Local runs
reuse verified services or start them at fixed ports; CI requires fresh services.
The frontend command explicitly binds 3000 and the backend 18000, preventing
silent port fallback. Preflight checks verify direct and proxied API health.
Behavior follows the official [Playwright web-server guidance](https://playwright.dev/docs/test-webserver)
and the plot lifecycle follows [Plotly's function reference](https://plotly.com/javascript/plotlyjs-function-reference/).
