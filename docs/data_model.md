# Data Model Draft

Design principle: model assessment evidence, not chat turns.

## Entity overview

```text
Tenant
  AssessmentRun
    ControlCheck
    Finding
      EvidenceItem
      RemediationAction
    EvidencePack
```

## Tenant

Represents the customer tenant being assessed.

Fields:

- tenant_id
- display_name
- primary_domain
- assessment_enabled_at
- notes

## AssessmentRun

One execution of the read-only assessment.

Fields:

- assessment_run_id
- tenant_id
- started_at
- completed_at
- initiated_by
- tool_version
- status: `RUNNING | COMPLETED | PARTIAL | FAILED`
- scope_summary
- limitations

## ControlCheck

A check against a Microsoft-native governance control.

Fields:

- control_check_id
- assessment_run_id
- control_family
- control_objective
- expected_state
- assessed_scope
- procedure
- required_evidence_types
- evidence_items_used
- observed_state
- status: `PASS | WARN | FAIL | UNKNOWN | NOT_LICENSED | NOT_ACCESSIBLE`
- status_cause: `verified | tenant_gap | assessment_limitation | permission_gap | not_licensed | unsupported_api | usage_absence | manual_evidence_required | demo_evidence`
- status_reason
- evidence_refs
- source_system
- collection_method: `API | POWERSHELL | EXPORT | MANUAL | UNKNOWN`
- evidence_completeness: `FULL | PARTIAL | NONE`
- limitations
- follow_up_required
- notes

## Finding

A risk, gap, or notable observation.

Fields:

- finding_id
- assessment_run_id
- finding_type: `CONTROL_GAP | EXPOSURE_RISK | EVIDENCE_GAP | LICENSE_GAP | PERMISSION_GAP | UNSUPPORTED_API_GAP | IMPROVEMENT_OPPORTUNITY`
- title
- criterion
- condition
- cause: `CONFIGURATION_ERROR | MISSING_CONTROL | LICENSE_GAP | PERMISSION_GAP | API_UNSUPPORTED | UNKNOWN_ROOT_CAUSE`
- impact_or_risk
- affected_scope
- affected_objects
- severity: `INFORMATIONAL | LOW | MEDIUM | HIGH | CRITICAL`
- confidence: `LOW | MEDIUM | HIGH`
- confidence_reason
- evidence_refs
- related_control_check_refs
- recommended_action_refs
- status: `OPEN | ACCEPTED | IN_PROGRESS | REMEDIATED | FALSE_POSITIVE`

## EvidenceItem

Concrete support for a check or finding.

Fields:

- evidence_id
- assessment_run_id
- evidence_type: `RAW_API_RESPONSE | NORMALIZED_OBSERVATION | AUDIT_RECORD | POLICY_SNAPSHOT | LICENSE_SNAPSHOT | PERMISSION_DENIAL | MANUAL_ARTIFACT | SCREENSHOT | REPORT_EXPORT`
- source_system
- source_endpoint_or_ui_path
- source_object_type
- source_object_id
- source_url
- collected_at_utc
- collector_identity
- permission_context
- collection_method
- content_hash
- normalized_facts
- raw_artifact_path
- relevance_rating
- reliability_rating
- sensitivity
- limitations

## Evidence semantics

Authoritative definitions for evidence items, control checks, findings, status values, distinction rules, and auditor-ready pack requirements are locked in:

`docs/evidence_contract.md`

Do not introduce new control statuses or evidence semantics without updating that contract and recording a decision.

## RemediationAction

A recommended human action.

Fields:

- remediation_id
- finding_id
- action_type
- title
- steps
- owner_role
- microsoft_tool
- requires_approval
- reversible
- estimated_effort
- status

## EvidencePack

Exportable report bundle.

Fields:

- evidence_pack_id
- assessment_run_id
- generated_at
- format: `HTML | PDF | JSON | ZIP`
- artifact_path
- hash
- audience: `EXECUTIVE | TECHNICAL | AUDIT | REMEDIATION`

## Non-goals

Do not model:

- LLM chat messages as the primary unit;
- prompt/response traces as the core schema;
- external model/web-search provider state;
- Teams conversation state.
