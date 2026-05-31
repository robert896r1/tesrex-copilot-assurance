"""Human-facing explanation text for each control check.

This module turns existing control-check fields into reviewer breadcrumbs. It does not add workflow state, owners, due dates, or remediation tracking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ControlBreadcrumbs:
    what_found: str
    why_this_appears: str
    why_it_matters: str
    next_evidence_step: str


def control_breadcrumbs(control: Any) -> ControlBreadcrumbs:
    """Return human-readable explanation breadcrumbs for a control check.

    This is intentionally presentation logic over existing evidence-pack fields.
    It does not add remediation workflow state, ownership, or closure tracking.
    """

    control_id = _field(control, "control_check_id")
    family = _field(control, "control_family").upper()
    status = _field(control, "status").upper() or "UNKNOWN"
    cause = _field(control, "status_cause") or "unknown"
    reason = _field(control, "status_reason") or "No status reason was provided."
    limitations = set(_list_field(control, "limitations"))
    follow_up = _useful_follow_up(_list_field(control, "follow_up_required"))

    what_found = _what_found(control_id, family, status, cause, limitations)
    why_it_matters = _why_it_matters(control_id, family, status, cause, limitations)
    next_step = follow_up or _next_evidence_step(control_id, family, status, cause, limitations)

    return ControlBreadcrumbs(
        what_found=what_found,
        why_this_appears=reason,
        why_it_matters=why_it_matters,
        next_evidence_step=next_step,
    )


def _field(control: Any, name: str) -> str:
    if isinstance(control, dict):
        value = control.get(name)
    else:
        value = getattr(control, name, "")
    return _value(value)


def _list_field(control: Any, name: str) -> list[str]:
    if isinstance(control, dict):
        value = control.get(name)
    else:
        value = getattr(control, name, [])
    if not value:
        return []
    return [_value(item) for item in value if _value(item).strip()]


def _value(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _useful_follow_up(items: list[str]) -> str:
    for item in items:
        text = item.strip()
        if not text:
            continue
        lowered = text.lower()
        if lowered.startswith("review limitations for ") and "rerun after evidence gap" in lowered:
            continue
        if lowered.startswith("provide manual/customer evidence for ") and "relevant read-only collector" in lowered:
            continue
        return text
    return ""


def _what_found(control_id: str, family: str, status: str, cause: str, limitations: set[str]) -> str:
    if status == "PASS":
        return "The report found enough evidence to support this control for the assessed scope."
    if status == "NOT_ACCESSIBLE" or cause == "permission_gap":
        return "The report could not read the Microsoft source needed to verify this control."
    if status == "NOT_LICENSED" or cause == "not_licensed":
        return "The required Microsoft capability appears unavailable in the assessed licensing evidence."
    if status == "FAIL" or cause == "tenant_gap":
        return "The report found evidence that the expected tenant control state is not met."
    if control_id.startswith("EDISC-002"):
        return "eDiscovery is reachable, but Copilot data discovery/export readiness is not proven."
    if control_id.startswith("EDISC-001"):
        return "The report does not yet have enough retention-policy evidence for Copilot or AI-related data."
    if family == "DLP":
        return "DLP policy/rule inventory was not collected, so Copilot DLP coverage is not proven."
    if family == "SAM":
        return "SharePoint sharing governance tooling is available locally, but tenant oversharing evidence was not collected."
    if family == "AUD":
        return "Audit capability signals are present, but audit evidence for this control is not complete."
    if family == "LABEL":
        return "Sensitivity-label evidence is partial, so label taxonomy or coverage is not fully proven."
    if "manual_only" in limitations or cause == "manual_evidence_required":
        return "The report needs customer-provided evidence before this control can be verified."
    if cause == "unsupported_api":
        return "The report reached a Microsoft API/support boundary for this control."
    if cause == "usage_absence":
        return "The report did not have relevant usage evidence for this control."
    return "The report collected partial evidence, but this control is not fully proven."


def _why_it_matters(control_id: str, family: str, status: str, cause: str, limitations: set[str]) -> str:
    if status == "PASS":
        return "This gives reviewers a defensible evidence point to retain for the audit trail."
    if status == "NOT_ACCESSIBLE" or cause == "permission_gap":
        return "The tenant may still have the control, but the assessment cannot prove it until access is corrected."
    if status == "NOT_LICENSED" or cause == "not_licensed":
        return "Controls that depend on unavailable licensing cannot be treated as implemented from this evidence pack."
    if status == "FAIL" or cause == "tenant_gap":
        return "This is a likely tenant control gap and should be reviewed before relying on Copilot governance posture."
    if control_id.startswith("EDISC-002"):
        return "This limits confidence that Copilot interaction data can be discovered and produced for investigation or audit."
    if control_id.startswith("EDISC-001"):
        return "Without retention evidence, reviewers cannot confirm how Copilot or AI-related records would be preserved."
    if family == "DLP":
        return "Without policy and rule evidence, reviewers cannot confirm whether Copilot-related activity is covered by expected data-loss controls."
    if family == "SAM":
        return "Without sharing and oversharing evidence, reviewers cannot judge whether Copilot could expose broadly shared content."
    if family == "AUD":
        return "Without audit evidence, reviewers cannot confirm that Copilot activity can be monitored or investigated."
    if family == "LABEL":
        return "Without label evidence, reviewers cannot confirm that sensitive content has the classification baseline expected for Copilot governance."
    if "manual_only" in limitations or cause == "manual_evidence_required":
        return "The assessment cannot distinguish a tenant gap from a missing evidence artifact until manual proof is supplied."
    if cause == "unsupported_api":
        return "A Microsoft API limitation means the control may need portal export, screenshot, or customer-attested evidence."
    if cause == "usage_absence":
        return "Without relevant activity, the report cannot prove how the control behaves in real Copilot use."
    return "Reviewers should not treat this as verified assurance until the missing evidence is supplied."


def _next_evidence_step(control_id: str, family: str, status: str, cause: str, limitations: set[str]) -> str:
    if status == "PASS":
        return "No action required; retain linked evidence for the audit trail."
    if status == "NOT_ACCESSIBLE" or cause == "permission_gap":
        return "Grant the least-privilege reader permission for the source, then rerun the assessment."
    if status == "NOT_LICENSED" or cause == "not_licensed":
        return "Confirm licensing in Microsoft 365 admin evidence, or remove this control from the active baseline."
    if status == "FAIL" or cause == "tenant_gap":
        return "Review the Microsoft control configuration, remediate the tenant gap, and rerun the assessment."
    if control_id.startswith("EDISC-002"):
        return "Provide existing Purview eDiscovery evidence, or approve a bounded validation procedure for a scoped mailbox/site."
    if control_id.startswith("EDISC-001"):
        return "Provide retention-policy evidence from Purview, or approve the relevant read-only retention evidence collector."
    if family == "DLP":
        return "Provide Purview DLP policy/rule export, or approve the read-only DLP inventory collector."
    if family == "SAM":
        return "Provide a current SharePoint Advanced Management/DAG export, or approve the read-only sharing evidence collector."
    if family == "AUD":
        return "Provide Purview audit evidence, or approve a bounded read-only audit query for the relevant Copilot activity."
    if family == "LABEL":
        return "Provide sensitivity-label taxonomy/coverage export, or approve the relevant read-only label collector."
    if "manual_only" in limitations or cause == "manual_evidence_required":
        return "Attach the required Microsoft export, screenshot, or customer-approved evidence artifact."
    if cause == "unsupported_api":
        return "Provide Microsoft portal/export evidence for this control until a supported API path exists."
    if cause == "usage_absence":
        return "Rerun after relevant activity exists, or provide a bounded usage sample approved for assessment."
    return "Provide supported Microsoft evidence for this control, then rerun the evidence pack."
