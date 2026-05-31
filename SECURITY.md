# Security Policy

## Data handling

Tesrex Copilot Assurance (TCA) is self-hosted. By default, it does not send evidence packs, tenant metadata, or assessment output to Tesrex.

Generated assessment artifacts may contain sensitive tenant metadata, including license state, policy names, site names, identities, and audit/eDiscovery context. Treat generated artifacts as controlled customer evidence.

Do not commit real assessment outputs to a public repository.

## Demo data

Demo mode uses synthetic/example data. It is for report review only and must not be presented as customer evidence.

## Supported security reports

Use GitHub issues or the contact route published by Tesrex for:

- accidental secret retention;
- unsafe default permissions;
- tenant mutation in a path documented as read-only;
- evidence leakage risk;
- dependency or packaging vulnerabilities.

Do not include real tenant secrets, bearer tokens, customer evidence packs, or private Microsoft tenant data in public issues.

## Support boundary

This free starter kit is community best-effort only. There is no support SLA and no guarantee of response time.
