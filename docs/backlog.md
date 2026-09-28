# Backlog and release follow-up

Updated: 2026-09-28.

## Rebrand complete

The Augmentr rebrand is complete through the Gate 6 documentation close-out. Public identity, package/API identifiers, generated contracts, repository links, and the production verification target now agree. The owner intentionally retained the local `TULYA` directory and did not authorize a storage/logger-key migration. See the [final summary](rebrand-summary-report.md) for gate outcomes and evidence.

The remaining release actions belong to the owner: review and push the local close-out commit through GitHub Desktop, spot-check the resulting `quality` CI job and deployment, then create the `v1.1.0` tag. No tag, push, or deployment is performed by this documentation gate.

## Open operational work, independent of the rebrand

These items remain unverified or unfinished in the recorded evidence. Confirm existing platform settings before changing them; absence of evidence here does not mean a setting is absent in Vercel.

| Item | Next action and completion evidence |
| --- | --- |
| WAF / rate limiting | Owner to confirm or configure the production policy, then verify ordinary bounded solver traffic succeeds and excess traffic receives the intended response. Record the policy and recovery procedure. |
| Log retention | Decide and record the application/platform retention windows and access policy. Confirm actual provider settings; keep the existing no-input/no-stack-trace application logging policy. |
| Billing alerts | Owner to confirm budgets, notification recipients, and spending alerts in the platform dashboard, then record verification without copying secrets. |
| Manual assistive-technology audit | Complete NVDA/VoiceOver, keyboard, zoom, and high-contrast review of matrix input, errors, replay, iteration tables, geometry alternatives, and report views. Automated axe checks passed but do not replace this review. |
| Optional local TeX compiler | If standalone `.tex` to `.pdf` validation is wanted, select an existing TeX Live/MiKTeX executable path and test a downloaded report. This is not needed for LaTeX downloads or the current KaTeX/browser PDF workflow. |

## Intentionally deferred or retained

- `tulya.draft.v1` remains the browser session-storage key; `tulya.requests` remains the Python logging namespace, not a second client-storage key. Rename only after explicit authorization and a decision about draft compatibility and log consumers.
- The local path remains `C:\Users\Advaet\Documents\Projects\TULYA`; the [Gate 3 plan](history/rebrand-gate-3-manual-steps.md) is archived as never executed. No environment recreation is required by the rebrand.
- Package/API versions remain unchanged by this documentation gate. The owner-requested `v1.1.0` release tag is a separate manual action.
- Exact inspection of Vercel's uncompressed function artifact remains the accepted [platform visibility limitation](decisions.md#d11--accepted-platform-artifact-visibility-limit), not a new rebrand blocker.
