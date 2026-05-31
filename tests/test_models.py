from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.models import ControlStatus, StatusCause, infer_status_cause


class StatusCauseInferenceTests(unittest.TestCase):
    def test_demo_evidence_does_not_mask_warn_assessment_limitation(self) -> None:
        cause = infer_status_cause(
            ControlStatus.WARN,
            ["demo_evidence", "assessment_limitation"],
            "Demo evidence is attached, but the assessment did not collect production control evidence.",
        )
        self.assertEqual(cause, StatusCause.ASSESSMENT_LIMITATION)

    def test_demo_evidence_does_not_mask_warn_without_other_markers(self) -> None:
        cause = infer_status_cause(ControlStatus.WARN, ["demo_evidence"], "Demo-only warning.")
        self.assertEqual(cause, StatusCause.ASSESSMENT_LIMITATION)

    def test_demo_evidence_can_be_fallback_for_unknown_when_only_marker(self) -> None:
        cause = infer_status_cause(ControlStatus.UNKNOWN, ["demo_evidence"], "Only demo evidence is available.")
        self.assertEqual(cause, StatusCause.DEMO_EVIDENCE)

    def test_demo_evidence_attached_to_pass_prevents_production_verified_cause(self) -> None:
        cause = infer_status_cause(
            ControlStatus.PASS,
            ["demo_evidence_in_full_check"],
            "A pass-like check was downgraded because demo evidence was attached.",
        )
        self.assertEqual(cause, StatusCause.ASSESSMENT_LIMITATION)


if __name__ == "__main__":
    unittest.main()
