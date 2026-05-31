# Microsoft Control Map

Purpose: map the Microsoft-native controls this product should read, validate, or reference.

This document is a working map, not a claim that every control is API-accessible.

## 1. SharePoint Advanced Management / SharePoint Admin

Governance role:

- oversharing detection;
- restricted access controls;
- restricted content discovery;
- site lifecycle hygiene;
- inactive/ownerless site identification;
- permission state review.

Product use:

- identify Copilot exposure created by broad SharePoint/OneDrive access;
- produce site-level risk findings;
- track before/after remediation.

Open question:

- Which SAM reports/settings are available through Graph, SharePoint Admin APIs, PowerShell, export, or manual evidence import?

## 2. Microsoft Purview Information Protection

Governance role:

- sensitivity labels;
- encryption and usage rights;
- label inheritance;
- classification.

Product use:

- check label taxonomy;
- assess label coverage;
- identify unlabeled sensitive content where possible;
- evidence whether labels support Copilot protection goals.

Open question:

- Which label/policy details are available through Graph/Purview APIs versus PowerShell/export?

## 3. Microsoft Purview DLP for Copilot

Governance role:

- restrict Copilot processing of sensitive prompts;
- restrict processing of files/emails with specific sensitivity labels;
- restrict grounding/web use under DLP conditions.

Product use:

- validate DLP for Copilot exists and targets the intended users/content;
- produce evidence that policy coverage exists;
- identify missing or weak DLP coverage.

Open question:

- What DLP for Copilot policy details and test evidence are accessible programmatically?

## 4. DSPM for AI

Governance role:

- AI usage discovery;
- data security posture;
- oversharing recommendations;
- AI activity explorer;
- one-click policies;
- risky AI usage views.

Product use:

- consume or mirror DSPM findings where accessible;
- produce simplified evidence packs;
- track remediation status.

Open question:

- Which DSPM reports and activity details are exposed through supported APIs or exports?

## 5. Microsoft Purview Audit

Governance role:

- audit records for Copilot prompts, responses, referenced content, and AI activities where supported.

Product use:

- validate Copilot interactions are auditable;
- sample audit availability;
- support evidence pack and incident review.

Open question:

- Which audit events are accessible with target customer licensing and roles?

## 6. eDiscovery / Data Lifecycle Management

Governance role:

- search, preserve, export, retain, or delete Copilot interaction data.

Product use:

- validate retention/eDiscovery readiness;
- evidence that Copilot interaction data can be found and retained according to policy.

Open question:

- starter kit may only record capability status and customer-provided proof if APIs are constrained.

## 7. Copilot Control System / Microsoft 365 Admin Center

Governance role:

- Copilot licensing and metering;
- agent lifecycle;
- connector controls;
- agent sharing/publishing controls;
- scenario settings.

Product use:

- inventory Copilot/agent settings where accessible;
- validate risky settings;
- produce control-state evidence.

Open question:

- Which Copilot Control System settings are exposed through Graph/admin APIs today?

## 8. Agent 365

Governance role:

- agent registry;
- agent observability;
- audit/logging;
- access control;
- data security;
- threat protection.

Product use:

- future phase; track agent governance readiness where customer has access.

Open question:

- GA and licensing posture must be verified for each tenant. Treat as optional until access is proven.

## 9. Microsoft Entra

Governance role:

- admin roles;
- conditional access;
- app registrations;
- enterprise apps;
- identities and permissions.

Product use:

- validate required admin roles;
- inventory app/agent identities where relevant;
- check consent and access posture.

## 10. Defender / Insider Risk / Communication Compliance

Governance role:

- risky AI usage signals;
- data exfiltration indicators;
- inappropriate communications;
- threat and incident handling.

Product use:

- later phase or optional evidence import unless direct API path is confirmed.
