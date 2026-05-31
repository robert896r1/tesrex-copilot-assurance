from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.demo_dataset import create_demo_dataset


class DemoDatasetTests(unittest.TestCase):
    def test_create_demo_dataset_writes_manual_bundle_with_demo_flags(self) -> None:
        with TemporaryDirectory() as tmp:
            out = create_demo_dataset(output_root=tmp, timestamp="20260430T000000Z", tenant_id="tenant1", provided_by="tester")
            bundle = json.loads((out / "manual_evidence_bundle.json").read_text(encoding="utf-8"))
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            readme = (out / "README.md").read_text(encoding="utf-8")
        self.assertEqual(bundle["schema_version"], "0.1.0")
        self.assertEqual(len(bundle["items"]), 5)
        self.assertTrue(any(item["asserted_facts"].get("demo_mode") is True for item in bundle["items"]))
        self.assertFalse(manifest["tenant_mutations"]["teams_messages_created"])
        self.assertTrue(manifest["is_demo_dataset"])
        self.assertIn("Do not use this dataset as customer audit proof", readme)

    def test_create_demo_dataset_with_tenant_case_includes_cleanup_instructions(self) -> None:
        with TemporaryDirectory() as tmp:
            out = create_demo_dataset(
                output_root=tmp,
                timestamp="20260430T000000Z",
                tenant_id="tenant1",
                provided_by="tester",
                tenant_ediscovery_request={"displayName": "TCA-DEMO Evidence Case 20260430T000000Z"},
                tenant_ediscovery_response={"id": "case1", "displayName": "TCA-DEMO Evidence Case 20260430T000000Z"},
            )
            readme = (out / "README.md").read_text(encoding="utf-8")
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("Tenant cleanup required", readme)
        self.assertIn("TCA-DEMO Evidence Case 20260430T000000Z", readme)
        self.assertTrue(manifest["tenant_mutations"]["ediscovery_case_created"])

    def test_public_demo_cli_has_no_live_tenant_mutation_path(self) -> None:
        script = (ROOT / "scripts" / "create_demo_dataset.py").read_text(encoding="utf-8")
        self.assertNotIn("--tenant-ediscovery-case", script)
        self.assertNotIn("az rest", script)
        self.assertNotIn("ediscoveryCases", script)


if __name__ == "__main__":
    unittest.main()
