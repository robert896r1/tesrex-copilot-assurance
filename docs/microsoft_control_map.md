# Microsoft Control Map

Purpose: distinguish the Microsoft-native control surfaces relevant to Copilot governance from the bounded evidence that version `0.1.0` actually collects.

This is a working map, not a claim that every control is API-accessible or implemented. Microsoft remains the control and enforcement plane.

## Implementation states

- **Implemented/read-only:** the default live probe calls a documented read-only endpoint or performs a local capability check.
- **Manual/partial:** the evidence pack can ingest or represent customer-provided evidence, but the default collector does not validate the underlying control.
- **Planned/reference:** relevant product context only; no current collector.

| Microsoft surface | Governance relevance | Current starter-kit state | What current evidence can establish |
|---|---|---|---|
| Microsoft Graph tenant/licensing | Tenant and Copilot-family entitlement signals | Implemented/read-only | Whether organization and subscribed-SKU data are readable and whether a known enabled Copilot-family service plan is present. It does not prove complete licensing or user assignment. |
| Purview Information Protection labels | Sensitivity taxonomy supporting information protection | Implemented/read-only for label listing | Whether the sensitivity-label endpoint is readable and returns a taxonomy. It does not measure label coverage across tenant content. |
| Purview DLP for Copilot | Restriction of prompt/content processing and web grounding under supported DLP conditions | Manual/partial; local PowerShell module capability check | Whether the local Exchange Online module is present, plus any separately supplied policy evidence. It does not currently collect or validate live DLP policy effectiveness. |
| SharePoint Advanced Management | Oversharing, access controls, restricted discovery, and site governance | Manual/partial; entitlement and local module capability signals | Whether known Copilot-family entitlement evidence and the local SharePoint module capability are present, plus customer-supplied reports. It does not scan sites or discover oversharing. |
| Purview Audit | Copilot/AI activity records where supported | Permission/scope signal only | Whether the acquired token contains a known audit-query role/scope. The default collector does not create a query or inspect audit records. |
| Purview eDiscovery | Search, retention, preservation, and export workflows | Implemented read-only case visibility plus manual evidence | Whether the case-list endpoint is visible to the identity. Visibility is `WARN`/partial and does not prove search or export readiness. |
| Purview retention / Data Lifecycle Management | Retention stance for Copilot interactions | Manual/partial | Customer-provided policy/export evidence only in the current public path. |
| Copilot Control System / Microsoft 365 admin center | Licensing, metering, agent lifecycle, connectors, and scenario settings | Planned/reference | No current collector. |
| DSPM for AI | AI usage discovery and data-security posture | Planned/reference | No current collector. |
| Microsoft Entra | Roles, application identity, consent, and access posture | Bounded preflight/context only | Exact Azure CLI tenant identity and the permission context available to the acquired token. It is not a Conditional Access or identity-governance assessment. |
| Agent 365 | Agent registry, observability, access, data security, and threat protection | Planned/reference | No current collector. Availability and licensing must be verified for each tenant before adding it to an assessed scope. |
| Defender, Insider Risk, Communication Compliance | Risk, threat, and communication signals | Planned/reference | No current collector. |

## Open integration questions

1. Which SharePoint Advanced Management reports/settings have supported read-only APIs, PowerShell, or stable exports for the intended customer scope?
2. Which Purview DLP and retention policy details can be collected with documented read-only operations and least-privilege roles?
3. Which audit evidence can be validated without turning a capability check into a query-creation workflow?
4. What positive eDiscovery evidence is sufficient for a customer-approved bounded validation, and how should it remain separate from the default collector?
5. Which Copilot Control System, DSPM for AI, and Agent 365 settings have supported APIs and stable licensing for the target tenant?

Any new collector must update the evidence contract, least-privilege matrix, current-source review, read-only guard, tests, and public claims before it is described as implemented.
