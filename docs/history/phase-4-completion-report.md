# Phase 4 — Reports, geometry, and workflow tests

Phase 4 is implemented and ready for user verification. No deployment was made.

## Delivered

- Deterministic Markdown, standalone LaTeX source, and JSON report downloads.
  Content includes original equations, arithmetic and display settings, rank and
  conditioning, analysis eligibility, applied permutations, every elimination
  snapshot or completed iteration, solution families or contradiction witnesses,
  original-system residual diagnostics, and warnings. Current and submitted
  display preferences remain distinguishable. JSON preserves full returned values;
  exact rational strings are never converted to floats for report formatting.
- A complete KaTeX report preview and browser Print / Save as PDF action, with
  print styling that removes controls and includes history beyond the visible page.
  The print action becomes available after the report component has loaded.
- Lazy Plotly geometry for exactly 2 × 2 and 3 × 3 systems: lines, clipped planes,
  unique points, parametric intersection lines, coincident constraints, and
  iterative trajectories. Zero-row equations, plane/full-space families, unsupported
  dimensions, off-window values, and unavailable WebGL receive explanations.
- Additional educational presets for coincident 2D lines, a unique 3D intersection,
  and a 3D line of solutions. Existing convergence charts are preserved.
- Desktop and mobile E2E coverage for matrix editing and keyboard navigation,
  all four methods, replay, permutation and non-zero fallback, risk consent,
  validation/error recovery, cancellation, geometry toggles, deterministic downloads,
  and print media. Tests verify Plotly is absent until geometry is opened.
- Updated Windows test-server handling, README, architecture documentation, and CI
  artifact retention. No dependencies or numerical/API contracts were changed.

## Verification results

| Gate | Result |
| --- | --- |
| Python numerical and API tests | 429 passed |
| Vitest unit/component tests | 124 passed across 9 files |
| Playwright desktop Chromium | 17 passed |
| Playwright mobile Chromium | 17 passed |
| ESLint with zero warnings | Passed |
| TypeScript and Next route generation | Passed |
| OpenAPI / generated TypeScript freshness | Passed |
| Next.js production build | Passed |
| Python Ruff checks and formatting | Passed |
| Python mypy | Passed |

Seven additional exact API fixtures cover 3D unique, line, plane, whole-space,
inconsistent, and empty geometry, plus coincident 2D lines. Geometry tests check
bounded coordinates and equation satisfaction independently of the plotting code.
Report tests parse generated formulas in KaTeX, verify escaping, preserve large
exact integers and raw JSON, and include every trace/history entry. A regression
test covers late Plotly promises during React Strict Mode remounts.

E2E tests save sample Markdown, TeX, JSON, a browser-generated PDF, printable-report
screenshots, and geometry screenshots under ignored `test-results/`. Desktop and
mobile geometry captures and the print layout were visually reviewed.

An optional standalone TeX compilation attempt could not run because the local
built-in compiler could not locate its platform directories. LaTeX source export
and all generated formula parsing tests passed; standalone TeX compilation is not
claimed. Browser-generated PDF export was exercised successfully.

## Scope and limitations

Geometry is an approximate bounded illustration, not a new solver or proof of
classification. The window is capped at ±1,000,000; off-window geometry is explained
and complete values remain available in tables and exports. 3D needs WebGL. A
rank-one 3D consistent system has a plane of solutions, not an invented line.

JSON round-trips the backend's float64 numbers and exact rational integer strings.
Text reports apply selected presentation precision to floating values and retain
exact fractions regardless of decimal-display selection. Standalone numerical
failures without a completed result retain their existing diagnostic panel; the
full report controls require the API's original-system and trace metadata.

E2E uses the local Next development proxy with FastAPI on port 18000. Vercel preview
deployment, production routing, a full accessibility audit, and deployment security
hardening remain Phase 5. Stop here for user verification before that phase.
