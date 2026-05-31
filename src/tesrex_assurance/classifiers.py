"""Conservative classifiers for Microsoft control evidence.

Classifiers should prefer UNKNOWN/WARN over false certainty when mappings are stale, inputs are partial, or Microsoft evidence is ambiguous."""

from __future__ import annotations

import re
from typing import Any

from .mappings import LoadedMapping, parse_assessment_date
from .models import ControlCheck, ControlStatus, EvidenceCompleteness, EvidenceType

ACCESS_DENIAL_MARKERS = (
    "401",
    "403",
    "authorization_requestdenied",
    "access denied",
    "insufficient privileges",
    "missing consent",
    "rbac",
    "unauthorized",
    "forbidden",
)
DISABLED_PLAN_STATES = {"disabled", "suspended", "deleted"}


def classify_subscribed_skus_response(
    response_or_error: dict[str, Any] | list[dict[str, Any]],
    capability_map: LoadedMapping,
    capability_key: str,
    assessment_date: str,
    assessment_run_id: str = "fixture-run",
    evidence_items_used: list[str] | None = None,
    independent_verification: bool = False,
) -> ControlCheck:
    """Classify a license/capability check from Graph subscribedSkus-like evidence.

    Exact mapping matches can PASS only when the mapping is fresh or independently verified.
    Fallback matches never PASS and never NOT_LICENSED; they produce WARN/manual review.
    Missing matches cannot produce NOT_LICENSED while the map declares incomplete coverage.
    """

    evidence_items_used = evidence_items_used or []
    assessment_day = parse_assessment_date(assessment_date)
    version = capability_map.version(assessment_day)
    limitations: list[str] = []
    follow_up: list[str] = []

    if _looks_like_access_denial(response_or_error):
        return _license_check(
            capability_key,
            assessment_run_id,
            evidence_items_used,
            ControlStatus.NOT_ACCESSIBLE,
            "License inventory could not be read due to access, RBAC, consent, or authorization denial.",
            EvidenceCompleteness.NONE,
            ["permission_gap"],
            ["Grant least-privilege Graph license-reading access and rerun."],
            version,
        )

    skus = _extract_skus(response_or_error)
    if skus is None:
        return _license_check(
            capability_key,
            assessment_run_id,
            evidence_items_used,
            ControlStatus.UNKNOWN,
            "License inventory response could not be interpreted as subscribedSkus evidence.",
            EvidenceCompleteness.NONE,
            ["api_unsupported"],
            ["Retain raw response and update parser or provide manual license artifact."],
            version,
        )

    stale = capability_map.is_stale(assessment_day)
    if stale:
        limitations.append("stale_mapping")

    capability = capability_map.data.get("capabilities", {}).get(capability_key)
    if not isinstance(capability, dict):
        return _license_check(
            capability_key,
            assessment_run_id,
            evidence_items_used,
            ControlStatus.UNKNOWN,
            f"Capability key {capability_key} is not present in the capability map.",
            EvidenceCompleteness.PARTIAL,
            limitations + ["license_limited"],
            ["Update versioned capability map before classifying this capability."],
            version,
        )

    exact_matches = _find_exact_license_matches(skus, capability.get("match", {}))
    fallback_matches = _find_fallback_matches(skus, capability.get("fallback_match_strategy") or {})

    if exact_matches:
        if stale and not independent_verification:
            return _license_check(
                capability_key,
                assessment_run_id,
                evidence_items_used,
                ControlStatus.WARN,
                "Exact entitlement match found, but mapping is stale; hard PASS is withheld until mapping is refreshed or independently verified.",
                EvidenceCompleteness.PARTIAL,
                limitations,
                ["Refresh mapping source references or independently verify entitlement."],
                version,
                observed_state={"exact_matches": exact_matches},
            )
        return _license_check(
            capability_key,
            assessment_run_id,
            evidence_items_used,
            ControlStatus.PASS,
            "Required capability entitlement matched a known enabled service plan in the versioned capability map.",
            EvidenceCompleteness.FULL,
            limitations,
            [],
            version,
            observed_state={"exact_matches": exact_matches},
        )

    if fallback_matches:
        return _license_check(
            capability_key,
            assessment_run_id,
            evidence_items_used,
            ControlStatus.WARN,
            "Possible Copilot entitlement matched only conservative fallback patterns; manual review is required and hard NOT_LICENSED is blocked.",
            EvidenceCompleteness.PARTIAL,
            sorted(set(limitations + ["manual_review_required", "license_limited"])),
            ["Review raw SKU/service-plan evidence and update mapping if this is a supported entitlement."],
            version,
            observed_state={"fallback_matches": fallback_matches},
        )

    complete = capability_map.data.get("mapping_completeness", {}).get("claims_complete_coverage") is True
    if complete and not stale:
        return _license_check(
            capability_key,
            assessment_run_id,
            evidence_items_used,
            ControlStatus.NOT_LICENSED,
            "Readable tenant SKU inventory contains no matching entitlement and the mapping claims complete coverage for this capability.",
            EvidenceCompleteness.FULL,
            limitations,
            ["Confirm customer baseline requires this capability before reporting a license gap."],
            version,
            observed_state={"sku_count": len(skus)},
        )

    return _license_check(
        capability_key,
        assessment_run_id,
        evidence_items_used,
        ControlStatus.UNKNOWN,
        "No exact entitlement match found, but the mapping does not claim complete coverage or is stale; license absence is not proven.",
        EvidenceCompleteness.PARTIAL,
        sorted(set(limitations + ["license_limited"])),
        ["Refresh capability map or provide manual/license-admin evidence."],
        version,
        observed_state={"sku_count": len(skus)},
    )


