from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.classifiers import classify_copilot_dlp_inventory, classify_subscribed_skus_response
from tesrex_assurance.mappings import load_dlp_copilot_location_map, load_microsoft_capability_map
from tesrex_assurance.models import ControlStatus

FIXTURES = ROOT / "tests" / "fixtures"


def fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


class LicenseClassifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.map = load_microsoft_capability_map(ROOT / "config" / "microsoft_capability_map.json")
        self.capability = "LIC-002.microsoft_365_copilot_work_graph_chat_present"

    def test_exact_match_passes_when_mapping_fresh(self) -> None:
        check = classify_subscribed_skus_response(
            fixture("license_exact_match.json"),
            self.map,
            self.capability,
            assessment_date="2026-04-29",
            evidence_items_used=["e-license"],
        )
        self.assertEqual(check.status, ControlStatus.PASS)
        self.assertEqual(check.evidence_completeness.value, "full")
        self.assertTrue(check.mapping_versions_used)

    def test_stale_exact_match_warns_not_passes(self) -> None:
        check = classify_subscribed_skus_response(
            fixture("license_exact_match.json"),
            self.map,
            self.capability,
            assessment_date="2027-04-29",
        )
        self.assertEqual(check.status, ControlStatus.WARN)
        self.assertIn("stale_mapping", check.limitations)

    def test_fallback_match_warns_and_blocks_not_licensed(self) -> None:
        check = classify_subscribed_skus_response(
            fixture("license_fallback_match.json"),
            self.map,
            "LIC-002.microsoft_365_copilot_service_plan_family_present",
            assessment_date="2026-04-29",
        )
        self.assertEqual(check.status, ControlStatus.WARN)
        self.assertIn("manual_review_required", check.limitations)
        self.assertIn("license_limited", check.limitations)

    def test_access_denial_is_not_accessible(self) -> None:
        check = classify_subscribed_skus_response(
            fixture("license_access_denied.json"),
            self.map,
            self.capability,
            assessment_date="2026-04-29",
        )
        self.assertEqual(check.status, ControlStatus.NOT_ACCESSIBLE)

    def test_guid_containing_403_in_success_payload_is_not_access_denial(self) -> None:
        response = {
            "value": [
                {
                    "skuPartNumber": "PLAIN_SKU",
                    "capabilityStatus": "Enabled",
                    "servicePlans": [
                        {
                            "servicePlanId": "0403bb98-9d17-4f94-b53e-eca56a7698a6",
                            "servicePlanName": "NON_COPILOT_PLAN",
                            "provisioningStatus": "Success",
                        }
                    ],
                }
            ]
        }
        check = classify_subscribed_skus_response(response, self.map, self.capability, assessment_date="2026-04-29")
        self.assertNotEqual(check.status, ControlStatus.NOT_ACCESSIBLE)
        self.assertEqual(check.status, ControlStatus.UNKNOWN)

    def test_no_match_with_incomplete_map_is_unknown_not_not_licensed(self) -> None:
        response = {"value": []}
        check = classify_subscribed_skus_response(response, self.map, self.capability, assessment_date="2026-04-29")
        self.assertEqual(check.status, ControlStatus.UNKNOWN)
        self.assertIn("license_limited", check.limitations)


class DlpClassifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.map = load_dlp_copilot_location_map(ROOT / "config" / "dlp_copilot_location_map.json")

    def test_exact_guid_passes_when_mapping_fresh(self) -> None:
        check = classify_copilot_dlp_inventory(
            fixture("dlp_exact_guid.json"),
            self.map,
            assessment_date="2026-04-29",
            evidence_items_used=["e-dlp"],
        )
        self.assertEqual(check.status, ControlStatus.PASS)
        self.assertTrue(check.mapping_versions_used)

    def test_stale_guid_warns_not_passes(self) -> None:
        check = classify_copilot_dlp_inventory(fixture("dlp_exact_guid.json"), self.map, assessment_date="2027-04-29")
        self.assertEqual(check.status, ControlStatus.WARN)
        self.assertIn("stale_mapping", check.limitations)

    def test_pattern_only_warns_manual_review(self) -> None:
        check = classify_copilot_dlp_inventory(fixture("dlp_pattern_only.json"), self.map, assessment_date="2026-04-29")
        self.assertEqual(check.status, ControlStatus.WARN)
        self.assertIn("manual_review_required", check.limitations)

    def test_invalid_schema_unknown_api_unsupported(self) -> None:
        check = classify_copilot_dlp_inventory(fixture("dlp_invalid_schema.json"), self.map, assessment_date="2026-04-29")
        self.assertEqual(check.status, ControlStatus.UNKNOWN)
        self.assertIn("api_unsupported", check.limitations)

    def test_valid_schema_no_copilot_can_fail_when_baseline_required(self) -> None:
        check = classify_copilot_dlp_inventory(
            fixture("dlp_no_copilot_valid_schema.json"),
            self.map,
            assessment_date="2026-04-29",
            baseline_required=True,
        )
        self.assertEqual(check.status, ControlStatus.FAIL)

    def test_license_absence_context_returns_not_licensed(self) -> None:
        check = classify_copilot_dlp_inventory(
            fixture("dlp_no_copilot_valid_schema.json"),
            self.map,
            assessment_date="2026-04-29",
            license_status=ControlStatus.NOT_LICENSED,
        )
        self.assertEqual(check.status, ControlStatus.NOT_LICENSED)


class StatusCoverageTests(unittest.TestCase):
    def test_fixture_classifiers_cover_all_control_statuses(self) -> None:
        cap_map = load_microsoft_capability_map(ROOT / "config" / "microsoft_capability_map.json")
        dlp_map = load_dlp_copilot_location_map(ROOT / "config" / "dlp_copilot_location_map.json")
        statuses = {
            classify_subscribed_skus_response(fixture("license_exact_match.json"), cap_map, "LIC-002.microsoft_365_copilot_work_graph_chat_present", "2026-04-29").status,
            classify_subscribed_skus_response(fixture("license_fallback_match.json"), cap_map, "LIC-002.microsoft_365_copilot_service_plan_family_present", "2026-04-29").status,
            classify_subscribed_skus_response({"value": []}, cap_map, "LIC-002.microsoft_365_copilot_work_graph_chat_present", "2026-04-29").status,
            classify_subscribed_skus_response(fixture("license_access_denied.json"), cap_map, "LIC-002.microsoft_365_copilot_work_graph_chat_present", "2026-04-29").status,
            classify_copilot_dlp_inventory(fixture("dlp_no_copilot_valid_schema.json"), dlp_map, "2026-04-29").status,
            classify_copilot_dlp_inventory(fixture("dlp_no_copilot_valid_schema.json"), dlp_map, "2026-04-29", license_status=ControlStatus.NOT_LICENSED).status,
        }
        self.assertEqual(statuses, set(ControlStatus))


class MappingValidationTests(unittest.TestCase):
    def test_mapping_schema_validation_rejects_bad_common_shape(self) -> None:
        tmp = ROOT / "tests" / "fixtures" / "bad_map.tmp.json"
        tmp.write_text(json.dumps({"schema_version": "0.1.0"}))
        try:
            with self.assertRaises(ValueError):
                load_microsoft_capability_map(tmp)
        finally:
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
