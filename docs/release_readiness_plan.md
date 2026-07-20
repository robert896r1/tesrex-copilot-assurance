# Public Release Readiness Plan

Date opened: 2026-07-20  
Release candidate: `0.1.0`  
Public repository: `https://github.com/robert896r1/tesrex-copilot-assurance`

## Objective

Make the public starter kit safe, understandable, reproducible, and honest before directing external users to it. The release is a **starter-kit release**, not a claim of tenant-wide assurance, certification, continuous monitoring, or automated remediation.

## Acceptance gates

A public release is a **GO** only when every required gate below passes or has an explicit, documented limitation that does not contradict the public claims.

| Gate | Acceptance criterion | Evidence | State |
|---|---|---|---|
| Tenant safety | Help and missing/mismatched tenant paths make no Graph call; live collection requires an exact expected tenant ID and shows the verified boundary before collection. | CLI safety tests and `just check` | In progress |
| Sample provenance | Every sample evidence reference resolves inside the committed synthetic source tree and its SHA-256 matches; demo markers are retained. | `just sample`, sample verifier, tamper test | In progress |
| Product truthfulness | README, product thesis, data model, limitations, and website distinguish implemented behavior from future scope. | Documentation review and link check | In progress |
| Microsoft currency | Advisory mappings record a current source review and remain conservative where coverage is incomplete. | Mapping tests and source-review record | In progress |
| Security reporting | A private vulnerability-reporting path is documented and enabled; public issues are explicitly prohibited for sensitive reports. | GitHub settings and `SECURITY.md` | In progress |
| Repository controls | CI passes on the release commit; required labels and protected-main controls are configured. | GitHub API/Actions evidence | Pending |
| Reproducibility | A fresh clone can run validation and produce the tenant-free demo without local history or private files. | Clean-clone run | Pending |
| User experience | Generated report and public website instructions are readable at desktop/mobile widths and contain no placeholder clone URL. | Playwright/browser evidence | Pending |
| Secret exposure | No committed secret or real tenant evidence is detected by available repository checks and secret scanning. | Repository guards and secret-scan result | Pending |

## Execution sequence

1. Add a fail-closed tenant identity preflight to tenant-connected commands.
2. Regenerate the public sample from committed synthetic source artifacts and verify file hashes.
3. Reconcile documentation and product claims with the code that exists in this release.
4. Refresh Microsoft source references and review dates without claiming complete mapping coverage.
5. Establish private security reporting and repository controls.
6. Correct the public website clone/onboarding copy and regenerate only the affected site output.
7. Run deterministic repository, clean-clone, link, secret, and browser validation.
8. Commit and push the release candidate, require CI, then record the final GO/NO-GO decision.

## Change boundaries

- No Microsoft tenant mutation or automatic remediation.
- No live tenant access is required for release validation.
- No customer evidence is committed.
- No claim that endpoint visibility proves an underlying control is configured or effective.
- No unrelated website redesign or cleanup of the separate website workspace.
- No release tag until the release commit passes its required checks.

## Final decision

Not yet recorded. Complete the gates above before changing this section to GO or NO-GO.
