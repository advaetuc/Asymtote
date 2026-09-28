# Augmentr — cosmetic rebrand gate 1

Date: 2026-09-27. Scope: visible branding, UI copy, documentation prose and
matching test expectations. Source copy:
[`rebranding-verification/ui-copy-rewrite.md`](../rebranding-verification/ui-copy-rewrite.md).

Status: **complete; all local verification passed. Stopped for owner verification.**

## What changed

- Replaced visible branding in page titles, navigation, report headings,
  downloaded report filenames, README and architecture/history prose.
- Applied the supplied landing heading/subheading, meta/OG description, both
  CTAs, three feature callouts, learning-page sections and footer.
- Applied workflow-stage headings/subheadings and result-panel labels using
  the current editor state and existing generated API contracts.
- Added specific incomplete-input, mathematical-outcome, non-convergence,
  method-eligibility, network and server-error copy. Existing parsing rules,
  request handling, calculations and eligibility decisions remain unchanged.
- Updated matching Vitest, local Playwright, remote verification expectations,
  and report filename assertions together. Existing tests now also verify the
  new titles, header accessible name, actual ranks/counts, iteration limits,
  error references, literal rendering of invalid tokens and fraction tooltips.
- Retained the terminology **linear equation coefficients** in the learning
  page and augmented-grid help/caption.

## Before and after verification

Counts below are fresh local runs for this gate, not the earlier remote audit.
Tests were extended in place; no test cases were removed or skipped.

| Suite/check | Before copy changes | Final copy changes |
| --- | ---: | ---: |
| pytest | 447 passed | 447 passed |
| Vitest | 130 passed, 10 files | 130 passed, 10 files |
| Local production Playwright, desktop + Pixel 7 | 46 passed | 46 passed |
| Accessibility/security cases within Playwright | 12 passed | 12 passed; zero detected axe violations |
| Next.js production build with local API proxy | Passed | Passed |
| ESLint | — | Passed, zero warnings |
| TypeScript | — | Passed |
| OpenAPI / generated TypeScript freshness | — | Passed |
| Ruff lint/format for updated verification script | — | Passed |

The baseline Playwright run completed all 46 cases but stalled during Windows
child-server teardown inside the restricted execution environment. After
identifying and stopping only its two test-server process trees, the runner
returned exit code 0. Subsequent runs used the approved unrestricted test
execution and completed teardown normally. No application or Playwright
configuration change was needed for that environment issue.

The final production browser run completed in 1.2 minutes, with zero failed or
skipped cases and normal server cleanup. Python's final run completed in 5.03s;
Vitest's final run completed in 3.12s. TypeScript also passed after restoring
the generated declaration file to its original contents.

Local production testing uses port 3000 for Next.js and port 18000 for FastAPI,
with fresh test-owned servers. The remote-only two-case observability file was
updated and typechecked, but this cosmetic gate did not run tests against or
deploy to the live site.

## Placeholder bindings and adaptations

The supplied document is a copy specification, not authorization to change
solver defaults, add APIs or introduce new export functionality. Exact headings,
subheadings and empty-state wording were used where the current behavior and
data support them. The following mappings and adaptations are explicit:

