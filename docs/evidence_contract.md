# Evidence Contract

Status: Starter-kit evidence semantics baseline
Last reviewed: 2026-04-30

## Purpose

This contract defines the semantic foundation for Tesrex Copilot Assurance.

The product is evidence-pack-led. Collectors, reports, storage, and future UI must preserve the distinctions in this document.

The core rule is:

> Do not turn missing evidence into confidence, and do not turn inferred risk into proven fact.

## Source basis

This baseline is synthesized from:

- Microsoft Copilot/Purview audit logging and Copilot data protection documentation.
- Microsoft guidance for secure and governed Microsoft 365 Copilot deployment.
- SharePoint Advanced Management and Microsoft Purview Audit licensing/permission documentation.
- NIST SP 800-53A control assessment concepts.
- Audit evidence principles from PCAOB/AICPA and IT audit reporting guidance from ISACA.

Key references:

- Microsoft Copilot audit logs: <https://learn.microsoft.com/en-us/purview/audit-copilot>
- Microsoft secure/governed Copilot foundation: <https://learn.microsoft.com/en-us/microsoft-365/copilot/configure-secure-governed-data-foundation-microsoft-365-copilot>
- Microsoft Copilot data protection/auditing: <https://learn.microsoft.com/en-us/microsoft-365/copilot/microsoft-365-copilot-architecture-data-protection-auditing>
- SharePoint Advanced Management: <https://learn.microsoft.com/en-us/SharePoint/advanced-management>
- Microsoft Graph Purview Audit Search API: <https://learn.microsoft.com/en-us/graph/api/security-auditcoreroot-post-auditlogqueries>
- Microsoft Purview Audit overview: <https://learn.microsoft.com/en-us/purview/audit-solutions-overview>
- NIST SP 800-53A Rev. 5: <https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53Ar5.pdf>
- PCAOB AS 1105 Audit Evidence: <https://pcaobus.org/oversight/standards/auditing-standards/details/AS1105>
- AICPA audit evidence topic: <https://www.aicpa-cima.com/topic/audit-assurance/audit-evidence>
- ISACA audit report components: <https://www.isaca.org/resources/isaca-journal/issues/2020/volume-1/is-audit-basics-the-components-of-the-it-audit-report>

## Evidence item

An evidence item is the smallest durable proof object the product can cite.

It may be:

- a raw Microsoft Graph response;
- a Purview audit record;
- a Purview, SAM, or admin-center export;
- a DLP policy snapshot;
- a sensitivity-label snapshot;
- a license or entitlement snapshot;
- a permission-denial record;
- a UI screenshot;
- a manual customer artifact.

An evidence item is not automatically a finding and does not automatically prove a control outcome. It supports a control check, a finding, or a declared limitation.

### Required fields

- `evidence_id`
- `assessment_run_id`
- `evidence_type`
- `source_system`
- `source_endpoint_or_ui_path`
- `collection_method`
- `collected_at_utc`
- `tenant_id`
- `collector_identity`
- `permission_context`
- `source_object_identifiers`
- `raw_artifact_path`
- `content_hash`
- `normalized_facts`
- `relevance_rating`
- `reliability_rating`
- `limitations`

For bounded validation evidence that exercises a Microsoft API without assessing tenant content, `normalized_facts` must explicitly state:

- `validation_scope` — for example, `api_connectivity_only`;
- `content_scope` — for example, `none`;
- `source_binding` — for example, `none`;
- `export_performed` — `false`;
- `purge_performed` — `false`.

This prevents a no-source API validation from being misread as a sampled content search.

`api_connectivity_only` means no tenant content is retrieved, exported, purged, or source-bound. If a validation retrieves tenant content, binds a mailbox/site/custodian source, exports data, or purges data, it is not `api_connectivity_only` and requires a separate explicit evidence scope.

For mailbox-location validation evidence, `normalized_facts` must explicitly state:

- `validation_scope` — `mailbox_location_validation`;
- `outcome_status` — for the current validated case, `zero_result`;
- `content_scope` — for the current validated case, `zero_result`;
- `source_binding` — `exchange_mailbox_location`;
- `query_string` — exact query used;
- `query_execution_id` — artifact/run identifier;
- `result_item_count`;
- `result_size`;
- `query_syntax_accepted`;
- `export_performed` — `false`;
- `purge_performed` — `false`;
- `hold_changes_performed` — `false`;
- `custodian_source_binding_performed` — `false`.

