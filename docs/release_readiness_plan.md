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
| Tenant safety | Help and missing/mismatched tenant paths make no Graph call; live collection requires an exact expected tenant ID and shows the verified boundary before collection. | CLI safety tests and `just check` | Pass |
| Sample provenance | Every sample evidence reference resolves inside the committed synthetic source tree and its SHA-256 matches; demo markers are retained. | `just sample`, sample verifier, tamper test | Pass |
| Product truthfulness | README, product thesis, data model, limitations, and website distinguish implemented behavior from future scope. | Documentation review and link check | Pass |
| Microsoft currency | Advisory mappings record a current source review and remain conservative where coverage is incomplete. | Mapping tests and source-review record | Pass |
| Security reporting | A private vulnerability-reporting path is documented and enabled; public issues are explicitly prohibited for sensitive reports. | GitHub settings and `SECURITY.md` | Pass |
| Repository controls | CI passes on the release commit; required labels and protected-main controls are configured. | GitHub API/Actions evidence | Pass |
| Reproducibility | A fresh clone can run validation and produce the tenant-free demo without local history or private files. | Clean-clone run | Pass |
| User experience | Generated report and public website instructions are readable at desktop/mobile widths and contain no placeholder clone URL. | Playwright/browser evidence | Pass |
| Secret exposure | No committed secret or real tenant evidence is detected by available repository checks and secret scanning. | Repository guards and secret-scan result | Pass |

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

**GO for the `v0.1.0` public starter-kit release as of 2026-07-20.**

The starter-kit repository passed its release checks. The website project's mandatory Qwen sidecar review was rerun with committed-patch and referenced-document evidence; its final verdict was `pass`, with no directive violations, unsupported claims, evidence gaps, or operator decisions remaining.

The approved copy-only website artifact was deployed through the existing Azure Static Web Apps production path. It differed from the last proven production artifact only at `copilot-governance-accuracy/index.html`. Live validation confirmed:

- the real GitHub clone URL is present and the placeholder is absent;
- the optional, exact expected-tenant boundary is present;
- the same-origin form action remains `/api/aiWorkflowIntake`;
- representative routes return `200`, redirects return `301`, and the form preflight returns `204`; and
- desktop and mobile browser checks render correctly with zero console errors.

The release remains bounded by `README.md`, `docs/limitations.md`, and the incomplete/advisory mapping rules. GO does not mean tenant certification, continuous monitoring, policy effectiveness, or complete Microsoft control coverage.

## Validation record

| Check | Result |
|---|---|
| `just check` | Pass: repository guards, JSON, compile, 61 unit tests, whitespace |
| `just sample` | Pass: deterministic sample regeneration and hash/provenance verifier |
| PACK-002 tamper behavior | Pass: a changed retained artifact produces `WARN` with `artifact_hash_mismatch` |
| Clean local clone | Pass: `just check` and tenant-free demo generation |
| Documentation links | Pass: Lychee checked 22 unique links with 0 errors |
| Secret controls | GitHub secret scanning and push protection enabled; 0 repository alerts; local high-signal heuristic found 0 matches |
| Report browser check | Pass at 1440×1000 and 390×844; expected content present; 0 console errors |
| Website local build/check | Pass: 44 pages built; only the intended route output changed; 72 offline link instances checked with 0 errors; desktop/mobile render and console checks passed |
| GitHub Actions | Pass on pull request #1 |
| GitHub repository settings | Private vulnerability reporting, vulnerability alerts, Dependabot security updates, required labels, and protected `main` with required `check` configured |
| Website Qwen review | Pass after an evidence-complete rerun; no unresolved findings or decisions |
| Production website verification | Pass on Azure Static Web Apps and `https://tesrex.com/copilot-governance-accuracy/`; corrected copy, form boundary, key routes, representative redirects, desktop/mobile rendering, and console checks verified |
