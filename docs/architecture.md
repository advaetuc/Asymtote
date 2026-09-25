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
