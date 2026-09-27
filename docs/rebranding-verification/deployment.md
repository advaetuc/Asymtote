# Deployment

## Topology

One Vercel project. Next.js serves `/`, FastAPI serves `/api/*` via `vercel.json`'s `/api/:path*` rewrite to the single ASGI entrypoint `api/index.py` (`app = create_app()`, 15s max duration). There is no separate backend host.

## Environments

| Environment | How it runs | API location |
|---|---|---|
| Local dev | `npm run dev:api` (Uvicorn on `127.0.0.1:18000`) + `npm run dev` | Proxied through Next.js |
| Local production build | `npm run build && npm start` | Proxied only if `AUGMENTR_LOCAL_API_PROXY=1` is set |
| Vercel preview/production | Single deployment | Same-origin `/api/*`, no rewrite — the `VERCEL` platform env var disables the localhost rewrite and the `/docs` / `/api/docs` Swagger routes entirely |

## Deploying

Deploys happen through Vercel's normal Git integration — push to the tracked branch, Vercel builds and deploys automatically. There is no separate manual deploy step for routine changes.

Before any deploy that changes the API surface:

```bash
python scripts/export_openapi.py     # regenerate docs/openapi.json
npx openapi-typescript                # regenerate lib/contracts/api.generated.ts
npm run contracts:check               # must report zero diff
```

CI enforces this same check — a PR that changes the backend schema without regenerating the frontend types fails the `quality` workflow.

## Domain & aliases

Production alias: `augmentr.vercel.app`. Vercel supports multiple aliases pointed at the same deployment, which is useful during any future domain transition (see `rebranding-migration-plan.md` for how this was used during the Tulya/Asymtote → Augmentr rename).

**If you ever add or change a domain alias, update these in the same change or the deployment breaks for legitimate browsers, not just old links:**
- The `Origin` / `Sec-Fetch-Site` allowlist the same-origin guard checks against (in `proxy.ts` / the API layer).
- Any CSP `connect-src` / `frame-ancestors` directive that names the domain explicitly.
- Any canonical-URL environment variable used for OG tags, sitemap, or `robots.txt`.
- `scripts/verify_preview.py` and `playwright.preview.config.ts`, which target a specific domain for remote verification.

## Rollback

The baseline instant-rollback target is deployment `dpl_6jgLVcERso8ffH6vxUwtiW837wii` — a deployment ID is immutable and does not change when the project or domain alias is renamed. A rollback restores that build; it does **not** by itself restore whatever alias mapping was pointed at it at the time, so after any rollback, confirm the alias/domain assignment matches what you expect before considering the incident closed.

## Remote verification suite

Run after any deploy that touches the API surface, the CSP, or the Origin allowlist:

- 70 remote HTTP checks (`scripts/verify_preview.py` → `http-results.json`, `http-log-audit-results.json`)
- 48 remote Playwright E2E checks across desktop Chromium and mobile Pixel 7 viewports (`browser-results.json`, `browser-observability-results.json`)
- `platform-evidence.json` — captures the platform-level evidence (function size, cold start, bundle closure) used to sign off a deploy without needing to extract deployment credentials/artifacts directly from the Vercel dashboard.

## Resource budgets to watch

- `vercel.json`'s `functions["api/index.py"].excludeFiles` glob: ≤256 characters. Any change to files/folders under `api/` should be followed by re-running the existing regression assertion that checks this.
- Runtime closure: <200 MB (`npm run audit:runtime`; ~32.5 MB as reported by Vercel, ~49.5 MB in the local/CI dependency-closure audit — the two numbers measure different things and are both expected to stay stable, not converge).
- Request body: 65,536 bytes, enforced before JSON parsing.
- Whole-request deadline: 10s (HTTP 504), inside Vercel's 15s platform ceiling.

## Still open (not blocking, tracked separately)

- Vercel Web Application Firewall (WAF) / rate limiting configuration.
- Log retention window policy.
- Billing/spending alerts.
- Manual assistive-technology audit (NVDA/VoiceOver + keyboard/zoom) to complement the automated `@axe-core/playwright` WCAG A/AA suite.
- A standalone local TeX Live/MiKTeX compiler path, if automated CLI `.tex → .pdf` verification is wanted alongside the existing KaTeX + headless-browser PDF export tests.
