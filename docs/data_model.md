# Data Model

The authoritative implemented model is `src/tesrex_assurance/models.py`. The summary below describes the public `0.1.0` evidence-pack shape; it is not a future product schema.

## Implemented entity overview

```text
AssessmentRun
  EvidenceItem[]
  ControlCheck[]
  Finding[]
EvidencePack
```

## `AssessmentRun`

One local assessment execution.

Fields: `assessment_run_id`, `tenant_id`, `started_at_utc`, `initiated_by`, `tool_version`, `status`, `completed_at_utc`, `scope_summary`, and `limitations`.

## `EvidenceItem`

Retained or explicitly unavailable support for a control check or finding.

Fields: `evidence_id`, `assessment_run_id`, `evidence_type`, `source_system`, `source_endpoint_or_ui_path`, `collection_method`, `collected_at_utc`, `tenant_id`, `collector_identity`, `permission_context`, `source_object_identifiers`, `raw_artifact_path`, `content_hash`, `normalized_facts`, `relevance_rating`, `reliability_rating`, `limitations`, and `mapping_versions_used`.

Allowed evidence types are defined by `EvidenceType` in the implementation. A retained artifact must have a content hash; an unretained artifact must disclose `raw_retention_unavailable`.

## `ControlCheck`

A classification for a bounded Microsoft-native governance control scope.

Fields: `control_check_id`, `assessment_run_id`, `control_family`, `control_objective`, `expected_state`, `assessed_scope`, `procedure`, `required_evidence_types`, `evidence_items_used`, `observed_state`, `status`, `status_reason`, `evidence_completeness`, `status_cause`, `limitations`, `follow_up_required`, and `mapping_versions_used`.

Status is one of `PASS`, `WARN`, `FAIL`, `UNKNOWN`, `NOT_LICENSED`, or `NOT_ACCESSIBLE`. Status cause and evidence completeness are separate fields; a clean-looking status does not expand the assessed scope.

## `Finding`

An evidence-linked gap, risk, or follow-up observation.

Fields: `finding_id`, `assessment_run_id`, `finding_type`, `title`, `criterion`, `condition`, `cause`, `impact_or_risk`, `affected_scope`, `affected_objects`, `severity`, `confidence`, `confidence_reason`, `evidence_references`, `related_control_checks`, `recommendation`, `owner`, `status`, and `due_date`.

The current implementation records recommendations and optional ownership metadata. It does not implement a remediation workflow engine.

## `EvidencePack`

The report container.

Fields: `evidence_pack_id`, `assessment_run`, `evidence_items`, `control_checks`, `findings`, `generated_at_utc`, `format`, `artifact_path`, and `content_hash`.

The renderers currently produce JSON, Markdown, and static HTML artifacts. The dataclass does not model a separate tenant registry, remediation-action entity, or historical comparison store.

## Evidence semantics

`docs/evidence_contract.md` defines the intended evidence and classification semantics. Code and tests are the executable source for the implemented field shape. Changes to either must keep the other aligned.

## Explicit future ideas

A tenant registry, normalized remediation-action entity, historical trend store, PDF/ZIP bundle metadata, or workflow state may be considered later. None is part of the current public data model, and this document does not authorize adding it.
