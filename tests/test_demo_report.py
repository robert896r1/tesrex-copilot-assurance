from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.demo_report import create_demo_report


class DemoReportTests(unittest.TestCase):
    def test_create_demo_report_is_tenant_free_and_labels_synthetic_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            paths = create_demo_report(output_root=tmp, timestamp="20260519T120000Z")
            summary = json.loads(paths.summary.read_text(encoding="utf-8"))
            pack = json.loads(paths.evidence_pack_json.read_text(encoding="utf-8"))
            manifest = json.loads((paths.demo_dataset_dir / "manifest.json").read_text(encoding="utf-8"))

            self.assertTrue(paths.evidence_pack_markdown.exists())
            self.assertTrue(paths.evidence_pack_ui.exists())
            self.assertTrue(summary["demo_mode"])
            self.assertTrue(summary["is_synthetic"])
            self.assertFalse(summary["boundary"]["live_microsoft_api_calls"])
            self.assertFalse(summary["boundary"]["tenant_policy_changes"])
            self.assertTrue(manifest["is_demo_dataset"])
            self.assertIn("demo_evidence_present", pack["assessment_run"]["limitations"])
            self.assertTrue(any(item["normalized_facts"].get("probe_status") == "OK" for item in pack["evidence_items"]))
            self.assertTrue(any("demo_only" in item["limitations"] for item in pack["evidence_items"]))

    def test_demo_report_paths_are_under_requested_output_root(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = create_demo_report(output_root=root, timestamp="20260519T121500Z")
        for path in [paths.demo_dataset_dir, paths.live_probe_dir, paths.evidence_pack_json, paths.evidence_pack_ui]:
            self.assertTrue(path.is_relative_to(root))


if __name__ == "__main__":
    unittest.main()
