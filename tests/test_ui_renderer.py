from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.ui_renderer import render_evidence_pack_html


class UiRendererTests(unittest.TestCase):
    def test_render_evidence_pack_html_contains_review_sections_and_data(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            pack = {
                "evidence_pack_id": "pack-test",
                "assessment_run": {
                    "assessment_run_id": "run-test",
                    "tenant_id": "tenant1",
                    "completed_at_utc": "2026-04-30T13:00:00Z",
                    "status": "COMPLETED",
                    "scope_summary": "Starter-kit first-slice",
                    "limitations": ["first_slice", "demo_evidence_present"],
                    "tool_version": "0.1.0",
                },
                "control_checks": [
                    {
                        "control_check_id": "LIC-001",
                        "control_family": "LIC",
                        "status": "PASS",
                        "status_cause": "verified",
                        "status_reason": "License inventory read.",
                        "evidence_completeness": "full",
                        "evidence_items_used": ["ev1"],
                    }
                ],
                "findings": [
                    {
                        "finding_id": "finding1",
                        "title": "Finding title",
                        "condition": "Condition text",
                        "recommendation": "Recommendation text",
                        "severity": "medium",
                        "related_control_checks": ["LIC-001"],
                        "evidence_references": ["ev1"],
                    }
                ],
                "evidence_items": [
                    {
                        "evidence_id": "ev1",
                        "evidence_type": "permission_denial",
                        "source_system": "Microsoft Graph",
                        "collected_at_utc": "2026-04-30T13:00:00Z",
                        "content_hash": "abc",
                        "raw_artifact_path": "raw.json",
                        "limitations": [],
                        "normalized_facts": {"ok": True, "demo_mode": True},
                    }
                ],
            }
            pack_path = base / "evidence_pack.json"
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            out = render_evidence_pack_html(pack_path)
            html = out.read_text(encoding="utf-8")
        self.assertIn("Tesrex Copilot Assurance Report", html)
        self.assertIn("Evidence-backed posture for Microsoft Copilot governance.", html)
        self.assertIn("Assess</strong><span>Microsoft-native control state", html)
        self.assertIn("DEMO MODE — Sample report disclosure", html)
        self.assertIn("Control Review", html)
        self.assertIn("Entitlement &amp; Licensing", html)
        self.assertIn("Control family: LIC", html)
        self.assertIn("Verified", html)
        self.assertIn("Verified evidence", html)
        self.assertIn("Cause:", html)
        self.assertIn("Evidence Inspector", html)
        self.assertIn("LIC-001", html)
        self.assertIn("finding1", html)
        self.assertIn("pack-test", html)
        self.assertIn("DEMO MODE", html)

    def test_control_rows_use_actionable_review_language(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            pack = {
                "evidence_pack_id": "pack-semantics",
                "assessment_run": {
                    "assessment_run_id": "run-semantics",
                    "tenant_id": "tenant1",
                    "completed_at_utc": "2026-05-01T09:00:00Z",
                    "status": "COMPLETED",
                    "scope_summary": "UI semantics test",
                    "limitations": [],
                    "tool_version": "0.1.0",
                },
                "control_checks": [
                    {
                        "control_check_id": "AUD-001",
                        "control_family": "AUD",
                        "status": "WARN",
                        "status_cause": "assessment_limitation",
                        "status_reason": "Audit query was not run in the default read-only probe.",
                        "evidence_completeness": "partial",
                        "limitations": ["not_configured_for_assessment"],
                        "follow_up_required": ["Approve the read-only audit query collector or provide Purview export."],
                        "evidence_items_used": [],
                    },
                    {
                        "control_check_id": "DLP-001",
                        "control_family": "DLP",
                        "status": "UNKNOWN",
                        "status_cause": "manual_evidence_required",
                        "status_reason": "DLP inventory was not supplied.",
                        "evidence_completeness": "partial",
                        "limitations": ["manual_only", "demo_evidence"],
                        "follow_up_required": ["Provide Purview DLP export."],
                        "evidence_items_used": [],
                    },
                    {
                        "control_check_id": "LABEL-001",
                        "control_family": "LABEL",
                        "status": "UNKNOWN",
                        "status_cause": "assessment_limitation",
                        "status_reason": "Sensitivity-label inventory was not collected in this run.",
                        "evidence_completeness": "partial",
                        "limitations": ["not_configured_for_assessment"],
                        "follow_up_required": ["Approve the read-only label collector or provide Purview export."],
                        "evidence_items_used": [],
                    },
                    {
                        "control_check_id": "SAM-001",
                        "control_family": "SAM",
                        "status": "NOT_ACCESSIBLE",
                        "status_cause": "permission_gap",
                        "status_reason": "SharePoint admin read was denied.",
                        "evidence_completeness": "none",
                        "limitations": ["permission_limited"],
                        "follow_up_required": ["Grant least-privilege SharePoint reader access."],
                        "evidence_items_used": [],
                    },
                ],
                "findings": [
                    {
                        "finding_id": "finding-dlp",
                        "title": "DLP-001: UNKNOWN",
                        "condition": "DLP inventory was not supplied.",
                        "recommendation": "Provide Purview DLP export.",
                        "severity": "low",
                        "related_control_checks": ["DLP-001"],
                        "evidence_references": [],
                    },
                    {
                        "finding_id": "finding-label",
                        "title": "LABEL-001: UNKNOWN",
                        "condition": "Sensitivity-label inventory was not collected.",
                        "recommendation": "Approve the read-only label collector or provide Purview export.",
                        "severity": "low",
                        "related_control_checks": ["LABEL-001"],
                        "evidence_references": [],
                    }
                ],
                "evidence_items": [],
            }
            pack_path = base / "evidence_pack.json"
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            out = render_evidence_pack_html(pack_path)
            html = out.read_text(encoding="utf-8")
        self.assertIn("Evidence incomplete", html)
        self.assertIn("Manual evidence required", html)
        self.assertIn("Access required", html)
        self.assertIn("This does not prove the tenant is misconfigured", html)
        self.assertIn("Demo evidence attached", html)
        self.assertIn("Not collected in this run", html)
        self.assertIn("What the report found:</b> DLP inventory was not supplied.", html)
        self.assertIn("What the report found:</b> Sensitivity-label inventory was not collected.", html)
        self.assertIn("Why this appears:</b> DLP inventory was not supplied.", html)
        self.assertIn("Why this matters:", html)
        self.assertIn("Next evidence step:</b> Provide Purview DLP export.", html)
        self.assertIn("Provide Purview DLP export.", html)
        self.assertIn('data-focus-status="UNKNOWN"', html)
        self.assertIn("Action linked", html)
        self.assertNotIn("Review Actions", html)
        self.assertNotIn("Review action:", html)
        self.assertNotIn("Gap Identified", html)


if __name__ == "__main__":
    unittest.main()
