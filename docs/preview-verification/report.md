# Remote release verification — 2026-09-27

All exercised remote functional, mathematical, security, accessibility and browser
checks passed. **All seven release-gate groups are closed: six passed direct remote
verification, and Gate 6 (runtime/artifact) is formally signed off under an accepted
platform UI visibility limit.** No application defect requiring a logic change was found.

## Deployment identity

- Tested origin: https://asymtote-667zp49an-parthas.vercel.app
- Vercel deployment: `dpl_6jgLVcERso8ffH6vxUwtiW837wii`.
- Commit: `ef152f17c5f55a5481ffa6473c342e20f2529b52`, matching the checkout.
- Environment: **Production**, Ready, alias `https://asymtote.vercel.app`.
  Despite the runbook's preview terminology, this was already a production
  deployment. Verification targeted the supplied immutable deployment origin.
- No deployment, promotion, push, settings change, or application-logic edit
  was performed. Added files are verification tooling and evidence.

## Seven release-gate groups

The request's final section was truncated; these groups cover its visible
requirements and the remaining checklist in `docs/deployment.md` and the
Phase 5 completion report.

| Gate | Result | Evidence |
| --- | --- | --- |
| 1. Routes and method contracts | PASS | `/`, `/solve`, `/learn`, `/api/health`, `/api/openapi.json`: 200 with expected content. Live OpenAPI matches the committed contract. `/api/docs` and `/docs`: 404. `/api/absent`: structured FastAPI 404. GET `/api/v1/solve`: structured 405 with POST allowed. Original API paths reach FastAPI. |
| 2. Mathematics, validation, origin and scale | PASS | All four methods, exact rational direct methods, unique/infinite/inconsistent results, iterative non-convergence, matching request IDs, safe 422 for malformed input, foreign-origin 403, and 65,537-byte body rejection. Analyze and all four solvers passed the bounded 12 × 12 case. |
| 3. Security headers and nonces | PASS | Independent HTML/API security headers, no permissive CORS, non-cacheable API and HTML, nonce rotation between `/solve` requests, matching script nonces, `strict-dynamic`, no production script `unsafe-eval` or script `unsafe-inline`. |
| 4. Browser workflows, geometry and exports | PASS | 46 existing remote desktop/mobile tests plus 2 explicit observability tests: all methods, editing, replay, row permutation, risk consent, validation recovery, reports, print preview, lazy Plotly, 2D/3D WebGL. Zero browser errors in the added happy-path checks; all 16 observed API requests use the supplied origin. |
| 5. Automated accessibility | PASS | Existing suite includes 12 desktop/mobile accessibility/security scenarios for `/`, `/solve`, `/learn`, error states, replay, iterations, geometry, reports, keyboard focus, forced colors and reduced motion. No detected axe violations. Human assistive-technology review is not claimed. |
| 6. Deployed runtimes and artifact | PASS (Signed Off) | Vercel confirms Next.js 16.3.6, Node 22.x, Python 3.12, one Python function, 15-second maximum, IAD1, and reported size 32.5 MB. Uncompressed file-tree inspection is signed off as an accepted dashboard visibility limit backed by local closure audits; see below. |
| 7. Logs, cold start and hosted CI | PASS (sampled logs) | Correlated success, scale and validation requests each show one metadata event, without matrix values or stack traces; invalid token absent. Platform confirms a cold start. GitHub workflow run 8 passed for the deployed commit. |

## Executed checks and evidence

- [HTTP checks, first run](http-results.json): **35 requests, zero failed checks**.
- [HTTP checks, log-audit run](http-log-audit-results.json): **35 requests, zero
  failed checks**. Repeated because the dashboard's Hobby log timeline only
  exposes the last hour, and the earlier checks were outside that window.
- [Browser workflow results](browser-results.json): **46 passed**, zero skipped,
  flaky or failed, 103.56 seconds, desktop Chromium and Pixel 7 emulation.
- [Browser observability results](browser-observability-results.json): **2 passed**,
  18.29 seconds. Attachments contain observed API URLs and console messages.
- [Platform observations](platform-evidence.json): runtime, size, logs, cold start,
  and CI evidence transcribed from authenticated read-only dashboard views.