`mailbox_location_validation` means a specific Exchange mailbox location was used in a permitted Compliance Search validation. It is stronger than no-source API reachability because the service accepted a real mailbox location, but a zero-result outcome still does not prove Copilot/AI content discovery readiness. A zero-result mailbox-location validation must remain `WARN`/partial for EDISC-002 unless paired later with a positive search plus export-validating evidence, or customer-provided Purview export/readiness evidence.

For EDISC-002, a "positive test" is not merely a search that returns a non-zero count. `PASS` requires either:

1. a permitted mailbox/content search with a positive result and separate export-validating evidence; or
2. a customer-provided Purview export/readiness artifact that explicitly supports search/export readiness.

A positive search count without export-validating evidence remains `WARN`/partial because it proves location/query reachability and result counting, not investigation/export readiness.

### Evidence type enum

Allowed values:

- `raw_api_response`
- `normalized_observation`
- `audit_record`
- `policy_snapshot`
- `license_snapshot`
- `permission_denial`
- `manual_artifact`
- `screenshot`
- `report_export`

Rejected value:

- `unsupported_api_note`

Reason: unsupported API behavior is a limitation or collection constraint, not evidence by itself. If an API gap matters, preserve a real artifact such as an API error response, screenshot, export, or manual artifact.

### Evidence rule

Never cite a normalized fact unless either:

1. the raw artifact is retained and hashable; or
2. the pack explicitly states why raw retention was not possible.

## Control check

A control check is a deterministic assessment procedure applied to one named control expectation in a defined scope.

It answers:

> Did this specific control expectation meet its expected state for this assessed scope, using this evidence?

### Required fields

- `control_check_id`
- `assessment_run_id`
- `control_family`
- `control_objective`
- `expected_state`
- `assessed_scope`
- `procedure`
- `required_evidence_types`
- `evidence_items_used`
- `observed_state`
- `status`
- `status_cause`
- `status_reason`
- `evidence_completeness`
- `limitations`
- `follow_up_required`

### Evidence completeness enum

- `full`: evidence is sufficient for the defined scope.
- `partial`: some evidence was collected, but scope, age, coverage, or source limitations remain.
- `none`: no usable evidence was collected.

Do not use arbitrary numeric confidence scores for control checks unless a later approved sampling/statistical model defines how the score is calculated.

### Control check rule

A control check can assess only the control and scope it actually observed.

Do not infer tenant-wide `PASS` from a narrow sample unless the sampling method and limitation are disclosed.

## Finding

A finding is an auditor-facing conclusion derived from one or more control checks and evidence items.

It is the actionable statement a reviewer or customer can understand and act on.

A failed control check may produce a finding, but not every finding is a failed check. Some findings are exposure risks, evidence gaps, license gaps, permission gaps, or improvement opportunities.

### Required fields

- `finding_id`
- `assessment_run_id`
- `finding_type`
- `title`
- `criterion`
- `condition`
- `cause`
- `impact_or_risk`
- `affected_scope`
- `affected_objects`
- `severity`
- `confidence`
- `confidence_reason`
- `evidence_references`
- `related_control_checks`
- `recommendation`
- `owner`
- `status`
- `due_date`

### Finding type enum

- `control_gap`
- `exposure_risk`
- `evidence_gap`
- `license_gap`
- `permission_gap`
- `unsupported_api_gap`
- `improvement_opportunity`

### Cause enum

- `configuration_error`
- `missing_control`
- `license_gap`
- `permission_gap`
- `api_unsupported`
- `unknown_root_cause`

If `cause` is `unknown_root_cause`, the finding type must not be `control_gap`. Use `evidence_gap` or `improvement_opportunity` until stronger evidence exists.

### Finding rule

Findings must distinguish observed condition from inferred risk.

Example:

- Proven condition: `Site X has Anyone links and sensitive-label hits.`
- Inferred risk: `Copilot exposure risk is elevated for Site X.`

The risk statement must reference the facts and rule that produced it.

## Control check status enum

Allowed values:

