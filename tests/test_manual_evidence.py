from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.manual_evidence import ManualEvidenceError, load_manual_evidence_bundle, manual_evidence_items


class ManualEvidenceTests(unittest.TestCase):
    def test_manual_evidence_bundle_loads_and_hashes_artifact(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            artifact = base / "export.txt"
            artifact.write_text("manual proof", encoding="utf-8")
            bundle = {
                "schema_version": "0.1.0",
                "assessment_run_id": "run1",
                "tenant_id": "tenant1",
                "provided_by": "admin@example.com",
                "provided_at_utc": "2026-04-30T00:00:00Z",
                "items": [
                    {
                        "evidence_id": "manual1",
                        "control_ids": ["EDISC-002"],
                        "evidence_type": "report_export",
                        "source_system": "Microsoft Purview",
                        "source_endpoint_or_ui_path": "Purview > eDiscovery",
                        "artifact_path": "export.txt",
                        "asserted_facts": {"customer_provided_purview_export": True},
                        "limitations": ["manual_only"],
                    }
                ],
            }
            bundle_path = base / "bundle.json"
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

            loaded = load_manual_evidence_bundle(bundle_path)
            items = manual_evidence_items(loaded, base_dir=base)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].evidence_id, "manual1")
        self.assertTrue(items[0].content_hash)
        self.assertEqual(items[0].normalized_facts["trust_level"], "customer_asserted")
        self.assertFalse(items[0].normalized_facts["independently_verified_by_tool"])
        self.assertIn("customer_asserted", items[0].limitations)

    def test_manual_evidence_rejects_missing_artifact(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            bundle = {
                "schema_version": "0.1.0",
                "assessment_run_id": "run1",
                "tenant_id": "tenant1",
                "provided_by": "admin@example.com",
                "provided_at_utc": "2026-04-30T00:00:00Z",
                "items": [
                    {
                        "evidence_id": "manual1",
                        "control_ids": ["EDISC-002"],
                        "evidence_type": "report_export",
                        "source_system": "Microsoft Purview",
                        "artifact_path": "missing.txt",
                        "asserted_facts": {},
                        "limitations": [],
                    }
                ],
            }
            bundle_path = base / "bundle.json"
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            with self.assertRaises(ManualEvidenceError):
                load_manual_evidence_bundle(bundle_path)


if __name__ == "__main__":
    unittest.main()
