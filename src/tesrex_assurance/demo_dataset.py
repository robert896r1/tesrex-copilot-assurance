"""Synthetic evidence fixture generation for local demos.

Public demo mode is local-only and never calls Microsoft services. The optional
tenant eDiscovery request/response parameters are for rendering already-approved
internal validation artifacts; this module does not perform tenant API calls."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1.0"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def create_demo_dataset(
    *,
    output_root: str | Path = "artifacts/demo_dataset",
    timestamp: str | None = None,
    tenant_id: str = "unknown-tenant",
    provided_by: str = "TCA Demo Seeder",
    expiry_days: int = 30,
    tenant_ediscovery_request: dict[str, Any] | None = None,
    tenant_ediscovery_response: dict[str, Any] | None = None,
    tenant_ediscovery_error: dict[str, Any] | None = None,
) -> Path:
    """Create a labelled demo evidence bundle without pretending synthetic data is production evidence."""

    stamp = timestamp or utc_timestamp()
    out = Path(output_root) / stamp
    out.mkdir(parents=True, exist_ok=True)
    provided_at = _iso_from_stamp(stamp)
    provided_datetime = datetime.fromisoformat(provided_at.replace("Z", "+00:00"))
    expiry = (provided_datetime + timedelta(days=expiry_days)).date().isoformat()

    _write_json(out / "synthetic_copilot_chat_transcripts.json", _synthetic_chat_transcripts(stamp, tenant_id, expiry))
    _write_json(out / "synthetic_dlp_policy_export.json", _synthetic_dlp_policy(stamp, tenant_id, expiry))
    _write_json(out / "synthetic_sam_oversharing_report.json", _synthetic_sam_report(stamp, tenant_id, expiry))
    _write_json(out / "synthetic_retention_policy_evidence.json", _synthetic_retention_evidence(stamp, tenant_id, expiry))

    edisc_item = _ediscovery_manual_item(out, stamp, tenant_ediscovery_request, tenant_ediscovery_response, tenant_ediscovery_error, expiry)

    items = [
        {
            "evidence_id": "ev-demo-copilot-chat-transcripts",
            "control_ids": ["AUD-002"],
            "evidence_type": "manual_artifact",
            "source_system": "TCA synthetic demo fixture",
            "source_endpoint_or_ui_path": "local synthetic fixture; not Microsoft Purview audit",
            "artifact_path": "synthetic_copilot_chat_transcripts.json",
            "asserted_facts": {
                "demo_mode": True,
                "is_synthetic": True,
                "tenant_artifact_created": False,
                "not_a_purview_audit_record": True,
                "not_a_copilotinteraction_record": True,
                "record_count": 6,
                "purpose": "UI/report depth demonstration only",
            },
            "limitations": ["demo_only", "synthetic_fixture", "not_independently_verified_by_tool"],
            "relevance_rating": "medium",
            "reliability_rating": "low",
        },
        {
            "evidence_id": "ev-demo-dlp-policy-export",
            "control_ids": ["DLP-001", "DLP-002"],
            "evidence_type": "policy_snapshot",
            "source_system": "TCA synthetic demo fixture",
            "source_endpoint_or_ui_path": "local synthetic fixture; representative Purview DLP export shape",
            "artifact_path": "synthetic_dlp_policy_export.json",
            "asserted_facts": {
                "demo_mode": True,
                "is_synthetic": True,
                "policy_count": 2,
                "copilot_related_policy_examples": 2,
                "tenant_policy_changed": False,
            },
            "limitations": ["demo_only", "synthetic_fixture", "not_customer_export"],
            "relevance_rating": "high",
            "reliability_rating": "low",
        },
        {
            "evidence_id": "ev-demo-sam-oversharing-report",
            "control_ids": ["SAM-001"],
            "evidence_type": "report_export",
            "source_system": "TCA synthetic demo fixture",
            "source_endpoint_or_ui_path": "local synthetic fixture; representative SAM/DAG output",
            "artifact_path": "synthetic_sam_oversharing_report.json",
            "asserted_facts": {
                "demo_mode": True,
                "is_synthetic": True,
                "high_risk_site_examples": 4,
                "tenant_sharing_changed": False,
            },
            "limitations": ["demo_only", "synthetic_fixture", "not_customer_export"],
            "relevance_rating": "high",
            "reliability_rating": "low",
        },
        {
            "evidence_id": "ev-demo-retention-policy-evidence",
            "control_ids": ["AUD-003", "EDISC-001"],
            "evidence_type": "policy_snapshot",
            "source_system": "TCA synthetic demo fixture",
            "source_endpoint_or_ui_path": "local synthetic fixture; representative Purview retention evidence",
            "artifact_path": "synthetic_retention_policy_evidence.json",
            "asserted_facts": {
                "demo_mode": True,
                "is_synthetic": True,
                "retention_policy_examples": 2,
                "tenant_policy_changed": False,
            },
            "limitations": ["demo_only", "synthetic_fixture", "not_customer_export"],
            "relevance_rating": "high",
            "reliability_rating": "low",
        },
        edisc_item,
    ]

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "assessment_run_id": f"run-{stamp}",
        "tenant_id": tenant_id,
        "provided_by": provided_by,
        "provided_at_utc": provided_at,
        "items": items,
    }
    _write_json(out / "manual_evidence_bundle.json", bundle)

    manifest = {
        "demo_dataset_id": f"TCA-DEMO-{stamp}",
        "created_at_utc": provided_at,
        "tenant_id": tenant_id,
        "provided_by": provided_by,
        "expiry_date": expiry,
        "is_demo_dataset": True,
        "tenant_mutations": {
            "ediscovery_case_create_attempted": tenant_ediscovery_request is not None,
            "ediscovery_case_created": tenant_ediscovery_response is not None,
            "ediscovery_case_cleanup": "manual deletion required before or at expiry target" if tenant_ediscovery_response is not None else "not applicable",
            "teams_messages_created": False,
            "reason_teams_messages_not_created": "Current app-only token cannot send Teams messages; Microsoft Graph send-message APIs require delegated ChannelMessage.Send/ChatMessage.Send except migration-only application permission.",
            "synthetic_audit_records_created": False,
        },
        "artifact_files": sorted(path.name for path in out.iterdir() if path.is_file()),
    }
    _write_json(out / "manifest.json", manifest)
    (out / "README.md").write_text(_readme(stamp, expiry, tenant_ediscovery_response is not None), encoding="utf-8")
    return out


def _ediscovery_manual_item(
    out: Path,
    stamp: str,
    request: dict[str, Any] | None,
    response: dict[str, Any] | None,
    error: dict[str, Any] | None,
    expiry: str,
) -> dict[str, Any]:
    if request is not None:
        _write_json(out / "tenant_ediscovery_case_request.json", request)
    if response is not None:
        _write_json(out / "tenant_ediscovery_case_response.json", response)
        return {
            "evidence_id": "ev-demo-tenant-ediscovery-case",
            "control_ids": ["EDISC-002"],
            "evidence_type": "raw_api_response",
            "source_system": "Microsoft Graph eDiscovery",
            "source_endpoint_or_ui_path": "POST /v1.0/security/cases/ediscoveryCases",
            "artifact_path": "tenant_ediscovery_case_response.json",
            "asserted_facts": {
                "demo_mode": True,
                "is_synthetic": False,
                "tenant_artifact_created": True,
                "artifact_type": "ediscovery_case",
                "display_name": response.get("displayName"),
                "case_id": response.get("id"),
                "expiry_date": expiry,
                "does_not_prove_export_readiness": True,
            },
            "limitations": ["demo_only", "tenant_demo_artifact", "no_export_validation", "no_content_search"],
            "relevance_rating": "high",
            "reliability_rating": "high",
        }
    if error is not None:
        _write_json(out / "tenant_ediscovery_case_error.json", error)
        return {
            "evidence_id": "ev-demo-tenant-ediscovery-case-error",
            "control_ids": ["EDISC-002"],
            "evidence_type": "permission_denial",
            "source_system": "Microsoft Graph eDiscovery",
            "source_endpoint_or_ui_path": "POST /v1.0/security/cases/ediscoveryCases",
            "artifact_path": "tenant_ediscovery_case_error.json",
            "asserted_facts": {
                "demo_mode": True,
                "is_synthetic": False,
                "tenant_artifact_created": False,
                "operation_attempted": True,
            },
            "limitations": ["demo_only", "tenant_mutation_failed", "permission_or_api_failure"],
            "relevance_rating": "medium",
            "reliability_rating": "medium",
        }
    _write_json(out / "synthetic_ediscovery_readiness.json", _synthetic_ediscovery_readiness(stamp, expiry))
    return {
        "evidence_id": "ev-demo-ediscovery-readiness-fixture",
        "control_ids": ["EDISC-002"],
        "evidence_type": "report_export",
        "source_system": "TCA synthetic demo fixture",
        "source_endpoint_or_ui_path": "local synthetic fixture; no tenant mutation",
        "artifact_path": "synthetic_ediscovery_readiness.json",
        "asserted_facts": {
            "demo_mode": True,
            "is_synthetic": True,
            "tenant_artifact_created": False,
            "does_not_prove_export_readiness": True,
        },
        "limitations": ["demo_only", "synthetic_fixture", "no_export_validation"],
        "relevance_rating": "medium",
        "reliability_rating": "low",
    }


def _synthetic_chat_transcripts(stamp: str, tenant_id: str, expiry: str) -> dict[str, Any]:
    prompts = [
        "Summarise the TCA-DEMO board pack and list the governance risks.",
        "Which demo SharePoint locations appear overshared?",
        "Does the demo policy pack contain confidential customer material?",
        "Prepare an auditor-facing explanation of missing DLP evidence.",
        "Identify whether public web grounding was used in this demo interaction.",
        "List remediation actions for unverified Copilot governance controls.",
    ]
    return {
        "artifact_type": "synthetic_copilot_chat_transcripts",
        "created_at_utc": _iso_from_stamp(stamp),
        "tenant_id": tenant_id,
        "expiry_date": expiry,
        "demo_mode": True,
        "is_synthetic": True,
        "not_posted_to_teams": True,
        "not_purview_audit": True,
        "not_copilotinteraction": True,
        "records": [
            {
                "conversation_id": f"TCA-DEMO-CHAT-{idx:02d}",
                "user_prompt": prompt,
                "assistant_response_summary": "Synthetic response used only to exercise report rendering and evidence traceability.",
                "classification": "demo_non_production",
            }
            for idx, prompt in enumerate(prompts, start=1)
        ],
    }


def _synthetic_dlp_policy(stamp: str, tenant_id: str, expiry: str) -> dict[str, Any]:
    return {
        "artifact_type": "synthetic_dlp_policy_export",
        "created_at_utc": _iso_from_stamp(stamp),
        "tenant_id": tenant_id,
        "expiry_date": expiry,
        "demo_mode": True,
        "is_synthetic": True,
        "policies": [
            {
                "name": "TCA-DEMO-DLP-Copilot-Sensitive-Data-Review",
                "mode": "audit_only_demo",
                "locations": ["Microsoft 365 Copilot", "Teams", "SharePoint"],
                "rules": ["Detect demo confidential marker", "Record user notification state"],
            },
            {
                "name": "TCA-DEMO-DLP-External-Sharing-Review",
                "mode": "audit_only_demo",
                "locations": ["SharePoint", "OneDrive"],
                "rules": ["Detect anyone links", "Flag unlabeled demo material"],
            },
        ],
    }


def _synthetic_sam_report(stamp: str, tenant_id: str, expiry: str) -> dict[str, Any]:
    return {
        "artifact_type": "synthetic_sam_oversharing_report",
        "created_at_utc": _iso_from_stamp(stamp),
        "tenant_id": tenant_id,
        "expiry_date": expiry,
        "demo_mode": True,
        "is_synthetic": True,
        "sites": [
            {"site": "TCA-DEMO Finance", "risk": "anyone_links", "recommended_action": "Expire links and review owners"},
            {"site": "TCA-DEMO HR", "risk": "external_users", "recommended_action": "Review guest access"},
            {"site": "TCA-DEMO Legal", "risk": "unlabeled_sensitive_docs", "recommended_action": "Apply sensitivity labels"},
            {"site": "TCA-DEMO Sales", "risk": "inactive_owner", "recommended_action": "Assign active owner"},
        ],
    }


def _synthetic_retention_evidence(stamp: str, tenant_id: str, expiry: str) -> dict[str, Any]:
    return {
        "artifact_type": "synthetic_retention_policy_evidence",
        "created_at_utc": _iso_from_stamp(stamp),
        "tenant_id": tenant_id,
        "expiry_date": expiry,
        "demo_mode": True,
        "is_synthetic": True,
        "policies": [
            {"name": "TCA-DEMO-Copilot-Audit-Retention", "scope": "CopilotInteraction audit records", "retention": "180 days demo assumption"},
            {"name": "TCA-DEMO-eDiscovery-Case-Retention", "scope": "eDiscovery case artifacts", "retention": "30 days demo artifact review"},
        ],
    }


def _synthetic_ediscovery_readiness(stamp: str, expiry: str) -> dict[str, Any]:
    return {
        "artifact_type": "synthetic_ediscovery_readiness",
        "created_at_utc": _iso_from_stamp(stamp),
        "expiry_date": expiry,
        "demo_mode": True,
        "is_synthetic": True,
        "case_visibility": "fixture_only",
        "export_validation": False,
        "content_search": False,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"path": path.name}


def _iso_from_stamp(stamp: str) -> str:
    try:
        return datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _readme(stamp: str, expiry: str, tenant_case_created: bool) -> str:
    cleanup = ""
    if tenant_case_created:
        cleanup = f"""
## Tenant cleanup required

This dataset created one Microsoft Purview eDiscovery case named `TCA-DEMO Evidence Case {stamp}`.

Manual cleanup before or at `{expiry}`:

1. Open Microsoft Purview eDiscovery.
2. Locate the case named `TCA-DEMO Evidence Case {stamp}` or external ID `TCA-DEMO-{stamp}`.
3. Confirm it contains no custodians, holds, exports, purges, or content searches created outside this seeder.
4. Delete or close/remove the demo case according to tenant policy.
5. Record the cleanup action in the demo notes if the evidence pack is shared.
"""
    return f"""# TCA Demo Dataset {stamp}

Purpose: enrich local evidence-pack review and demos without representing synthetic material as production governance evidence.

Important boundaries:

- Demo fixtures are explicitly marked `demo_mode=true` and `is_synthetic=true`.
- Synthetic chat transcripts are not Teams messages, not CopilotInteraction records, and not Purview audit records.
- Tenant eDiscovery case created: {tenant_case_created}.
- If a tenant eDiscovery case was created, it must be manually deleted before or at the expiry target; this tool does not auto-delete tenant cases.
- Expiry target: {expiry}.
- Do not use this dataset as customer audit proof.
{cleanup}
"""
