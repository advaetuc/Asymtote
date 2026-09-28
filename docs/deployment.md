# Deployment

## Topology

One Vercel project. Next.js serves `/`, FastAPI serves `/api/*` via `vercel.json`'s `/api/:path*` rewrite to the single ASGI entrypoint `api/index.py` (`app = create_app()`, 15s max duration). There is no separate backend host.

## Environments

| Environment | How it runs | API location |
|---|---|---|
| Local dev | `npm run dev:api` (Uvicorn on `127.0.0.1:18000`) + `npm run dev` | Proxied through Next.js |
| Local production build | `npm run build`, then `npm start` | Proxied only if `AUGMENTR_LOCAL_API_PROXY=1` is set before building |
| Vercel preview/production | Single deployment | Same-origin `/api/*` via the Vercel rewrite; `VERCEL` disables only the Next.js localhost rewrite and `/api/docs`. `/docs` is not configured |

## Deploying

Deploys happen through Vercel's normal Git integration — push to the tracked branch, Vercel builds and deploys automatically. There is no separate manual deploy step for routine changes.

Before any deploy that changes the API surface:

```powershell
uv run python scripts/export_openapi.py
npx openapi-typescript docs/openapi.json -o lib/contracts/api.generated.ts --default-non-nullable false
npm run contracts:check
```

CI enforces this same check — a PR that changes the backend schema without regenerating the frontend types fails the `quality` job in [the CI workflow](../.github/workflows/ci.yml) (display name: “Quality and API contract gates”). CI has no deployment job; deployment belongs to the owner-managed Vercel Git integration.

## Domain & aliases

