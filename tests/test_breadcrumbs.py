from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.breadcrumbs import control_breadcrumbs
from tesrex_assurance.models import ControlStatus, EvidenceCompleteness, EvidenceType, ControlCheck


def check(**overrides) -> ControlCheck:
    data = {
        "control_check_id": "EDISC-002",
        "assessment_run_id": "run-test",
        "control_family": "EDISC",
        "control_objective": "Assess eDiscovery readiness.",
        "expected_state": "Evidence is sufficient.",
        "assessed_scope": "tenant / test",
        "procedure": "fixture",
        "required_evidence_types": [EvidenceType.RAW_API_RESPONSE],
        "evidence_items_used": [],
        "observed_state": "partial",
        "status": ControlStatus.WARN,
        "status_reason": "eDiscovery case endpoint is visible, but no positive/export-validating readiness evidence is present in the default run.",
        "evidence_completeness": EvidenceCompleteness.PARTIAL,
        "limitations": ["partial_scope", "no_export_validation"],
        "follow_up_required": ["Review limitations for EDISC-002 and rerun after evidence gap is resolved."],
    }
    data.update(overrides)
    return ControlCheck(**data)


class BreadcrumbTests(unittest.TestCase):
    def test_edisc_warning_breadcrumbs_are_specific_and_not_duplicate_reason(self) -> None:
        item = check()
        breadcrumbs = control_breadcrumbs(item)
        self.assertEqual(
            breadcrumbs.what_found,
            "eDiscovery is reachable, but Copilot data discovery/export readiness is not proven.",
        )
        self.assertEqual(breadcrumbs.why_this_appears, item.status_reason)
        self.assertNotEqual(breadcrumbs.what_found, breadcrumbs.why_this_appears)
        self.assertIn("Copilot interaction data", breadcrumbs.why_it_matters)
        self.assertIn("Purview eDiscovery evidence", breadcrumbs.next_evidence_step)

    def test_manual_dlp_breadcrumbs_point_to_evidence_not_workflow(self) -> None:
        item = check(
            control_check_id="DLP-001",
            control_family="DLP",
            status=ControlStatus.UNKNOWN,
            status_reason="ExchangeOnlineManagement module is locally available, but tenant DLP policy/rule inventory was not read in this default run.",
            limitations=["manual_only", "not_configured_for_assessment"],
            follow_up_required=[],
        )
        breadcrumbs = control_breadcrumbs(item)
        self.assertIn("DLP policy/rule inventory", breadcrumbs.what_found)
        self.assertIn("Copilot-related activity", breadcrumbs.why_it_matters)
        self.assertIn("Purview DLP policy/rule export", breadcrumbs.next_evidence_step)


if __name__ == "__main__":
    unittest.main()
