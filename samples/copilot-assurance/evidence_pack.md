# Tesrex Copilot Assurance Evidence Pack

> **Synthetic sample only.** This file is committed so visitors can inspect the output format before running the starter kit. It is not customer evidence, not an audit certification, and was generated without live Microsoft tenant access.


- Pack ID: `pack-run-20260530T000000Z`
- Assessment run: `run-20260530T000000Z`
- Tenant: `TCA-DEMO-SYNTHETIC`
- Tool version: `0.1.0`
- Scope: Starter-kit capability/configuration evidence pack from read-only probes and optional manual evidence.
- Run limitations: first_slice, configuration_capability_focus, demo_evidence_present

## Control checks

### LIC-001 — PASS

Reason: Microsoft Graph subscribedSkUs inventory was read successfully.
Evidence completeness: full
Limitations: (none)

### LIC-002.copilot_family — UNKNOWN

Reason: No exact entitlement match found, but the mapping does not claim complete coverage or is stale; license absence is not proven.
Evidence completeness: partial
Limitations: license_limited

### LIC-002.work_graph_chat — UNKNOWN

Reason: No exact entitlement match found, but the mapping does not claim complete coverage or is stale; license absence is not proven.
Evidence completeness: partial
Limitations: license_limited

### AUD-001 — WARN

Reason: Audit query scope is present in the token, but no audit query was created in the default read-only probe; full audit search access is not proven.
Evidence completeness: partial
Limitations: not_configured_for_assessment

### AUD-002 — UNKNOWN

Reason: CopilotInteraction audit record observability requires an explicitly approved audit query and independent usage context; neither is part of the default read-only probe.
Evidence completeness: partial
Limitations: manual_only, not_configured_for_assessment, manual_evidence_linked, demo_evidence

### AUD-003 — UNKNOWN

Reason: Audit retention capability is not proven by token-scope inspection alone; provide Purview audit configuration evidence or approved historical query evidence.
Evidence completeness: partial
Limitations: manual_only, manual_evidence_linked, demo_evidence

### LABEL-001 — WARN

Reason: Sensitivity-label endpoint is reachable but the $top=1 probe returned zero labels; taxonomy coverage is not proven.
Evidence completeness: partial
Limitations: partial_scope

### DLP-001 — UNKNOWN

Reason: ExchangeOnlineManagement module is locally available, but tenant DLP policy/rule inventory was not read in this default run. Provide Purview export or run an approved read-only DLP inventory collector.
Evidence completeness: partial
Limitations: manual_only, not_configured_for_assessment, manual_evidence_linked, demo_evidence

### DLP-002 — UNKNOWN

Reason: ExchangeOnlineManagement module is locally available, but tenant DLP policy/rule inventory was not read in this default run. Provide Purview export or run an approved read-only DLP inventory collector.
Evidence completeness: partial
Limitations: manual_only, not_configured_for_assessment, manual_evidence_linked, demo_evidence

### SAM-001 — WARN

Reason: SharePoint Online PowerShell module is locally available, but SAM/DAG tenant read capability and report freshness were not validated.
Evidence completeness: partial
Limitations: manual_only, partial_scope, manual_evidence_linked, demo_evidence

### EDISC-001 — UNKNOWN

Reason: Explicit Copilot/AI retention stance requires retention policy evidence or customer-provided manual artifact; no retention policy read was run in the default probe.
Evidence completeness: partial
Limitations: manual_only, manual_evidence_linked, demo_evidence

### EDISC-002 — WARN

Reason: eDiscovery case endpoint is visible, but no positive/export-validating readiness evidence is present in the default run.
Evidence completeness: partial
Limitations: partial_scope, no_export_validation, manual_evidence_linked, manual_only, demo_evidence

### PACK-001 — PASS

Reason: All starter-kit controls are represented before pack generation.
Evidence completeness: full
Limitations: (none)

### PACK-002 — PASS

Reason: Evidence inventory has raw artifact paths/hashes or explicit raw-retention limitations.
Evidence completeness: full
Limitations: (none)

## Unread / limited controls register