| Source/template | Binding or adapted copy | Reason |
| --- | --- | --- |
| `{method name}` / `{method}` | Display name mapped from the existing `Method` enum; `draft.method` before execution and `outcome.result.method` afterwards. | No new API field. Names include “elimination” or “iteration” as supplied. |
| `{m}×{n}` | Editor `system.a.length` / first-row length while solving; response `problem.shape` for completed outcomes. | Before submitting, dimensions exist in local state rather than a response. |
| `{classification}` | `outcome.result.classification.classification`. | Rendered as returned; an iterative system classified unique can still have a non-converged iteration status, which remains separately visible. |
| Results stage when classification is absent | “A numerical limitation prevented a result — review the returned explanation below.” | Top-level `numeric_breakdown` outcomes contain an error and shape, not a classification. No classification is invented. |
| Incomplete `{n} of {m×(n+1)}` | Number of empty editor cells and total augmented-grid cell count. | The first placeholder denotes missing cells, not unknowns. These are unsent editor values, so no API field exists or is needed. Whitespace/invalid tokens retain their specific validation messages. |
| Invalid `{token}` | Current local token, escaped by React, in the supplied unrecognized-number message. | Local malformed syntax can show the user's own editable token. Empty, oversized, zero-denominator and exponent-bound messages retain specific reasons. Server validation payloads/logging remain untouched and do not acquire rejected tokens. |
| `{r}`, `{r_a}`, `{r_ab}`, `{n}` | `classification.rank_a`, `classification.rank_augmented`, and `problem.shape.unknowns`. | Direct use of existing response fields. `rank({A})` is displayed as `rank(A)`, the coefficient-matrix notation, not the literal matrix contents. |
| Infinite-solution `{k}` | `problem.shape.unknowns - classification.rank_a`. | Presentation of nullity from returned dimensions/rank; no new rank calculation or response field. |
| `{max_iterations}`, `{tol}` | `result.options.max_iterations` and `.tolerance`; existing schema defaults 25 and 1e-8 if omitted. | These fields are optional in generated TypeScript. Budget-exhaustion copy is used only for `max_iterations_reached`, never for a declined run or numeric breakdown. |
| Ill-conditioned `{value}` warning | “This system's condition number is {value} — a large value means small changes in input can produce disproportionately large changes in the result. Treat the result's precision with that in mind.” | The contract provides a finite/singular/unavailable estimate, not an `ill_conditioned` flag or warning threshold. The wording explains finite estimates without inventing a numerical cutoff or claiming a solution already exists during analysis. `{value}` uses existing metric formatting. |
| Spectral-radius risk example | Uses the supplied risk wording when the returned eligibility requires override and the returned radius is at least 1; otherwise retains the backend's reason. | An unavailable spectral estimate must not be presented as a known radius ≥ 1. The method availability decision remains the backend's. |
| Non-square method template | `{method} requires a square system. This one has {m} equations and {n} unknowns — try a direct method instead.` | Bound to `MethodEligibility.code === "requires_square"` and `analysis.shape`, rather than hard-coding the illustrative 3-by-2 case. |
| Geometry panel subheading | “A 2D line or 3D plane for two- or three-unknown square systems; a convergence plot in Steps for iterative methods.” | Existing plotting supports 2×2/3×3 systems; the convergence chart already lives in Steps. This gate does not expand plotting support or move charts. |
| Geometry unavailable template | “A 2D or 3D plot only applies to 2 × 2 or 3 × 3 systems. This system has {m} equations and {n} unknowns; see Diagnostics and Steps for the equivalent algebraic description.” | The unknown count alone is insufficient: for example, 2 equations and 3 unknowns are unsupported. Both dimensions come from the response. |
| Report subheading | “Print, or download as Markdown, LaTeX, or JSON.” | No existing Copy LaTeX action is present. Adding clipboard behavior is outside this text-only gate. Existing `.md` and `.tex` buttons were relabeled verbatim; JSON export remains available. |
| Method-configuration subheading | Exact supplied iterative text; direct methods use “Choose exact rational or float64 arithmetic and how results should display.” | Direct methods do not have a starting guess or iteration budget. |
| Row-reordering default “off” | Label updated to “Attempt row reordering for diagonal dominance”; existing default remains enabled. | Changing defaults would violate the cosmetic-only instruction. Preset-specific reordering settings are unchanged. |
| Decimal-place / iteration defaults | Existing 6 decimal places and 25 iterations, capped at 500, remain unchanged. | No invented “classroom convention” setting. The display and solver configuration continue to use existing state. |
| “Copy LaTeX” | No new button or action added. | Functionality change, not a cosmetic label change. “Print / Save as PDF” already exists and is preserved. |
| Approximate-fraction tooltip | Supplied sentence followed by the existing stored value, on iterative solution and history-vector values in fraction mode. | Preserves inspection of the raw value; exact rational displays do not get an approximate tooltip. |
| `{request_id}` | Existing `ApiError.requestId`, including response correlation IDs. | No API/logging changes. The network-failure sentence is used for network failures; the supplied server-error sentence is used for HTTP 500. |

Additional factual qualifications preserve the numerical contract: the landing
feature about arbitrary-precision rational arithmetic includes a note about
existing resource bounds; the learning page qualifies float64 partial pivoting,
potentially unavailable spectral estimates, and retains both convergence tests
and the distinction between SPD guarantees for the two iterative methods.

## Every file changed by this gate