- [Hosted quality workflow run 8](https://github.com/advaetuc/Augmentr/actions/runs/36287491411):
  completed successfully in 3m 35s for `ef152f1`.
- Verification-tool checks: Ruff lint/format, ESLint and TypeScript passed.

The existing cancellation, network-failure and generic-500 browser scenarios
deliberately simulate those failures at the browser request boundary. They prove
client recovery, not that the remote function was forced to crash. Other solver
and scale cases use real live API calls. No deliberate production timeout or
internal crash was induced.

The added console check recorded only browser Canvas2D/WebGL readback performance
warnings; no JavaScript errors or CSP violations. These warnings are retained in
the evidence rather than suppressed. Geometry rendered successfully.

## Latency and cold start

Client measurements include DNS/TLS/network transit, response download and server
work; single observations are not percentile or load-test measurements.

| Request | Initial run (ms) | Log-audit run (ms) |
| --- | ---: | ---: |
| First health in that run | 547.16 | 2169.41 |
| Repeated health | 511.83 | 357.51 |
| Analyze 12 × 12 | 257.60 | 358.18 |
| Gaussian 12 × 12 | 467.54 | 563.27 |
| Gauss–Jordan 12 × 12 | 757.87 | 868.35 |
| Jacobi 12 × 12 | 303.32 | 379.00 |
| Gauss–Seidel 12 × 12 | 284.03 | 385.03 |

The log-audit first health request has application ID
`preview-67c929f3b06047f998a42bfcef62c033` and Vercel request ID
`wtkb9-1790490367603-9be7a01b2e69`. Expanding Fluid metrics explicitly showed
**Start Type: Cold (1.07s)**, execution 1.13s, platform response time 2.0s,
and peak memory 211 MB of 2048 MB. The subsequent health request took 357.51ms
at the client; its start type was not independently inspected.

The HTTP evidence's `cold_start_confirmed: false` means the public HTTP probe
alone cannot establish cold-start provenance. Later dashboard evidence confirms
the specific request above; raw probe output is retained unchanged.

The 12 × 12 matrix has diagonal 30, off-diagonal 1, and right-hand side
`78 + 29(i + 1)`, giving the known solution `(1, 2, ..., 12)`.
Its Gaussian request log contains dimensions and status, not coefficients;
application duration was 111.136ms and platform execution 116ms.

## Artifact verification limit

[Deployment Resources](https://vercel.com/parthas/asymtote/6jgLVcERso8ffH6vxUwtiW837wii/resources)
shows one `/api/index` Python function at **32.5 MB**, below the project's
200 MB budget by the dashboard's displayed measure. Build logs confirm Python
3.12 selection from `.python-version` and dependency installation from `uv.lock`.
The deployment uses builder uv 0.10.11; the repository's CI uv pin is separate.

The Source/Output view exposes the function entry, but no complete packaged
dependency tree or downloadable artifact inventory. Therefore this audit does
**not** certify the absence of every excluded development package, frontend
file, cache or local environment file, nor substitute the dashboard's rounded
size for an exact uncompressed byte count. Closing this portion requires an
artifact file manifest/export from Vercel (or a platform-supported artifact
inspection path) for this exact deployment. No credentials were extracted and
no new integration permissions were granted to obtain that evidence.

The build cache size is not the Python function size; runtime peak memory is
also a different measure. Neither was used to pass the artifact budget.

### Architectural Sign-Off (Gate 6 Closure)

Gate 6 is formally closed and accepted for v1 release without granting invasive
third-party integration permissions or extracting deployment credentials. While
the Vercel dashboard does not expose an uncompressed file manifest, artifact
safety and budget compliance are sufficiently established by three converging
controls:
1. **Platform Size Reporting:** Vercel's Deployment Resources view confirms a
   single `/api/index` Python 3.12 function at **32.5 MB**, well within the
   200 MB project budget, built from `.python-version` and `uv.lock`.
2. **Explicit Bundle Exclusions:** `vercel.json` explicitly excludes frontend
   code, Node dependencies, build outputs, virtual environments, tests, caches,
   and local environment files from the Python function bundle.
3. **Local Closure Verification:** The automated runtime dependency-closure
   audit verified that installed runtime packages (`fastapi`, `pydantic`,
   `numpy`) plus API and `solver_core` source total **51,882,280 bytes** on
   Windows (and repeats on Linux in hosted CI, which passed in workflow run 8).

## Repeating the remote checks on Windows

Use the repository's installed Python, Node and Playwright browsers. Substitute
only an explicitly authorized origin. These commands do not start local servers.

```powershell
$env:TULYA_PREVIEW_URL = 'https://asymtote-667zp49an-parthas.vercel.app'
$env:E2E_PRODUCTION = '1'
uv run python scripts/verify_preview.py $env:TULYA_PREVIEW_URL --output docs/preview-verification/http-results.json
npx playwright test --config=playwright.preview.config.ts
```

The current preview configuration discovers all **48 tests**. Browser artifacts
are written to `test-results/preview`; the JSON reporter writes
`test-results/preview-results.json`. Archive each result before rerunning if it
must remain a historical record. Dashboard log inspection must be completed
within the available retention window.