- `LIC-002.copilot_family`: UNKNOWN — No exact entitlement match found, but the mapping does not claim complete coverage or is stale; license absence is not proven.
- `LIC-002.work_graph_chat`: UNKNOWN — No exact entitlement match found, but the mapping does not claim complete coverage or is stale; license absence is not proven.
- `AUD-001`: WARN — Audit query scope is present in the token, but no audit query was created in the default read-only probe; full audit search access is not proven.
- `AUD-002`: UNKNOWN — CopilotInteraction audit record observability requires an explicitly approved audit query and independent usage context; neither is part of the default read-only probe.
- `AUD-003`: UNKNOWN — Audit retention capability is not proven by token-scope inspection alone; provide Purview audit configuration evidence or approved historical query evidence.
- `LABEL-001`: WARN — Sensitivity-label endpoint is reachable but the $top=1 probe returned zero labels; taxonomy coverage is not proven.
- `DLP-001`: UNKNOWN — ExchangeOnlineManagement module is locally available, but tenant DLP policy/rule inventory was not read in this default run. Provide Purview export or run an approved read-only DLP inventory collector.
- `DLP-002`: UNKNOWN — ExchangeOnlineManagement module is locally available, but tenant DLP policy/rule inventory was not read in this default run. Provide Purview export or run an approved read-only DLP inventory collector.
- `SAM-001`: WARN — SharePoint Online PowerShell module is locally available, but SAM/DAG tenant read capability and report freshness were not validated.
- `EDISC-001`: UNKNOWN — Explicit Copilot/AI retention stance requires retention policy evidence or customer-provided manual artifact; no retention policy read was run in the default probe.
- `EDISC-002`: WARN — eDiscovery case endpoint is visible, but no positive/export-validating readiness evidence is present in the default run.

## Findings

### finding-lic-002-copilot_family — low

Type: evidence_gap
Condition: The report collected partial evidence, but this control is not fully proven.
Evidence: ev-graph-subscribed_skus
Recommendation: Refresh capability map or provide manual/license-admin evidence.

### finding-lic-002-work_graph_chat — low

Type: evidence_gap
Condition: The report collected partial evidence, but this control is not fully proven.
Evidence: ev-graph-subscribed_skus
Recommendation: Refresh capability map or provide manual/license-admin evidence.

### finding-aud-001 — low

Type: improvement_opportunity
Condition: Audit capability signals are present, but audit evidence for this control is not complete.
Evidence: ev-graph-token_scopes
Recommendation: Provide Purview audit evidence, or approve a bounded read-only audit query for the relevant Copilot activity.

### finding-aud-002 — low

Type: evidence_gap
Condition: Audit capability signals are present, but audit evidence for this control is not complete.
Evidence: ev-demo-copilot-chat-transcripts
Recommendation: Provide Purview audit evidence, or approve a bounded read-only audit query for the relevant Copilot activity.

### finding-aud-003 — low

Type: evidence_gap
Condition: Audit capability signals are present, but audit evidence for this control is not complete.
Evidence: ev-demo-retention-policy-evidence
Recommendation: Provide Purview audit evidence, or approve a bounded read-only audit query for the relevant Copilot activity.

### finding-label-001 — low

Type: improvement_opportunity
Condition: Sensitivity-label evidence is partial, so label taxonomy or coverage is not fully proven.
Evidence: ev-graph-sensitivity_labels
Recommendation: Provide sensitivity-label taxonomy/coverage export, or approve the relevant read-only label collector.

### finding-dlp-001 — low

Type: evidence_gap
Condition: DLP policy/rule inventory was not collected, so Copilot DLP coverage is not proven.
Evidence: ev-powershell-exchange_online_management, ev-demo-dlp-policy-export
Recommendation: Provide Purview DLP policy/rule export, or approve the read-only DLP inventory collector.

### finding-dlp-002 — low

Type: evidence_gap
Condition: DLP policy/rule inventory was not collected, so Copilot DLP coverage is not proven.
Evidence: ev-powershell-exchange_online_management, ev-demo-dlp-policy-export
Recommendation: Provide Purview DLP policy/rule export, or approve the read-only DLP inventory collector.

### finding-sam-001 — low

Type: improvement_opportunity
Condition: SharePoint sharing governance tooling is available locally, but tenant oversharing evidence was not collected.
Evidence: ev-powershell-sharepoint_online, ev-demo-sam-oversharing-report
Recommendation: Provide a current SharePoint Advanced Management/DAG export, or approve the read-only sharing evidence collector.

### finding-edisc-001 — low

Type: evidence_gap
Condition: The report does not yet have enough retention-policy evidence for Copilot or AI-related data.
Evidence: ev-demo-retention-policy-evidence
Recommendation: Provide retention-policy evidence from Purview, or approve the relevant read-only retention evidence collector.

### finding-edisc-002 — low

Type: improvement_opportunity
Condition: eDiscovery is reachable, but Copilot data discovery/export readiness is not proven.
Evidence: ev-graph-ediscovery_cases, ev-demo-ediscovery-readiness-fixture
Recommendation: Provide existing Purview eDiscovery evidence, or approve a bounded validation procedure for a scoped mailbox/site.


## Evidence inventory

