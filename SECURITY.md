# Security Policy

## Data handling

Tesrex Copilot Assurance (TCA) is self-hosted. By default, it does not send evidence packs, tenant metadata, or assessment output to Tesrex.

Generated assessment artifacts may contain sensitive tenant metadata, including license state, policy names, site names, identities, and audit/eDiscovery context. Treat generated artifacts as controlled customer evidence.

Do not commit real assessment outputs to a public repository.

## Demo data

Demo mode uses synthetic/example data. It is for report review only and must not be presented as customer evidence.

## Report a vulnerability privately

Use [GitHub private vulnerability reporting](https://github.com/robert896r1/tesrex-copilot-assurance/security/advisories/new) for suspected vulnerabilities, including:

- accidental secret retention;
- unsafe default permissions;
- tenant mutation in a path documented as read-only;
- evidence leakage risk; or
- dependency and packaging vulnerabilities.

**Do not open a public issue for a suspected vulnerability.** Do not include bearer tokens, credentials, real tenant data, customer evidence packs, or other sensitive material in a public issue, discussion, pull request, or repository artifact.

GitHub private vulnerability reporting is the supported confidential route for this public repository. Provide a concise impact description, affected version or commit, reproduction details that do not expose customer data, and any proposed mitigation.

## Support boundary

This free starter kit is community best-effort only. There is no support SLA and no guarantee of response time.
