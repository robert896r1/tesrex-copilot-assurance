"""Evidence-pack assembly pipeline.

Combines live probe summaries, static mappings, and optional manual evidence into validated control checks, findings, and output artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .classifiers import classify_subscribed_skus_response
from .breadcrumbs import control_breadcrumbs
from .evidence_pack import render_markdown_pack, write_json_pack
from .manual_evidence import load_manual_evidence_bundle, manual_evidence_items
from .mappings import load_dlp_copilot_location_map, load_microsoft_capability_map
from .models import (
    AssessmentRun,
    ControlCheck,
    ControlStatus,
    EvidenceCompleteness,
    EvidenceItem,
    EvidencePack,
    EvidenceType,
    Finding,
    FindingCause,
    FindingConfidence,
    FindingType,
    Severity,
)

TOOL_VERSION = "0.1.0"

PROBE_EVIDENCE_TYPES = {
    "az_account": EvidenceType.RAW_API_RESPONSE,
    "az_cloud": EvidenceType.RAW_API_RESPONSE,
    "graph.organization": EvidenceType.RAW_API_RESPONSE,
    "graph.subscribed_skus": EvidenceType.LICENSE_SNAPSHOT,
    "graph.sensitivity_labels": EvidenceType.RAW_API_RESPONSE,
    "graph.ediscovery_cases": EvidenceType.RAW_API_RESPONSE,
    "graph.token_scopes": EvidenceType.NORMALIZED_OBSERVATION,
    "powershell.exchange_online_management": EvidenceType.NORMALIZED_OBSERVATION,
    "powershell.sharepoint_online": EvidenceType.NORMALIZED_OBSERVATION,
}

READINESS_CONTROLS = (
    "LIC-001",
    "LIC-002.copilot_family",
    "LIC-002.work_graph_chat",
    "AUD-001",
    "AUD-002",
    "AUD-003",
    "LABEL-001",
    "DLP-001",
    "DLP-002",
    "SAM-001",
    "EDISC-001",
    "EDISC-002",
    "PACK-001",
    "PACK-002",
)


def latest_live_probe_summary(base_dir: str | Path = "artifacts/live_probe") -> Path:
    root = Path(base_dir)
    candidates = sorted(root.glob("*/summary.json"))
    if not candidates:
        raise FileNotFoundError(f"No live probe summary found under {root}")
    return candidates[-1]


def build_evidence_pack_from_live_probe(
    summary_path: str | Path,
    *,
    output_dir: str | Path = "artifacts/evidence_packs",
    manual_evidence_paths: list[str | Path] | None = None,
    generated_at_utc: str | None = None,
) -> tuple[Path, Path, EvidencePack]:
    summary_file = Path(summary_path)
    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    assessment_run_id = f"run-{summary.get('generated_at_utc', datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))}"
    tenant_id = str(summary.get("tenant_id") or "unknown-tenant")
    initiated_by = str(summary.get("user") or "unknown-assessor")

    pack_timestamp = generated_at_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    run = AssessmentRun(
        assessment_run_id=assessment_run_id,
        tenant_id=tenant_id,
        started_at_utc=str(summary.get("generated_at_utc") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
        initiated_by=initiated_by,
        tool_version=TOOL_VERSION,
        status="COMPLETED",
        completed_at_utc=pack_timestamp,
        scope_summary="Starter-kit capability/configuration evidence pack from read-only probes and optional manual evidence.",
        limitations=["first_slice", "configuration_capability_focus"],
    )

    evidence = _evidence_from_probe_summary(summary, assessment_run_id, tenant_id, initiated_by)
    for manual_path in manual_evidence_paths or []:
        bundle = load_manual_evidence_bundle(manual_path)
        evidence.extend(manual_evidence_items(bundle, base_dir=Path(manual_path).parent))
    if _has_demo_evidence(evidence) and "demo_evidence_present" not in run.limitations:
        run.limitations.append("demo_evidence_present")

    evidence_by_probe = {item.source_object_identifiers.get("probe_id"): item for item in evidence}
    probe_results = {result["probe_id"]: result for result in summary.get("probe_results", []) if isinstance(result, dict)}
    checks = _control_checks_from_probes(assessment_run_id, probe_results, evidence_by_probe, evidence, summary_file)
    _link_manual_evidence_to_checks(checks, evidence)
    findings = _findings_from_checks(assessment_run_id, tenant_id, checks)
    findings.extend(
        _overprivileged_identity_findings(
            assessment_run_id,
            tenant_id,
            evidence_by_probe.get("graph.token_scopes"),
            bounded_validation_approved=_bounded_validation_approved(summary),
        )
    )

    pack = EvidencePack(
        evidence_pack_id=f"pack-{assessment_run_id}",
        assessment_run=run,
        evidence_items=evidence,
        control_checks=checks,
        findings=findings,
        generated_at_utc=pack_timestamp,
        format="JSON+Markdown",
    )

    out_root = Path(output_dir) / assessment_run_id
    json_path = out_root / "evidence_pack.json"
    markdown_path = out_root / "evidence_pack.md"
    digest = write_json_pack(pack, json_path)
    pack.content_hash = digest
    markdown_path.write_text(render_markdown_pack(pack), encoding="utf-8")
    return json_path, markdown_path, pack


def _evidence_from_probe_summary(summary: dict[str, Any], assessment_run_id: str, tenant_id: str, initiated_by: str) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    collected_at = str(summary.get("generated_at_utc") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    for result in summary.get("probe_results", []):
        if not isinstance(result, dict):
            continue
        probe_id = str(result.get("probe_id") or "unknown_probe")
        limitations = list(result.get("limitations") or [])
        raw_path = result.get("raw_artifact_path")
        content_hash = result.get("content_hash")
        if raw_path and not content_hash and Path(raw_path).exists():
            import hashlib

            content_hash = hashlib.sha256(Path(raw_path).read_bytes()).hexdigest()
        if not content_hash:
            limitations = sorted(set(limitations + ["raw_retention_unavailable"]))
        evidence_type = EvidenceType.PERMISSION_DENIAL if result.get("status") == "NOT_ACCESSIBLE" else PROBE_EVIDENCE_TYPES.get(probe_id, EvidenceType.NORMALIZED_OBSERVATION)
        item = EvidenceItem(
            evidence_id=f"ev-{probe_id.replace('.', '-')}",
            assessment_run_id=assessment_run_id,
            evidence_type=evidence_type,
            source_system=_source_system_for_probe(probe_id),
            source_endpoint_or_ui_path=str(result.get("source_ref") or probe_id),
            collection_method="live read-only probe",
            collected_at_utc=collected_at,
            tenant_id=tenant_id,
            collector_identity=initiated_by,
            permission_context="assessment identity / local tool context",
            source_object_identifiers={"probe_id": probe_id, "control_ids": result.get("control_ids", [])},
            raw_artifact_path=str(raw_path) if raw_path else None,
            content_hash=str(content_hash) if content_hash else None,
            normalized_facts={
                "probe_status": result.get("status"),
                "summary": result.get("summary", {}),
                "status_reason": result.get("status_reason", ""),
            },
            limitations=limitations,
        )
        item.validate()
        items.append(item)
    return items


def _control_checks_from_probes(
    assessment_run_id: str,
    probe_results: dict[str, dict[str, Any]],
    evidence_by_probe: dict[object, EvidenceItem],
    evidence_items: list[EvidenceItem],
    summary_file: Path,
) -> list[ControlCheck]:
    cap_map = load_microsoft_capability_map()
    dlp_map = load_dlp_copilot_location_map()
    assessment_date = _assessment_date_from_run_id(assessment_run_id)
    checks: list[ControlCheck] = []

    subscribed = probe_results.get("graph.subscribed_skus")
    subscribed_evidence = evidence_by_probe.get("graph.subscribed_skus")
    checks.append(_lic001_check(assessment_run_id, subscribed, subscribed_evidence))

    sku_payload = _load_probe_json(subscribed_evidence)
    if subscribed and subscribed.get("status") == "OK" and sku_payload is not None:
        for key, suffix in [
            ("LIC-002.microsoft_365_copilot_service_plan_family_present", "copilot_family"),
            ("LIC-002.microsoft_365_copilot_work_graph_chat_present", "work_graph_chat"),
        ]:
            check = classify_subscribed_skus_response(
                sku_payload,
                cap_map,
                key,
                assessment_date=assessment_date,
                assessment_run_id=assessment_run_id,
                evidence_items_used=[subscribed_evidence.evidence_id] if subscribed_evidence else [],
            )
            check.control_check_id = f"LIC-002.{suffix}"
            checks.append(check)
    else:
        checks.append(_basic_check(assessment_run_id, "LIC-002.copilot_family", "LIC", ControlStatus.UNKNOWN, "Copilot entitlement cannot be classified because subscribed SKU evidence is unavailable or unreadable.", EvidenceCompleteness.NONE, ["license_limited"], [subscribed_evidence.evidence_id] if subscribed_evidence else []))
        checks.append(_basic_check(assessment_run_id, "LIC-002.work_graph_chat", "LIC", ControlStatus.UNKNOWN, "Work Graph chat entitlement cannot be classified because subscribed SKU evidence is unavailable or unreadable.", EvidenceCompleteness.NONE, ["license_limited"], [subscribed_evidence.evidence_id] if subscribed_evidence else []))

    checks.append(_audit_access_check(assessment_run_id, probe_results.get("graph.token_scopes"), evidence_by_probe.get("graph.token_scopes")))
    checks.append(_basic_check(assessment_run_id, "AUD-002", "AUD", ControlStatus.UNKNOWN, "CopilotInteraction audit record observability requires an explicitly approved audit query and independent usage context; neither is part of the default read-only probe.", EvidenceCompleteness.NONE, ["manual_only", "not_configured_for_assessment"], []))
    checks.append(_basic_check(assessment_run_id, "AUD-003", "AUD", ControlStatus.UNKNOWN, "Audit retention capability is not proven by token-scope inspection alone; provide Purview audit configuration evidence or approved historical query evidence.", EvidenceCompleteness.NONE, ["manual_only"], []))
    checks.append(_label_check(assessment_run_id, probe_results.get("graph.sensitivity_labels"), evidence_by_probe.get("graph.sensitivity_labels")))
    checks.append(_dlp_placeholder_check(assessment_run_id, "DLP-001", probe_results.get("powershell.exchange_online_management"), evidence_by_probe.get("powershell.exchange_online_management"), dlp_map.version(_parse_date(assessment_date))))
    checks.append(_dlp_placeholder_check(assessment_run_id, "DLP-002", probe_results.get("powershell.exchange_online_management"), evidence_by_probe.get("powershell.exchange_online_management"), dlp_map.version(_parse_date(assessment_date))))
    checks.append(_sam_check(assessment_run_id, probe_results.get("powershell.sharepoint_online"), evidence_by_probe.get("powershell.sharepoint_online"), cap_map.version(_parse_date(assessment_date))))
    checks.append(_basic_check(assessment_run_id, "EDISC-001", "EDISC", ControlStatus.UNKNOWN, "Explicit Copilot/AI retention stance requires retention policy evidence or customer-provided manual artifact; no retention policy read was run in the default probe.", EvidenceCompleteness.NONE, ["manual_only"], []))
    checks.append(_ediscovery_check(assessment_run_id, probe_results.get("graph.ediscovery_cases"), evidence_by_probe.get("graph.ediscovery_cases")))
    checks.append(_pack001_check(assessment_run_id, checks))
    checks.append(_pack002_check(assessment_run_id, evidence_items, summary_file))
    return checks


def _lic001_check(assessment_run_id: str, result: dict[str, Any] | None, evidence: EvidenceItem | None) -> ControlCheck:
    if not result:
        return _basic_check(assessment_run_id, "LIC-001", "LIC", ControlStatus.UNKNOWN, "Subscribed SKU probe did not run or was not present in the live summary.", EvidenceCompleteness.NONE, ["probe_missing"], [])
    status = result.get("status")
    evidence_ids = [evidence.evidence_id] if evidence else []
    if status == "OK":
        return _basic_check(assessment_run_id, "LIC-001", "LIC", ControlStatus.PASS, "Microsoft Graph subscribedSkUs inventory was read successfully.", EvidenceCompleteness.FULL, [], evidence_ids)
    if status == "NOT_ACCESSIBLE":
        return _basic_check(assessment_run_id, "LIC-001", "LIC", ControlStatus.NOT_ACCESSIBLE, "Microsoft Graph subscribedSkUs inventory could not be read due to access/permission limits.", EvidenceCompleteness.NONE, list(result.get("limitations") or ["permission_gap"]), evidence_ids)
    return _basic_check(assessment_run_id, "LIC-001", "LIC", ControlStatus.UNKNOWN, "Microsoft Graph subscribedSkUs inventory probe did not return conclusive evidence.", EvidenceCompleteness.NONE, list(result.get("limitations") or ["probe_failed"]), evidence_ids)


def _audit_access_check(assessment_run_id: str, result: dict[str, Any] | None, evidence: EvidenceItem | None) -> ControlCheck:
    evidence_ids = [evidence.evidence_id] if evidence else []
    if not result:
        return _basic_check(assessment_run_id, "AUD-001", "AUD", ControlStatus.UNKNOWN, "Audit token-scope probe was not present.", EvidenceCompleteness.NONE, ["probe_missing"], evidence_ids)
    if result.get("status") == "OK":
        return _basic_check(assessment_run_id, "AUD-001", "AUD", ControlStatus.WARN, "Audit query scope is present in the token, but no audit query was created in the default read-only probe; full audit search access is not proven.", EvidenceCompleteness.PARTIAL, ["not_configured_for_assessment"], evidence_ids)
    if result.get("status") == "NOT_ACCESSIBLE":
        return _basic_check(assessment_run_id, "AUD-001", "AUD", ControlStatus.NOT_ACCESSIBLE, "Audit query role/scope was not present or token introspection was blocked.", EvidenceCompleteness.NONE, list(result.get("limitations") or ["permission_gap"]), evidence_ids)
    return _basic_check(assessment_run_id, "AUD-001", "AUD", ControlStatus.UNKNOWN, "Audit access could not be classified from token-scope evidence.", EvidenceCompleteness.NONE, list(result.get("limitations") or ["probe_failed"]), evidence_ids)


def _label_check(assessment_run_id: str, result: dict[str, Any] | None, evidence: EvidenceItem | None) -> ControlCheck:
    evidence_ids = [evidence.evidence_id] if evidence else []
    if not result:
        return _basic_check(assessment_run_id, "LABEL-001", "LABEL", ControlStatus.UNKNOWN, "Sensitivity-label probe was not present.", EvidenceCompleteness.NONE, ["probe_missing"], evidence_ids)
    if result.get("status") == "NOT_ACCESSIBLE":
        return _basic_check(assessment_run_id, "LABEL-001", "LABEL", ControlStatus.NOT_ACCESSIBLE, "Sensitivity-label taxonomy could not be read due to access/permission limits.", EvidenceCompleteness.NONE, list(result.get("limitations") or ["permission_gap"]), evidence_ids)
    if result.get("status") == "OK":
        count = int((result.get("summary") or {}).get("count_returned") or 0)
        if count > 0:
            return _basic_check(assessment_run_id, "LABEL-001", "LABEL", ControlStatus.PASS, "Sensitivity-label taxonomy endpoint returned at least one label in the permission probe.", EvidenceCompleteness.PARTIAL, ["partial_scope"], evidence_ids)
        return _basic_check(assessment_run_id, "LABEL-001", "LABEL", ControlStatus.WARN, "Sensitivity-label endpoint is reachable but the $top=1 probe returned zero labels; taxonomy coverage is not proven.", EvidenceCompleteness.PARTIAL, ["partial_scope"], evidence_ids)
    return _basic_check(assessment_run_id, "LABEL-001", "LABEL", ControlStatus.UNKNOWN, "Sensitivity-label taxonomy probe did not return conclusive evidence.", EvidenceCompleteness.NONE, list(result.get("limitations") or ["probe_failed"]), evidence_ids)


def _dlp_placeholder_check(assessment_run_id: str, control_id: str, result: dict[str, Any] | None, evidence: EvidenceItem | None, mapping_version) -> ControlCheck:
    evidence_ids = [evidence.evidence_id] if evidence else []
    if result and result.get("status") == "OK":
        check = _basic_check(assessment_run_id, control_id, "DLP", ControlStatus.UNKNOWN, "ExchangeOnlineManagement module is locally available, but tenant DLP policy/rule inventory was not read in this default run. Provide Purview export or run an approved read-only DLP inventory collector.", EvidenceCompleteness.NONE, ["manual_only", "not_configured_for_assessment"], evidence_ids)
    elif result and result.get("status") == "NOT_ACCESSIBLE":
        check = _basic_check(assessment_run_id, control_id, "DLP", ControlStatus.NOT_ACCESSIBLE, "DLP inventory prerequisite probe was not accessible.", EvidenceCompleteness.NONE, list(result.get("limitations") or ["permission_gap"]), evidence_ids)
    else:
        check = _basic_check(assessment_run_id, control_id, "DLP", ControlStatus.UNKNOWN, "DLP inventory cannot be assessed from current probe evidence.", EvidenceCompleteness.NONE, ["manual_only"], evidence_ids)
    check.mapping_versions_used = [mapping_version]
    check.validate()
    return check


def _sam_check(assessment_run_id: str, result: dict[str, Any] | None, evidence: EvidenceItem | None, mapping_version) -> ControlCheck:
    evidence_ids = [evidence.evidence_id] if evidence else []
    if result and result.get("status") == "OK":
        check = _basic_check(assessment_run_id, "SAM-001", "SAM", ControlStatus.WARN, "SharePoint Online PowerShell module is locally available, but SAM/DAG tenant read capability and report freshness were not validated.", EvidenceCompleteness.PARTIAL, ["manual_only", "partial_scope"], evidence_ids)
    else:
        check = _basic_check(assessment_run_id, "SAM-001", "SAM", ControlStatus.UNKNOWN, "SAM/DAG capability cannot be assessed from current evidence.", EvidenceCompleteness.NONE, ["manual_only"], evidence_ids)
    check.mapping_versions_used = [mapping_version]
    check.validate()
    return check


def _ediscovery_check(assessment_run_id: str, result: dict[str, Any] | None, evidence: EvidenceItem | None) -> ControlCheck:
    evidence_ids = [evidence.evidence_id] if evidence else []
    if not result:
        return _basic_check(assessment_run_id, "EDISC-002", "EDISC", ControlStatus.UNKNOWN, "eDiscovery case-list probe was not present.", EvidenceCompleteness.NONE, ["probe_missing"], evidence_ids)
    if result.get("status") == "OK":
        return _basic_check(assessment_run_id, "EDISC-002", "EDISC", ControlStatus.WARN, "eDiscovery case endpoint is visible, but no positive/export-validating readiness evidence is present in the default run.", EvidenceCompleteness.PARTIAL, ["partial_scope", "no_export_validation"], evidence_ids)
    if result.get("status") == "NOT_ACCESSIBLE":
        return _basic_check(assessment_run_id, "EDISC-002", "EDISC", ControlStatus.NOT_ACCESSIBLE, "eDiscovery case endpoint is not accessible to the assessment identity.", EvidenceCompleteness.NONE, list(result.get("limitations") or ["permission_gap"]), evidence_ids)
    return _basic_check(assessment_run_id, "EDISC-002", "EDISC", ControlStatus.UNKNOWN, "eDiscovery readiness cannot be classified from current probe evidence.", EvidenceCompleteness.NONE, list(result.get("limitations") or ["probe_failed"]), evidence_ids)


def _pack001_check(assessment_run_id: str, checks_so_far: list[ControlCheck]) -> ControlCheck:
    present = {check.control_check_id for check in checks_so_far}
    missing = [control for control in READINESS_CONTROLS if control not in present and not control.startswith("PACK-")]
    status = ControlStatus.FAIL if missing else ControlStatus.PASS
    reason = "All starter-kit controls are represented before pack generation." if not missing else f"Starter-kit controls missing from pack: {missing}"
    return _basic_check(assessment_run_id, "PACK-001", "PACK", status, reason, EvidenceCompleteness.FULL if not missing else EvidenceCompleteness.PARTIAL, [], [])


def _pack002_check(assessment_run_id: str, evidence_items: list[EvidenceItem], summary_file: Path) -> ControlCheck:
    issues: dict[str, list[str]] = {
        "raw_retention_unavailable": [],
        "artifact_missing": [],
        "artifact_hash_missing": [],
        "artifact_hash_mismatch": [],
    }
    verified = 0
    for item in evidence_items:
        if not item.raw_artifact_path:
            issues["raw_retention_unavailable"].append(item.evidence_id)
            continue
        artifact = Path(item.raw_artifact_path)
        if not artifact.is_file():
            issues["artifact_missing"].append(item.evidence_id)
            continue
        if not item.content_hash:
            issues["artifact_hash_missing"].append(item.evidence_id)
            continue
        actual_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual_hash != item.content_hash:
            issues["artifact_hash_mismatch"].append(item.evidence_id)
            continue
        verified += 1

    limitations = [name for name, evidence_ids in issues.items() if evidence_ids]
    issue_count = sum(len(evidence_ids) for evidence_ids in issues.values())
    if issue_count:
        reason = (
            f"Verified {verified} evidence artifacts, but {issue_count} item(s) were missing, not retained, "
            "or did not match the recorded SHA-256 hash."
        )
    else:
        reason = f"Verified the existence and SHA-256 hash of all {verified} retained evidence artifacts."
    return _basic_check(
        assessment_run_id,
        "PACK-002",
        "PACK",
        ControlStatus.PASS if not limitations else ControlStatus.WARN,
        reason,
        EvidenceCompleteness.FULL if not limitations else EvidenceCompleteness.PARTIAL,
        limitations,
        [item.evidence_id for item in evidence_items],
        observed_state=f"source_summary={summary_file}",
    )


def _basic_check(
    assessment_run_id: str,
    control_id: str,
    family: str,
    status: ControlStatus,
    reason: str,
    completeness: EvidenceCompleteness,
    limitations: list[str],
    evidence_items: list[str],
    *,
    observed_state: str = "See cited evidence and status reason.",
) -> ControlCheck:
    check = ControlCheck(
        control_check_id=control_id,
        assessment_run_id=assessment_run_id,
        control_family=family,
        control_objective=f"Assess {control_id} for starter-kit Copilot governance evidence pack.",
        expected_state="Control evidence is present and sufficient for the assessed scope.",
        assessed_scope="tenant / starter-kit first-slice scope",
        procedure="Generated from live read-only probe summary and optional manual evidence.",
        required_evidence_types=[EvidenceType.RAW_API_RESPONSE, EvidenceType.NORMALIZED_OBSERVATION, EvidenceType.MANUAL_ARTIFACT],
        evidence_items_used=evidence_items,
        observed_state=observed_state,
        status=status,
        status_reason=reason,
        evidence_completeness=completeness,
        limitations=limitations,
        follow_up_required=_follow_up_for(status, control_id, limitations),
    )
    check.validate()
    return check


def _findings_from_checks(assessment_run_id: str, tenant_id: str, checks: list[ControlCheck]) -> list[Finding]:
    findings: list[Finding] = []
    for check in checks:
        if check.status == ControlStatus.PASS:
            continue
        if check.status == ControlStatus.NOT_ACCESSIBLE:
            finding_type = FindingType.PERMISSION_GAP
            cause = FindingCause.PERMISSION_GAP
            severity = Severity.MEDIUM
        elif check.status == ControlStatus.FAIL:
            finding_type = FindingType.CONTROL_GAP
            cause = FindingCause.MISSING_CONTROL
            severity = Severity.HIGH
        elif check.status == ControlStatus.NOT_LICENSED:
            finding_type = FindingType.LICENSE_GAP
            cause = FindingCause.LICENSE_GAP
            severity = Severity.MEDIUM
        elif check.status == ControlStatus.WARN:
            finding_type = FindingType.IMPROVEMENT_OPPORTUNITY
            cause = FindingCause.UNKNOWN_ROOT_CAUSE
            severity = Severity.LOW
        else:
            finding_type = FindingType.EVIDENCE_GAP
            cause = FindingCause.UNKNOWN_ROOT_CAUSE
            severity = Severity.LOW
        breadcrumbs = control_breadcrumbs(check)
        finding = Finding(
            finding_id=f"finding-{check.control_check_id.lower().replace('.', '-')}",
            assessment_run_id=assessment_run_id,
            finding_type=finding_type,
            title=f"{check.control_check_id}: {check.status.value}",
            criterion=check.expected_state,
            condition=breadcrumbs.what_found,
            cause=cause,
            impact_or_risk=breadcrumbs.why_it_matters,
            affected_scope=tenant_id,
            affected_objects=[check.control_check_id],
            severity=severity,
            confidence=FindingConfidence.MEDIUM,
            confidence_reason="Finding generated mechanically from control-check status and limitations; review before customer delivery.",
            evidence_references=list(check.evidence_items_used),
            related_control_checks=[check.control_check_id],
            recommendation=breadcrumbs.next_evidence_step,
        )
        finding.validate()
        findings.append(finding)
    return findings


def _overprivileged_identity_findings(
    assessment_run_id: str,
    tenant_id: str,
    token_evidence: EvidenceItem | None,
    *,
    bounded_validation_approved: bool = False,
) -> list[Finding]:
    if not token_evidence or not token_evidence.raw_artifact_path:
        return []
    try:
        claims = json.loads(Path(token_evidence.raw_artifact_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    actual = set(str(value) for value in (claims.get("roles") or claims.get("scp") or []))
    if not actual:
        return []
    expected = _default_expected_permissions(include_bounded_validation=bounded_validation_approved)
    unexpected = sorted(actual.difference(expected))
    high_risk = sorted(
        role
        for role in actual
        if (role.endswith(".ReadWrite.All") or role in {"Sites.FullControl.All", "Directory.ReadWrite.All"})
        and not (bounded_validation_approved and role in expected)
    )
    if not unexpected and not high_risk:
        return []
    condition_parts = []
    if unexpected:
        condition_parts.append(f"Assessment token contains permissions outside current starter-kit default matrix: {unexpected}")
    if high_risk:
        condition_parts.append(f"Assessment token contains elevated validation/write-capable permissions: {high_risk}")
    finding = Finding(
        finding_id="finding-over-privileged-identity",
        assessment_run_id=assessment_run_id,
        finding_type=FindingType.IMPROVEMENT_OPPORTUNITY,
        title="Assessment identity has broader permissions than the starter-kit default requires",
        criterion="Starter-kit collectors should use least-privilege read-only permissions unless a bounded validation is separately approved.",
        condition="; ".join(condition_parts),
        cause=FindingCause.UNKNOWN_ROOT_CAUSE,
        impact_or_risk="Broader permissions increase deployment risk and should be separated from the default read-only assessment identity before customer use.",
        affected_scope=tenant_id,
        affected_objects=unexpected + high_risk,
        severity=Severity.MEDIUM if high_risk else Severity.LOW,
        confidence=FindingConfidence.HIGH,
        confidence_reason="Derived from redacted Graph token role/scope artifact and collector permission matrix.",
        evidence_references=[token_evidence.evidence_id],
        related_control_checks=["PACK-002"],
        recommendation="Create a least-privilege assessment identity for default runs and reserve elevated permissions for explicitly approved bounded validation.",
    )
    finding.validate()
    return [finding]


def _default_expected_permissions(*, include_bounded_validation: bool = False) -> set[str]:
    path = Path("config/collector_permission_matrix.json")
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    expected: set[str] = set()
    for collector in (data.get("collectors") or {}).values():
        if not isinstance(collector, dict):
            continue
        if collector.get("default_collector") is False and not include_bounded_validation:
            continue
        for key in ["minimum_permissions", "fallback_permissions"]:
            expected.update(str(value) for value in collector.get(key, []) if isinstance(value, str) and "." in value)
    return expected


def _link_manual_evidence_to_checks(checks: list[ControlCheck], evidence_items: list[EvidenceItem]) -> None:
    checks_by_id = {check.control_check_id: check for check in checks}
    checks_by_prefix = {check.control_check_id.split(".", 1)[0]: check for check in checks}
    for evidence in evidence_items:
        if evidence.collection_method != "manual customer/assessor evidence":
            continue
        control_ids = evidence.source_object_identifiers.get("control_ids") or []
        for control_id in control_ids:
            check = checks_by_id.get(control_id) or checks_by_prefix.get(str(control_id).split(".", 1)[0])
            if check and evidence.evidence_id not in check.evidence_items_used:
                check.evidence_items_used.append(evidence.evidence_id)
                if "manual_evidence_linked" not in check.limitations:
                    check.limitations.append("manual_evidence_linked")
                if "manual_only" not in check.limitations:
                    check.limitations.append("manual_only")
                if _evidence_is_demo(evidence) and "demo_evidence" not in check.limitations:
                    check.limitations.append("demo_evidence")
                if check.evidence_completeness == EvidenceCompleteness.NONE:
                    check.evidence_completeness = EvidenceCompleteness.PARTIAL
                elif _evidence_is_demo(evidence) and check.evidence_completeness == EvidenceCompleteness.FULL:
                    check.evidence_completeness = EvidenceCompleteness.PARTIAL
                    if "demo_evidence_in_full_check" not in check.limitations:
                        check.limitations.append("demo_evidence_in_full_check")
                check.status_cause = None
                check.validate()


def _has_demo_evidence(evidence_items: list[EvidenceItem]) -> bool:
    return any(_evidence_is_demo(item) for item in evidence_items)


def _evidence_is_demo(item: EvidenceItem) -> bool:
    if item.normalized_facts.get("demo_mode") is True or item.normalized_facts.get("is_synthetic") is True:
        return True
    if any(marker in item.limitations for marker in ["demo_only", "synthetic_fixture", "tenant_demo_artifact"]):
        return True
    return str(item.source_system).startswith("TCA synthetic demo fixture")


def _bounded_validation_approved(summary: dict[str, Any]) -> bool:
    boundary = summary.get("boundary")
    if not isinstance(boundary, dict):
        return False
    if boundary.get("bounded_validation_approved") is True:
        return True
    methods = boundary.get("mutation_methods_used") or []
    return any(str(method).lower().startswith("bounded_validation") for method in methods)


def _source_system_for_probe(probe_id: str) -> str:
    if probe_id.startswith("graph."):
        return "Microsoft Graph"
    if probe_id.startswith("powershell."):
        return "Local PowerShell module check"
    if probe_id.startswith("az_"):
        return "Azure CLI"
    return "Tesrex collector"


def _load_probe_json(evidence: EvidenceItem | None) -> dict[str, Any] | None:
    if not evidence or not evidence.raw_artifact_path:
        return None
    try:
        return json.loads(Path(evidence.raw_artifact_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _follow_up_for(status: ControlStatus, control_id: str, limitations: list[str]) -> list[str]:
    if status == ControlStatus.PASS:
        return []
    if status == ControlStatus.NOT_ACCESSIBLE:
        return [f"Grant least-privilege access needed for {control_id} or provide customer evidence."]
    if status == ControlStatus.NOT_LICENSED:
        return [f"Confirm whether {control_id} is in customer baseline or update licensing/evidence."]
    if "manual_only" in limitations:
        return [f"Provide manual/customer evidence for {control_id} or approve the relevant read-only collector."]
    return [f"Review limitations for {control_id} and rerun after evidence gap is resolved."]


def _assessment_date_from_run_id(run_id: str) -> str:
    for token in run_id.split("-"):
        if len(token) >= 8 and token[:8].isdigit():
            return f"{token[:4]}-{token[4:6]}-{token[6:8]}"
    return datetime.now(timezone.utc).date().isoformat()


def _parse_date(value: str):
    from .mappings import parse_assessment_date

    return parse_assessment_date(value)
