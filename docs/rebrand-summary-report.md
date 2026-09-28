# Augmentr rebrand — final summary and Gate 6 close-out

Date: 2026-09-28. Reference checkout before this gate: `cfa708f188b484825bb55ca32ffd0e095e967738`.

## Final identity

| Item | Final value |
| --- | --- |
| Public name | Augmentr |
| Repository | [https://github.com/advaetuc/Augmentr](https://github.com/advaetuc/Augmentr) |
| Production | [https://augmentr-solvr.vercel.app](https://augmentr-solvr.vercel.app) |
| License | [MIT](../LICENSE), copyright 2026 advaetuc; explicitly selected by the owner during Gate 6 |
| Local directory | `C:\Users\Advaet\Documents\Projects\TULYA`, intentionally retained |
| Planned release tag | `v1.1.0`, to be created manually by the owner after review and push |

The owner confirmed the repository rename and remote update through GitHub Desktop. Gate 6 does not change remotes, domains, deployment settings, package/API versions, storage keys, or application logic. The unavailable `augmentr.vercel.app` domain belongs to another user and is not an application target.

## Every gate's outcome

| Gate | Outcome and evidence |
| --- | --- |
| 1 — Cosmetic identity | Complete. Visible page/report branding and supplied workflow copy updated with matching tests; numerical logic and parsing retained. Placeholder adaptations are recorded in the [Gate 1 report](history/rebrand-gate-1-completion-report.md). |
| 2 — Machine identifiers | Complete. Python/npm package identities and FastAPI metadata renamed; locks and OpenAPI regenerated. TypeScript regenerated with no artificial diff because top-level API metadata is not emitted by the generator. Contract freshness passed. See [Gate 2](history/rebrand-gate-2-completion-report.md). |
| 3 — Local directory migration | Intentionally skipped by the owner. No move to `AUGMENTR`, `.venv` deletion/recreation, or dependency bootstrap was executed. The separately prepared `AUGMENTR_LOCAL_API_PROXY` rename was retained and verified in later gates. The [manual plan](history/rebrand-gate-3-manual-steps.md) and [path inventory](history/rebrand-gate-3-path-inventory.md) are marked never executed; there is no Gate 3 completion report. |
| 4 — GitHub identity | Complete. Owner renamed the repository and updated GitHub Desktop; documentation URLs were updated locally. The workflow audit found no required Vercel secret-ID changes. See [Gate 4](history/rebrand-gate-4-completion-report.md). |
| 5a — Deployment identity code | Complete, including the correction to `augmentr-solvr.vercel.app`. Preview defaults, examples, documentation, and domain regression fixtures agree. The Origin guard is host-relative and CSP uses same-origin sources, so no domain allowlist or CSP trust expansion was necessary. The exclusion glob stayed at 214 characters. See [Gate 5a](history/rebrand-gate-5a-completion-report.md). |
| 5b — Remote verification | Complete on 2026-09-27: 70 HTTP requests / 718 assertions and 48 remote browser tests passed against the confirmed production origin. Old alias retirement was observed directly. See [Gate 5b](history/rebrand-gate-5b-completion-report.md) and its unchanged raw evidence. |
| 6 — Documentation and license | Canonical README, architecture, decisions, and deployment documents adapted from the four supplied deliverables. MIT license added; twelve historical documents archived; backlog and this final summary added. Local verification and preservation checks are recorded below. The close-out is committed locally for owner review, with no push or tag. |

## Verification counts and limits

The before column is the latest recorded result before this gate. The after column distinguishes fresh local checks from retained remote evidence; no tests were added, removed, or skipped for documentation changes.

| Suite | Before | Final result / provenance |
| --- | ---: | --- |
| Python pytest | 472 | 472 passed, freshly run in Gate 6; 4.71s |
| Vitest | 139 in 11 files | 139 passed in 11 files, freshly run in Gate 6; 16.18s |
| Local production Playwright | 46 | 46 passed, freshly run in Gate 6; 23 desktop + 23 Pixel 7, no failures/skips/retries, 1.2 minutes |
| Remote Playwright | 48 | 48 passed on 2026-09-27 in Gate 5b, 24 desktop + 24 Pixel 7; not rerun in this documentation gate |
| Remote HTTP | 70 requests / 718 assertions | Two 35-request passes with 359 assertions each, passed in Gate 5b; not rerun here |
| Supplemental old-alias / Origin probes | 7 | Three retirement probes + four Origin checks passed in Gate 5b, separate from the 70-request count |

The 12 local desktop/mobile accessibility and security cases passed with zero detected axe violations, including nonce rotation and WebGL/KaTeX under production CSP. Test-owned servers shut down normally. The runner emitted only the existing NO_COLOR/FORCE_COLOR formatting warning.

Fresh Gate 6 checks also passed: Ruff lint and formatting (79 files), mypy (30 source files), ESLint with zero warnings, TypeScript, Next.js 16.3.6 production build, and `npm run contracts:check` with no generated-file drift. The runtime audit measured **51,882,682 bytes**, below the 200,000,000-byte budget, and correctly reports `platform_artifact_verified: false`. The full pytest run includes the `excludeFiles` length regression assertion; the unchanged glob is **214 characters**, within the 256-character limit.

Local verification used the existing Python 3.12 environment under `.tools/gate-2-env`, Node 22.23.3, installed dependencies and Chromium. The production build enabled `AUGMENTR_LOCAL_API_PROXY=1`; Playwright owns local servers on ports 3000 and 18000. No local directory relocation or `.venv` recreation was involved. Console logs are retained locally under `.tools/gate6-pytest.log`, `.tools/gate6-frontend.log`, and `.tools/gate6-playwright.log` (ignored verification output, not release artifacts).

The remote report remains a dated observation, not a fresh claim about today's deployment. In Gate 5b the old alias returned HTTP 404 `DEPLOYMENT_NOT_FOUND`, without a redirect/Location header, for `/`, `/solve`, and `/api/health`. It was retired, not retained as a redirect. Public checks did not independently identify the new deployment ID or inspect current dashboard logs/artifact size. Deployment **`dpl_6jgLVcERso8ffH6vxUwtiW837wii` remains the identity of the historical build**; changing alias mappings does not change that ID, while a subsequent build can have its own ID.

## Documentation adaptations and preservation

The four supplied files in `docs/rebranding-verification/` were used as source deliverables. Their pre-existing working-tree edits were preserved byte-for-byte and excluded from this gate's local commit. The current canonical documents include these corrections:

- Use the confirmed repository/domain and the owner-selected MIT license. The active badge points to `ci.yml`, whose display name is “Quality and API contract gates” and job ID is `quality`; the draft's `quality.yml` does not exist.
- Provide locked installs, accurate Windows local-production proxy setup, and the actual remote verifier's positional origin and required `--output` option. Regeneration retains `--default-non-nullable false`.
- Keep Vercel's production API rewrite distinct from the disabled localhost proxy. `/api/docs` is disabled on Vercel, `/docs` is not configured, and OpenAPI remains available.
- Correct the API package layout, actual font stacks, approximate display-fraction behavior, the host-relative Origin guard's Fetch Metadata branches, and the policy-wide inline-style CSP exception. These are documentation corrections, not behavioral changes.
- Label earlier size/cold-start measurements as historical. A local installed-runtime audit does not establish an exact deployed artifact manifest. Preserve the previously accepted visibility-limit ADR in `docs/decisions.md` (D11).
- Avoid claiming repository branch protection or current WAF/retention/billing settings were independently verified. Keep operational follow-ups separate from rebrand completion.

All twelve archived documents retain their original content except repaired relative Markdown links and the explicit never-executed note on the two Gate 3 planning files. Historical filenames, old names, audit commands, numeric observations, and complete console output are retained as provenance. The eleven Gate 5b evidence files still match their LF-normalized SHA-256 manifest. The original source deliverables, application/configuration/contract files, git remote configuration, and tags are unchanged by this gate. Internal Markdown destinations and heading links were checked after the moves.

## Complete file inventory

| File | Change |
| --- | --- |
| `README.md` | Replace with adapted supplied README, working badge/domain links, setup, checks and MIT attribution. |
| `LICENSE` | Add the complete MIT license. |
| `docs/architecture.md` | Replace with adapted supplied architecture; current implementation facts and dated evidence. |
| `docs/decisions.md` | Add adapted supplied decisions, preserved artifact-visibility ADR, and intentional identity-retention decision. |
| `docs/deployment.md` | Replace with adapted supplied deployment runbook and executable verification commands. |
| `docs/backlog.md` | Add a dedicated backlog because no separate maintained backlog existed; consolidate the operational next steps previously in deployment documentation. |
| `docs/history/README.md` | Add navigation and provenance context. |
| `docs/rebrand-summary-report.md` | This final report. |
| `docs/phase-1-completion-report.md` → `docs/history/phase-1-completion-report.md` | Move, preserving evidence. |
| `docs/phase-2-completion-report.md` → `docs/history/phase-2-completion-report.md` | Move, preserving evidence. |
| `docs/phase-3-completion-report.md` → `docs/history/phase-3-completion-report.md` | Move, preserving evidence. |
| `docs/phase-4-completion-report.md` → `docs/history/phase-4-completion-report.md` | Move, preserving evidence. |
| `docs/phase-5-completion-report.md` → `docs/history/phase-5-completion-report.md` | Move; repair evidence link. |
| `docs/rebrand-gate-1-completion-report.md` → `docs/history/rebrand-gate-1-completion-report.md` | Move; repair source-copy link. |
| `docs/rebrand-gate-2-completion-report.md` → `docs/history/rebrand-gate-2-completion-report.md` | Move, preserving evidence. |
| `docs/rebrand-gate-3-manual-steps.md` → `docs/history/rebrand-gate-3-manual-steps.md` | Move; prepend never-executed note. |
| `docs/rebrand-gate-3-path-inventory.md` → `docs/history/rebrand-gate-3-path-inventory.md` | Move; prepend never-executed note. |
| `docs/rebrand-gate-4-completion-report.md` → `docs/history/rebrand-gate-4-completion-report.md` | Move, preserving historical URL inventory. |
| `docs/rebrand-gate-5a-completion-report.md` → `docs/history/rebrand-gate-5a-completion-report.md` | Move, preserving gate/correction evidence. |
| `docs/rebrand-gate-5b-completion-report.md` → `docs/history/rebrand-gate-5b-completion-report.md` | Move; repair all raw-evidence links. |

## Intentionally outside this rebrand

- The local `TULYA` directory stays. Gate 3's relocation and environment rebuild were never executed.
- `tulya.draft.v1` stays because no storage-key migration was authorized. `tulya.requests` is the Python request logger, not client storage, and also stays unchanged.
- WAF/rate limiting, log retention, billing alerts, manual assistive-technology review, and optional local TeX compiler setup remain independent follow-ups in [backlog.md](backlog.md).
- No new package/API version bump, infrastructure change, remote verification, push, deployment, or tag was performed in Gate 6. The accepted exact-function-artifact visibility limitation remains documented, not reopened.

## Owner release handoff

Review this local close-out commit and push through GitHub Desktop. Spot-check the resulting **`quality`** job in **`ci.yml`**; no hosted CI result is claimed for an unpushed commit. Confirm the resulting Vercel deployment as appropriate, then create **`v1.1.0`** through GitHub Desktop (History → right-click the close-out commit → Create Tag). The assistant creates neither the tag nor a further rebrand gate.
