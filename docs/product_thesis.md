# Product Thesis

## One-sentence product definition

Tesrex Copilot Assurance is a Microsoft-native Copilot Assurance Cockpit: a single, shareable view that turns fragmented Microsoft governance signals into evidence-backed posture, remediation priorities, and auditor/director-ready assurance packs.

## What the product is

A Copilot governance evidence cockpit and evidence layer that:

1. inventories Microsoft-native Copilot governance controls;
2. assesses tenant readiness and exposure risk;
3. validates policy coverage;
4. produces auditor-ready evidence;
5. tracks remediation over time.
6. reduces assessor burden by collating Purview, SharePoint, Entra, Graph, admin-center, and customer-provided evidence into one defensible view.

## What the product is not

It is not:

- a generic LLM assistant;
- a custom model inference product;
- a Copilot replacement;
- a Teams chatbot as the primary product;
- an external web-search bot;
- a runtime interceptor of all Copilot outputs;
- a claim that Tesrex replaces Microsoft Purview, SAM, Copilot Control System, Agent 365, Entra, Defender, Audit, or eDiscovery.
- a deep DSPM scanner competing directly with Varonis, Concentric, ShareGate, Netskope, or Microsoft Purview.

## Honest market position

Microsoft owns the enforcement and control plane. Tesrex operationalizes it.

The product claim is not:

> We provide the controls Microsoft lacks.

The product claim is:

> You already have Microsoft controls; Tesrex helps prove they are configured, working, monitored, and producing defensible evidence.

## Single-pane-of-glass thesis

Microsoft already provides much of the control surface, but the assessor experience is fragmented across Purview, SharePoint admin, Entra, Microsoft 365 admin center, Copilot Control System, Graph, PowerShell, exports, and tenant-specific RBAC. The product value is not merely copying data into another dashboard. The value is decision compression:

- one place to see which Copilot readiness controls are verified, blocked, not licensed, unsupported, or dependent on manual evidence;
- one evidence trail that preserves source, timestamp, hash, limitation, and control mapping;
- one remediation view that separates tenant gaps from assessment limitations;
- one director/auditor pack that can be shared without forcing every reviewer through Microsoft admin portals.

This is viable only if the cockpit remains transparent about source limits. It must never turn unavailable evidence into false assurance.

## Buyer pain

Organizations adopting Microsoft 365 Copilot need to answer:

1. What data can Copilot expose today?
2. Which SharePoint/OneDrive/Teams areas are overshared?
3. Are sensitivity labels and DLP policies actually protecting Copilot interactions?
4. Can we prove Copilot interactions are audited, retained, and discoverable?
5. What changed since the last assessment?
6. What remediation work is required before broad rollout?

## Product wedge

The wedge is not model quality. The wedge is governance assurance:

- clear readiness assessment;
- evidence packs for compliance and leadership;
- before/after remediation tracking;
- simplified cross-portal view over Microsoft-native controls;
- read-only first to lower trust and deployment barriers.
- explicit cause classification for every non-clean result: tenant gap, permission gap, assessment limitation, not licensed, unsupported API, no usage context, manual evidence required, demo evidence, or verified evidence.

## Current implementation priority

The accepted near-term slice is to harden the Assurance Cockpit communication layer:

1. preserve the fixed status enum (`PASS`, `WARN`, `FAIL`, `UNKNOWN`, `NOT_LICENSED`, `NOT_ACCESSIBLE`);
2. add a separate `status_cause` field so reviewers understand why a status exists;
3. surface that cause in the generated evidence pack and UI;
4. derive simple human review labels from `status + status_cause`;
5. show prioritized demo/manual/stale/sample limitations as evidence-quality notes, not as a replacement for the primary reason;
6. keep the UI clean and director/auditor-readable, not a generic SaaS dashboard.
7. make the control row the central review object so status, action, next step, and evidence are connected in one interaction.

Every non-clean control should answer:

- what is known;
- what is not known;
- why the report cannot go further;
- what action closes the gap.

The page must not make reviewers connect separate dashboard regions by memory. Status counts, control rows, findings, and evidence must behave as one linked review path.

Warnings should act as breadcrumbs, not tickets. A non-clean control should show what the report found, why the result appears, why it matters, and what evidence would close the gap. This is explanation and evidence direction only; it is not remediation assignment or workflow tracking.

## Public sample/reporting direction

The planned public launch direction is a site-hosted sample report plus a GitHub repository for a free, open-source/self-hosted report generator. The claim must stay narrow: the tool helps teams understand Copilot governance evidence, gaps, and Microsoft-native control readiness. It must not be positioned as tenant-wide Copilot enforcement or independent audit certification.
