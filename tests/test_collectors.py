from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.collectors.base import ProbeSpec, ProbeStatus
from tesrex_assurance.collectors.graph import (
    ReadOnlyGraphCollector,
    _looks_like_access_denial,
    _redact_raw_artifact,
    graph_base_url_for_cloud,
    graph_probe_specs,
)


class CollectorSafetyTests(unittest.TestCase):
    def test_probe_spec_rejects_mutation_methods(self) -> None:
        with self.assertRaises(ValueError):
            ProbeSpec("bad", ("X",), "POST", "/v1.0/test", "bad", "unit-test")

    def test_graph_collector_has_no_mutation_methods(self) -> None:
        collector = ReadOnlyGraphCollector()
        for name in ["post", "put", "patch", "delete", "run_post", "run_mutation"]:
            self.assertFalse(hasattr(collector, name), f"ReadOnlyGraphCollector exposes mutation method {name}")

    def test_graph_probe_specs_are_get_only(self) -> None:
        specs = graph_probe_specs()
        self.assertGreaterEqual(len(specs), 3)
        for spec in specs.values():
            self.assertEqual(spec.method, "GET")
            self.assertTrue(spec.no_side_effects)

    def test_cloud_base_urls(self) -> None:
        base, limitations = graph_base_url_for_cloud("AzureCloud")
        self.assertEqual(base, "https://graph.microsoft.com")
        self.assertEqual(limitations, [])
        gov, gov_limitations = graph_base_url_for_cloud("AzureUSGovernment")
        self.assertEqual(gov, "https://graph.microsoft.us")
        self.assertEqual(gov_limitations, [])
        unknown, unknown_limitations = graph_base_url_for_cloud("UnknownCloud")
        self.assertIsNone(unknown)
        self.assertIn("national_cloud_limited", unknown_limitations)

    def test_unknown_cloud_probe_does_not_execute_and_returns_unknown(self) -> None:
        collector = ReadOnlyGraphCollector(environment_name="UnknownCloud")
        result = collector.run_probe("graph.subscribed_skus")
        self.assertEqual(result.status, ProbeStatus.UNKNOWN)
        self.assertIn("national_cloud_limited", result.limitations)

    def test_ediscovery_access_denial_marks_purview_rbac_prerequisite(self) -> None:
        collector = ReadOnlyGraphCollector()
        denied = 'ERROR: Unauthorized({"error":{"code":"UnknownError","message":""}})'

        with patch("tesrex_assurance.collectors.graph.subprocess.run") as run:
            run.return_value.returncode = 1
            run.return_value.stdout = ""
            run.return_value.stderr = denied

            result = collector.run_probe("graph.ediscovery_cases")

        self.assertEqual(result.status, ProbeStatus.NOT_ACCESSIBLE)
        self.assertIn("permission_gap", result.limitations)
        self.assertIn("purview_rbac_gap", result.limitations)
        self.assertIn("prerequisite_missing", result.limitations)

    def test_access_denial_parser_handles_json_error_body(self) -> None:
        raw = '{"error":{"code":"Authorization_RequestDenied","message":"Insufficient privileges to complete the operation."}}'
        self.assertTrue(_looks_like_access_denial(raw))

    def test_raw_artifact_redaction_removes_obvious_tokens_and_secrets(self) -> None:
        raw = 'Authorization: Bearer abc.def.ghi\\n{"access_token":"tok","client_secret":"secret-value"}\\nclient_secret=query-secret'
        redacted = _redact_raw_artifact(raw)
        self.assertNotIn("abc.def.ghi", redacted)
        self.assertNotIn('"tok"', redacted)
        self.assertNotIn("secret-value", redacted)
        self.assertNotIn("query-secret", redacted)
        self.assertIn("[REDACTED]", redacted)


if __name__ == "__main__":
    unittest.main()
