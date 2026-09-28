# Phase 5 — Hardening and deployment readiness

Subsequent remote audit (2026-09-27): see the
[remote release verification report](../preview-verification/report.md) for the
user-deployed production URL, 70 HTTP checks, 48 remote browser tests, runtime
and cold-start evidence, hosted CI, and the remaining artifact-inventory limit.
The original local completion record below is retained as historical context.

Verified locally on Windows and remotely against production deployment
`dpl_6jgLVcERso8ffH6vxUwtiW837wii` (`https://asymtote.vercel.app`, commit
`ef152f1`), 2026-09-27. Local and remote release checks are complete.

## Delivered

### Routing, runtime and build

- Retained the Next.js framework and sole `api/index.py` ASGI entrypoint.
  `/api/:path*` maps to the file-based `/api` function route in `vercel.json`.
- Local development uses port 18000. A separate local production integration
  flag supports `next start` E2E tests; `VERCEL` disables localhost rewrites
  regardless of that flag. Unit tests cover both paths.
- Configured a 15-second Python function duration and excluded frontend code,
  Node dependencies, builds, development environments, tests, caches, and local
  environment files from the Python bundle. Deployment uploads retain the
  generated OpenAPI JSON needed by the frontend.
- Kept runtime Python dependencies limited to FastAPI, Pydantic and NumPy.
  `pyproject.toml`, Python 3.12 selection, and `uv.lock` remain authoritative;
  no duplicate requirements file or additional runtime dependency was added.
- Added a runtime dependency-closure audit with a 200 MB project budget.
  Measured installed runtime files plus API/core source: **51,882,280 bytes** on
  this Windows host. This is an estimate, not a built Vercel artifact size.
- Built a separate clean source snapshot with a fresh `npm ci` and `VERCEL=1`.
  Its generated route manifest contains **no localhost rewrites**. Explicit
  Next.js project roots and bounded Tailwind source directories prevent
  ancestor-lockfile inference and broad scans of unrelated files/tool caches.

### Security

- Added nonce-based production script CSP with `strict-dynamic`, no script
  `unsafe-inline`, and no production `unsafe-eval`. Next.js dynamically renders
  nonce-bearing pages; HTML is not shared through a static nonce cache.
- Added `nosniff`, `no-referrer`, `X-Frame-Options: DENY`, and restrictive
  Permissions Policy headers to both frontend and API responses.
- Replaced the Plotly partial bundle with its strict distribution, retaining
  lazy loading and working WebGL under production CSP. Removed cloud sharing.
  The deferred vendor chunk is **4,951,275 bytes**, approximately **1,500,045
  bytes gzip**. Initial landing/solver views do not fetch it, verified in E2E.
- Retained inline style permission for KaTeX and Plotly. This is a documented
  style-only compatibility exception; script evaluation remains blocked.
- Enforced same-origin browser mutations without permissive CORS. No-Origin
  command-line clients remain supported; this is not an authentication layer.
- Verified the 65,536-byte body cap including chunked requests. Added a
  five-second reception deadline, ten-second request deadline, and scoped
  five-second cooperative numerical deadline.
- Added typed 403/408/504 error contracts and regenerated OpenAPI/TypeScript.
  Mathematical outcomes remain HTTP 200; validation remains 422; internal
  errors remain generic 500s.
- Sanitized unknown validation field names, preserved valid matrix-cell
  locations, and tested that rejected tokens, queries, unknown paths and
  exception messages do not leak into application logs or error responses.
  Uvicorn access logging is disabled in project scripts and browser tests.
- Disabled remote Swagger assets on Vercel while retaining JSON OpenAPI.

### Accessibility and workflow

- Added automated axe checks on `/`, `/solve`, and `/learn` at desktop and
  mobile sizes, with WCAG A/AA and best-practice checks enabled.
- Audited matrix validation, direct replay, method diagnostics, iteration
  tables, geometry, report preview, keyboard skip links, visible focus,
  forced-colors mode, and reduced-motion states.
