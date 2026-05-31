# Limitations

Tesrex Copilot Assurance (TCA) is a free, self-hosted Copilot governance evidence starter kit. It helps surface Microsoft-native control visibility and evidence gaps. It does not certify compliance.

## What TCA can help with

- Show which first-slice Copilot governance controls are visible to the assessment identity.
- Separate verified evidence from permission gaps, licensing gaps, unsupported API paths, manual evidence needs, and assessment limitations.
- Generate a local evidence pack for review.
- Demonstrate the evidence model with synthetic/demo data before tenant access is configured.
- Provide a starting point for Microsoft 365 administrators and consultants to extend safely.

## What TCA does not do

- It does not provide legal advice.
- It does not provide audit certification.
- It does not guarantee compliance.
- It does not replace Microsoft Purview, SharePoint Advanced Management, Entra, Audit, eDiscovery, Copilot Control System, or related Microsoft controls.
- It does not continuously monitor a tenant.
- It does not remediate automatically.
- It does not intercept or govern Copilot runtime responses.
- It does not operate as a hosted Tesrex service.
- It does not guarantee that Microsoft mappings are current for every tenant, license, region, or preview feature.

## Demo mode limitations

Demo mode is synthetic/example data only.

- Demo output is not customer evidence.
- Demo output is not a Purview audit record.
- Demo output is not a CopilotInteraction record.
- Demo output is not a Teams or SharePoint scan.
- Demo output does not prove tenant configuration.
- Demo output exists so users can inspect the report format without Microsoft tenant access.

If a report says demo or synthetic, do not use it as audit proof.

## Tenant-connected mode limitations

Tenant-connected mode depends on Microsoft permissions, licensing, RBAC, API availability, and customer-approved evidence boundaries.

Common unresolved states:

- `NOT_ACCESSIBLE`: the assessment identity cannot read the control or API.
- `NOT_LICENSED`: available evidence indicates the control/license is not present.
- `UNKNOWN`: the current assessment did not collect enough evidence to classify the control.
- `Manual evidence required`: a Microsoft UI export, customer artifact, or separately approved collector is needed.
- `Unsupported API`: Microsoft does not expose enough supported API evidence for that control in the current path.

These states are not automatically customer failures. They describe what the starter kit could or could not prove.

## Evidence sensitivity

Evidence packs and raw artifacts can contain tenant metadata, identities, site names, policy names, license details, and audit-related context.

Do not publish real assessment artifacts publicly unless they have been reviewed and sanitized by the tenant owner.

## Local report server

The `just serve` helper binds to `127.0.0.1` and serves the ignored local `artifacts/` directory only. Do not expose generated evidence reports on a public or shared network without authentication and tenant-owner approval.
