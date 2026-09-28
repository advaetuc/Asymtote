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

Production alias: `augmentr-solvr.vercel.app`. Note the `-solvr` suffix — the plain `augmentr.vercel.app` subdomain was already claimed by an unrelated Vercel account, discovered only when trying to claim it during the Tulya/Asymtote → Augmentr rename. **Renaming a Vercel project to `X` does not guarantee you get `X.vercel.app`** — Vercel doesn't reserve or auto-provision it if someone else already has it, and there's no warning until you try. Confirm the actual assigned subdomain in the dashboard before hardcoding it anywhere.

Vercel supports multiple aliases pointed at the same deployment, which is useful during any future domain transition (see `rebranding-migration-plan.md` for how this was evaluated during the same rename — the retired `asymtote.vercel.app` alias was ultimately dropped entirely rather than kept as a redirect).

**The good news for future domain changes:** none of the usual suspects hardcode a domain in this codebase, so a domain/alias change is close to a no-op on the code side —
- The same-origin guard (`api_app/security.py`'s `cross_origin`) is **host-relative, not an allowlist**: it parses the incoming `Origin` header and compares its scheme/authority directly against the current request's own scheme/`Host`, and separately rejects `Sec-Fetch-Site: cross-site`/`same-site`. There is no list of permitted hostnames to maintain — it self-adjusts to whatever domain Vercel actually routes the request to.
- CSP uses `connect-src 'self'` and `frame-ancestors 'none'` — no domain named explicitly.
- `app/layout.tsx` sets branded OG title/description but no `metadataBase`, absolute OG URL, or canonical URL — there's nothing there to point at a new domain either.

What **does** still need updating on a domain change: `scripts/verify_preview.py` and `playwright.preview.config.ts`, which read their target from an `AUGMENTR_PREVIEW_URL` override (falling back to a hardcoded default) — update the default and/or the override value. Confirm the above still holds for your app rather than assuming it — the fact that no allowlist exists today is a property of this specific implementation, not a guarantee that stays true after future changes.

## Rollback

The baseline instant-rollback target is deployment `dpl_6jgLVcERso8ffH6vxUwtiW837wii` — a deployment ID is immutable and does not change when the project or domain alias is renamed. A rollback restores that build; it does **not** by itself restore whatever alias mapping was pointed at it at the time, so after any rollback, confirm the alias/domain assignment matches what you expect before considering the incident closed.

## Remote verification suite

Run after any deploy that touches the API surface, the CSP, or the deployment's domain:

- Two independent passes of the 35-request HTTP suite (`scripts/verify_preview.py`) — 70 requests / ~718 individual assertions total last confirmed run, covering `/`, `/solve`, `/learn`, health and OpenAPI, disabled Swagger, 422/403/404/405 handling, correlation IDs, script nonce rotation, and all four solvers at 12×12.
- 48 remote Playwright E2E checks across desktop Chromium and mobile Pixel 7 viewports (24 each), including 12 accessibility/CSP/security cases with zero axe violations.
- If retiring an old alias: a few no-redirect HTTPS probes against it confirming Vercel's `DEPLOYMENT_NOT_FOUND` with no `Location` header, rather than assuming the retirement took effect.
- `platform-evidence.json` — captures the platform-level evidence (function size, cold start, bundle closure) used to sign off a deploy without needing to extract deployment credentials/artifacts directly from the Vercel dashboard.

Exact counts will drift slightly release to release as regression cases get added — treat the most recent gate/verification report as ground truth over any number hardcoded here.

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