def classify_copilot_dlp_inventory(
    policy_rule_export: dict[str, Any],
    dlp_map: LoadedMapping,
    assessment_date: str,
    assessment_run_id: str = "fixture-run",
    evidence_items_used: list[str] | None = None,
    baseline_required: bool = True,
    license_status: ControlStatus | str | None = None,
    independent_verification: bool = False,
) -> ControlCheck:
    """Classify DLP for Copilot inventory evidence.

    Hard FAIL requires readable inventory, schema validation, baseline requirement, and no high-strength
    or manual-review Copilot targeting evidence. Stale mappings and schema drift block hard FAIL.
    """

    evidence_items_used = evidence_items_used or []
    assessment_day = parse_assessment_date(assessment_date)
    version = dlp_map.version(assessment_day)
    limitations: list[str] = []

    if _looks_like_access_denial(policy_rule_export):
        return _dlp_check(
            assessment_run_id,
            evidence_items_used,
            ControlStatus.NOT_ACCESSIBLE,
            "DLP policy/rule inventory could not be read due to access, RBAC, consent, or authorization denial.",
            EvidenceCompleteness.NONE,
            ["permission_gap"],
            ["Grant least-privilege Purview/Security & Compliance policy-read access and rerun."],
            version,
        )

    if _status_value(license_status) == ControlStatus.NOT_LICENSED:
        return _dlp_check(
            assessment_run_id,
            evidence_items_used,
            ControlStatus.NOT_LICENSED,
            "Readable entitlement evidence indicates required DLP for Copilot capability is absent.",
            EvidenceCompleteness.NONE,
            ["license_gap"],
            ["Confirm licensing or exclude DLP for Copilot from the assessment baseline."],
            version,
        )

    schema_ok, schema_reason = _validate_dlp_export_schema(policy_rule_export)
    if not schema_ok:
        return _dlp_check(
            assessment_run_id,
            evidence_items_used,
            ControlStatus.UNKNOWN,
            schema_reason,
            EvidenceCompleteness.NONE,
            ["api_unsupported"],
            ["Retain raw policy/rule export and update DLP parser or provide manual Purview export."],
            version,
        )

    stale = dlp_map.is_stale(assessment_day)
    if stale:
        limitations.append("stale_mapping")

    policies = policy_rule_export.get("policies", [])
    exact = []
    review = []
    for policy in policies:
        strength = _match_dlp_policy(policy, dlp_map)
        if strength == "high":
            exact.append(policy.get("name") or policy.get("Name") or policy.get("id") or "unnamed-policy")
        elif strength in {"medium", "low"}:
            review.append(policy.get("name") or policy.get("Name") or policy.get("id") or "unnamed-policy")

    if exact:
        if stale and not independent_verification:
            return _dlp_check(
                assessment_run_id,
                evidence_items_used,
                ControlStatus.WARN,
                "Copilot-targeted DLP policy evidence was found, but mapping is stale; hard PASS is withheld until mapping is refreshed or independently verified.",
                EvidenceCompleteness.PARTIAL,
                limitations,
                ["Refresh DLP location mapping or independently verify Purview location metadata."],
                version,
                observed_state={"exact_copilot_policy_matches": exact},
            )
        return _dlp_check(
            assessment_run_id,
            evidence_items_used,
            ControlStatus.PASS,
            "Readable DLP policy inventory contains a high-strength Microsoft 365 Copilot/Copilot Chat location match.",
            EvidenceCompleteness.FULL,
            limitations,
            [],
            version,
            observed_state={"exact_copilot_policy_matches": exact},
        )

    if review:
        return _dlp_check(
            assessment_run_id,
            evidence_items_used,
            ControlStatus.WARN,
            "Possible Copilot-targeted DLP policy evidence found only through pattern/display/enforcement-plane matching; manual review is required.",
            EvidenceCompleteness.PARTIAL,
            sorted(set(limitations + ["manual_review_required"])),
            ["Review raw DLP policy/rule export and update DLP location mapping if confirmed."],
            version,
            observed_state={"manual_review_policy_matches": review},
        )

    if stale and not independent_verification:
        return _dlp_check(
            assessment_run_id,
            evidence_items_used,
            ControlStatus.UNKNOWN,
            "No Copilot DLP location was recognized, but the DLP mapping is stale; hard FAIL is blocked.",
            EvidenceCompleteness.PARTIAL,
            sorted(set(limitations + ["stale_mapping"])),
            ["Refresh DLP location mapping and rerun before treating absence as a control gap."],
            version,
            observed_state={"policy_count": len(policies)},
        )

    if baseline_required:
        return _dlp_check(
            assessment_run_id,
            evidence_items_used,
            ControlStatus.FAIL,
            "DLP policy/rule schema is readable and validated, baseline requires Copilot DLP, and no Copilot-targeted policy location was found.",
            EvidenceCompleteness.FULL,
            limitations,
            ["Create or evidence Copilot-targeted DLP policy coverage, or revise customer baseline."],
            version,
            observed_state={"policy_count": len(policies)},
        )

    return _dlp_check(
        assessment_run_id,
        evidence_items_used,
        ControlStatus.UNKNOWN,
        "DLP policy/rule schema is readable, but no Copilot-targeted policy was found and no baseline requirement was supplied.",
        EvidenceCompleteness.PARTIAL,
        limitations + ["not_configured_for_assessment"],
        ["Confirm whether Copilot-targeted DLP is required in the customer baseline."],
        version,
        observed_state={"policy_count": len(policies)},
    )


