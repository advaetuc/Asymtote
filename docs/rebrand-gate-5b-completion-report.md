# Augmentr rebrand — Gate 5b remote verification

Date: 2026-09-27

**PASS: 70 HTTP requests / 718 assertions and all 48 remote browser E2E tests.**
Tested live origin: [augmentr-solvr.vercel.app](https://augmentr-solvr.vercel.app).
The old `asymtote.vercel.app` alias is retired, with no redirect observed.
No application defect or application-code change was needed. Halt before Gate 6.

## Deployment and scope

The owner confirmed pushing Gate 5a through GitHub Desktop and completing the
Vercel deployment. The request’s `{new domain}` placeholder was resolved to the
explicitly selected `https://augmentr-solvr.vercel.app`. The unrelated
`augmentr.vercel.app` site was not contacted.

Reference checkout: `ddeec74845cb655ba439d3aae1d7ffa75e4c0338`. The live OpenAPI exactly matches the committed
contract. The public endpoint does not expose a deployment commit or deployment
ID, so exact build identity was not independently established through the dashboard.
The historical deployment ID `dpl_6jgLVcERso8ffH6vxUwtiW837wii` remains the identity
of that historical deployment; this report does not relabel it as the new build.

## Verification results

| Check group | Result |
| --- | --- |
| HTTP pass 1 | 35 requests; 359 individual assertions; zero failed checks. |
| HTTP pass 2 | 35 requests; 359 individual assertions; zero failed checks. |
| Browser suite | 48 passed, 0 failed, 0 skipped, 0 flaky; 24 desktop Chromium and 24 Pixel 7 cases; no retries. |
| Browser duration | 125.07 seconds. |
| Alias retirement | Three HTTPS GET probes returned Vercel 404 `DEPLOYMENT_NOT_FOUND`; no Location header; redirects were disabled. |
| Additional Origin probes | Two matching-origin requests accepted (200); old/unrelated origins rejected (403). |
| Accessibility and CSP | All 12 desktop/mobile accessibility/security cases passed, including axe checks, keyboard/forced-colors states, nonce rotation, strict CSP, KaTeX and WebGL. Zero axe violations. |
| Browser observations | Zero application errors; all 16 recorded API calls remained on the new origin. |

The 70-request bar is two complete invocations of the existing 35-request HTTP
suite. The seven supplemental alias/Origin requests are additional, not counted
in that bar. Browser-issued traffic is also separate.

The HTTP suite verifies `/`, `/solve`, `/learn`, health and OpenAPI; disabled
Swagger and structured 404/405 responses; all four methods with float/exact cases;
unique/infinite/inconsistent/non-convergent outcomes; safe 422 input rejection;
correlation IDs; foreign-origin 403; body-size rejection; HTML/API headers and
script nonce rotation; and bounded 12 × 12 analysis plus all four solvers.

The browser suite covers presets, input editing, analysis, exact row-operation
replay, iterative permutations and risk consent, validation recovery, cancellation,
2D/3D geometry, lazy loading, report exports/preview, desktop/mobile accessibility
and same-origin API traffic. Network-failure/500 recovery cases intentionally
mock those failures in the browser; they do not claim the deployed function crashed.

## Old alias: retired, not redirected

All three probes used a no-redirect HTTP handler:

| Old URL path | Status | Vercel error | Location |
| --- | ---: | --- | --- |
| `/` | 404 | `DEPLOYMENT_NOT_FOUND` | Absent |
| `/solve` | 404 | `DEPLOYMENT_NOT_FOUND` | Absent |
| `/api/health` | 404 | `DEPLOYMENT_NOT_FOUND` | Absent |

This is direct public evidence that the old HTTPS alias no longer serves the
application and is not retained as a redirect at the observed endpoints/time.
It does not claim a dashboard setting was inspected or predict future alias changes.

At the new API origin, matching Origin worked both with and without
`Sec-Fetch-Site: same-origin` (200). An old-alias Origin without Fetch Metadata
was rejected (403); the unrelated unavailable-name Origin with `cross-site` was
also rejected (403). No request was sent to the other user’s domain.

## Latencies and limits

| Request | Pass 1 (ms) | Pass 2 (ms) |
| --- | ---: | ---: |
| `first_observed_health` | 2213.41 | 327.64 |
| `repeat_health` | 409.54 | 323.85 |
| `analyze_12x12` | 332.12 | 358.38 |
| `gaussian_12x12` | 465.33 | 512.52 |
| `gauss_jordan_12x12` | 658.84 | 920.52 |
| `jacobi_12x12` | 279.76 | 404.22 |
| `gauss_seidel_12x12` | 319.04 | 460.38 |

These are client-observed samples, not load-test percentiles. First-observed
latency does not independently establish a cold start; both raw outputs correctly
record `cold_start_confirmed: false`. No dashboard runtime/function-log inspection,
artifact-size audit or hosted CI re-verification is claimed for this gate.

The desktop observation recorded one Canvas2D readback performance warning; the
mobile observation recorded that warning plus four WebGL ReadPixels performance
warnings. They are retained in full and did not produce application errors,
CSP violations or test failures. The test runner also emitted NO_COLOR/FORCE_COLOR
formatting warnings, retained in its console output.

## Complete saved evidence

| Artifact | Contents |
| --- | --- |
| [http-pass-1.json](rebrand-gate-5b-verification/http-pass-1.json) | All 35 request records, headers, checks, response hashes, mathematical summaries and timings. |
| [http-pass-2.json](rebrand-gate-5b-verification/http-pass-2.json) | Complete independent second HTTP pass. |
| [http-pass-1.txt](rebrand-gate-5b-verification/http-pass-1.txt) | Unabridged first HTTP console output. |
| [http-pass-2.txt](rebrand-gate-5b-verification/http-pass-2.txt) | Unabridged second HTTP console output. |
| [browser-results.json](rebrand-gate-5b-verification/browser-results.json) | Complete Playwright JSON report, configuration, results, timings and embedded observations. |
| [browser-results.txt](rebrand-gate-5b-verification/browser-results.txt) | Unabridged browser console output. |
| [browser-test-summary.json](rebrand-gate-5b-verification/browser-test-summary.json) | All 48 test names, projects, attempt counts, outcomes and durations. |
| [browser-observations.json](rebrand-gate-5b-verification/browser-observations.json) | Decoded desktop/mobile console errors, warnings and API request URLs. |
| [alias-and-origin-results.json](rebrand-gate-5b-verification/alias-and-origin-results.json) | All seven supplemental responses, complete headers/bodies and Origin expectations. |
| [alias-and-origin-results.txt](rebrand-gate-5b-verification/alias-and-origin-results.txt) | Unabridged supplemental-probe console output. |
| [alias-and-origin-probe.txt](rebrand-gate-5b-verification/alias-and-origin-probe.txt) | Exact Python source of the supplemental no-redirect probe, archived as text. |
| [sha256-manifest.json](rebrand-gate-5b-verification/sha256-manifest.json) | SHA-256 hashes of LF-normalized UTF-8 text for every evidence file listed above. |

The HTTP suite retains response hashes and parsed summaries rather than every
raw HTML/JSON body; its complete native output is attached unchanged. The alias
probe retains raw response bodies. Evidence headers contain public request IDs
and nonces; no credentials were used for the probes. Manifest hashing normalizes
CRLF to LF so Windows/Git newline conversion does not invalidate the hashes.

## Commands executed

```powershell
$env:AUGMENTR_PREVIEW_URL = 'https://augmentr-solvr.vercel.app'
$env:E2E_PRODUCTION = '1'
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\.tools\browsers"
.\.tools\gate-2-env\Scripts\python.exe scripts/verify_preview.py $env:AUGMENTR_PREVIEW_URL --output docs/rebrand-gate-5b-verification/http-pass-1.json
.\.tools\gate-2-env\Scripts\python.exe scripts/verify_preview.py $env:AUGMENTR_PREVIEW_URL --output docs/rebrand-gate-5b-verification/http-pass-2.json
npx playwright test --config playwright.preview.config.ts
```

The browser config starts no local servers and selected the live origin. Its
JSON output was copied unchanged from `test-results/preview-results.json`.
The previous browser JSON report was preserved before execution. Both HTTP pass
outputs and the browser console output are reproduced in full below.

## Full console output

### HTTP pass 1

```text
first_observed_health: HTTP 200, 2213.41 ms
repeat_health: HTTP 200, 409.54 ms
html_/: HTTP 200, 461.06 ms
html_/solve: HTTP 200, 408.51 ms
html_/learn: HTTP 200, 301.68 ms
html_/solve: HTTP 200, 362.73 ms
openapi: HTTP 200, 358.26 ms
disabled_or_absent_/api/docs: HTTP 404, 254.53 ms
disabled_or_absent_/docs: HTTP 404, 359.19 ms
disabled_or_absent_/api/absent: HTTP 404, 306.14 ms
wrong_method: HTTP 405, 285.71 ms
analyze_float64: HTTP 200, 379.69 ms
analyze_exact: HTTP 200, 358.16 ms
gaussian_float64: HTTP 200, 358.17 ms
gaussian_exact: HTTP 200, 323.46 ms
gauss_jordan_float64: HTTP 200, 256.22 ms
gauss_jordan_exact: HTTP 200, 251.57 ms
jacobi_float64: HTTP 200, 277.64 ms
gauss_seidel_float64: HTTP 200, 322.32 ms
analyze_inconsistent: HTTP 200, 250.63 ms
gaussian_inconsistent: HTTP 200, 262.48 ms
gauss_jordan_inconsistent: HTTP 200, 236.96 ms
analyze_infinite: HTTP 200, 245.74 ms
gaussian_infinite: HTTP 200, 248.67 ms
gauss_jordan_infinite: HTTP 200, 261.94 ms
jacobi_nonconvergence: HTTP 200, 250.66 ms
gauss_seidel_nonconvergence: HTTP 200, 1802.3 ms
analyze_12x12: HTTP 200, 332.12 ms
gaussian_12x12: HTTP 200, 465.33 ms
gauss_jordan_12x12: HTTP 200, 658.84 ms
jacobi_12x12: HTTP 200, 279.76 ms
gauss_seidel_12x12: HTTP 200, 319.04 ms
invalid_token: HTTP 422, 279.19 ms
foreign_origin: HTTP 403, 294.99 ms
body_limit: HTTP 422, 716.55 ms
{
  "request_count": 35,
  "failures": []
}
```

### HTTP pass 2

```text
first_observed_health: HTTP 200, 327.64 ms
repeat_health: HTTP 200, 323.85 ms
html_/: HTTP 200, 388.13 ms
html_/solve: HTTP 200, 459.32 ms
html_/learn: HTTP 200, 409.06 ms
html_/solve: HTTP 200, 364.16 ms
openapi: HTTP 200, 300.56 ms
disabled_or_absent_/api/docs: HTTP 404, 284.98 ms
disabled_or_absent_/docs: HTTP 404, 276.73 ms
disabled_or_absent_/api/absent: HTTP 404, 265.74 ms
wrong_method: HTTP 405, 311.62 ms
analyze_float64: HTTP 200, 343.8 ms
analyze_exact: HTTP 200, 312.67 ms
gaussian_float64: HTTP 200, 301.66 ms
gaussian_exact: HTTP 200, 306.77 ms
gauss_jordan_float64: HTTP 200, 353.49 ms
gauss_jordan_exact: HTTP 200, 362.84 ms
jacobi_float64: HTTP 200, 358.49 ms
gauss_seidel_float64: HTTP 200, 307.35 ms
analyze_inconsistent: HTTP 200, 252.28 ms
gaussian_inconsistent: HTTP 200, 270.28 ms
gauss_jordan_inconsistent: HTTP 200, 346.89 ms
analyze_infinite: HTTP 200, 359.15 ms
gaussian_infinite: HTTP 200, 307.08 ms
gauss_jordan_infinite: HTTP 200, 357.21 ms
jacobi_nonconvergence: HTTP 200, 511.85 ms
gauss_seidel_nonconvergence: HTTP 200, 307.06 ms
analyze_12x12: HTTP 200, 358.38 ms
gaussian_12x12: HTTP 200, 512.52 ms
gauss_jordan_12x12: HTTP 200, 920.52 ms
jacobi_12x12: HTTP 200, 404.22 ms
gauss_seidel_12x12: HTTP 200, 460.38 ms
invalid_token: HTTP 422, 358.24 ms
foreign_origin: HTTP 403, 358.01 ms
body_limit: HTTP 422, 496.52 ms
{
  "request_count": 35,
  "failures": []
}
```

### Browser E2E

```text

Running 48 tests using 2 workers

(node:29816) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:26076) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
  ok  2 [chromium] › tests\e2e\accessibility.spec.ts:10:7 › accessible page, keyboard skip link and security headers: / (8.4s)
  ok  1 [chromium] › tests\e2e\scaffold.spec.ts:3:5 › landing renders and the same-origin Python health endpoint responds (9.4s)
  ok  3 [chromium] › tests\e2e\accessibility.spec.ts:10:7 › accessible page, keyboard skip link and security headers: /solve (1.4s)
  ok  5 [chromium] › tests\e2e\accessibility.spec.ts:10:7 › accessible page, keyboard skip link and security headers: /learn (1.1s)
  ok  4 [chromium] › tests\e2e\workflow.spec.ts:22:5 › matrix editing, keyboard navigation, validation recovery and Gaussian replay (3.5s)
  ok  7 [chromium] › tests\e2e\workflow.spec.ts:43:5 › server validation 422 recovers after a bounded-value correction (2.4s)
  ok  6 [chromium] › tests\e2e\accessibility.spec.ts:29:5 › matrix errors, direct replay and complete report remain accessible (6.5s)
  ok  8 [chromium] › tests\e2e\workflow.spec.ts:52:5 › exact Gauss-Jordan row swaps and deterministic full report downloads (5.7s)
  ok  9 [chromium] › tests\e2e\accessibility.spec.ts:50:5 › iterative table and geometry descriptions remain accessible (5.7s)
  ok 10 [chromium] › tests\e2e\workflow.spec.ts:85:7 › Jacobi iteration applies row permutation and draws an iteration trajectory (4.7s)
  ok 11 [chromium] › tests\e2e\accessibility.spec.ts:65:5 › fresh script nonces and CSP-compatible 3D WebGL and KaTeX (6.1s)
  ok 12 [chromium] › tests\e2e\workflow.spec.ts:97:7 › Jacobi iteration declines risk, then honors explicit consent without claiming convergence (4.0s)
  ok 14 [chromium] › tests\e2e\workflow.spec.ts:85:7 › Gauss–Seidel iteration applies row permutation and draws an iteration trajectory (4.3s)
  ok 15 [chromium] › tests\e2e\workflow.spec.ts:97:7 › Gauss–Seidel iteration declines risk, then honors explicit consent without claiming convergence (4.0s)
  ok 16 [chromium] › tests\e2e\workflow.spec.ts:108:5 › infinite rectangular system explains eligibility and unavailable geometry (1.1s)
  ok 13 [chromium] › tests\preview\observability.spec.ts:3:5 › live happy paths have same-origin API traffic and no browser errors (11.2s)
(node:31228) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
  ok 18 [mobile-chromium] › tests\e2e\accessibility.spec.ts:10:7 › accessible page, keyboard skip link and security headers: / (1.1s)
  ok 19 [mobile-chromium] › tests\e2e\accessibility.spec.ts:10:7 › accessible page, keyboard skip link and security headers: /solve (1.3s)
  ok 17 [chromium] › tests\e2e\workflow.spec.ts:117:7 › geometry renders inconsistent and toggles cleanly (4.2s)
  ok 20 [mobile-chromium] › tests\e2e\accessibility.spec.ts:10:7 › accessible page, keyboard skip link and security headers: /learn (1.1s)
  ok 21 [chromium] › tests\e2e\workflow.spec.ts:117:7 › geometry renders coincident and toggles cleanly (4.7s)
  ok 22 [mobile-chromium] › tests\e2e\accessibility.spec.ts:29:5 › matrix errors, direct replay and complete report remain accessible (5.7s)
  ok 23 [chromium] › tests\e2e\workflow.spec.ts:117:7 › geometry renders planes and toggles cleanly (5.3s)
  ok 24 [mobile-chromium] › tests\e2e\accessibility.spec.ts:50:5 › iterative table and geometry descriptions remain accessible (4.9s)
  ok 25 [chromium] › tests\e2e\workflow.spec.ts:117:7 › geometry renders line3d and toggles cleanly (5.3s)
  ok 27 [chromium] › tests\e2e\workflow.spec.ts:131:5 › network failure and 500 can be retried without losing the matrix (1.2s)
  ok 26 [mobile-chromium] › tests\e2e\accessibility.spec.ts:65:5 › fresh script nonces and CSP-compatible 3D WebGL and KaTeX (5.9s)
  ok 29 [mobile-chromium] › tests\e2e\scaffold.spec.ts:3:5 › landing renders and the same-origin Python health endpoint responds (2.1s)
  ok 30 [mobile-chromium] › tests\e2e\workflow.spec.ts:22:5 › matrix editing, keyboard navigation, validation recovery and Gaussian replay (2.7s)
  ok 28 [chromium] › tests\e2e\workflow.spec.ts:147:5 › non-zero diagonal fallback is explicit and supports a bounded risky run (6.1s)
  ok 32 [chromium] › tests\e2e\workflow.spec.ts:164:5 › canceling an in-flight request preserves editable input (698ms)
  ok 31 [mobile-chromium] › tests\e2e\workflow.spec.ts:43:5 › server validation 422 recovers after a bounded-value correction (2.0s)
  ok 33 [chromium] › tests\e2e\workflow.spec.ts:177:5 › Plotly is fetched only after opening geometry, and reopening draws a fresh plot (5.1s)
(node:5816) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
  ok 34 [mobile-chromium] › tests\e2e\workflow.spec.ts:52:5 › exact Gauss-Jordan row swaps and deterministic full report downloads (5.4s)
  ok 36 [mobile-chromium] › tests\e2e\workflow.spec.ts:85:7 › Jacobi iteration applies row permutation and draws an iteration trajectory (4.7s)
  ok 35 [mobile-chromium] › tests\preview\observability.spec.ts:3:5 › live happy paths have same-origin API traffic and no browser errors (8.7s)
  ok 37 [mobile-chromium] › tests\e2e\workflow.spec.ts:97:7 › Jacobi iteration declines risk, then honors explicit consent without claiming convergence (4.4s)
  ok 38 [mobile-chromium] › tests\e2e\workflow.spec.ts:85:7 › Gauss–Seidel iteration applies row permutation and draws an iteration trajectory (4.6s)
  ok 39 [mobile-chromium] › tests\e2e\workflow.spec.ts:97:7 › Gauss–Seidel iteration declines risk, then honors explicit consent without claiming convergence (4.6s)
  ok 40 [mobile-chromium] › tests\e2e\workflow.spec.ts:108:5 › infinite rectangular system explains eligibility and unavailable geometry (1.3s)
  ok 41 [mobile-chromium] › tests\e2e\workflow.spec.ts:117:7 › geometry renders inconsistent and toggles cleanly (4.9s)
  ok 42 [mobile-chromium] › tests\e2e\workflow.spec.ts:117:7 › geometry renders coincident and toggles cleanly (4.4s)
  ok 43 [mobile-chromium] › tests\e2e\workflow.spec.ts:117:7 › geometry renders planes and toggles cleanly (5.1s)
  ok 44 [mobile-chromium] › tests\e2e\workflow.spec.ts:117:7 › geometry renders line3d and toggles cleanly (5.1s)
  ok 45 [mobile-chromium] › tests\e2e\workflow.spec.ts:131:5 › network failure and 500 can be retried without losing the matrix (1.2s)
  ok 46 [mobile-chromium] › tests\e2e\workflow.spec.ts:147:5 › non-zero diagonal fallback is explicit and supports a bounded risky run (5.5s)
  ok 47 [mobile-chromium] › tests\e2e\workflow.spec.ts:164:5 › canceling an in-flight request preserves editable input (664ms)
  ok 48 [mobile-chromium] › tests\e2e\workflow.spec.ts:177:5 › Plotly is fetched only after opening geometry, and reopening draws a fresh plot (5.1s)

  48 passed (2.1m)
```

### Alias and Origin probes

```text
{"url": "https://asymtote.vercel.app/", "method": "GET", "checked_at": "2026-09-27T17:17:11.376448+00:00", "status": 404, "bytes": 107, "sha256": "9a052bfa70bf8133a5ff2ab12e69d70b0d87fdfb46a0fb374330159d165fe193"}
{"url": "https://asymtote.vercel.app/solve", "method": "GET", "checked_at": "2026-09-27T17:17:11.557964+00:00", "status": 404, "bytes": 107, "sha256": "96d42d92c1d111f79cc1711afeac60c1d26be0c697dde29552c4ab50b572beb0"}
{"url": "https://asymtote.vercel.app/api/health", "method": "GET", "checked_at": "2026-09-27T17:17:11.714981+00:00", "status": 404, "bytes": 107, "sha256": "880d3404be5ac49579115ff21e7897691105891247e98738236c4d5a89817d00"}
{"url": "https://augmentr-solvr.vercel.app/api/v1/solve", "method": "POST", "checked_at": "2026-09-27T17:17:11.867719+00:00", "status": 200, "bytes": 1198, "sha256": "38928035975a79fc7814ce46e86872bce99d1beb48ba71b585cc4994d3290f7c"}
{"url": "https://augmentr-solvr.vercel.app/api/v1/solve", "method": "POST", "checked_at": "2026-09-27T17:17:12.178221+00:00", "status": 200, "bytes": 1198, "sha256": "465bff7553ba96c00c855a9733abf7ef4d3eb09cec0741c16e99eaf58205efd4"}
{"url": "https://augmentr-solvr.vercel.app/api/v1/solve", "method": "POST", "checked_at": "2026-09-27T17:17:12.533370+00:00", "status": 403, "bytes": 178, "sha256": "1d913593868ac516d4966ab8d46889a5caca99c8c4e7f99d8d5a8692cf5f70ba"}
{"url": "https://augmentr-solvr.vercel.app/api/v1/solve", "method": "POST", "checked_at": "2026-09-27T17:17:12.892413+00:00", "status": 403, "bytes": 178, "sha256": "fbdabfeb5955db7b4a02553d5d1cea60d507f10c90326c35ef779e415c130dc5"}
```

## Files changed and handoff

- `README.md`: keeps the corrected live URL, removes pending-verification wording and links this report.
- `docs/deployment.md`: replaces pending status with this successful remote verification.
- `docs/rebrand-gate-5b-completion-report.md`: this report.
- `docs/rebrand-gate-5b-verification/`: the 12 evidence files listed above.

No application logic, security policy, dependency, remote, Vercel configuration,
domain setting or deployment was changed. Results were checked against the raw
JSON reports and the documentation diff passed whitespace validation. These are
remote observations, not a new deployment or an assurance about future changes.

No push was performed. Stop here for owner verification before Gate 6.
