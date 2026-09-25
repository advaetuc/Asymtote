# Phase 0 implementation report

Completed locally on 2026-09-25 in `C:/Users/Advaet/Documents/Projects/TULYA`.

## Delivered

- Audited the original repository; preserved existing editor/environment files.
- Exact dependency manifests, npm and uv lockfiles, Python 3.12 and Node 22 pins.
- Repeatable PowerShell folder scaffold matching Section 5, with `api_app` added
  to implement the thin-entrypoint factory pattern from Section 11.1.
- Next.js App Router landing page, Tailwind setup, strict TypeScript and ESLint.
- Stateless FastAPI app factory and typed `GET /api/health` response.
- Python lint/type/test commands; frontend unit/build/type/lint commands;
  Chromium local integration test; GitHub Actions CI skeleton.
- Architecture, numerical-constraint, and Windows setup documentation.

## Verification

| Acceptance or check | Result |
| --- | --- |
| Local frontend and backend boot | Passed in Playwright-managed processes |
| Next.js landing route renders | Passed in Chromium |
| FastAPI health responds | Passed directly and through frontend proxy |
| Python health/contract/isolation tests | 3 passed |
| Python lint and formatting | Passed |
| Python strict typing | Passed |
| Frontend lint and strict typing | Passed |
| Frontend landing test | 1 passed |
| Next.js production build | Passed |
| Chromium local integration smoke | 1 passed |
| npm dependency audit | 0 reported vulnerabilities after CLI removal |
| Python lock consistency | `uv sync --locked --offline` passed |
| CI skeleton | Added; its test/build commands executed locally |
| Hosted GitHub Actions execution | Not run; no push made |
| Vercel parity/preview/production | Not run; Phase 5 |

## Decisions and remaining work

The API uses local port 18000 because this Windows host rejects binds to 8000.
Vercel routing has an explicit prefix rewrite based on current file-routing
documentation, with hosted verification still required.

Vercel CLI 60.0.1 was removed from the project dependency tree after its trial
installation introduced security findings. Deployment CLI selection/audit is
deferred to Phase 5; optional `vercel dev` requires a separate installation.
ESLint 9.39.5 is deprecated upstream but retained to satisfy the declared peer
compatibility of the current Next.js lint plugins. Reassess when they support 10.

The numerical-policy document records requirements, not an implemented numeric
engine. Exact scale formulas, numeric bounds, and algorithms await Phase 1.
No solve/analyze handlers, solver UI workflow, dummy numerical methods, or
generated API contracts were added. Future directories are reproducible through
the scaffold script; empty directories are not tracked by Git.

Source and lockfiles are present in the working tree. No Git commit, push,
remote CI run, deployment, or Phase 1 implementation was performed.

Next approval gate: Phase 1, beginning with `solver_core/constants.py`, followed
by `solver_core/parsing.py` and parser tests.