- Fixed explicit canvas/background contrast, system colors for diagnostics,
  warnings and primary controls, and high-contrast result/row markers.
- Changed the interactive plot from an image role to a labeled region, making
  its toolbar controls available without nested-interactive violations.
- Made overflowing report formulas labeled, keyboard-focusable scroll regions.
- Final automated audit has **zero detected violations in the tested states**;
  no axe rules were disabled and no application region was excluded.

### CI and operations

- CI uses locked installs, read-only repository permissions, concurrency
  cancellation, Python lint/format/types/tests, frontend lint/types/unit tests,
  production build, contract freshness, runtime size, dependency audit, and
  production desktop/mobile E2E including CSP and accessibility.
- CI contains no deployment job. Browser failure evidence is retained for
  seven days. Hosted GitHub Actions was not triggered from this workspace;
  the equivalent local checks below were executed.
- Updated README and architecture/API documentation, added `.env.example`,
  and wrote a deployment runbook covering preview gates, environment settings,
  function logs, artifact checks, promotion, monitoring, and rollback.

## Final verification

| Gate | Result |
| --- | --- |
| Ruff lint and format | Passed; 60 Python files formatted |
| mypy | Passed; 30 source files |
| Python tests | **446 passed** |
| ESLint | Passed, zero warnings |
| TypeScript / Next.js type generation | Passed |
| Vitest | **130 passed**, 10 files |
| OpenAPI and generated TypeScript freshness | Passed |
| Production Next.js build with local integration proxy | Passed |
| Clean-source snapshot, fresh npm install, Vercel-mode production build | Passed |
| Production Playwright desktop/mobile | **46 passed**, including 12 accessibility/security scenarios |
| Production 2D/3D WebGL and KaTeX CSP checks | Passed; no CSP violations in tested flows |
| Lazy Plotly fetch boundary | Passed on desktop and mobile |
| npm vulnerability audit | **0 vulnerabilities reported** |
| Runtime dependency closure and 200 MB budget | Passed on Windows; CI repeats on Linux |

The final production E2E run completed in approximately 1.1 minutes. Generated
reports, replay controls, row reordering, risk consent, cancellation, and error
recovery continue to pass the expanded suite.

## Remaining release gates and practical limits

1. **Remote preview/production verification (Closed 2026-09-27):** Verified on
   deployment `dpl_6jgLVcERso8ffH6vxUwtiW837wii` (`ef152f1`). Remote rewriting,
   original-path preservation, Python 3.12 runtime selection, 32.5 MB reported
   function size, 1.07s cold start, platform logs, and hosted Linux CI (run 8)
   all passed. Exact uncompressed artifact file-tree inspection is formally
   signed off as a Vercel dashboard UI limitation backed by the 51.9 MB local
   dependency-closure audit and `vercel.json` exclusions.
2. **Hosted CI and human accessibility review:** require a successful hosted
   `quality` check before promotion. Automated checks do not certify complete
   accessibility or replace screen-reader and assistive-technology review.
3. **Timeout limits:** cooperative checks cannot forcibly interrupt a native
   NumPy call or kill a Python worker thread. Small dimensions/resource limits
   and the platform duration provide additional bounds. Platform errors may
   use a non-contract response body, which the client handles generically.
4. **CSP tradeoffs:** nonce-bearing HTML is dynamic; Plotly's strict deferred
   bundle is larger; generated inline styles remain allowed. Do not weaken
   script policy to accommodate third-party deployment-toolbar injections.
5. **Operational controls:** application logging privacy does not control
   provider access logs. Correlation IDs are intentionally visible. Configure
   platform log access/retention, traffic protection, and spending alerts when
   the owner configures the deployment.

No changes to numerical tolerance policy, exact-value semantics, or solver
classification behavior were introduced. The numerical core remains portable
and independent of Vercel.