- `PASS`
- `WARN`
- `FAIL`
- `UNKNOWN`
- `NOT_LICENSED`
- `NOT_ACCESSIBLE`

Do not add `UNSUPPORTED_API` as a status. Unsupported API access is a limitation/reason, not a control state.

## Control check status-cause enum

`status` is the canonical result. `status_cause` explains why the result exists in a way a director, assessor, or auditor can understand without reading every raw artifact.

Allowed values:

- `verified` — the evidence supports the result for the assessed scope.
- `tenant_gap` — the collected evidence indicates a tenant configuration/control gap.
- `assessment_limitation` — the product did not collect enough supported evidence to decide the real tenant state.
- `permission_gap` — the assessment identity lacked permission/RBAC/consent to read the source.
- `not_licensed` — the required Microsoft capability appears unavailable because of licensing/entitlement.
- `unsupported_api` — the needed fact is not exposed through a supported API path for the current assessment route.
- `usage_absence` — the check cannot prove behavior because there is no observed usage/sample in scope.
- `manual_evidence_required` — the required fact is expected from UI/export/customer artifact and none is currently usable.
- `demo_evidence` — synthetic/demo evidence influenced the check and must not be treated as production assurance.

Do not use `status_cause` to change the meaning of `status`. Example: `WARN` + `assessment_limitation` is not a tenant failure; it says the report needs better evidence before stronger assurance can be claimed.

Default interpretation rules:

- `UNKNOWN` defaults to `assessment_limitation` unless permission, license, unsupported-API, usage-absence, or manual-evidence markers are present.
- `WARN` defaults to `assessment_limitation` unless explicit tenant-gap markers are present.
- `FAIL` can map to `tenant_gap` because `FAIL` requires sufficient evidence that the expected state is not met.
- Current automated inference uses structured limitations first, then selected status-reason keywords. Treat the generated cause as a review aid, not a substitute for reading the linked evidence and limitations.
- Demo/synthetic/manual/stale/sample markers are evidence-quality notes. They must be visible when material, but they should not mask the primary reason a control is unresolved when a clearer cause exists. UI renderers should prioritize and cap quality tags so the primary message remains readable.

## Human review-label rule

The UI may derive human labels from `status + status_cause`, but those labels must not replace the canonical status.

Examples:

- `WARN + assessment_limitation` -> `Evidence incomplete`.
- `UNKNOWN + assessment_limitation` -> `Not assessed`.
- `NOT_ACCESSIBLE + permission_gap` -> `Access required`.
- `NOT_LICENSED + not_licensed` -> `Licensing required`.
- `WARN/FAIL + tenant_gap` -> `Tenant action required`.
- `UNKNOWN/WARN + unsupported_api` -> `Microsoft API limitation`.

Every non-clean control should include a plain-language meaning and next action so a reviewer can tell whether they are seeing a tenant problem, an assessment limitation, an access/licensing problem, an unsupported API path, usage absence, or evidence quality limitation.

## Status semantics

### PASS

Required evidence was collected for the defined scope and shows the expected state is met.

Limitations, if any, do not materially undermine the conclusion.

### WARN

Evidence shows the control is present or partly effective, but there is a material caveat.

Use for:

- partial coverage;
- stale evidence;
- weak configuration;
- risky exception;
- unvalidated sample;
- early risk signal;
- alternate evidence exists but supported API coverage is incomplete.

`WARN` is not a disguised `FAIL`.

When evidence is operationally useful but inconclusive for readiness, use `WARN` with `evidence_completeness=partial` and a plain-language status reason that says the result is inconclusive. Do not introduce an unapproved `INCONCLUSIVE` status.

### FAIL

Sufficient evidence shows the expected state is not met for the defined scope.

### UNKNOWN

Evidence is insufficient to decide `PASS`, `WARN`, or `FAIL`, and the reason is not proven license absence or access denial.

Use for:

- inconclusive data;
- stale data with no current substitute;
- conflicting data;
- timeout or rate limit without authorization failure;
- API returns success with empty or null data where interpretation is unclear;
- data exists only in UI/export/PowerShell and no manual artifact was supplied;
- API unsupported and no alternate evidence exists.

Do not use `UNKNOWN` for authorization failures.

