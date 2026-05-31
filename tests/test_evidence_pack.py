from __future__ import annotations

from datetime import datetime, timezone
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.classifiers import classify_subscribed_skus_response
from tesrex_assurance.evidence_pack import generate_pack_dict, render_markdown_pack, validate_evidence_pack
from tesrex_assurance.mappings import load_microsoft_capability_map
from tesrex_assurance.models import (
    AssessmentRun,
    ControlCheck,
    ControlStatus,
    EvidenceCompleteness,
    EvidenceItem,
    EvidencePack,
    EvidenceType,
)


class EvidencePackTests(unittest.TestCase):
    def test_unread_register_includes_warn_unknown_not_accessible_and_limitations(self) -> None:
        cap_map = load_microsoft_capability_map(ROOT / "config" / "microsoft_capability_map.json")
        warn_check = classify_subscribed_skus_response(
            {"value": [{"skuPartNumber": "FUTURE_COPILOT", "capabilityStatus": "Enabled", "servicePlans": []}]},
            cap_map,
            "LIC-002.microsoft_365_copilot_service_plan_family_present",
            assessment_date="2026-04-29",
            evidence_items_used=["ev1"],
        )
        evidence = EvidenceItem(
            evidence_id="ev1",
            assessment_run_id="run1",
            evidence_type=EvidenceType.LICENSE_SNAPSHOT,
            source_system="Microsoft Graph",
            source_endpoint_or_ui_path="/subscribedSkus",
            collection_method="fixture",
            collected_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            tenant_id="tenant1",
            collector_identity="unit-test",
            permission_context="fixture",
            raw_artifact_path="tests/fixtures/license_fallback_match.json",
            content_hash="0" * 64,
        )
        run = AssessmentRun(
            assessment_run_id="run1",
            tenant_id="tenant1",
            started_at_utc="2026-04-29T00:00:00Z",
            initiated_by="unit-test",
            tool_version="0.1.0",
        )
        pack = EvidencePack("pack1", run, [evidence], [warn_check])
        data = generate_pack_dict(pack)
        self.assertEqual(len(data["unread_controls_register"]), 1)
        self.assertEqual(data["unread_controls_register"][0]["status"], "WARN")
        self.assertEqual(data["unread_controls_register"][0]["status_cause"], "assessment_limitation")
        self.assertIn("Evidence Pack", render_markdown_pack(pack))

    def test_mapping_required_control_without_mapping_metadata_fails_validation(self) -> None:
        cap_map = load_microsoft_capability_map(ROOT / "config" / "microsoft_capability_map.json")
        check = classify_subscribed_skus_response(
            {"value": []},
            cap_map,
            "LIC-002.microsoft_365_copilot_work_graph_chat_present",
            assessment_date="2026-04-29",
        )
        check.mapping_versions_used = []
        run = AssessmentRun("run1", "tenant1", "2026-04-29T00:00:00Z", "unit-test", "0.1.0")
        pack = EvidencePack("pack1", run, [], [check])
        with self.assertRaises(ValueError):
            validate_evidence_pack(pack)

    def test_evidence_without_hash_requires_raw_retention_limitation(self) -> None:
        evidence = EvidenceItem(
            evidence_id="ev1",
            assessment_run_id="run1",
            evidence_type=EvidenceType.RAW_API_RESPONSE,
            source_system="fixture",
            source_endpoint_or_ui_path="fixture",
            collection_method="fixture",
            collected_at_utc="2026-04-29T00:00:00Z",
            tenant_id="tenant1",
            collector_identity="unit-test",
            permission_context="fixture",
        )
        with self.assertRaises(ValueError):
            evidence.validate()
        evidence.limitations.append("raw_retention_unavailable")
        evidence.validate()

    def test_api_connectivity_only_evidence_requires_zero_content_scope_fields(self) -> None:
        evidence = EvidenceItem(
            evidence_id="ev-api",
            assessment_run_id="run1",
            evidence_type=EvidenceType.RAW_API_RESPONSE,
            source_system="Microsoft Graph",
            source_endpoint_or_ui_path="/security/cases/ediscoveryCases/{id}/searches",
            collection_method="assessor-approved bounded validation",
            collected_at_utc="2026-04-30T00:00:00Z",
            tenant_id="tenant1",
            collector_identity="unit-test",
            permission_context="app-only",
            raw_artifact_path="artifacts/example.json",
            content_hash="1" * 64,
            normalized_facts={"validation_scope": "api_connectivity_only"},
        )
        with self.assertRaises(ValueError):
            evidence.validate()

        evidence.normalized_facts.update(
            {
                "content_scope": "none",
                "source_binding": "none",
                "export_performed": False,
                "purge_performed": False,
            }
        )
        with self.assertRaises(ValueError):
            evidence.validate()

        evidence.limitations.append("zero_content_scope")
        evidence.validate()

    def test_api_connectivity_only_evidence_rejects_content_binding_export_or_purge(self) -> None:
        base = {
            "content_scope": "none",
            "source_binding": "none",
            "export_performed": False,
            "purge_performed": False,
            "validation_scope": "api_connectivity_only",
        }
        invalid_cases = [
            {"content_scope": "partial"},
            {"source_binding": "mailbox"},
            {"export_performed": True},
            {"purge_performed": True},
        ]
        for override in invalid_cases:
            with self.subTest(override=override):
                facts = dict(base)
                facts.update(override)
                evidence = EvidenceItem(
                    evidence_id="ev-api",
                    assessment_run_id="run1",
                    evidence_type=EvidenceType.RAW_API_RESPONSE,
                    source_system="Microsoft Graph",
                    source_endpoint_or_ui_path="/security/cases/ediscoveryCases/{id}/searches",
                    collection_method="assessor-approved bounded validation",
                    collected_at_utc="2026-04-30T00:00:00Z",
                    tenant_id="tenant1",
                    collector_identity="unit-test",
                    permission_context="app-only",
                    raw_artifact_path="artifacts/example.json",
                    content_hash="1" * 64,
                    normalized_facts=facts,
                    limitations=["zero_content_scope"],
                )
                with self.assertRaises(ValueError):
                    evidence.validate()

    def test_control_check_using_api_connectivity_only_evidence_requires_scope_limitation(self) -> None:
        evidence = EvidenceItem(
            evidence_id="ev-api",
            assessment_run_id="run1",
            evidence_type=EvidenceType.RAW_API_RESPONSE,
            source_system="Microsoft Graph",
            source_endpoint_or_ui_path="/security/cases/ediscoveryCases/{id}/searches",
            collection_method="assessor-approved bounded validation",
            collected_at_utc="2026-04-30T00:00:00Z",
            tenant_id="tenant1",
            collector_identity="unit-test",
            permission_context="app-only",
            raw_artifact_path="artifacts/example.json",
            content_hash="1" * 64,
            normalized_facts={
                "validation_scope": "api_connectivity_only",
                "content_scope": "none",
                "source_binding": "none",
                "export_performed": False,
                "purge_performed": False,
            },
            limitations=["zero_content_scope"],
        )
        check = ControlCheck(
            control_check_id="EDISC-002.test",
            assessment_run_id="run1",
            control_family="eDiscovery",
            control_objective="API reachability signal only",
            expected_state="No-source validation succeeds",
            assessed_scope="API connectivity only",
            procedure="fixture",
            required_evidence_types=[EvidenceType.RAW_API_RESPONSE],
            evidence_items_used=["ev-api"],
            observed_state="No-source validation succeeded",
            status=ControlStatus.WARN,
            status_reason="API reachability observed; content-bound readiness not assessed.",
            evidence_completeness=EvidenceCompleteness.PARTIAL,
        )
        run = AssessmentRun("run1", "tenant1", "2026-04-30T00:00:00Z", "unit-test", "0.1.0")
        pack = EvidencePack("pack1", run, [evidence], [check])

        with self.assertRaises(ValueError):
            validate_evidence_pack(pack)

        check.limitations.append("zero_content_scope")
        validate_evidence_pack(pack)

    def test_mailbox_location_zero_result_validation_cannot_be_pass(self) -> None:
        evidence = EvidenceItem(
            evidence_id="ev-mailbox-zero",
            assessment_run_id="run1",
            evidence_type=EvidenceType.RAW_API_RESPONSE,
            source_system="Purview eDiscovery",
            source_endpoint_or_ui_path="ComplianceSearch",
            collection_method="assessor-approved mailbox-location validation",
            collected_at_utc="2026-04-30T00:00:00Z",
            tenant_id="tenant1",
            collector_identity="unit-test",
            permission_context="delegated admin search-only session",
            raw_artifact_path="artifacts/example.json",
            content_hash="2" * 64,
            normalized_facts={
                "validation_scope": "mailbox_location_validation",
                "outcome_status": "zero_result",
                "content_scope": "zero_result",
                "source_binding": "exchange_mailbox_location",
                "result_item_count": 0,
                "result_size": 0,
                "query_syntax_accepted": True,
                "query_string": "(ItemClass=IPM.SkypeTeams.Message.Copilot.BizChat)",
                "query_execution_id": "20260430T123734Z-mailbox-bound-copilot-bizchat",
                "export_performed": False,
                "purge_performed": False,
                "hold_changes_performed": False,
                "custodian_source_binding_performed": False,
            },
            limitations=["partial_scope", "sampled", "zero_result", "no_positive_hit", "no_export_validation"],
        )
        evidence.validate()

        check = ControlCheck(
            control_check_id="EDISC-002.test",
            assessment_run_id="run1",
            control_family="eDiscovery",
            control_objective="Mailbox-location Copilot data search validation",
            expected_state="Permitted test search supports readiness",
            assessed_scope="Single mailbox and exact Copilot BizChat ItemClass query",
            procedure="fixture",
            required_evidence_types=[EvidenceType.RAW_API_RESPONSE],
            evidence_items_used=["ev-mailbox-zero"],
            observed_state="Search completed with zero items.",
            status=ControlStatus.PASS,
            status_reason="Incorrect overclaim for test coverage.",
            evidence_completeness=EvidenceCompleteness.PARTIAL,
            limitations=["partial_scope", "sampled", "zero_result", "no_positive_hit", "no_export_validation"],
        )
        run = AssessmentRun("run1", "tenant1", "2026-04-30T00:00:00Z", "unit-test", "0.1.0")
        pack = EvidencePack("pack1", run, [evidence], [check])

        with self.assertRaises(ValueError):
            validate_evidence_pack(pack)

        check.status = ControlStatus.WARN
        check.status_reason = "Mailbox-location search completed, but zero results make readiness inconclusive."
        validate_evidence_pack(pack)

    def test_mailbox_location_zero_result_validation_requires_reproducible_query_and_limits(self) -> None:
        facts = {
            "validation_scope": "mailbox_location_validation",
            "outcome_status": "zero_result",
            "content_scope": "zero_result",
            "source_binding": "exchange_mailbox_location",
            "result_item_count": 0,
            "result_size": 0,
            "query_syntax_accepted": True,
            "export_performed": False,
            "purge_performed": False,
            "hold_changes_performed": False,
            "custodian_source_binding_performed": False,
        }
        evidence = EvidenceItem(
            evidence_id="ev-mailbox-zero",
            assessment_run_id="run1",
            evidence_type=EvidenceType.RAW_API_RESPONSE,
            source_system="Purview eDiscovery",
            source_endpoint_or_ui_path="ComplianceSearch",
            collection_method="assessor-approved mailbox-location validation",
            collected_at_utc="2026-04-30T00:00:00Z",
            tenant_id="tenant1",
            collector_identity="unit-test",
            permission_context="delegated admin search-only session",
            raw_artifact_path="artifacts/example.json",
            content_hash="2" * 64,
            normalized_facts=facts,
            limitations=["partial_scope", "sampled", "zero_result", "no_positive_hit", "no_export_validation"],
        )
        with self.assertRaises(ValueError):
            evidence.validate()

        evidence.normalized_facts["query_string"] = "(ItemClass=IPM.SkypeTeams.Message.Copilot.BizChat)"
        evidence.normalized_facts["query_execution_id"] = "20260430T123734Z-mailbox-bound-copilot-bizchat"
        evidence.limitations.remove("no_positive_hit")
        with self.assertRaises(ValueError):
            evidence.validate()

        evidence.limitations.append("no_positive_hit")
        evidence.validate()

    def test_ediscovery_not_accessible_with_purview_rbac_gap_is_valid(self) -> None:
        evidence = EvidenceItem(
            evidence_id="ev-edisc-denied",
            assessment_run_id="run1",
            evidence_type=EvidenceType.PERMISSION_DENIAL,
            source_system="Microsoft Graph",
            source_endpoint_or_ui_path="/security/cases/ediscoveryCases",
            collection_method="fixture",
            collected_at_utc="2026-04-30T00:00:00Z",
            tenant_id="tenant1",
            collector_identity="unit-test",
            permission_context="app-only token contains eDiscovery.Read.All",
            raw_artifact_path="artifacts/example.json",
            content_hash="3" * 64,
            normalized_facts={"http_status": 401, "graph_role_present": "eDiscovery.Read.All"},
            limitations=["permission_gap", "purview_rbac_gap", "prerequisite_missing"],
        )
        check = ControlCheck(
            control_check_id="EDISC-002.permission_probe",
            assessment_run_id="run1",
            control_family="eDiscovery",
            control_objective="eDiscovery case endpoint accessibility",
            expected_state="Assessment identity can read case visibility signal",
            assessed_scope="Graph eDiscovery case-list endpoint",
            procedure="fixture",
            required_evidence_types=[EvidenceType.PERMISSION_DENIAL],
            evidence_items_used=["ev-edisc-denied"],
            observed_state="Graph role present but eDiscovery cases endpoint returned unauthorized.",
            status=ControlStatus.NOT_ACCESSIBLE,
            status_reason="Purview app-only RBAC prerequisite is missing or unverified.",
            evidence_completeness=EvidenceCompleteness.NONE,
            limitations=["permission_gap", "purview_rbac_gap", "prerequisite_missing"],
        )
        run = AssessmentRun("run1", "tenant1", "2026-04-30T00:00:00Z", "unit-test", "0.1.0")
        validate_evidence_pack(EvidencePack("pack1", run, [evidence], [check]))

    def test_ediscovery_pass_requires_export_validating_evidence_for_mailbox_validation(self) -> None:
        search_evidence = EvidenceItem(
            evidence_id="ev-mailbox-positive-no-export",
            assessment_run_id="run1",
            evidence_type=EvidenceType.RAW_API_RESPONSE,
            source_system="Purview eDiscovery",
            source_endpoint_or_ui_path="ComplianceSearch",
            collection_method="fixture",
            collected_at_utc="2026-04-30T00:00:00Z",
            tenant_id="tenant1",
            collector_identity="unit-test",
            permission_context="delegated admin search-only session",
            raw_artifact_path="artifacts/example.json",
            content_hash="4" * 64,
            normalized_facts={
                "validation_scope": "mailbox_location_validation",
                "outcome_status": "positive_result",
                "content_scope": "metadata_count_only",
                "source_binding": "exchange_mailbox_location",
                "result_item_count": 1,
                "result_size": 1024,
                "query_syntax_accepted": True,
                "query_string": "(ItemClass=IPM.SkypeTeams.Message.Copilot.BizChat)",
                "query_execution_id": "fixture-positive",
                "export_performed": False,
                "purge_performed": False,
                "hold_changes_performed": False,
                "custodian_source_binding_performed": False,
            },
            limitations=["partial_scope", "sampled", "no_export_validation"],
        )
        check = ControlCheck(
            control_check_id="EDISC-002.export_probe",
            assessment_run_id="run1",
            control_family="eDiscovery",
            control_objective="eDiscovery search and export readiness",
            expected_state="Positive search and export-validating evidence exist",
            assessed_scope="Single mailbox",
            procedure="fixture",
            required_evidence_types=[EvidenceType.RAW_API_RESPONSE],
            evidence_items_used=["ev-mailbox-positive-no-export"],
            observed_state="Positive search count exists but no export validation was provided.",
            status=ControlStatus.PASS,
            status_reason="Incorrect overclaim without export validation.",
            evidence_completeness=EvidenceCompleteness.PARTIAL,
        )
        run = AssessmentRun("run1", "tenant1", "2026-04-30T00:00:00Z", "unit-test", "0.1.0")
        with self.assertRaises(ValueError):
            validate_evidence_pack(EvidencePack("pack1", run, [search_evidence], [check]))

        export_evidence = EvidenceItem(
            evidence_id="ev-export",
            assessment_run_id="run1",
            evidence_type=EvidenceType.REPORT_EXPORT,
            source_system="Purview eDiscovery",
            source_endpoint_or_ui_path="ComplianceSearch export artifact",
            collection_method="customer-provided fixture",
            collected_at_utc="2026-04-30T00:00:00Z",
            tenant_id="tenant1",
            collector_identity="unit-test",
            permission_context="customer provided",
            raw_artifact_path="artifacts/example-export.zip",
            content_hash="5" * 64,
            normalized_facts={"customer_provided_purview_export": True},
        )
        check.evidence_items_used.append("ev-export")
        check.evidence_completeness = EvidenceCompleteness.FULL
        validate_evidence_pack(EvidencePack("pack1", run, [search_evidence, export_evidence], [check]))


if __name__ == "__main__":
    unittest.main()