- `ev-az_account` — raw_api_response from Azure CLI; artifact: `samples/copilot-assurance/generated-source/live_probe/20260530T000000Z/raw/az_account.json`; hash: `34d1b63d588244e08713e76deca1adc7f282d3e683fc06b1e7b9c79b07063f3b`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-az_cloud` — raw_api_response from Azure CLI; artifact: `samples/copilot-assurance/generated-source/live_probe/20260530T000000Z/raw/az_cloud.json`; hash: `dfa498925b153826c6dbc39c906e8e2d086f7b6717d33d1e69c5658e5daac1bb`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-graph-organization` — raw_api_response from Microsoft Graph; artifact: `samples/copilot-assurance/generated-source/live_probe/20260530T000000Z/raw/graph_organization.json`; hash: `865baf356f6de27d39b9389e1c5e6e632d7a9bdc9749876a837e3d080befa30b`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-graph-subscribed_skus` — license_snapshot from Microsoft Graph; artifact: `samples/copilot-assurance/generated-source/live_probe/20260530T000000Z/raw/graph_subscribed_skus.json`; hash: `0f214086a7f13ceb0682b985ee95269d166afac7fc3ffee1890c40a55840cc4a`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-graph-sensitivity_labels` — raw_api_response from Microsoft Graph; artifact: `samples/copilot-assurance/generated-source/live_probe/20260530T000000Z/raw/graph_sensitivity_labels.json`; hash: `0f214086a7f13ceb0682b985ee95269d166afac7fc3ffee1890c40a55840cc4a`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-graph-token_scopes` — normalized_observation from Microsoft Graph; artifact: `samples/copilot-assurance/generated-source/live_probe/20260530T000000Z/raw/graph_token_scopes.json`; hash: `73ac54da7eac95c787ace30e457949c4d6b25a8f4f4a9decd08afce91fbf8b18`; limitations: demo_only, not_customer_evidence, raw_secret_not_retained, synthetic_fixture
- `ev-graph-ediscovery_cases` — raw_api_response from Microsoft Graph; artifact: `samples/copilot-assurance/generated-source/live_probe/20260530T000000Z/raw/graph_ediscovery_cases.json`; hash: `0f214086a7f13ceb0682b985ee95269d166afac7fc3ffee1890c40a55840cc4a`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-powershell-exchange_online_management` — normalized_observation from Local PowerShell module check; artifact: `samples/copilot-assurance/generated-source/live_probe/20260530T000000Z/raw/powershell_exchange_online_management.json`; hash: `22084f3d5e6b023f039e153c1d9406c2196ed8331371ca04611b487e09d4adab`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-powershell-sharepoint_online` — normalized_observation from Local PowerShell module check; artifact: `samples/copilot-assurance/generated-source/live_probe/20260530T000000Z/raw/powershell_sharepoint_online.json`; hash: `c6742b879a2ae69ada32d8cef4b981f968285bd4dd6ee03f04dec674f61ae54c`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-demo-copilot-chat-transcripts` — manual_artifact from TCA synthetic demo fixture; artifact: `samples/copilot-assurance/generated-source/demo_dataset/20260530T000000Z/synthetic_copilot_chat_transcripts.json`; hash: `63bc815ad365c30c627cd04196e9085f4951bc393851416fc38378ad7dbba677`; limitations: customer_asserted, demo_only, manual_only, not_independently_verified_by_tool, synthetic_fixture
- `ev-demo-dlp-policy-export` — policy_snapshot from TCA synthetic demo fixture; artifact: `samples/copilot-assurance/generated-source/demo_dataset/20260530T000000Z/synthetic_dlp_policy_export.json`; hash: `cf96f0ece504c1c72ab9cc5ff02934a79867126440b568a80b4ae33f47f3589a`; limitations: customer_asserted, demo_only, manual_only, not_customer_export, synthetic_fixture
- `ev-demo-sam-oversharing-report` — report_export from TCA synthetic demo fixture; artifact: `samples/copilot-assurance/generated-source/demo_dataset/20260530T000000Z/synthetic_sam_oversharing_report.json`; hash: `0e52cebeb175a90263ec82f3875b7aa822b2aa68fae093ebff5c995aa5d194a8`; limitations: customer_asserted, demo_only, manual_only, not_customer_export, synthetic_fixture
- `ev-demo-retention-policy-evidence` — policy_snapshot from TCA synthetic demo fixture; artifact: `samples/copilot-assurance/generated-source/demo_dataset/20260530T000000Z/synthetic_retention_policy_evidence.json`; hash: `a1f4919081a764d0bab6acb66321f362104732d142d70b703abdf12807e2042f`; limitations: customer_asserted, demo_only, manual_only, not_customer_export, synthetic_fixture
- `ev-demo-ediscovery-readiness-fixture` — report_export from TCA synthetic demo fixture; artifact: `samples/copilot-assurance/generated-source/demo_dataset/20260530T000000Z/synthetic_ediscovery_readiness.json`; hash: `2b69623e924c6b563f85a3c77ca54f9509277803876e201186d1191cf7a91cee`; limitations: customer_asserted, demo_only, manual_only, no_export_validation, synthetic_fixture
