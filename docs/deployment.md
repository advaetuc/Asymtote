# Deployment and release runbook

Repository: [advaetuc/Augmentr](https://github.com/advaetuc/Augmentr).
Live-demo address: [augmentr-solvr.vercel.app](https://augmentr-solvr.vercel.app).
The owner reports configuring the new domain; remote verification is pending.
The historical audit below records the origin actually tested.

Latest remote audit: [2026-09-27 verification report](preview-verification/report.md).
It records checks against the user-deployed production URL, repeatable remote
test commands, and the remaining packaged-file inventory verification limit.

## Release boundary

Phase 5 prepares the source, security controls, CI gates, and this runbook.
No Vercel project has been linked or deployed by this work. Obtain the owner's
manual confirmation before creating a preview or production deployment. A
passing local build is not proof of the remote Python artifact or rewrite.

## Production topology and settings

Use one Vercel project, repository root as Root Directory, Next.js framework,
Node 22.x, and Python 3.12. Keep `pyproject.toml`, `.python-version`, `uv.lock`,
and `package-lock.json`. Install frontend dependencies with `npm ci`; build
with `npm run build`. Leave the framework's Output Directory at its default.
The Python builder consumes root Python metadata; do not add a competing
requirements file or install the development group into the runtime.

`api/index.py` is the only Python file in `api/`, exporting the application
factory's ASGI app. `vercel.json` explicitly selects Next.js and rewrites the
entire `/api/:path*` prefix to the `/api` function route. That includes health,
OpenAPI, `/api/v1/analyze`, `/api/v1/solve`, and unknown API paths (structured
404s). The frontend proxy is disabled whenever `VERCEL` is set, including
preview builds. There is no second API service URL or wildcard CORS rule.
These choices follow Vercel's supported
[file-based Python function mapping](https://vercel.com/docs/functions/runtimes/python/api-directory)
and [Python metadata support](https://vercel.com/docs/functions/runtimes/python).

## Environment variables

| Variable | Use |
| --- | --- |
| `VERCEL` | Platform-provided. Disables local rewrites and interactive Swagger docs. Do not set locally for ordinary development. |
| `NODE_ENV` | Set by Next.js. Only development permits debugging evaluation and hot reload connections. |
| `AUGMENTR_LOCAL_API_PROXY=1` | Local production integration build only. Adds the port-18000 rewrite to the build. Never configure on Vercel; the Vercel guard disables it regardless. |
| `E2E_PRODUCTION=1` | Playwright starts `next start` using the previously built local integration build. |
| `E2E_REUSE_SERVERS=0` | Require fresh test servers; occupied ports fail immediately. CI always requires fresh servers. |
| `PLAYWRIGHT_BROWSERS_PATH` | Optional local browser cache location. |
| `UV_CACHE_DIR` | Optional local Python package cache location. |
| `AUGMENTR_PREVIEW_URL` | Explicit HTTPS origin override for the remote HTTP/browser tools. Both default to `https://augmentr-solvr.vercel.app`. Run only after the owner confirms deployment and authorizes remote verification. |

No secrets, credentials, `NEXT_PUBLIC_API_URL`, or CORS origin list are needed.
Do not upload local environment files. `.vercelignore` retains the frontend's
required `docs/openapi.json` while excluding other documents and test artifacts.

## Security controls and limits

HTML responses receive a fresh cryptographically random script nonce through
Next.js `proxy.ts`. Dynamic rendering prevents cached HTML from reusing nonces.
Production `script-src` uses `strict-dynamic` without `unsafe-eval` or script
`unsafe-inline`; inline event handlers, plugins, framing, and off-origin form
submissions are blocked. Connections are same-origin. HTTPS requests upgrade
insecure subresources. Local HTTP tests do not force HTTPS.

Inline **styles** remain allowed for KaTeX and Plotly's generated styles; this
exception does not permit inline scripts. Plotly's strict distribution avoids
WebGL function constructors and remains lazy-loaded. It is larger than the
former three-trace bundle; CSP compatibility is the deliberate tradeoff. Its
cloud-sharing control is removed. No external Plotly or math CDN is required.

Next.js and Python responses both set `nosniff`, `no-referrer`, `DENY`, and a
Permissions Policy disabling camera, microphone, location, payment, and USB.
API responses are non-cacheable and use `default-src 'none'`. Swagger is local
only; JSON OpenAPI remains available. Do not enable the Vercel preview toolbar
or analytics injections without reviewing their CSP requirements; never solve
an injected-script failure by adding production `unsafe-eval`.

Python rejects cross-site and same-site browser mutations using Fetch Metadata
and validates Origin when same-origin metadata is absent. Modern browser
same-origin metadata survives the local proxy. No-Origin CLI requests remain
supported. This is a browser origin policy, not authentication or rate limiting.
Do not configure a permissive CORS middleware. Enable platform firewall/rate
controls and spending alerts appropriate to the owner's public traffic policy.

Limits apply before or during computation:

- Actual request bytes: 65,536, including chunked uploads (422 when exceeded).
- Total body reception: 5 seconds (408); whole ASGI request: 10 seconds (504).
- Cooperative numerical budget: 5 seconds, checked during direct arithmetic and
  iterative sweeps, and before/after the service call. Native NumPy operations
  and Python worker threads cannot be forcibly interrupted by this guard;
  matrix/resource caps bound their work. A 15-second Vercel function limit is
  the final platform guard and can produce a platform-specific error body.
- Dimensions 1–12, iterations at most 500, numeric token length 48, bounded
  magnitudes/exponents, exact intermediates at most 4096 bits, and bounded traces.

Application logs contain one JSON metadata event per request and never include
matrices, rejected values or field names, query strings, or exception messages.
Correlate errors using `X-Request-ID`; supplied IDs intentionally remain visible
and must not contain secrets. Uvicorn access logs are disabled in local scripts
and CI. Vercel's platform access logs are separate: do not put private values
in URLs or headers, and set platform log retention/access according to policy.

## Bundle checks

`npm run audit:runtime` traverses installed runtime dependencies, excludes dev
packages, includes numerical/API source, and enforces a conservative **200 MB**
project budget. Its output is an installed-file estimate for the current host,
not a Vercel artifact measurement. CI repeats it on Linux.

The Python function excludes node_modules, frontend source, build output,
tests, caches, local environments, environment files, and documentation.
Vercel currently documents a [500 MB Python uncompressed limit](https://vercel.com/docs/functions/limitations);
the project budget intentionally remains much lower. At preview time inspect
the actual artifact, including runtime adapter/layers, and require it below
the project budget. Verify that it includes no pytest, Ruff, mypy, SciPy,
SymPy, local secrets, or frontend bundles. Verify build logs select Python 3.12.

Next.js build/tracing roots are explicitly the project working directory (npm
scripts set that directory). Tailwind scans only `app`, `components`, and `lib`,
so clean source snapshots do not scan unrelated repositories or tool caches.
Add new UI source directories to the stylesheet's `@source` list when needed.

## Approval-gated preview verification

The owner selected `https://augmentr-solvr.vercel.app` and will retire
`https://asymtote.vercel.app` entirely. Alias removal belongs in the Vercel
dashboard: the application does not contain a hostname allowlist. Its API guard
rejects cross-site/same-site Fetch Metadata and otherwise checks Origin against
the request scheme and Host; browser same-origin metadata supports local rewrites.
The CSP uses `connect-src 'self'` and `frame-ancestors 'none'`, so neither directive
needs a hostname substitution. Do not add cross-alias CORS or framing permission.
Leaving the old Vercel alias mapped would continue serving it; this code does not
implement alias retirement or redirects.

After the owner pushes through GitHub Desktop, confirms that Vercel has deployed,
and authorizes remote checks, run the following. These are future remote commands,
not part of the local-only Gate 5a verification:

```powershell
$env:AUGMENTR_PREVIEW_URL = 'https://augmentr-solvr.vercel.app'
uv run python scripts/verify_preview.py --output .tools/augmentr-http-results.json
npx playwright test --config playwright.preview.config.ts
```

The HTTP tool also accepts an explicit positional HTTPS origin, which overrides
the environment variable. The browser tool uses the environment variable or its
Augmentr default. Historical commands/results in the earlier remote audit retain
the origin actually tested; use the commands above for the rebranded deployment.

After explicit authorization, use the Vercel dashboard to import the intended
repository/project and create a **Preview** deployment. Keep automatic production
deployments disabled until the release is approved. An external, reviewed CLI
is optional; it is intentionally not an application dependency.

1. Run the README's complete verification from a clean checkout. Require the
   GitHub Actions `quality` status before promotion. No deployment job is in CI.
2. Confirm the build uses Next.js 16, Node 22, Python 3.12, one Python API
   function, the 15-second duration, and the expected dependency/bundle sizes.
3. On the preview origin, fetch `/`, `/solve`, `/learn`, `/api/health`, and
   `/api/openapi.json`. All must succeed. `/api/absent` must return structured
   JSON 404; `/api/v1/solve` with GET must return structured JSON 405.
4. POST the documented example to both analyze and solve. Require JSON 200,
   correct mathematical results, and matching header/body request IDs. Check
   inconsistent and non-convergent systems still return HTTP 200; invalid
   numeric input must return a safe 422. A foreign Origin must return 403.
5. In the browser, use all four methods, a row-permutation preset, risk consent,
   exact rationals, 2D and 3D geometry, report downloads, and print preview.
   Check mobile layout, keyboard controls, and the browser console. Verify no
   CSP violations and no requests to a different API origin.
6. Inspect HTML headers and script nonces across two reloads. Verify the nonce
   changes and production permits no script evaluation. Confirm the API has
   independent security headers and no permissive CORS response headers.
7. Inspect function logs: one metadata event per request, no request values or
   stack traces. Exercise cold starts and a bounded 12 × 12 system. Record
   latency, actual artifact size, preview URL, commit, and test results.

If rewritten requests lose their original path or reach Next.js instead of
FastAPI, do not promote. Inspect the deployment's generated routing and Python
adapter; this behavior requires platform validation, not an assumption based
on the local proxy.

## Promotion, monitoring, and rollback

Renaming the project or changing an alias does not change the existing deployment
ID `dpl_6jgLVcERso8ffH6vxUwtiW837wii`. It remains the recorded historical rollback
candidate. A new code deployment may have its own ID, but do not invent a new ID
for the old deployment after a rename. Check the alias mapping separately when
rolling back; this gate has not changed any deployment or alias mapping.

Present the preview URL, commit, gate results, and limitations to the owner.
Promote that tested deployment only after explicit production approval. After
promotion repeat health, analyze, solve, headers, and one browser geometry/report
flow on the production hostname. Record the previous known-good deployment.

Monitor status counts, latency, solver timeouts, numeric-breakdown outcomes,
and cost using metadata logs. Mathematical inconsistency/non-convergence are
valid outcomes, not service failures. Investigate 500s by request ID without
adding raw payload logging. For a regression, use Vercel's deployment rollback
to restore the recorded known-good release and repeat smoke checks. There is
no database or migration to roll back.

Automated axe checks cover WCAG A/AA rules and key interaction states on desktop
and mobile. They do not certify complete accessibility: human screen-reader,
zoom, and assistive-technology testing remains part of release review. Geometry
has an algebraic/text alternative and does not require pointer use to understand
the mathematical result.
