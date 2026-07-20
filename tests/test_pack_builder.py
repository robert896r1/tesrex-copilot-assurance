from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.evidence_pack import generate_pack_dict
from tesrex_assurance.models import ControlStatus, StatusCause
from tesrex_assurance.pack_builder import build_evidence_pack_from_live_probe


def write_raw(base: Path, name: str, payload) -> tuple[str, str]:
    path = base / f"{name}.json"
    text = json.dumps(payload)
    path.write_text(text, encoding="utf-8")
    return str(path), hashlib.sha256(text.encode("utf-8")).hexdigest()


class PackBuilderTests(unittest.TestCase):
    def test_build_pack_includes_starter_kit_controls_and_unread_register(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw = base / "raw"
            raw.mkdir()
            sku_path, sku_hash = write_raw(raw, "graph_subscribed_skus", {"value": []})
            org_path, org_hash = write_raw(raw, "graph_organization", {"id": "tenant1"})
            label_path, label_hash = write_raw(raw, "graph_sensitivity_labels", {"value": []})
            token_path, token_hash = write_raw(raw, "graph_token", {"audit_query_scopes_present": ["AuditLogsQuery.Read.All"]})
            edisc_path, edisc_hash = write_raw(raw, "graph_ediscovery_cases", {"value": []})
            ps_path, ps_hash = write_raw(raw, "ps", {"Name": "ExchangeOnlineManagement", "Version": "3.9.0"})
            spo_path, spo_hash = write_raw(raw, "spo", {"Name": "Microsoft.Online.SharePoint.PowerShell", "Version": "16.0"})
            summary = {
                "generated_at_utc": "20260430T130000Z",
                "tenant_id": "tenant1",
                "user": "unit-test",
                "probe_results": [
                    {"probe_id": "graph.organization", "status": "OK", "control_ids": ["LIC-001"], "source_ref": "Graph", "raw_artifact_path": org_path, "content_hash": org_hash, "summary": {"payload_shape": "object"}, "limitations": [], "status_reason": "ok"},
                    {"probe_id": "graph.subscribed_skus", "status": "OK", "control_ids": ["LIC-001", "LIC-002"], "source_ref": "Graph", "raw_artifact_path": sku_path, "content_hash": sku_hash, "summary": {"payload_shape": "collection", "count_returned": 0}, "limitations": [], "status_reason": "ok"},
                    {"probe_id": "graph.sensitivity_labels", "status": "OK", "control_ids": ["LABEL-001"], "source_ref": "Graph", "raw_artifact_path": label_path, "content_hash": label_hash, "summary": {"payload_shape": "collection", "count_returned": 0}, "limitations": [], "status_reason": "ok"},
                    {"probe_id": "graph.token_scopes", "status": "OK", "control_ids": ["AUD-001"], "source_ref": "Graph", "raw_artifact_path": token_path, "content_hash": token_hash, "summary": {"audit_query_scopes_present": ["AuditLogsQuery.Read.All"]}, "limitations": ["raw_secret_not_retained"], "status_reason": "ok"},
                    {"probe_id": "graph.ediscovery_cases", "status": "OK", "control_ids": ["EDISC-002"], "source_ref": "Graph", "raw_artifact_path": edisc_path, "content_hash": edisc_hash, "summary": {"payload_shape": "collection", "count_returned": 0}, "limitations": [], "status_reason": "ok"},
                    {"probe_id": "powershell.exchange_online_management", "status": "OK", "control_ids": ["DLP-001"], "source_ref": "PowerShell", "raw_artifact_path": ps_path, "content_hash": ps_hash, "summary": {"module": "ExchangeOnlineManagement"}, "limitations": [], "status_reason": "ok"},
                    {"probe_id": "powershell.sharepoint_online", "status": "OK", "control_ids": ["SAM-001"], "source_ref": "PowerShell", "raw_artifact_path": spo_path, "content_hash": spo_hash, "summary": {"module": "Microsoft.Online.SharePoint.PowerShell"}, "limitations": [], "status_reason": "ok"},
                ],
            }
            summary_path = base / "summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            json_path, md_path, pack = build_evidence_pack_from_live_probe(summary_path, output_dir=base / "packs")
            data = generate_pack_dict(pack)

            control_ids = {check["control_check_id"] for check in data["control_checks"]}
            for expected in ["LIC-001", "LIC-002.copilot_family", "AUD-001", "DLP-001", "SAM-001", "EDISC-002", "PACK-001", "PACK-002"]:
                self.assertIn(expected, control_ids)
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            edisc = next(check for check in pack.control_checks if check.control_check_id == "EDISC-002")
            self.assertEqual(edisc.status, ControlStatus.WARN)
            edisc_finding = next(finding for finding in pack.findings if finding.related_control_checks == ["EDISC-002"])
            self.assertNotEqual(edisc_finding.condition, edisc.status_reason)
            self.assertIn("Copilot data discovery/export readiness", edisc_finding.condition)
            self.assertIn("Purview eDiscovery evidence", edisc_finding.recommendation)
            self.assertTrue(data["unread_controls_register"])
            pack002 = next(check for check in pack.control_checks if check.control_check_id == "PACK-002")
            self.assertEqual(pack002.status, ControlStatus.PASS)
            self.assertIn("Verified the existence and SHA-256 hash", pack002.status_reason)

    def test_pack002_warns_when_retained_artifact_hash_does_not_match(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw = base / "raw"
            raw.mkdir()
            sku_path, sku_hash = write_raw(raw, "graph_subscribed_skus", {"value": []})
            Path(sku_path).write_text(
                '{"value": [{"skuPartNumber": "CHANGED", "capabilityStatus": "Disabled"}]}',
                encoding="utf-8",
            )
            summary = {
                "generated_at_utc": "20260430T130000Z",
                "tenant_id": "tenant1",
                "user": "unit-test",
                "probe_results": [
                    {
                        "probe_id": "graph.subscribed_skus",
                        "status": "OK",
                        "control_ids": ["LIC-001"],
                        "source_ref": "Graph",
                        "raw_artifact_path": sku_path,
                        "content_hash": sku_hash,
                        "summary": {"payload_shape": "collection", "count_returned": 0},
                        "limitations": [],
                        "status_reason": "ok",
                    }
                ],
            }
            summary_path = base / "summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            _json_path, _md_path, pack = build_evidence_pack_from_live_probe(
                summary_path,
                output_dir=base / "packs",
            )

        pack002 = next(check for check in pack.control_checks if check.control_check_id == "PACK-002")
        self.assertEqual(pack002.status, ControlStatus.WARN)
        self.assertIn("artifact_hash_mismatch", pack002.limitations)
        self.assertIn("did not match the recorded SHA-256 hash", pack002.status_reason)

class PackBuilderManualAndPermissionTests(unittest.TestCase):
    def test_manual_evidence_is_linked_to_matching_control_check(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw = base / "raw"
            raw.mkdir()
            sku_path, sku_hash = write_raw(raw, "graph_subscribed_skus", {"value": []})
            manual_dir = base / "manual"
            manual_dir.mkdir()
            manual_artifact = manual_dir / "dlp.txt"
            manual_artifact.write_text("dlp export", encoding="utf-8")
            manual_bundle = manual_dir / "bundle.json"
            manual_bundle.write_text(json.dumps({
                "schema_version": "0.1.0",
                "assessment_run_id": "run-20260430T130000Z",
                "tenant_id": "tenant1",
                "provided_by": "admin@example.com",
                "provided_at_utc": "2026-04-30T13:00:00Z",
                "items": [{
                    "evidence_id": "manual-dlp",
                    "control_ids": ["DLP-001"],
                    "evidence_type": "policy_snapshot",
                    "source_system": "Microsoft Purview",
                    "artifact_path": "dlp.txt",
                    "asserted_facts": {"dlp_export_present": True},
                    "limitations": []
                }]
            }), encoding="utf-8")
            summary = {
                "generated_at_utc": "20260430T130000Z",
                "tenant_id": "tenant1",
                "user": "unit-test",
                "probe_results": [
                    {"probe_id": "graph.subscribed_skus", "status": "OK", "control_ids": ["LIC-001"], "source_ref": "Graph", "raw_artifact_path": sku_path, "content_hash": sku_hash, "summary": {"payload_shape": "collection", "count_returned": 0}, "limitations": [], "status_reason": "ok"}
                ],
            }
            summary_path = base / "summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            _json_path, _md_path, pack = build_evidence_pack_from_live_probe(summary_path, output_dir=base / "packs", manual_evidence_paths=[manual_bundle])
            dlp = next(check for check in pack.control_checks if check.control_check_id == "DLP-001")
        self.assertIn("manual-dlp", dlp.evidence_items_used)
        self.assertIn("manual_evidence_linked", dlp.limitations)
        self.assertEqual(dlp.status_cause, StatusCause.MANUAL_EVIDENCE_REQUIRED)

    def test_demo_manual_evidence_marks_pack_and_partial_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw = base / "raw"
            raw.mkdir()
            sku_path, sku_hash = write_raw(raw, "graph_subscribed_skus", {"value": []})
            manual_dir = base / "manual"
            manual_dir.mkdir()
            manual_artifact = manual_dir / "sam.json"
            manual_artifact.write_text("{}", encoding="utf-8")
            manual_bundle = manual_dir / "bundle.json"
            manual_bundle.write_text(json.dumps({
                "schema_version": "0.1.0",
                "assessment_run_id": "run-20260430T130000Z",
                "tenant_id": "tenant1",
                "provided_by": "tester",
                "provided_at_utc": "2026-04-30T13:00:00Z",
                "items": [{
                    "evidence_id": "manual-demo-sam",
                    "control_ids": ["SAM-001"],
                    "evidence_type": "report_export",
                    "source_system": "TCA synthetic demo fixture",
                    "artifact_path": "sam.json",
                    "asserted_facts": {"demo_mode": True, "is_synthetic": True},
                    "limitations": ["demo_only"]
                }]
            }), encoding="utf-8")
            summary = {
                "generated_at_utc": "20260430T130000Z",
                "tenant_id": "tenant1",
                "user": "unit-test",
                "probe_results": [
                    {"probe_id": "graph.subscribed_skus", "status": "OK", "control_ids": ["LIC-001"], "source_ref": "Graph", "raw_artifact_path": sku_path, "content_hash": sku_hash, "summary": {"payload_shape": "collection", "count_returned": 0}, "limitations": [], "status_reason": "ok"}
                ],
            }
            summary_path = base / "summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            _json_path, _md_path, pack = build_evidence_pack_from_live_probe(summary_path, output_dir=base / "packs", manual_evidence_paths=[manual_bundle])
            sam = next(check for check in pack.control_checks if check.control_check_id == "SAM-001")
        self.assertIn("demo_evidence_present", pack.assessment_run.limitations)
        self.assertIn("demo_evidence", sam.limitations)
        self.assertIn("manual-demo-sam", sam.evidence_items_used)
        self.assertEqual(sam.status_cause, StatusCause.MANUAL_EVIDENCE_REQUIRED)

    def test_demo_evidence_downgrades_full_check_to_partial(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw = base / "raw"
            raw.mkdir()
            sku_path, sku_hash = write_raw(raw, "graph_subscribed_skus", {"value": []})
            manual_dir = base / "manual"
            manual_dir.mkdir()
            manual_artifact = manual_dir / "lic.json"
            manual_artifact.write_text("{}", encoding="utf-8")
            manual_bundle = manual_dir / "bundle.json"
            manual_bundle.write_text(json.dumps({
                "schema_version": "0.1.0",
                "assessment_run_id": "run-20260430T130000Z",
                "tenant_id": "tenant1",
                "provided_by": "tester",
                "provided_at_utc": "2026-04-30T13:00:00Z",
                "items": [{
                    "evidence_id": "manual-demo-lic",
                    "control_ids": ["LIC-001"],
                    "evidence_type": "manual_artifact",
                    "source_system": "TCA synthetic demo fixture",
                    "artifact_path": "lic.json",
                    "asserted_facts": {"demo_mode": True, "is_synthetic": True},
                    "limitations": ["demo_only"]
                }]
            }), encoding="utf-8")
            summary = {
                "generated_at_utc": "20260430T130000Z",
                "tenant_id": "tenant1",
                "user": "unit-test",
                "probe_results": [
                    {"probe_id": "graph.subscribed_skus", "status": "OK", "control_ids": ["LIC-001"], "source_ref": "Graph", "raw_artifact_path": sku_path, "content_hash": sku_hash, "summary": {"payload_shape": "collection", "count_returned": 0}, "limitations": [], "status_reason": "ok"}
                ],
            }
            summary_path = base / "summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            _json_path, _md_path, pack = build_evidence_pack_from_live_probe(summary_path, output_dir=base / "packs", manual_evidence_paths=[manual_bundle])
            lic = next(check for check in pack.control_checks if check.control_check_id == "LIC-001")
        self.assertEqual(lic.evidence_completeness.value, "partial")
        self.assertIn("demo_evidence_in_full_check", lic.limitations)
        self.assertEqual(lic.status_cause, StatusCause.ASSESSMENT_LIMITATION)

    def test_bounded_validation_flag_suppresses_expected_readwrite_overprivilege(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw = base / "raw"
            raw.mkdir()
            token_path, token_hash = write_raw(raw, "graph_token", {"roles": ["AuditLogsQuery.Read.All", "eDiscovery.ReadWrite.All"]})
            sku_path, sku_hash = write_raw(raw, "graph_subscribed_skus", {"value": []})
            summary = {
                "generated_at_utc": "20260430T130000Z",
                "tenant_id": "tenant1",
                "user": "unit-test",
                "boundary": {"bounded_validation_approved": True, "mutation_methods_used": ["bounded_validation.ediscovery"]},
                "probe_results": [
                    {"probe_id": "graph.token_scopes", "status": "OK", "control_ids": ["AUD-001"], "source_ref": "Graph", "raw_artifact_path": token_path, "content_hash": token_hash, "summary": {"audit_query_scopes_present": ["AuditLogsQuery.Read.All"]}, "limitations": [], "status_reason": "ok"},
                    {"probe_id": "graph.subscribed_skus", "status": "OK", "control_ids": ["LIC-001"], "source_ref": "Graph", "raw_artifact_path": sku_path, "content_hash": sku_hash, "summary": {"payload_shape": "collection", "count_returned": 0}, "limitations": [], "status_reason": "ok"}
                ],
            }
            summary_path = base / "summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            _json_path, _md_path, pack = build_evidence_pack_from_live_probe(summary_path, output_dir=base / "packs")
        self.assertNotIn("finding-over-privileged-identity", {finding.finding_id for finding in pack.findings})


if __name__ == "__main__":
    unittest.main()
