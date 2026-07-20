"""Evidence-pack validation and serialization helpers.

This module enforces key proof safeguards before writing JSON/Markdown output, including eDiscovery and mapping-related false-assurance checks."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ControlCheck, ControlStatus, EvidenceItem, EvidencePack, to_plain

MAPPING_REQUIRED_CONTROL_PREFIXES = ("LIC-002", "DLP-001", "DLP-002", "SAM-001")


def validate_evidence_pack(pack: EvidencePack) -> None:
    evidence_by_id = {item.evidence_id: item for item in pack.evidence_items}
    for item in pack.evidence_items:
        item.validate()
    for check in pack.control_checks:
        check.validate()
        missing = [eid for eid in check.evidence_items_used if eid not in evidence_by_id]
        if missing:
            raise ValueError(f"Control check {check.control_check_id} cites missing evidence items: {missing}")
        connectivity_only = [
            eid
            for eid in check.evidence_items_used
            if evidence_by_id[eid].normalized_facts.get("validation_scope") == "api_connectivity_only"
        ]
        mailbox_zero_result = [
            eid
            for eid in check.evidence_items_used
            if evidence_by_id[eid].normalized_facts.get("validation_scope") == "mailbox_location_validation"
            and evidence_by_id[eid].normalized_facts.get("outcome_status") == "zero_result"
        ]
        mailbox_location_no_export = [
            eid
            for eid in check.evidence_items_used
            if evidence_by_id[eid].normalized_facts.get("validation_scope") == "mailbox_location_validation"
            and evidence_by_id[eid].normalized_facts.get("export_performed") is False
        ]
        export_validating = [
            eid
            for eid in check.evidence_items_used
            if evidence_by_id[eid].evidence_type.value == "report_export"
            or evidence_by_id[eid].normalized_facts.get("export_performed") is True
            or evidence_by_id[eid].normalized_facts.get("customer_provided_purview_export") is True
        ]
        if connectivity_only and "zero_content_scope" not in check.limitations:
            raise ValueError(
                f"Control check {check.control_check_id} uses api_connectivity_only evidence "
                f"{connectivity_only} without zero_content_scope limitation"
            )
        if check.control_check_id.startswith("EDISC-002") and connectivity_only and check.status == ControlStatus.PASS:
            raise ValueError(
                f"Control check {check.control_check_id} cannot PASS using only api_connectivity_only evidence {connectivity_only}"
            )
        if mailbox_zero_result:
            if check.status == ControlStatus.PASS:
                raise ValueError(
                    f"Control check {check.control_check_id} cannot PASS using zero-result mailbox evidence {mailbox_zero_result}"
                )
            required_limitations = {"partial_scope", "sampled", "zero_result", "no_positive_hit", "no_export_validation"}
            missing_limitations = sorted(required_limitations.difference(check.limitations))
            if missing_limitations:
                raise ValueError(
                    f"Control check {check.control_check_id} uses zero-result mailbox evidence "
                    f"{mailbox_zero_result} without limitations: {missing_limitations}"
                )
        if check.control_check_id.startswith("EDISC-002") and check.status == ControlStatus.PASS and mailbox_location_no_export and not export_validating:
            raise ValueError(
                f"Control check {check.control_check_id} cannot PASS using mailbox-location evidence "
                f"{mailbox_location_no_export} without export-validating evidence"
            )
        if check.control_check_id.startswith(MAPPING_REQUIRED_CONTROL_PREFIXES) and not check.mapping_versions_used:
            raise ValueError(f"Control check {check.control_check_id} requires mapping_versions_used metadata")
    for finding in pack.findings:
        finding.validate()


def unread_controls_register(checks: list[ControlCheck]) -> list[dict[str, Any]]:
    unread: list[dict[str, Any]] = []
    for check in checks:
        if check.status in {ControlStatus.PASS, ControlStatus.FAIL} and not check.limitations:
            continue
        unread.append(
            {
                "control_check_id": check.control_check_id,
                "status": check.status.value,
                "status_cause": check.status_cause.value if check.status_cause else None,
                "evidence_completeness": check.evidence_completeness.value,
                "status_reason": check.status_reason,
                "limitations": list(check.limitations),
                "follow_up_required": list(check.follow_up_required),
            }
        )
    return unread


def generate_pack_dict(pack: EvidencePack) -> dict[str, Any]:
    validate_evidence_pack(pack)
    data = to_plain(pack)
    data["unread_controls_register"] = unread_controls_register(pack.control_checks)
    data["pack_generated_at_utc"] = pack.generated_at_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if "demo_evidence_present" in (data.get("assessment_run", {}).get("limitations") or []):
        data["sample_notice"] = {
            "product_name": "Tesrex Copilot Assurance",
            "sample_only": True,
            "synthetic_only": True,
            "not_customer_evidence": True,
            "no_live_microsoft_api_calls": True,
        }
    return data


def write_json_pack(pack: EvidencePack, path: str | Path) -> str:
    data = generate_pack_dict(pack)
    rendered = json.dumps(data, indent=2, sort_keys=True)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered + "\n", encoding="utf-8")
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def render_markdown_pack(pack: EvidencePack) -> str:
    data = generate_pack_dict(pack)
    run = data["assessment_run"]
    lines = [
        "# Tesrex Copilot Assurance Evidence Pack",
        "",
    ]
    if data.get("sample_notice"):
        lines.extend(
            [
                "> **SYNTHETIC DEMO ONLY:** No live Microsoft tenant was accessed. This is not customer evidence or audit proof.",
                "",
            ]
        )
    lines.extend([
        f"- Pack ID: `{data['evidence_pack_id']}`",
        f"- Assessment run: `{run['assessment_run_id']}`",
        f"- Tenant: `{run['tenant_id']}`",
        f"- Tool version: `{run['tool_version']}`",
        f"- Scope: {run.get('scope_summary') or '(not stated)'}",
        f"- Run limitations: {', '.join(run.get('limitations') or []) if run.get('limitations') else '(none)'}",
        "",
        "## Control checks",
        "",
    ])
    for check in data["control_checks"]:
        lines.extend(
            [
                f"### {check['control_check_id']} — {check['status']}",
                "",
                f"Reason: {check['status_reason']}",
                f"Evidence completeness: {check['evidence_completeness']}",
                f"Limitations: {', '.join(check['limitations']) if check['limitations'] else '(none)'}",
                "",
            ]
        )
    lines.extend(["## Unread / limited controls register", ""])
    if data["unread_controls_register"]:
        for item in data["unread_controls_register"]:
            lines.append(f"- `{item['control_check_id']}`: {item['status']} — {item['status_reason']}")
    else:
        lines.append("No unread or limited controls recorded.")
    lines.extend(["", "## Findings", ""])
    if data["findings"]:
        for finding in data["findings"]:
            lines.extend(
                [
                    f"### {finding['finding_id']} — {finding['severity']}",
                    "",
                    f"Type: {finding['finding_type']}",
                    f"Condition: {finding['condition']}",
                    f"Evidence: {', '.join(finding['evidence_references']) if finding['evidence_references'] else '(none cited)'}",
                    f"Recommendation: {finding['recommendation']}",
                    "",
                ]
            )
    else:
        lines.append("No findings generated.")
    lines.extend(["", "## Evidence inventory", ""])
    if data["evidence_items"]:
        for evidence in data["evidence_items"]:
            lines.extend(
                [
                    f"- `{evidence['evidence_id']}` — {evidence['evidence_type']} from {evidence['source_system']}; "
                    f"artifact: `{evidence['raw_artifact_path'] or '(not retained)'}`; "
                    f"hash: `{evidence['content_hash'] or '(none)'}`; "
                    f"limitations: {', '.join(evidence['limitations']) if evidence['limitations'] else '(none)'}",
                ]
            )
    else:
        lines.append("No evidence items recorded.")
    lines.append("")
    return "\n".join(lines)


def content_hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
