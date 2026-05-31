"""Tenant-free demo report orchestration.

Creates synthetic probe evidence, demo manual evidence, a JSON/Markdown evidence pack, and the static HTML UI without calling Microsoft services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .demo_dataset import create_demo_dataset, utc_timestamp
from .pack_builder import build_evidence_pack_from_live_probe
from .ui_renderer import render_evidence_pack_html

DEMO_TENANT_ID = "TCA-DEMO-SYNTHETIC"
DEMO_OPERATOR = "TCA demo mode"


@dataclass(frozen=True)
class DemoReportPaths:
    timestamp: str
    demo_dataset_dir: Path
    manual_evidence: Path
    live_probe_dir: Path
    summary: Path
    evidence_pack_json: Path
    evidence_pack_markdown: Path
    evidence_pack_ui: Path


def create_demo_report(
    *,
    output_root: str | Path = "artifacts",
    timestamp: str | None = None,
    tenant_id: str = DEMO_TENANT_ID,
    provided_by: str = DEMO_OPERATOR,
) -> DemoReportPaths:
    """Create a tenant-free synthetic TCA demo report.

    This path performs no Microsoft API calls and creates no tenant artifacts. It is
    strictly for local report review and launch/demo onboarding.
    """

    stamp = timestamp or utc_timestamp()
    root = Path(output_root)
    demo_dataset_dir = create_demo_dataset(
        output_root=root / "demo_dataset",
        timestamp=stamp,
        tenant_id=tenant_id,
        provided_by=provided_by,
    )
    live_probe_dir = root / "live_probe" / stamp
    raw_dir = live_probe_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    summary = _demo_summary(stamp, tenant_id, provided_by, raw_dir)
    summary_path = live_probe_dir / "summary.json"
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    summary_path.write_text(rendered + "\n", encoding="utf-8")
    (live_probe_dir / "summary.sha256").write_text(hashlib.sha256(rendered.encode("utf-8")).hexdigest() + "\n", encoding="utf-8")

    manual_evidence = demo_dataset_dir / "manual_evidence_bundle.json"
    json_path, md_path, _pack = build_evidence_pack_from_live_probe(
        summary_path,
        output_dir=root / "evidence_packs",
        manual_evidence_paths=[manual_evidence],
    )
    ui_path = Path(render_evidence_pack_html(json_path))
    return DemoReportPaths(
        timestamp=stamp,
        demo_dataset_dir=demo_dataset_dir,
        manual_evidence=manual_evidence,
        live_probe_dir=live_probe_dir,
        summary=summary_path,
        evidence_pack_json=json_path,
        evidence_pack_markdown=md_path,
        evidence_pack_ui=ui_path,
    )


def _demo_summary(stamp: str, tenant_id: str, provided_by: str, raw_dir: Path) -> dict[str, Any]:
    generated_at = stamp
    return {
        "generated_at_utc": generated_at,
        "environment_name": "TCA-DEMO-LOCAL",
        "tenant_id": tenant_id,
        "subscription_id": "TCA-DEMO-NONE",
        "user": provided_by,
        "demo_mode": True,
        "is_synthetic": True,
        "boundary": {
            "mutation_methods_used": [],
            "broad_content_scan": False,
            "tenant_policy_changes": False,
            "permission_changes": False,
            "audit_query_created": False,
            "live_microsoft_api_calls": False,
            "demo_only": True,
        },
        "limitations": [
            "demo_only",
            "synthetic_fixture",
            "not_customer_evidence",
            "no_live_microsoft_api_calls",
        ],
        "probe_results": _demo_probe_results(raw_dir),
    }


def _demo_probe_results(raw_dir: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    def add(
        probe_id: str,
        status: str,
        control_ids: list[str],
        source_ref: str,
        payload: dict[str, Any],
        summary: dict[str, Any],
        status_reason: str,
        limitations: list[str] | None = None,
    ) -> None:
        path, digest = _write_raw(raw_dir, probe_id.replace(".", "_"), payload)
        results.append(
            {
                "probe_id": probe_id,
                "status": status,
                "control_ids": control_ids,
                "source_ref": source_ref,
                "raw_artifact_path": str(path),
                "content_hash": digest,
                "summary": summary,
                "limitations": sorted(set(["demo_only", "synthetic_fixture", "not_customer_evidence"] + (limitations or []))),
                "status_reason": status_reason,
            }
        )

    add(
        "az_account",
        "OK",
        ["PACK-002"],
        "TCA local synthetic demo context",
        {"demo_mode": True, "is_synthetic": True, "tenantId": DEMO_TENANT_ID, "user": {"name": DEMO_OPERATOR}},
        {"context": "synthetic local demo"},
        "SYNTHETIC DEMO: no Azure account or tenant context was read.",
    )
    add(
        "az_cloud",
        "OK",
        ["PACK-002"],
        "TCA local synthetic demo context",
        {"demo_mode": True, "is_synthetic": True, "name": "TCA-DEMO-LOCAL"},
        {"context": "synthetic local demo"},
        "SYNTHETIC DEMO: no Azure cloud context was read.",
    )
    add(
        "graph.organization",
        "OK",
        ["PACK-002"],
        "TCA local synthetic demo fixture",
        {"demo_mode": True, "is_synthetic": True, "value": [{"id": DEMO_TENANT_ID, "displayName": "TCA Demo Tenant"}]},
        {"payload_shape": "collection", "count_returned": 1},
        "SYNTHETIC DEMO: representative organization payload only; no Graph tenant call was made.",
    )
    add(
        "graph.subscribed_skus",
        "OK",
        ["LIC-001", "LIC-002"],
        "TCA local synthetic demo fixture",
        {"demo_mode": True, "is_synthetic": True, "value": []},
        {"payload_shape": "collection", "count_returned": 0},
        "SYNTHETIC DEMO: representative subscribedSkus payload only; no Graph tenant call was made.",
    )
    add(
        "graph.sensitivity_labels",
        "OK",
        ["LABEL-001"],
        "TCA local synthetic demo fixture",
        {"demo_mode": True, "is_synthetic": True, "value": []},
        {"payload_shape": "collection", "count_returned": 0},
        "SYNTHETIC DEMO: label endpoint shape is represented, but no real label taxonomy was read.",
    )
    add(
        "graph.token_scopes",
        "OK",
        ["AUD-001"],
        "TCA local synthetic demo fixture",
        {"demo_mode": True, "is_synthetic": True, "roles": ["AuditLogsQuery.Read.All"], "raw_access_token_retained": False},
        {"audit_query_scopes_present": ["AuditLogsQuery.Read.All"], "raw_access_token_retained": False},
        "SYNTHETIC DEMO: representative token-scope evidence only; no token was requested or retained.",
        ["raw_secret_not_retained"],
    )
    add(
        "graph.ediscovery_cases",
        "OK",
        ["EDISC-002"],
        "TCA local synthetic demo fixture",
        {"demo_mode": True, "is_synthetic": True, "value": []},
        {"payload_shape": "collection", "count_returned": 0},
        "SYNTHETIC DEMO: eDiscovery case-list shape is represented, but no Purview or Graph tenant call was made.",
    )
    add(
        "powershell.exchange_online_management",
        "OK",
        ["DLP-001", "DLP-002"],
        "TCA local synthetic demo fixture",
        {"demo_mode": True, "is_synthetic": True, "module": "ExchangeOnlineManagement", "available": True},
        {"module": "ExchangeOnlineManagement", "available": True},
        "SYNTHETIC DEMO: module availability is represented for UI review only; local PowerShell was not probed.",
    )
    add(
        "powershell.sharepoint_online",
        "OK",
        ["SAM-001"],
        "TCA local synthetic demo fixture",
        {"demo_mode": True, "is_synthetic": True, "module": "Microsoft.Online.SharePoint.PowerShell", "available": True},
        {"module": "Microsoft.Online.SharePoint.PowerShell", "available": True},
        "SYNTHETIC DEMO: module availability is represented for UI review only; local PowerShell was not probed.",
    )
    return results


def _write_raw(raw_dir: Path, name: str, payload: dict[str, Any]) -> tuple[Path, str]:
    payload = {**payload, "demo_mode": True, "is_synthetic": True, "not_customer_evidence": True}
    text = json.dumps(payload, indent=2, sort_keys=True)
    path = raw_dir / f"{name}.json"
    path.write_text(text + "\n", encoding="utf-8")
    return path, hashlib.sha256(text.encode("utf-8")).hexdigest()