def _license_check(
    capability_key: str,
    assessment_run_id: str,
    evidence_items_used: list[str],
    status: ControlStatus,
    reason: str,
    completeness: EvidenceCompleteness,
    limitations: list[str],
    follow_up: list[str],
    version,
    observed_state: dict[str, Any] | None = None,
) -> ControlCheck:
    check = ControlCheck(
        control_check_id=capability_key.split(".", 1)[0],
        assessment_run_id=assessment_run_id,
        control_family="LIC",
        control_objective="Classify Microsoft capability entitlement from tenant SKU inventory.",
        expected_state="Required entitlement evidence is present or absence is explicitly proven.",
        assessed_scope="tenant",
        procedure="Evaluate Microsoft Graph subscribedSkus evidence against the versioned capability map.",
        required_evidence_types=[EvidenceType.LICENSE_SNAPSHOT, EvidenceType.RAW_API_RESPONSE],
        evidence_items_used=evidence_items_used,
        observed_state=str(observed_state or {}),
        status=status,
        status_reason=reason,
        evidence_completeness=completeness,
        limitations=limitations,
        follow_up_required=follow_up,
        mapping_versions_used=[version],
    )
    check.validate()
    return check


def _dlp_check(
    assessment_run_id: str,
    evidence_items_used: list[str],
    status: ControlStatus,
    reason: str,
    completeness: EvidenceCompleteness,
    limitations: list[str],
    follow_up: list[str],
    version,
    observed_state: dict[str, Any] | None = None,
) -> ControlCheck:
    check = ControlCheck(
        control_check_id="DLP-001",
        assessment_run_id=assessment_run_id,
        control_family="DLP",
        control_objective="Determine whether DLP policies targeting Microsoft 365 Copilot and Copilot Chat can be inventoried.",
        expected_state="Copilot-targeted DLP policy inventory is readable and classifiable.",
        assessed_scope="tenant",
        procedure="Evaluate Security & Compliance policy/rule export against versioned DLP Copilot location mapping.",
        required_evidence_types=[EvidenceType.POLICY_SNAPSHOT, EvidenceType.RAW_API_RESPONSE],
        evidence_items_used=evidence_items_used,
        observed_state=str(observed_state or {}),
        status=status,
        status_reason=reason,
        evidence_completeness=completeness,
        limitations=limitations,
        follow_up_required=follow_up,
        mapping_versions_used=[version],
    )
    check.validate()
    return check


