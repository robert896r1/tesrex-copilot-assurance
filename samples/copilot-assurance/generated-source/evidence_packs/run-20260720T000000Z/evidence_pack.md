# Tesrex Copilot Assurance Evidence Pack

> **SYNTHETIC DEMO ONLY:** No live Microsoft tenant was accessed. This is not customer evidence or audit proof.

- Pack ID: `pack-run-20260720T000000Z`
- Assessment run: `run-20260720T000000Z`
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

Reason: Verified the existence and SHA-256 hash of all 14 retained evidence artifacts.
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

- `ev-az_account` — raw_api_response from Azure CLI; artifact: `samples/copilot-assurance/generated-source/live_probe/20260720T000000Z/raw/az_account.json`; hash: `8823614292b26a98847390cca6af809ee52dd0ac87fc272814c1fcb272f30ec4`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-az_cloud` — raw_api_response from Azure CLI; artifact: `samples/copilot-assurance/generated-source/live_probe/20260720T000000Z/raw/az_cloud.json`; hash: `17db73c705b5262147c29aa1f454c2cf66ab6b47b6f7c9223752d079abe32efe`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-graph-organization` — raw_api_response from Microsoft Graph; artifact: `samples/copilot-assurance/generated-source/live_probe/20260720T000000Z/raw/graph_organization.json`; hash: `507c7c8aa2514878dd065571c39fbedff489ac7f199eb7e39e5fc09e75191a3d`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-graph-subscribed_skus` — license_snapshot from Microsoft Graph; artifact: `samples/copilot-assurance/generated-source/live_probe/20260720T000000Z/raw/graph_subscribed_skus.json`; hash: `d5be965331812580127ba5ac22be7be6e74dbf2e07070470e3614a6432f69edd`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-graph-sensitivity_labels` — raw_api_response from Microsoft Graph; artifact: `samples/copilot-assurance/generated-source/live_probe/20260720T000000Z/raw/graph_sensitivity_labels.json`; hash: `d5be965331812580127ba5ac22be7be6e74dbf2e07070470e3614a6432f69edd`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-graph-token_scopes` — normalized_observation from Microsoft Graph; artifact: `samples/copilot-assurance/generated-source/live_probe/20260720T000000Z/raw/graph_token_scopes.json`; hash: `7f8ad131ff948d9685ac77c9c04281f97e959392b3f75a74fd35f3575f26228b`; limitations: demo_only, not_customer_evidence, raw_secret_not_retained, synthetic_fixture
- `ev-graph-ediscovery_cases` — raw_api_response from Microsoft Graph; artifact: `samples/copilot-assurance/generated-source/live_probe/20260720T000000Z/raw/graph_ediscovery_cases.json`; hash: `d5be965331812580127ba5ac22be7be6e74dbf2e07070470e3614a6432f69edd`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-powershell-exchange_online_management` — normalized_observation from Local PowerShell module check; artifact: `samples/copilot-assurance/generated-source/live_probe/20260720T000000Z/raw/powershell_exchange_online_management.json`; hash: `bcb00e4490f59a16d540e1ce645cd90758d082f8944d4356d3e5a86ab8c3b6bf`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-powershell-sharepoint_online` — normalized_observation from Local PowerShell module check; artifact: `samples/copilot-assurance/generated-source/live_probe/20260720T000000Z/raw/powershell_sharepoint_online.json`; hash: `ed3c897c510d34b16085a7e71e0439b82b0f0567fa4b326be5930531ad74d68e`; limitations: demo_only, not_customer_evidence, synthetic_fixture
- `ev-demo-copilot-chat-transcripts` — manual_artifact from TCA synthetic demo fixture; artifact: `samples/copilot-assurance/generated-source/demo_dataset/20260720T000000Z/synthetic_copilot_chat_transcripts.json`; hash: `8e89b23518cfb4f32561b3bb0b0acff0352d6694bcde030758c18146a5921aa3`; limitations: customer_asserted, demo_only, manual_only, not_independently_verified_by_tool, synthetic_fixture
- `ev-demo-dlp-policy-export` — policy_snapshot from TCA synthetic demo fixture; artifact: `samples/copilot-assurance/generated-source/demo_dataset/20260720T000000Z/synthetic_dlp_policy_export.json`; hash: `197c7b016d1b9eb0ecba4c0f584a485f4a47fac0096de9f84c2cfd9dc02dc2e1`; limitations: customer_asserted, demo_only, manual_only, not_customer_export, synthetic_fixture
- `ev-demo-sam-oversharing-report` — report_export from TCA synthetic demo fixture; artifact: `samples/copilot-assurance/generated-source/demo_dataset/20260720T000000Z/synthetic_sam_oversharing_report.json`; hash: `53631d7a8263203f8bf70f68d16ac0c2a7f123fda077cbf51ccf2b57d5bd875b`; limitations: customer_asserted, demo_only, manual_only, not_customer_export, synthetic_fixture
- `ev-demo-retention-policy-evidence` — policy_snapshot from TCA synthetic demo fixture; artifact: `samples/copilot-assurance/generated-source/demo_dataset/20260720T000000Z/synthetic_retention_policy_evidence.json`; hash: `59bca5cd4bc247dfed83d01e0147d576f49b284bf9d42e1ad81480dc89b6b6a5`; limitations: customer_asserted, demo_only, manual_only, not_customer_export, synthetic_fixture
- `ev-demo-ediscovery-readiness-fixture` — report_export from TCA synthetic demo fixture; artifact: `samples/copilot-assurance/generated-source/demo_dataset/20260720T000000Z/synthetic_ediscovery_readiness.json`; hash: `a7bc69a44e8b9d21c4bac867edbba38450295e002e27f1d5e9c22ce5d24b7070`; limitations: customer_asserted, demo_only, manual_only, no_export_validation, synthetic_fixture
