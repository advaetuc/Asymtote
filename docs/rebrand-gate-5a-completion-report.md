# Augmentr rebrand — Gate 5a completion report

Date: 2026-09-27

Status: local code, tests and documentation complete. No push, deployment,
dashboard change or remote verification was performed. The owner confirmed
`https://augmentr.vercel.app` as the target and chose to retire the old
`https://asymtote.vercel.app` alias entirely, without retaining a redirect.
Actual alias activation/removal remains an owner-operated Vercel dashboard step.

## Exact Origin-allowlist diff

**Empty: zero added entries, zero removed entries.** There was no hardcoded
hostname allowlist before this gate, and none was introduced. In particular,
the old alias was never an entry that could be removed.

| Location | Existing behavior, unchanged |
| --- | --- |
| `api_app/observability.py`, `RequestMiddleware.__call__` | Calls `cross_origin` before reading mutation bodies or invoking the solver for POST, PUT, PATCH and DELETE; rejects with structured 403. |
| `api_app/security.py`, `cross_origin` | Rejects `Sec-Fetch-Site: cross-site` and `same-site`. Supports requests without Origin. Accepts browser `same-origin` metadata through the local proxy. Otherwise parses Origin and compares its scheme/authority to the request scheme/Host. Arbitrary forwarded-host headers do not authorize a foreign origin. |
| `proxy.ts` | Generates CSP nonces for frontend routes. Its matcher excludes `/api`; it does not implement the API origin guard. |

The same unchanged policy supports the new alias when Vercel routes its requests
to this application. Local ASGI tests now prove matching-origin and CLI requests
work on `augmentr.vercel.app`, while old-origin, foreign-origin, lookalike-domain,
scheme/port mismatch and cross-site/same-site requests are rejected before solving.
These tests do not contact either public hostname.

Retirement is **not** implemented by adding a hostname blacklist or a cross-alias
allowlist. If the owner leaves the old alias mapped to this application, requests
that are same-origin on that old alias can still work. Removing the old mapping
at Vercel is therefore required to implement the owner's retirement choice.
This local gate does not claim that removal has occurred.

## CSP and canonical URL audit

No domain substitution was needed:

- `lib/security.ts` uses `connect-src 'self'` in production and
  `frame-ancestors 'none'`. Neither directive names the old alias. Development
  loopback WebSocket source exceptions are unchanged.
- The API CSP remains `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`.
- `proxy.ts` retains per-response nonces and the existing HTTPS policy.
- `app/layout.tsx` contains branded OG title/description without `metadataBase`,
  an absolute OG URL or a canonical URL. No site-URL environment variable,
  sitemap route or robots route referencing the old domain was found.
- Byte-hash checks confirm the production guard, middleware, proxy, CSP and
  root metadata files remain unchanged. No CORS or framing permissions were added.

## Every file changed in this gate

| File | Change |
| --- | --- |
| `scripts/verify_preview.py` | Default target is `https://augmentr.vercel.app`; optional `AUGMENTR_PREVIEW_URL` override; explicit positional origin has precedence. Argument parsing is independently testable without HTTP requests. `--output` remains required. |
| `playwright.preview.config.ts` | Default target is `https://augmentr.vercel.app`; renamed the override from `TULYA_PREVIEW_URL` to `AUGMENTR_PREVIEW_URL`; validates HTTPS and rejects credentials, paths, queries and fragments. No local servers are started by this remote config. |
| `.env.example` | Documents the optional remote-target override and post-deployment approval requirement. |
| `tests/python/test_security.py` | Adds 13 in-process production-host origin regression cases. |
| `tests/python/test_preview_config.py` | Adds 11 offline parsing/default/override/error tests with HTTP access forbidden. |
| `tests/frontend/preview-config.test.ts` | Adds nine offline remote-config default/override/error tests. |
| `docs/deployment.md` | Documents the confirmed alias/retirement plan, actual host-relative origin policy, future remote commands and deployment-ID rollback rule. |
| `docs/rebrand-gate-5a-completion-report.md` | This report. |

Historical deployment reports, captured origins, dashboard/resource URLs and
previous test commands remain historical evidence. The active remote tooling
does not consume `TULYA_PREVIEW_URL`; use the new variable or defaults described
in the current deployment runbook. The tools still accept an explicit authorized
HTTPS preview origin for future verification of other deployments.

## Exclusion-glob regression

`vercel.json` is unchanged. Its `functions["api/index.py"].excludeFiles` value is
**214 characters**, below Vercel's 256-character limit. The existing
`test_python_function_exclude_glob_fits_vercel_limit` assertion was rerun both
in the focused deployment/security checks and in the full Python suite.

## Local verification

| Check | Result |
| --- | --- |
| Full pytest suite | 471 passed; previous baseline 447. |
| Full Vitest suite | 139 passed across 11 files; previous baseline 130. |
| Local production Playwright suite | 46 passed, desktop Chromium and Pixel 7; zero axe violations. |
| Python Ruff lint/format and mypy | Passed. |
| ESLint and TypeScript/Next.js type generation | Passed. |
| Next.js production build | Passed with the local integration proxy. |
| `npm run contracts:check` | Passed; generated contracts unchanged. |
| HTTP tool `--help` | Passed; target/default and CLI documented without requests. |
| Remote Playwright `--list` | 48 tests collected; no tests executed, no public origin contacted. |
| Protected-file hashes and Git whitespace check | Passed. |

The executed browser suite explicitly used `playwright.config.ts` and loopback
servers at `127.0.0.1:3000` and `127.0.0.1:18000`. It was not the remote suite.
Local evidence is in ignored `.tools/rebrand-gate-5a-*.log` files and Playwright's
test-results directory. The generated `next-env.d.ts` build-path change was
restored before the commit and is not part of this gate.

## Deployment identity and handoff

**The existing deployment ID remains `dpl_6jgLVcERso8ffH6vxUwtiW837wii`.** Renaming
the project or changing its alias mapping does not create a new identity for
that deployment. Its mapping can change while the ID stays the same. Do not
search for an invented replacement deployment ID when rolling back. A subsequent
code deployment may receive a different ID; record that separately after the
owner has pushed and Vercel has deployed. Neither a new deployment nor an alias
mapping was assumed or verified here.

The local repository is still under `C:\Users\Advaet\Documents\Projects\TULYA`.
The owner's existing commit `e28ebfd` is preserved. No local folder/environment
recreation, remote mutation, Vercel project/domain update or dependency change
was performed in Gate 5a.

The owner will review and push through GitHub Desktop, configure/confirm the
Vercel alias changes, and confirm deployment before any remote verification.
Local test results do not establish live routing, certificate readiness, retired
alias behavior, deployed Host/scheme handling or public CSP behavior. Work halts
at this local gate until that confirmation arrives.