### NOT_LICENSED

The required Microsoft capability or data source is unavailable because the tenant or user lacks the required license, entitlement, or add-on.

This is not a security failure. It is an assurance coverage limitation and product capability gap.

### NOT_ACCESSIBLE

The capability may exist, but the assessment identity cannot read it.

Use for:

- `401` or `403` responses;
- missing Microsoft Graph permission;
- missing admin role;
- missing consent;
- RBAC denial;
- Conditional Access block;
- tenant policy block;
- national-cloud unsupported route for the attempted API;
- explicit access-denied UI/API response.

This is not proof that the control is absent.

## Limitation enum

Allowed values:

- `api_unsupported`
- `manual_only`
- `sampled`
- `stale`
- `partial_scope`
- `permission_limited`
- `license_limited`
- `rate_limited`
- `timeout`
- `conflicting_sources`
- `raw_retention_unavailable`
- `national_cloud_limited`
- `not_configured_for_assessment`
- `zero_content_scope`
- `zero_result`
- `no_positive_hit`
- `no_export_validation`
- `syntax_constraint`
- `customer_asserted`

## Distinction rules

### Proven fact

A proven fact is directly observed from an authoritative source with:

- timestamp;
- source object ID;
- collection method;
- collector identity;
- raw artifact or hash;
- no hidden inference.

Example:

> Purview audit query `abc` returned `succeeded` for the date range `2026-04-01` to `2026-04-29`.

### Inferred risk

An inferred risk is derived from proven facts plus an explicit rule, threshold, or mapping.

Example:

> Site has broad sharing links and sensitive-label hits, therefore Copilot exposure risk is elevated.

The pack must show both the source facts and the rule.

### Unavailable control

An unavailable control means the product or tenant does not expose or enable the capability in the assessed environment for reasons other than assessor permissions.

Use `UNKNOWN` with a precise limitation unless the root cause is proven license or access.

### Missing permission

A missing permission means the collector encountered authorization, RBAC, consent, role, or policy denial.

Status: `NOT_ACCESSIBLE`.

The evidence pack must include the denial artifact and the likely required role/permission if known.

### Not licensed

Not licensed means entitlement evidence shows the required capability is absent.

Status: `NOT_LICENSED`.

The evidence pack must cite the license/entitlement artifact.

### Unsupported by API

Unsupported by API means Microsoft may expose the relevant state in UI, export, or PowerShell, but no supported API exposes the required field/control, or the attempted API explicitly excludes it.

This is not a control failure.

Status:

- `UNKNOWN` if no alternate evidence exists;
- `WARN` if alternate evidence exists but API repeatability is weaker;
- `PASS` or `FAIL` only if alternate evidence is sufficient for the defined scope.

Limitation: `api_unsupported`.

## Review-ready evidence pack target

The items in this section describe the evidence-contract target for a mature pack. Version `0.1.0` does not claim that every generated pack contains every appendix below or is sufficient for an external audit. The generated control checks, inventory, findings, and limitations are the implemented first slice; missing target sections remain product gaps rather than implied assurance.

An evidence pack must be complete enough for a reviewer to understand:

- what was assessed;
- how it was assessed;
- what was proven;
- what was inferred;
- what could not be concluded;
- what action is recommended.

Minimum contents:

1. Executive summary.
2. Assessment scope and methodology.
3. Control matrix.
4. Evidence inventory.
5. Findings register.
6. Unread/unassessed controls register.
7. License and permission limitations.
8. Unsupported-by-API limitations.
9. Microsoft-native control-state appendix.
10. Copilot exposure appendix.
11. Assumptions and exclusions.
12. Reproducibility details.
13. Management/remediation view.

### Unread controls rule

Unread controls remain first-class evidence-pack entries.

The product must not:

- hide unread controls;
- silently skip unread controls;
- mark unread controls as failed by default;
- imply assurance where no evidence exists.

Every unread control must include:

- attempted method;
- source system;
- exact failure or limitation;
- status;
- evidence artifact for the failure/limitation;
- assessor action required.

Starter-kit design consequence

Before collector implementation, every starter kit control must map to this contract:

- expected evidence item types;
- status rules;
- limitation handling;
- unread-control behavior;
- pack output section.