Production: [augmentr-solvr.vercel.app](https://augmentr-solvr.vercel.app). Repository: [advaetuc/Augmentr](https://github.com/advaetuc/Augmentr). The owner confirmed that `augmentr.vercel.app` belongs to someone else; it is not an alias of this project. Always confirm the actual assigned domain rather than deriving it from a project name.

The old `asymtote.vercel.app` alias was retired entirely. Gate 5b verified `/`, `/solve`, and `/api/health` returned HTTP 404 with `DEPLOYMENT_NOT_FOUND` and no `Location` header, with redirects disabled. See the [Gate 5b report](history/rebrand-gate-5b-completion-report.md) for the dated observations; this does not guarantee the domain can never be reassigned in the future.

The current security and metadata configuration has no hardcoded production hostname:

- The same-origin guard (`api_app/security.py`'s `cross_origin`) is **host-relative, not an allowlist**: it rejects `Sec-Fetch-Site: cross-site`/`same-site`, permits requests without `Origin`, and accepts `Sec-Fetch-Site: same-origin`. Otherwise it validates the Origin syntax and compares scheme/authority against the current request’s scheme/`Host`. There is no list of permitted hostnames to maintain — it self-adjusts to whatever domain Vercel actually routes the request to.
- CSP uses `connect-src 'self'` and `frame-ancestors 'none'` — no domain named explicitly.
- `app/layout.tsx` sets branded OG title/description but no `metadataBase`, absolute OG URL, or canonical URL — there's nothing there to point at a new domain either.

What **does** still need updating on a domain change: `scripts/verify_preview.py` and `playwright.preview.config.ts`, which read their target from an `AUGMENTR_PREVIEW_URL` override (falling back to a hardcoded default) — update the default and/or the override value. Confirm the above still holds for your app rather than assuming it — the fact that no allowlist exists today is a property of this specific implementation, not a guarantee that stays true after future changes.

## Rollback

The baseline instant-rollback target is deployment `dpl_6jgLVcERso8ffH6vxUwtiW837wii` — a deployment ID is immutable and does not change when the project or domain alias is renamed. A rollback restores that build; it does **not** by itself restore whatever alias mapping was pointed at it at the time, so after any rollback, confirm the alias/domain assignment matches what you expect before considering the incident closed.

## Remote verification suite

Run after any deploy that touches the API surface, the CSP, or the deployment's domain:

- Two independent passes of the 35-request HTTP suite (`scripts/verify_preview.py`) — 70 requests / 718 individual assertions total last confirmed run, covering `/`, `/solve`, `/learn`, health and OpenAPI, disabled Swagger, 422/403/404/405 handling, correlation IDs, script nonce rotation, and all four solvers at 12×12.
- 48 remote Playwright E2E checks across desktop Chromium and mobile Pixel 7 viewports (24 each), including 12 accessibility/CSP/security cases with zero axe violations.
- If retiring an old alias: a few no-redirect HTTPS probes against it confirming Vercel's `DEPLOYMENT_NOT_FOUND` with no `Location` header, rather than assuming the retirement took effect.
- [Earlier platform evidence](preview-verification/platform-evidence.json) records the historical dashboard function size and runtime observations. A new release needs its own platform observations if platform verification is in scope; neither HTTP/browser success nor a local closure audit proves the current function artifact size. The accepted visibility limitation is documented in [D11](decisions.md#d11--accepted-platform-artifact-visibility-limit).

Exact counts will drift slightly release to release as regression cases get added — treat the most recent gate/verification report as ground truth over any number hardcoded here.

For a newly authorized remote verification, these commands reproduce the two HTTP passes and full browser suite without starting local servers:

```powershell
$env:AUGMENTR_PREVIEW_URL = "https://augmentr-solvr.vercel.app"
uv run python scripts/verify_preview.py $env:AUGMENTR_PREVIEW_URL --output test-results/http-pass-1.json
uv run python scripts/verify_preview.py $env:AUGMENTR_PREVIEW_URL --output test-results/http-pass-2.json
$env:E2E_PRODUCTION = "1"
npx playwright test --config playwright.preview.config.ts
```

Save the full command outputs and JSON evidence with each release report. The Gate 5b files and their hash manifest remain in [rebrand-gate-5b-verification](rebrand-gate-5b-verification/); the [archived report](history/rebrand-gate-5b-completion-report.md) contains exact commands and results. The local test/build procedure is in the [README](../README.md#testing).

## Resource budgets to watch

- `vercel.json`'s `functions["api/index.py"].excludeFiles` glob: ≤256 characters. Any change to files/folders under `api/` should be followed by re-running the existing regression assertion that checks this.
- Runtime closure: <200 MB (`npm run audit:runtime`; historically 32.5 MB reported by Vercel versus about 49.5 MiB in the local dependency audit; these measure different things and are not current artifact guarantees).
- Request body: 65,536 bytes, enforced before JSON parsing.
- Whole-request deadline: 10s (HTTP 504), inside Vercel's 15s platform ceiling.

## Still open (not blocking, tracked separately)

- Vercel Web Application Firewall (WAF) / rate limiting configuration.
- Log retention window policy.
- Billing/spending alerts.
- Manual assistive-technology audit (NVDA/VoiceOver + keyboard/zoom) to complement the automated `@axe-core/playwright` WCAG A/AA suite.
- A standalone local TeX Live/MiKTeX compiler path, if automated CLI `.tex → .pdf` verification is wanted alongside the existing KaTeX + headless-browser PDF export tests.

These follow-ups are tracked in [backlog.md](backlog.md). Their current platform configuration must be confirmed by the owner; the rebrand does not claim to have configured WAF, retention, or alerts. TeX compilation is optional: existing LaTeX downloads and browser/KaTeX PDF rendering do not require a local TeX installation.

## Documentation close-out and owner release steps

The [rebrand summary](rebrand-summary-report.md) records the completed documentation pass and verification evidence. Review the local close-out commit, push through GitHub Desktop, spot-check the resulting `quality` CI job and Vercel deployment, then create the planned `v1.1.0` tag manually. Renaming an alias does not change deployment ID `dpl_6jgLVcERso8ffH6vxUwtiW837wii`; a later code build can have a different ID. Do not invent a replacement rollback ID from a project rename, and confirm the desired build and alias mapping in the dashboard before rollback.
