# Augmentr rebrand — Gate 4 completion report

Date: 2026-09-27

Subsequent domain correction: the owner selected `https://augmentr-solvr.vercel.app`
because the originally planned alias below belongs to another user. Current
links/tool defaults use the corrected address; this Gate 4 URL inventory retains
the choices recorded in that commit. Remote verification remains pending.

Status: repository documentation updated for a local-only commit. The owner
confirmed renaming `advaetuc/Asymtote` to `advaetuc/Augmentr` on GitHub and updating
the local remote through GitHub Desktop. Neither operation was performed by this
gate. The owner selected `https://augmentr.vercel.app` as the live-demo address.
Its activation and remote verification remain Gate 5 work.

## Every URL changed or added

| File | Previous URL | New URL | Purpose |
| --- | --- | --- | --- |
| `docs/preview-verification/report.md` | `https://github.com/advaetuc/Asymtote/actions/runs/36287491411` | `https://github.com/advaetuc/Augmentr/actions/runs/36287491411` | Link to the same historical workflow run under the renamed repository. |
| `docs/preview-verification/platform-evidence.json` | `https://github.com/advaetuc/Asymtote/actions/runs/36287491411` | `https://github.com/advaetuc/Augmentr/actions/runs/36287491411` | Same historical run; run ID, commit, status and measurements unchanged. |
| `README.md` | No existing repository link | `https://github.com/advaetuc/Augmentr` | Public repository identity. |
| `README.md` | No existing live-demo link | `https://augmentr.vercel.app` | Owner-selected demo address, explicitly marked pending Gate 5 activation/verification. |
| `docs/deployment.md` | No existing current repository link | `https://github.com/advaetuc/Augmentr` | Repository reference in the runbook. |
| `docs/deployment.md` | No existing current live-demo link | `https://augmentr.vercel.app` | Current intended demo address, with the same Gate 5 boundary. |

These four files and this report are the complete Gate 4 commit scope.

## Badges and workflow audit

- No old repository CI/status/license badge URLs existed in the maintained
  README or documentation. No license was inferred and no new license badge
  was added.
- `.github/workflows/ci.yml` is the workflow file. Its display name is
  `Quality and API contract gates`; its job ID is `quality`.
- All `.github/workflows/*.yml` and `*.yaml` files were searched case-insensitively
  for `asymtote`. No hardcoded repository strings, badge URLs or artifact names
  required a Gate 4 change. The artifact is named `browser-test-results`.
- No workflow references to `VERCEL_PROJECT_ID` or `VERCEL_ORG_ID` were found.
  Repository renaming supplies no reason to alter these platform IDs. No secrets
  or Vercel configuration were inspected remotely or changed.
- Owner-supplied, untracked `docs/rebranding-verification/README.md` already uses
  the new repository slug in commented example badges. Its CI example names
  `quality.yml`, whereas the actual workflow file is `ci.yml`; that inactive
  draft was left untouched and was not copied into the active README. Any future
  CI badge should target `https://github.com/advaetuc/Augmentr/actions/workflows/ci.yml/badge.svg`.

## Historical URLs retained deliberately

`docs/phase-5-completion-report.md` and `docs/preview-verification/report.md`
record `https://asymtote.vercel.app` as the alias at the time of the earlier
audit. They are historical evidence, not current live-demo links. Replacing
those observations would incorrectly claim the new domain had been verified.
They remain intact alongside the new, explicitly qualified demo links.

The immutable tested origin
`https://asymtote-667zp49an-parthas.vercel.app`, its captured API URLs and request
results, and the `vercel.com/parthas/asymtote/...` deployment dashboard/resource
links also remain unchanged. They identify existing deployment evidence and
Vercel project settings are outside this gate. The old GitHub URL appears in this
report only to document the before/after change.

## Local verification and pending hosted CI

- Case-insensitive URL/workflow audit completed across README, documentation
  and all workflow files.
- JSON evidence parses successfully. A structural comparison confirms its only
  changed value is `hosted_ci.url`, preserving the original workflow run ID.
- All six new/updated URL sites match the owner-confirmed repository and demo
  address. No old repository slug remains in maintained links outside this
  report's change inventory.
- The staged diff is limited to this gate's five documentation/evidence files;
  `git diff --cached --check` passes. No application code changed, so numerical,
  frontend or browser suites were not rerun for these documentation edits.
- Existing uncommitted proxy-variable changes and the manual Gate 3 planning
  documents were preserved separately, not included in the Gate 4 commit.
  The owner elected to retain the local `TULYA` directory; no relocation,
  environment recreation or successful Gate 3 relocation was claimed.

**After pushing this commit through GitHub Desktop, spot-check the GitHub Actions
`quality` job in `Quality and API contract gates` (`ci.yml`) for the pushed commit.**
Confirm that the workflow completes successfully and its required status check
still applies to the renamed repository. No push or hosted workflow verification
was performed here; the successful historical run linked above is not evidence
for this new commit.

Git remotes, Vercel project/domain settings, Origin/Fetch Metadata security
policy, dependency metadata and lockfiles remain unchanged by Gate 4. No Gate 5
work has begun. Halt for the owner's verification and explicit approval.
