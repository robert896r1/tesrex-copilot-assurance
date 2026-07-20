# Product Thesis

## One-sentence definition for this release

Tesrex Copilot Assurance is a free, self-hosted starter kit that packages selected Microsoft 365 Copilot governance signals and customer-provided evidence into an explainable local evidence report.

## What version 0.1.0 implements

The current repository provides:

1. a tenant-free synthetic demo and committed sample report;
2. an allowlisted, read-only tenant probe for selected Graph and local PowerShell capability signals;
3. conservative classification of control visibility, permissions, licensing evidence, manual evidence needs, and assessment limitations;
4. a JSON, Markdown, and static HTML evidence-pack format;
5. source paths, timestamps, hashes, limitations, and control mappings for retained evidence; and
6. tests and repository guards intended to prevent tenant mutation and accidental publication of generated assessment artifacts.

It is a readiness aid and evidence-pack scaffold. It does not independently establish that a tenant is secure, compliant, or ready for broad Copilot deployment.

## What it does not implement

This release does not provide:

- continuous monitoring;
- automatic remediation or workflow ownership;
- tenant-wide content or oversharing discovery;
- proof that policies are effective merely because an endpoint or policy object is visible;
- positive eDiscovery export validation in the default path;
- an audit certification or compliance guarantee;
- a hosted Tesrex service;
- a Copilot replacement, chatbot, or runtime interception layer.

## Honest market position

Microsoft owns the enforcement and control planes. The starter kit helps a reviewer collate a bounded set of Microsoft-native and manually supplied evidence without hiding gaps in access, licensing, API support, or collection scope.

The current claim is:

> Tesrex Copilot Assurance helps teams package and explain selected Copilot governance evidence, including what was verified and what remains unverified.

It is not:

> Tesrex Copilot Assurance proves that Microsoft controls are configured, effective, continuously monitored, or audit-ready.

## Why the approach may be useful

Copilot governance evidence is distributed across Microsoft Purview, SharePoint administration, Entra, Microsoft Graph, licensing, Audit, eDiscovery, PowerShell, exports, and tenant-specific RBAC. A common evidence contract can reduce review friction by showing:

- the control and assessed scope;
- evidence used and retained hashes;
- the classification and separate reason/cause;
- limitations and permission or licensing gaps; and
- the next evidence step.

The report must remain transparent about source limits. Unavailable or partial evidence must never become false assurance.

## Product direction, not current capability

Possible later work includes broader read-only collectors, before/after comparison, operator-owned remediation tracking, and more Microsoft control surfaces. Those are roadmap ideas, not behavior delivered by this repository. Any extension must preserve the read-only default and update the evidence contract, permission matrix, tests, and public claims.
