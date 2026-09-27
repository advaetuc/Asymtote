# Augmentr architecture

## Boundaries

Browser → Next.js 16 route shell and client workspace → same-origin REST/JSON
`/api/*` → `api/index.py` → FastAPI application factory → `solver_core`.

The Python core imports neither HTTP models nor FastAPI/Vercel code. Its domain
models use immutable Pydantic values; request and response contracts live in
`api_models`. `api_app/services.py` parses string tokens, selects the numerical
method, and adapts results. The entrypoint only constructs the ASGI application.

Every solve is synchronous and self-contained. No database, queue, accounts,
application WebSocket, or persistent server calculation state is involved.
Browser state uses a reducer and validated per-tab session storage; cancellation
and request ownership prevent stale responses from replacing a newer draft.

## Numerical dependency graph

Limits and errors → immutable values → strict parser and tolerance policy →
row-operation primitives/classification → direct methods and residuals.

Independent bipartite row matching supports the iterative engine. Convergence
analysis provides method-specific iteration matrices and spectral diagnostics.
Jacobi uses the previous complete vector; Gauss–Seidel uses updated components.
Both require residual and step-change tests and retain unrounded float64 values.
Row permutations change equations, never variable ordering.

Exact direct methods use Fraction values parsed from text; no float conversion
is used to construct exact values. NumPy supplies float diagnostics, not the
educational elimination algorithm. Rank uncertainty and arithmetic breakdown
are explicit outcomes. Numerical thresholds are documented in
[numerical-policy.md](numerical-policy.md).

A framework-independent ContextVar budget optionally interrupts arithmetic and
iteration at cooperative checkpoints. The API applies a five-second budget;
standalone core calls have no imposed wall-clock deadline. NumPy native calls
cannot be forcibly interrupted; small dimensions and platform limits bound work.

## HTTP contract and privacy

FastAPI/Pydantic owns deterministic OpenAPI and the generated TypeScript
contract. The client uses those types plus schema-driven response validation.
Mathematical outcomes, including inconsistent systems and non-convergence,
remain HTTP 200. Validation/resource violations are 422, browser-origin failures
403, reception deadlines 408, computational deadlines 504, and unexpected
exceptions generic 500. Every response carries its request correlation ID.

Pure ASGI middleware limits actual request bytes before JSON parsing, bounds
reception and request time, checks browser origin metadata, attaches security
headers, and records one metadata log event. Known contract locations remain
available for inline cell validation; unknown field names are sanitized.
Rejected values, request bodies, queries, and exception messages never enter
application logs. No wildcard CORS rule is installed.

## Frontend, exports, and geometry

Server-rendered shells compose the `/`, `/solve`, and `/learn` pages. Matrix
inputs support bounded dimensions, keyboard navigation and bulk paste. Method
settings, educational replay, iteration history, and residual panels consume
backend results without duplicating solver decisions in TypeScript.

Reports share an ordered document model. Markdown, LaTeX and the KaTeX print
view include the original system, settings, analysis, complete trace and final
diagnostics. JSON preserves full returned precision and exact integer strings.
Print and downloads are local browser operations; no server TeX installation
or report storage is required.

Geometry is limited to 2 × 2 and 3 × 3 systems. Data derivation clips original
equations and returned solution families to bounded viewing regions; it never
reclassifies a system. Degenerate cases have explicit text descriptions. The
lazy plot component uses Plotly's strict distribution to support WebGL without
production `unsafe-eval`. This increases the deferred chunk compared with the
previous partial bundle. The initial landing and solver views do not fetch it;
a production browser test inspects the vendor chunk to enforce that boundary.

Each plot effect owns its DOM element and cleans up resize observers and WebGL
resources, including late completions from React Strict Mode. The plot is a
labeled region with controls, with an algebraic/text alternative. The iterative
convergence chart remains lightweight SVG and does not load Plotly.

## Rendering security and accessibility

`proxy.ts` adds a new random nonce per HTML request and forwards the CSP to
Next.js so framework scripts receive it. Root layout uses `connection()` for
dynamic rendering; nonce-bearing HTML must not be statically cached. Production
scripts require nonce authorization and do not allow dynamic evaluation. Inline
styles are the documented KaTeX/Plotly compatibility exception. Next.js and API
responses have independent security headers. Details and limitations are in
[deployment.md](deployment.md).

Automated axe checks cover routes and important solver states, plus keyboard
skip links and forced-colors/reduced-motion pages. Visible focus outlines and
system colors support keyboard and high-contrast use. Automated tests supplement,
and do not replace, human screen-reader and assistive-technology review.

## Deployment and release gates

One Vercel project explicitly selects Next.js. The `/api/:path*` rewrite targets
`/api`, which maps to the sole file-based Python function `api/index.py`.
This retains the original project architecture rather than migrating to Vercel
Services. Runtime Python dependencies are FastAPI, Pydantic and NumPy only;
root `pyproject.toml` and `uv.lock` are authoritative. Python is pinned to 3.12.

Local development proxies to port 18000. A separate explicit local production
integration flag enables the same proxy for `next start` tests. The presence of
`VERCEL` disables both local rewrite paths, even if that flag is mistakenly set.
The Python function excludes frontend/build/test/cache files and has a 15-second
platform duration. A runtime dependency audit enforces a 200 MB project budget.

GitHub Actions runs locked installs, lint/types/tests, generated-contract checks,
production build, dependency/size checks and desktop/mobile Playwright including
accessibility/CSP. It contains no deployment job. Phase 5 has not created a remote
preview. The actual Python artifact, remote rewrite, cold start and platform logs
must pass the approval-gated preview runbook before production promotion.

## ADR: Acceptance of Vercel Function Artifact Visibility Limit (Gate 6)

- **Date:** 2026-09-27
- **Status:** Accepted
- **Context:** The release verification checklist requires confirming that the deployed Vercel Python function stays under the 200 MB budget and excludes frontend/development files. During remote verification of commit `ef152f1` (`dpl_6jgLVcERso8ffH6vxUwtiW837wii`), the read-only Vercel dashboard confirmed a single `/api/index` Python 3.12 function at **32.5 MB** built from `uv.lock`, but the dashboard UI does not expose a full uncompressed file manifest or exact byte count.
- **Decision:** Accept the combined evidence of the **32.5 MB** dashboard-reported size, the **51,882,280-byte** automated dependency-closure audit (enforced in Windows and Linux CI), and explicit `vercel.json` exclusion rules as sufficient proof to close Gate 6.
- **Consequences:** Avoids introducing custom deployment-extraction credentials or weakening read-only operational security just to inspect the remote zip tree. The exact uncompressed artifact manifest remains a documented platform visibility limitation.