def _looks_like_access_denial(value: Any) -> bool:
    if isinstance(value, list):
        return False
    if not isinstance(value, dict):
        text = str(value).lower()
        return any(marker in text for marker in ACCESS_DENIAL_MARKERS)

    # Successful payloads can contain marker-like substrings inside GUIDs or object names
    # (for example a servicePlanId segment containing "403"). Only classify access denial
    # from explicit error/status fields, not by scanning full successful payloads.
    if "value" in value or "skus" in value or ("policies" in value and "rules" in value):
        return False

    status = value.get("status") or value.get("status_code") or value.get("statusCode")
    if str(status) in {"401", "403"}:
        return True

    error = value.get("error")
    if isinstance(error, dict):
        text = " ".join(str(error.get(key, "")) for key in ["code", "message", "innerError", "details"]).lower()
        return any(marker in text for marker in ACCESS_DENIAL_MARKERS)
    if isinstance(error, str):
        return any(marker in error.lower() for marker in ACCESS_DENIAL_MARKERS)

    text = " ".join(str(value.get(key, "")) for key in ["code", "message", "error_description"]).lower()
    return any(marker in text for marker in ACCESS_DENIAL_MARKERS)


def _extract_skus(value: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    if isinstance(value, list):
        return value if all(isinstance(item, dict) for item in value) else None
    if not isinstance(value, dict):
        return None
    if isinstance(value.get("value"), list):
        return value["value"]
    if isinstance(value.get("skus"), list):
        return value["skus"]
    return None


def _find_exact_license_matches(skus: list[dict[str, Any]], match: dict[str, Any]) -> list[dict[str, str]]:
    if not match:
        return []
    ids = set(match.get("any_servicePlanId") or [])
    names = {str(name).lower() for name in (match.get("any_servicePlanName") or [])}
    if match.get("servicePlanId"):
        ids.add(match["servicePlanId"])
    if match.get("servicePlanName"):
        names.add(str(match["servicePlanName"]).lower())

    found: list[dict[str, str]] = []
    for sku in skus:
        if str(sku.get("capabilityStatus", "")).lower() != "enabled":
            continue
        for plan in sku.get("servicePlans") or []:
            if str(plan.get("provisioningStatus", "")).lower() in DISABLED_PLAN_STATES:
                continue
            plan_id = str(plan.get("servicePlanId", ""))
            plan_name = str(plan.get("servicePlanName", ""))
            if plan_id in ids or plan_name.lower() in names:
                found.append({
                    "skuPartNumber": str(sku.get("skuPartNumber", "")),
                    "servicePlanId": plan_id,
                    "servicePlanName": plan_name,
                })
    return found


def _find_fallback_matches(skus: list[dict[str, Any]], fallback: dict[str, Any]) -> list[dict[str, str]]:
    if not fallback.get("enabled"):
        return []
    sku_patterns = [re.compile(p) for p in fallback.get("match_any_skuPartNumber_regex") or []]
    plan_patterns = [re.compile(p) for p in fallback.get("match_any_servicePlanName_regex") or []]
    found: list[dict[str, str]] = []
    for sku in skus:
        sku_part = str(sku.get("skuPartNumber", ""))
        if any(pattern.search(sku_part) for pattern in sku_patterns):
            found.append({"skuPartNumber": sku_part, "match": "skuPartNumber"})
        for plan in sku.get("servicePlans") or []:
            plan_name = str(plan.get("servicePlanName", ""))
            if any(pattern.search(plan_name) for pattern in plan_patterns):
                found.append({"skuPartNumber": sku_part, "servicePlanName": plan_name, "match": "servicePlanName"})
    return found


def _validate_dlp_export_schema(export: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(export, dict):
        return False, "DLP export is not an object and cannot be interpreted."
    if "policies" not in export or "rules" not in export:
        return False, "DLP export missing expected policies/rules collections; schema cannot be validated."
    if not isinstance(export["policies"], list) or not isinstance(export["rules"], list):
        return False, "DLP export policies/rules fields are not arrays; schema cannot be validated."
    for idx, policy in enumerate(export["policies"]):
        if not isinstance(policy, dict):
            return False, f"DLP policy at index {idx} is not an object."
        if not any(key in policy for key in ["locations", "Location", "workload", "Workload", "applications"]):
            return False, f"DLP policy at index {idx} lacks recognizable location/workload metadata."
    return True, "DLP export schema validated for starter-kit parser."


def _match_dlp_policy(policy: dict[str, Any], dlp_map: LoadedMapping) -> str | None:
    text = str(policy)
    locations = dlp_map.data.get("known_locations", [])
    for loc in locations:
        guid = str(loc.get("location_guid", ""))
        workload = str(loc.get("workload", ""))
        if guid and guid in text and workload and workload.lower() in text.lower():
            return "high"
        if any(str(plane) in text for plane in loc.get("enforcement_planes", [])):
            return "medium"
        if any(str(name).lower() in text.lower() for name in loc.get("display_names", [])):
            return "low"
    if "applications" in text.lower() and any(token in text.lower() for token in ["copilot", "copilotexperiences", " ai"]):
        return "medium"
    return None


def _status_value(status: ControlStatus | str | None) -> ControlStatus | None:
    if status is None:
        return None
    if isinstance(status, ControlStatus):
        return status
    return ControlStatus(str(status))