| File | Change |
| --- | --- |
| `README.md` | Visible product name in heading and development prose. |
| `app/layout.tsx` | Browser title and supplied description/OG copy. |
| `app/page.tsx` | Landing heading/subheading, CTA labels/targets, feature copy and footer. |
| `app/learn/page.tsx` | Supplied primer headings/body, explanatory qualifications, page title and footer. |
| `app/solve/page.tsx` | Page title and footer. |
| `components/site-header.tsx` | Visible wordmark and home-link accessible name. |
| `components/site-copy.ts` | Shared literal description, footer and tooltip strings. |
| `components/solver/analysis-panel.tsx` | Conditioning explanation, selection subheading and data-bound eligibility copy. |
| `components/solver/configuration.tsx` | Method-specific heading, iterative subheading and control labels. |
| `components/solver/geometry-panel.tsx` | Visualize heading/subheading and accurate unavailable-state text. |
| `components/solver/iterative-inspector.tsx` | Approximate-fraction tooltip for history vector values. |
| `components/solver/matrix-grid.tsx` | Accepted formats, coefficient terminology and accessible caption. |
| `components/solver/report-tools.tsx` | Report heading/subheading, download labels and branded filenames. |
| `components/solver/result-inspector.tsx` | Panel headings, response-bound outcome explanations and fraction tooltip. |
| `components/solver/workspace.tsx` | Workflow headings/subheadings, missing-cell count, empty state, display label and error copy. |
| `docs/architecture.md` | Visible product heading only. |
| `docs/phase-1-direct-report.md` | Historical product-name prose; file paths unchanged. |
| `docs/rebrand-gate-1-completion-report.md` | This report. |
| `lib/reports/render.ts` | One shared user-visible report-heading literal, also rendered inside components. |
| `lib/solver/grid.ts` | One malformed-token message literal/interpolation; parser conditions unchanged. |
| `lib/solver/presets.ts` | Method display names/descriptions/advantages/limitations only; preset data unchanged. |
| `scripts/verify_preview.py` | Expected visible brand in HTML verification. |
| `tests/e2e/accessibility.spec.ts` | Updated iterative method accessible-name expectation. |
| `tests/e2e/global-setup.ts` | Product name in the test health-preflight diagnostic. |
| `tests/e2e/scaffold.spec.ts` | New page titles/header/heading/CTA expectations across all routes. |
| `tests/e2e/workflow.spec.ts` | Labels, filenames, geometry copy and explicit network/server-error copy checks. |
| `tests/frontend/grid.test.tsx` | Local invalid-token copy and escaped rendering assertion. |
| `tests/frontend/inspectors.test.tsx` | Eligibility, response ranks, iteration-budget and fraction-tooltip assertions. |
| `tests/frontend/landing.test.tsx` | Landing copy, header accessible name, links and feature-count assertions. |
| `tests/frontend/reports.test.tsx` | Report brand, filename and download label assertions. |
| `tests/frontend/workspace.test.tsx` | Method/control labels, headings, missing-cell counts and returned classification assertions. |
| `tests/preview/observability.spec.ts` | Updated method display-name expectations only. |

The shared report heading and method/message literals physically reside under
`lib/`; only their presentation strings were edited. No numerical behavior or
data was changed there.

Next.js temporarily regenerated `next-env.d.ts` while building. Its generated
import-path change is restored before handoff; it is not part of this gate's
final diff. The pre-existing missing terminal newline in `docs/architecture.md`
is retained to keep that diff to its heading alone.

Ignored local evidence consists of `.tools/rebrand-before-*.log`,
`.tools/rebrand-after-*.log`, `.tools/rebrand-final-*.log`, and Playwright's
`test-results` artifacts; these are test outputs, not application changes.

## Scope protection and handoff

- No changes to `solver_core`, `api_models`, `api_app`, `api`, their numerical
  logic, API title/description, generated OpenAPI/TypeScript, or request schemas.
- No package metadata, dependency/lockfile, folder, Git remote, Vercel/domain,
  routing, proxy, CI or Playwright configuration changes.
- Existing technical identifiers remain accurate: package identifiers,
  `tulya.draft.v1`, `tulya.requests`, environment variable names, real filesystem
  paths, source/repository URLs and deployment URLs. They are not display-brand
  replacements and changing them would exceed this gate.
- The supplied files in `docs/rebranding-verification/` are input documents and
  remain untouched. Their future deployment/migration proposals were not
  executed or copied into the current runbooks.
- Copy and corresponding tests are present in one reviewable working-tree
  change set. No commit, push, external test, deployment or later rebrand gate
  was performed. Work halts here for verification and explicit authorization
  of any later gate.
