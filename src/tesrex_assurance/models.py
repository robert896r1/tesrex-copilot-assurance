"""Core TCA evidence contract models.

The dataclasses and enums here define the public evidence-pack shape: evidence items, control checks, findings, assessment runs, and status semantics."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import StrEnum
from typing import Any


class EvidenceType(StrEnum):
    RAW_API_RESPONSE = "raw_api_response"
    NORMALIZED_OBSERVATION = "normalized_observation"
    AUDIT_RECORD = "audit_record"
    POLICY_SNAPSHOT = "policy_snapshot"
    LICENSE_SNAPSHOT = "license_snapshot"
    PERMISSION_DENIAL = "permission_denial"
    MANUAL_ARTIFACT = "manual_artifact"
    SCREENSHOT = "screenshot"
    REPORT_EXPORT = "report_export"


class ControlStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_LICENSED = "NOT_LICENSED"
    NOT_ACCESSIBLE = "NOT_ACCESSIBLE"


class EvidenceCompleteness(StrEnum):
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class StatusCause(StrEnum):
    VERIFIED = "verified"
    TENANT_GAP = "tenant_gap"
    ASSESSMENT_LIMITATION = "assessment_limitation"
    PERMISSION_GAP = "permission_gap"
    NOT_LICENSED = "not_licensed"
    UNSUPPORTED_API = "unsupported_api"
    USAGE_ABSENCE = "usage_absence"
    MANUAL_EVIDENCE_REQUIRED = "manual_evidence_required"
    DEMO_EVIDENCE = "demo_evidence"


class FindingType(StrEnum):
    CONTROL_GAP = "control_gap"
    EXPOSURE_RISK = "exposure_risk"
    EVIDENCE_GAP = "evidence_gap"
    LICENSE_GAP = "license_gap"
    PERMISSION_GAP = "permission_gap"
    UNSUPPORTED_API_GAP = "unsupported_api_gap"
    IMPROVEMENT_OPPORTUNITY = "improvement_opportunity"


class FindingCause(StrEnum):
    CONFIGURATION_ERROR = "configuration_error"
    MISSING_CONTROL = "missing_control"
    LICENSE_GAP = "license_gap"
    PERMISSION_GAP = "permission_gap"
    API_UNSUPPORTED = "api_unsupported"
    UNKNOWN_ROOT_CAUSE = "unknown_root_cause"


class Severity(StrEnum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class MappingVersion:
    artifact_path: str
    schema_version: str
    last_reviewed: str
    stale: bool


@dataclass
class EvidenceItem:
    evidence_id: str
    assessment_run_id: str
    evidence_type: EvidenceType
    source_system: str
    source_endpoint_or_ui_path: str
    collection_method: str
    collected_at_utc: str
    tenant_id: str
    collector_identity: str
    permission_context: str
    source_object_identifiers: dict[str, Any] = field(default_factory=dict)
    raw_artifact_path: str | None = None
    content_hash: str | None = None
    normalized_facts: dict[str, Any] = field(default_factory=dict)
    relevance_rating: str = "medium"
    reliability_rating: str = "medium"
    limitations: list[str] = field(default_factory=list)
    mapping_versions_used: list[MappingVersion] = field(default_factory=list)

    def validate(self) -> None:
        if self.evidence_type == "unsupported_api_note":
            raise ValueError("unsupported_api_note is not an allowed evidence type")
        if not self.content_hash and "raw_retention_unavailable" not in self.limitations:
            raise ValueError(f"Evidence item {self.evidence_id} lacks content_hash or raw_retention_unavailable limitation")
        validation_scope = self.normalized_facts.get("validation_scope")
        if validation_scope == "api_connectivity_only":
            required = {
                "content_scope",
                "source_binding",
                "export_performed",
                "purge_performed",
            }
            missing = sorted(required.difference(self.normalized_facts))
            if missing:
                raise ValueError(f"Bounded validation evidence {self.evidence_id} lacks normalized_facts fields: {missing}")
            if self.normalized_facts.get("content_scope") != "none":
                raise ValueError(f"Bounded validation evidence {self.evidence_id} must declare content_scope=none")
            if self.normalized_facts.get("source_binding") != "none":
                raise ValueError(f"Bounded validation evidence {self.evidence_id} must declare source_binding=none")
            if self.normalized_facts.get("export_performed") is not False:
                raise ValueError(f"Bounded validation evidence {self.evidence_id} must declare export_performed=false")
            if self.normalized_facts.get("purge_performed") is not False:
                raise ValueError(f"Bounded validation evidence {self.evidence_id} must declare purge_performed=false")
            if "zero_content_scope" not in self.limitations:
                raise ValueError(f"Bounded validation evidence {self.evidence_id} must include zero_content_scope limitation")
        if validation_scope == "mailbox_location_validation":
            required = {
                "content_scope",
                "source_binding",
                "outcome_status",
                "query_string",
                "query_execution_id",
                "result_item_count",
                "result_size",
                "query_syntax_accepted",
                "export_performed",
                "purge_performed",
                "hold_changes_performed",
                "custodian_source_binding_performed",
            }
            missing = sorted(required.difference(self.normalized_facts))
            if missing:
                raise ValueError(f"Mailbox-location validation evidence {self.evidence_id} lacks normalized_facts fields: {missing}")
            if self.normalized_facts.get("source_binding") != "exchange_mailbox_location":
                raise ValueError(f"Mailbox-location validation evidence {self.evidence_id} must declare source_binding=exchange_mailbox_location")
            if self.normalized_facts.get("query_syntax_accepted") is not True:
                raise ValueError(f"Mailbox-location validation evidence {self.evidence_id} must declare query_syntax_accepted=true")
            if self.normalized_facts.get("export_performed") is not False:
                raise ValueError(f"Mailbox-location validation evidence {self.evidence_id} must declare export_performed=false")
            if self.normalized_facts.get("purge_performed") is not False:
                raise ValueError(f"Mailbox-location validation evidence {self.evidence_id} must declare purge_performed=false")
            if self.normalized_facts.get("hold_changes_performed") is not False:
                raise ValueError(f"Mailbox-location validation evidence {self.evidence_id} must declare hold_changes_performed=false")
            if self.normalized_facts.get("custodian_source_binding_performed") is not False:
                raise ValueError(
                    f"Mailbox-location validation evidence {self.evidence_id} must declare custodian_source_binding_performed=false"
                )
            if self.normalized_facts.get("outcome_status") == "zero_result":
                if self.normalized_facts.get("content_scope") != "zero_result":
                    raise ValueError(f"Mailbox-location zero-result evidence {self.evidence_id} must declare content_scope=zero_result")
                if self.normalized_facts.get("result_item_count") != 0:
                    raise ValueError(f"Mailbox-location zero-result evidence {self.evidence_id} must declare result_item_count=0")
                required_limitations = {"partial_scope", "sampled", "zero_result", "no_positive_hit", "no_export_validation"}
                missing_limitations = sorted(required_limitations.difference(self.limitations))
                if missing_limitations:
                    raise ValueError(
                        f"Mailbox-location zero-result evidence {self.evidence_id} lacks limitations: {missing_limitations}"
                    )


@dataclass
class ControlCheck:
    control_check_id: str
    assessment_run_id: str
    control_family: str
    control_objective: str
    expected_state: str
    assessed_scope: str
    procedure: str
    required_evidence_types: list[EvidenceType]
    evidence_items_used: list[str]
    observed_state: str
    status: ControlStatus
    status_reason: str
    evidence_completeness: EvidenceCompleteness
    status_cause: StatusCause | None = None
    limitations: list[str] = field(default_factory=list)
    follow_up_required: list[str] = field(default_factory=list)
    mapping_versions_used: list[MappingVersion] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status_cause is None:
            self.status_cause = infer_status_cause(self.status, self.limitations, self.status_reason)

    def validate(self) -> None:
        if self.status_cause is None:
            self.status_cause = infer_status_cause(self.status, self.limitations, self.status_reason)
        if str(self.status) == "UNSUPPORTED_API":
            raise ValueError("UNSUPPORTED_API is not an allowed control status")
        if self.status == ControlStatus.UNKNOWN and any(
            marker in " ".join(self.limitations + [self.status_reason]).lower()
            for marker in ["403", "401", "access denied", "rbac", "consent", "authorization"]
        ):
            raise ValueError("Access/authorization failures must use NOT_ACCESSIBLE, not UNKNOWN")


def infer_status_cause(status: ControlStatus, limitations: list[str], status_reason: str) -> StatusCause:
    text = " ".join(limitations + [status_reason]).lower()
    has_demo_marker = any(marker in limitations for marker in ["demo_evidence", "demo_only", "synthetic_fixture", "demo_evidence_in_full_check"])
    tenant_gap_markers = [
        "missing_control",
        "tenant_gap",
        "configuration_gap",
        "misconfigured",
        "not configured",
        "policy missing",
        "no matching policy",
        "expected state is not met",
        "non-compliant",
        "violation",
    ]
    assessment_markers = [
        "assessment_limitation",
        "not_configured_for_assessment",
        "probe_missing",
        "partial_scope",
        "no_export_validation",
        "collector_not_implemented",
        "manual_review_required",
        "license_limited",
        "stale_mapping",
        "sampled",
    ]
    if status == ControlStatus.PASS:
        if has_demo_marker:
            return StatusCause.ASSESSMENT_LIMITATION
        return StatusCause.VERIFIED
    if status == ControlStatus.NOT_ACCESSIBLE or any(marker in text for marker in ["permission", "rbac", "consent", "authorization", "access denied", "401", "403"]):
        return StatusCause.PERMISSION_GAP
    if status == ControlStatus.NOT_LICENSED or "not licensed" in text or "license_gap" in limitations:
        return StatusCause.NOT_LICENSED
    if "api_unsupported" in limitations or "unsupported_api" in limitations or "unsupported" in text:
        return StatusCause.UNSUPPORTED_API
    if any(marker in limitations for marker in ["usage_absence", "no_usage_context"]) or "no copilot usage" in text:
        return StatusCause.USAGE_ABSENCE
    if "manual_only" in limitations and "not_configured_for_assessment" not in limitations and "partial_scope" not in limitations:
        return StatusCause.MANUAL_EVIDENCE_REQUIRED
    if any(marker in limitations for marker in assessment_markers):
        return StatusCause.ASSESSMENT_LIMITATION
    if status == ControlStatus.FAIL:
        return StatusCause.TENANT_GAP
    if status == ControlStatus.WARN and any(marker in text for marker in tenant_gap_markers):
        return StatusCause.TENANT_GAP
    if status == ControlStatus.WARN:
        return StatusCause.ASSESSMENT_LIMITATION
    if has_demo_marker:
        return StatusCause.DEMO_EVIDENCE
    return StatusCause.ASSESSMENT_LIMITATION


@dataclass
class Finding:
    finding_id: str
    assessment_run_id: str
    finding_type: FindingType
    title: str
    criterion: str
    condition: str
    cause: FindingCause
    impact_or_risk: str
    affected_scope: str
    affected_objects: list[str]
    severity: Severity
    confidence: FindingConfidence
    confidence_reason: str
    evidence_references: list[str]
    related_control_checks: list[str]
    recommendation: str
    owner: str | None = None
    status: str = "open"
    due_date: str | None = None

    def validate(self) -> None:
        if self.cause == FindingCause.UNKNOWN_ROOT_CAUSE and self.finding_type == FindingType.CONTROL_GAP:
            raise ValueError("unknown_root_cause cannot be used for a control_gap finding")


@dataclass
class AssessmentRun:
    assessment_run_id: str
    tenant_id: str
    started_at_utc: str
    initiated_by: str
    tool_version: str
    status: str = "RUNNING"
    completed_at_utc: str | None = None
    scope_summary: str = ""
    limitations: list[str] = field(default_factory=list)


@dataclass
class EvidencePack:
    evidence_pack_id: str
    assessment_run: AssessmentRun
    evidence_items: list[EvidenceItem]
    control_checks: list[ControlCheck]
    findings: list[Finding] = field(default_factory=list)
    generated_at_utc: str | None = None
    format: str = "JSON"
    artifact_path: str | None = None
    content_hash: str | None = None


def to_plain(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_plain(item) for key, item in asdict(value).items()}
    return value
