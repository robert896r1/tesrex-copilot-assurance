# Contributing

Tesrex Copilot Assurance (TCA) welcomes focused contributions that improve the free self-hosted starter kit without changing its safety posture.

## Good contribution areas

- Documentation corrections.
- Microsoft UI/API/control change reports with source links.
- Test fixtures.
- UI clarity and report readability improvements.
- Bug fixes.
- Safer setup and troubleshooting guidance.


## Before opening a pull request

Run the local validation path from the repository root before committing or opening a pull request:

```bash
just check
```

If you do not have `just`, run the equivalent raw checks from `README.md`. Do not commit generated files under `artifacts/`, real tenant evidence, secrets, exported audit data, or unsanitized screenshots.

## Optional pre-commit guard

If you use `pre-commit`, enable the local guards before contributing:

```bash
pre-commit install
pre-commit run --all-files
```

The local hooks run the repository boundary guard, committed-evidence/artifact guard, synthetic sample verification, and read-only Microsoft tenant contract guard. They are not a substitute for careful review, but they reduce accidental evidence leakage.

## Microsoft mapping and ecosystem change reports

TCA can benefit from community reports when Microsoft changes a control surface, API response, admin UI label, or documentation page. Keep these reports narrow and evidence-backed.

Please include:

1. the affected TCA control, script, or document;
2. the Microsoft documentation URL or reproducible observation;
3. screenshots only if they contain no tenant secrets or customer data;
4. expected behavior versus observed behavior;
5. why the change affects evidence collection or report interpretation.

Do not submit source-less mapping changes. UI/API change reports are treated as inputs for review, not automatic proof that TCA mappings should change. If the repository has GitHub issue templates enabled, use the Mapping Discrepancy template.

## Contributions that need extra scrutiny

- Control mapping changes.
- Permission/RBAC changes.
- Collector changes touching Microsoft Graph, Purview, SharePoint, Audit, eDiscovery, or Entra.
- Evidence-pack status or finding semantics.

For these, include:

1. source links or Microsoft documentation references;
2. before/after behavior;
3. tests or fixtures;
4. explanation of why the change does not create false assurance.

## Out of scope by default

- Auto-remediation.
- Tenant mutation in the default run path.
- Generic chatbot or LLM-answering features.
- Copilot runtime interception or enforcement.
- Hidden telemetry.
- Compliance/certification claims.
- Source-less mapping changes.

## Support expectations

Contributions are reviewed best-effort. There is no SLA, no guaranteed response time, and no guarantee that a pull request or issue will be accepted.
