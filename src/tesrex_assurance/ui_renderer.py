"""Static HTML evidence-pack renderer.

The renderer is intentionally self-contained so users can open or host a generated report without a web framework or external frontend build step."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

from .breadcrumbs import control_breadcrumbs

STATUS_META = {
    "PASS": {
        "label": "Verified",
        "canonical": "PASS",
        "icon": "✓",
        "class": "status-verified",
        "meaning": "Evidence was collected and supports the control check.",
    },
    "WARN": {
        "label": "Needs Review",
        "canonical": "WARN",
        "icon": "!",
        "class": "status-gap",
        "meaning": "Evidence indicates a gap, limitation, or configuration requiring review.",
    },
    "UNKNOWN": {
        "label": "Unverified",
        "canonical": "UNKNOWN",
        "icon": "?",
        "class": "status-unverified",
        "meaning": "The control was not proven. This is not the same as a failed control.",
    },
    "NOT_ACCESSIBLE": {
        "label": "Access Required",
        "canonical": "NOT_ACCESSIBLE",
        "icon": "⊘",
        "class": "status-access",
        "meaning": "The assessment identity does not have enough access to validate the control.",
    },
    "NOT_LICENSED": {
        "label": "Not Licensed",
        "canonical": "NOT_LICENSED",
        "icon": "⌁",
        "class": "status-license",
        "meaning": "The tenant does not appear to have the required Microsoft capability licensed.",
    },
    "FAIL": {
        "label": "Failed",
        "canonical": "FAIL",
        "icon": "×",
        "class": "status-failed",
        "meaning": "Evidence shows the control is not met.",
    },
}

CAUSE_META = {
    "verified": {"label": "Verified evidence", "class": "cause-verified"},
    "tenant_gap": {"label": "Tenant gap", "class": "cause-tenant"},
    "assessment_limitation": {"label": "Assessment limitation", "class": "cause-assessment"},
    "permission_gap": {"label": "Permission gap", "class": "cause-permission"},
    "not_licensed": {"label": "Not licensed", "class": "cause-license"},
    "unsupported_api": {"label": "Unsupported API", "class": "cause-assessment"},
    "usage_absence": {"label": "No usage context", "class": "cause-assessment"},
    "manual_evidence_required": {"label": "Manual evidence required", "class": "cause-manual"},
    "demo_evidence": {"label": "Demo evidence", "class": "cause-demo"},
    "unknown": {"label": "Cause not specified", "class": "cause-unknown"},
}

EVIDENCE_QUALITY_LABELS = {
    "demo_evidence": "Demo evidence attached",
    "demo_only": "Demo evidence attached",
    "synthetic_fixture": "Synthetic evidence",
    "demo_evidence_in_full_check": "Demo evidence attached",
    "manual_evidence_linked": "Manual evidence linked",
    "manual_only": "Manual evidence required",
    "not_configured_for_assessment": "Not collected in this run",
    "partial_scope": "Partial scope",
    "sampled": "Sampled evidence",
    "stale": "Stale evidence",
    "stale_mapping": "Stale mapping",
    "license_limited": "License mapping limited",
    "permission_limited": "Permission limited",
    "no_export_validation": "No export validation",
    "no_positive_hit": "No positive content hit",
    "zero_result": "Zero-result validation",
    "api_unsupported": "API limitation",
    "unsupported_api": "API limitation",
    "raw_retention_unavailable": "Raw artifact not retained",
}

DEMO_LIMITATION_MARKERS = {"demo_evidence", "demo_only", "synthetic_fixture", "demo_evidence_in_full_check"}
EVIDENCE_QUALITY_PRIORITY = {
    "raw_retention_unavailable": 95,
    "stale": 90,
    "stale_mapping": 88,
    "permission_limited": 85,
    "license_limited": 82,
    "api_unsupported": 80,
    "unsupported_api": 80,
    "not_configured_for_assessment": 75,
    "manual_only": 70,
    "no_export_validation": 65,
    "no_positive_hit": 62,
    "zero_result": 60,
    "partial_scope": 55,
    "sampled": 50,
    "manual_evidence_linked": 30,
    "demo_evidence": 10,
    "demo_only": 10,
    "synthetic_fixture": 10,
    "demo_evidence_in_full_check": 10,
}

STATUS_ORDER = ["PASS", "WARN", "UNKNOWN", "NOT_ACCESSIBLE", "NOT_LICENSED", "FAIL"]
STATUS_PRIORITY = {"FAIL": 60, "NOT_ACCESSIBLE": 50, "WARN": 40, "UNKNOWN": 30, "NOT_LICENSED": 20, "PASS": 10}
SEVERITY_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "informational": 1}

FAMILY_META = {
    "LIC": {
        "name": "Entitlement & Licensing",
        "summary": "Confirms whether the tenant has the Microsoft service plans needed for Copilot governance assessment.",
    },
    "AUD": {
        "name": "Audit & Activity Logging",
        "summary": "Checks whether Copilot activity and audit evidence can be observed for governance review.",
    },
    "LABEL": {
        "name": "Data Classification & Sensitivity",
        "summary": "Reviews whether sensitivity-label taxonomy evidence is available for Copilot data protection assurance.",
    },
    "DLP": {
        "name": "Data Loss Prevention",
        "summary": "Assesses whether DLP policy inventory evidence is available for Copilot-related protection coverage.",
    },
    "SAM": {
        "name": "Advanced Sharing & Oversharing Controls",
        "summary": "Checks readiness evidence for SharePoint sharing and oversharing governance controls.",
    },
    "EDISC": {
        "name": "eDiscovery & Retention Readiness",
        "summary": "Assesses whether eDiscovery and retention evidence is sufficient to support investigation and audit needs.",
    },
    "PACK": {
        "name": "Evidence Integrity & Provenance",
        "summary": "Verifies whether the evidence pack itself contains traceable controls, artifacts, hashes, and limitations.",
    },
}


def render_evidence_pack_html(pack_path: str | Path, output_path: str | Path | None = None) -> Path:
    pack_file = Path(pack_path)
    pack = json.loads(pack_file.read_text(encoding="utf-8"))
    html = render_html(pack)
    out = Path(output_path) if output_path else pack_file.with_name("evidence_pack_ui.html")
    out.write_text(html, encoding="utf-8")
    return out


def render_html(pack: dict[str, Any]) -> str:
    data_json = json.dumps(pack, ensure_ascii=False).replace("</", "<\\/")
    run = pack.get("assessment_run") or {}
    controls = pack.get("control_checks") or []
    findings = sorted(pack.get("findings") or [], key=lambda f: SEVERITY_ORDER.get(str(f.get("severity", "")).lower(), 0), reverse=True)
    findings_by_control = _findings_by_control(findings)
    evidence = pack.get("evidence_items") or []
    status_counts = _canonical_status_counts(controls)
    completeness_counts = _counts(controls, "evidence_completeness")
    default_evidence = evidence[0].get("evidence_id") if evidence else ""
    demo_mode = _has_demo_evidence(pack)

    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<link rel=\"icon\" href=\"data:,\">
<title>{escape(str(pack.get('evidence_pack_id', 'Evidence Pack')))}</title>
<style>
{_css()}
</style>
</head>
<body>
<div class=\"report-shell\">
  <header class=\"report-header\">
    <div class=\"header-copy\">
      <h1>Tesrex Copilot Assurance Report</h1>
      <p class=\"value-prop\">Evidence-backed posture for Microsoft Copilot governance.</p>
      <p>See which Microsoft-native controls are verified, incomplete, inaccessible, not licensed, or waiting on manual evidence — with proof links preserved for review.</p>
      <p class=\"assurance-disclaimer\">Status labels reflect automated check results, not independent audit verification.</p>
      <div class=\"proof-path\" aria-label=\"Report review path\">
        <div><strong>Assess</strong><span>Microsoft-native control state</span></div>
        <div><strong>Explain</strong><span>Why each result appears</span></div>
        <div><strong>Prove</strong><span>Link action to evidence</span></div>
      </div>
      <div class=\"header-actions\">
        <button type=\"button\" id=\"download-json\">Download JSON</button>
        <button type=\"button\" id=\"print-view\">Print</button>
      </div>
    </div>
    <dl class=\"run-meta\">
      {_meta_pair('Pack ID', pack.get('evidence_pack_id'))}
      {_meta_pair('Tenant', run.get('tenant_id'))}
      {_meta_pair('Generated', _fmt_time(run.get('completed_at_utc') or pack.get('generated_at_utc') or pack.get('pack_generated_at_utc')))}
      {_meta_pair('Scope', run.get('scope_summary'))}
    </dl>
  </header>

  {_demo_banner() if demo_mode else ""}

  <section class=\"posture-strip\" aria-label=\"Assessment posture summary\">
    {_status_cards(status_counts, len(controls))}
  </section>

  <section class=\"scope-note\" aria-labelledby=\"scope-title\">
    <div>
      <h2 id=\"scope-title\">Scope & Limitations</h2>
      <p>This assessment reflects the evidence visible to the assessment identity at execution time. Unverified controls identify missing proof, access, licensing, or approved validation evidence; they are not silently treated as failures.</p>
    </div>
    <div class=\"scope-facts\">
      {_field('Run status', run.get('status'), badge='status-verified')}
      {_field('Limitations', ', '.join(run.get('limitations') or ['none']))}
      {_field('Evidence coverage', _coverage_sentence(completeness_counts))}
    </div>
  </section>

  <main class=\"content-grid\">
    <section class=\"main-content\">
      <section class="section" aria-labelledby="domain-title">
        <div class="section-heading">
          <div>
            <h2 id="domain-title">Control Review</h2>
            <p>Controls are the primary review path. Each row connects the status, action, next step, and evidence in the inspector.</p>
          </div>
          <span class="focus-summary" id="focus-summary">Showing all controls</span>
        </div>
        <div class="domain-list" id="domain-list">
          {_domain_cards(controls, findings_by_control)}
        </div>
      </section>
    </section>

    <aside class=\"evidence-panel\" aria-label=\"Evidence inspector\">
      <div class=\"panel-heading\">
        <h2>Evidence Inspector</h2>
        <p>Drill-down proof for auditors and technical assessors.</p>
      </div>
      <section class=\"evidence-detail\" id=\"evidence-detail\" data-default-evidence=\"{escape(str(default_evidence))}\">
        <h3>Select evidence</h3>
        <p class=\"muted\">Choose a finding, control check, or evidence item.</p>
      </section>
      <section class=\"evidence-index\">
        <h3>Evidence Inventory</h3>
        <div class=\"evidence-list\">
          {_evidence_list(evidence)}
        </div>
      </section>
    </aside>
  </main>
</div>
<script id=\"pack-data\" type=\"application/json\">{data_json}</script>
<script>
{_js()}
</script>
</body>
</html>
"""



def _has_demo_evidence(pack: dict[str, Any]) -> bool:
    run = pack.get("assessment_run") or {}
    return "demo_evidence_present" in (run.get("limitations") or [])


def _demo_banner() -> str:
    return """
  <section class="demo-banner" aria-label="Demo evidence warning">
    <strong>DEMO MODE — Sample report disclosure</strong>
    <p>This report includes synthetic or isolated demo evidence. Use it for review and presentation only; it is not representative of production governance posture.</p>
  </section>
"""

def _status_cards(status_counts: dict[str, int], total_controls: int) -> str:
    cards = []
    for status in STATUS_ORDER:
        meta = STATUS_META[status]
        count = status_counts.get(status, 0)
        cards.append(
            f"""
            <button type=\"button\" class=\"posture-card {meta['class']}\" data-focus-status=\"{escape(status)}\" data-status=\"{escape(status)}\">
              <span class=\"status-icon\" aria-hidden=\"true\">{meta['icon']}</span>
              <span class=\"posture-label\">{escape(meta['label'])}</span>
              <strong>{count}</strong>
              <small>{escape(meta['canonical'])}</small>
            </button>
            """
        )
    cards.append(
        f"""
        <div class=\"posture-note\">
          <strong>{total_controls} total checks</strong>
          <span>Click a status to focus matching controls without losing context. <b>No weighted score is applied.</b></span>
          <button type=\"button\" class=\"reset-focus\" data-focus-status=\"ALL\">Reset focus</button>
        </div>
        """
    )
    return "".join(cards)


def _domain_cards(controls: list[dict[str, Any]], findings_by_control: dict[str, list[dict[str, Any]]]) -> str:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for control in controls:
        grouped.setdefault(str(control.get("control_family") or "OTHER"), []).append(control)

    parts: list[str] = []
    for family in sorted(grouped, key=lambda item: _domain_review_sort_key(item, grouped)):
        items = grouped[family]
        meta = _family_meta(family)
        dominant_control = _dominant_control(items)
        dominant_label, dominant_class = _review_badge(dominant_control) if dominant_control else ("Review required", "status-unverified")
        counts = _canonical_status_counts(items)
        statuses = " ".join(str(item.get("status") or "UNKNOWN") for item in items)
        rows = "".join(_control_row(item, findings_by_control.get(str(item.get("control_check_id")), [])) for item in sorted(items, key=_control_review_sort_key))
        parts.append(
            f"""
            <article class=\"domain-card\" data-domain-code=\"{escape(family)}\" data-statuses=\"{escape(statuses)}\">
              <div class=\"domain-card-header\">
                <div>
                  <h3>{escape(meta['name'])}</h3>
                  <p>Control family: {escape(family)}</p>
                </div>
                <span class=\"status-badge {dominant_class}\">{escape(dominant_label)}</span>
              </div>
              <p class=\"domain-summary\">{escape(meta['summary'])}</p>
              <div class=\"domain-counts\">{_domain_counts(counts)}</div>
              <details open>
                <summary>View controls, actions, and evidence links</summary>
                <div class=\"control-list\">{rows}</div>
              </details>
            </article>
            """
        )
    return "".join(parts)


def _review_badge(control: dict[str, Any]) -> tuple[str, str]:
    status = str(control.get("status") or "UNKNOWN")
    cause = str(control.get("status_cause") or "unknown")
    limitations = set(str(item) for item in (control.get("limitations") or []))
    has_demo = bool(limitations.intersection(DEMO_LIMITATION_MARKERS))
    if status == "PASS" and has_demo:
        return ("Demo evidence attached", "status-gap")
    if status == "PASS":
        return ("Verified", "status-verified")
    if status == "NOT_ACCESSIBLE" or cause == "permission_gap":
        return ("Access required", "status-access")
    if status == "NOT_LICENSED" or cause == "not_licensed":
        return ("Licensing required", "status-license")
    if status == "FAIL" or cause == "tenant_gap":
        return ("Tenant action required", "status-failed" if status == "FAIL" else "status-gap")
    if cause == "unsupported_api":
        return ("Microsoft API limitation", "status-unverified")
    if cause == "usage_absence":
        return ("No usage evidence", "status-unverified")
    if cause == "manual_evidence_required":
        return ("Manual evidence required", "status-unverified")
    if cause == "demo_evidence":
        return ("Demo evidence only", "status-gap")
    if cause == "assessment_limitation":
        return ("Not assessed" if status == "UNKNOWN" else "Evidence incomplete", "status-unverified")
    return ("Review required", "status-unverified")


def _meaning_text(control: dict[str, Any]) -> str:
    status = str(control.get("status") or "UNKNOWN")
    cause = str(control.get("status_cause") or "unknown")
    if status == "PASS" and cause == "verified":
        return "Available evidence supports this control for the assessed scope."
    if status == "FAIL" or cause == "tenant_gap":
        return "Collected evidence points to a tenant configuration or control gap that needs remediation."
    if status == "NOT_ACCESSIBLE" or cause == "permission_gap":
        return "The control may exist, but the assessment identity could not read the required source."
    if status == "NOT_LICENSED" or cause == "not_licensed":
        return "The required Microsoft capability appears unavailable or outside the current license baseline."
    if cause == "unsupported_api":
        return "The required evidence is not available through the supported Microsoft API path used by this assessment."
    if cause == "usage_absence":
        return "No relevant activity sample was available, so the control behavior cannot be assessed from usage evidence."
    if cause == "manual_evidence_required":
        return "This control depends on customer/assessor evidence or a separately approved collector."
    if cause == "demo_evidence":
        return "Only demo or synthetic evidence is attached; do not treat this as production assurance."
    if cause == "assessment_limitation":
        return "This does not prove the tenant is misconfigured; the assessment lacks enough supported evidence."
    return "The report cannot classify the reason confidently from the available evidence."


def _next_action_text(control: dict[str, Any]) -> str:
    actions = [str(item) for item in (control.get("follow_up_required") or []) if str(item).strip()]
    if actions:
        return actions[0]
    status = str(control.get("status") or "UNKNOWN")
    cause = str(control.get("status_cause") or "unknown")
    if status == "PASS" and cause == "verified":
        return "No action required; retain linked evidence for the audit trail."
    if cause == "permission_gap":
        return "Grant the least-privilege reader role/permission for this source, then rerun."
    if cause == "not_licensed":
        return "Confirm licensing or remove this control from the assessment baseline."
    if cause == "unsupported_api":
        return "Provide native Microsoft UI/export evidence for this control."
    if cause == "usage_absence":
        return "Provide a bounded usage sample or rerun after relevant activity exists."
    if cause == "tenant_gap":
        return "Remediate the Microsoft control configuration and rerun the assessment."
    return "Review the evidence manually, then decide whether a collector, export, permission, or tenant change is required."


def _responsible_domain(control: dict[str, Any]) -> str:
    family = str(control.get("control_family") or "").upper()
    # Broad domain hint only; this is not an inferred accountable owner.
    return {
        "LIC": "Licensing",
        "AUD": "Audit / Purview",
        "LABEL": "Data protection",
        "DLP": "Data protection",
        "SAM": "SharePoint governance",
        "EDISC": "Compliance / eDiscovery",
        "PACK": "Assessment evidence",
    }.get(family, "Governance review")


def _evidence_quality_tags(control: dict[str, Any]) -> list[str]:
    limitations = [str(item) for item in (control.get("limitations") or [])]
    tags: list[str] = []
    completeness = str(control.get("evidence_completeness") or "")
    if completeness == "partial":
        tags.append("Partial evidence")
    elif completeness == "none":
        tags.append("No usable evidence")

    ordered_limitations = sorted(limitations, key=lambda item: EVIDENCE_QUALITY_PRIORITY.get(item, 0), reverse=True)
    for limitation in ordered_limitations:
        label = EVIDENCE_QUALITY_LABELS.get(limitation)
        if label and label not in tags and len(tags) < 3:
            tags.append(label)

    demo_labels = [EVIDENCE_QUALITY_LABELS[item] for item in limitations if item in DEMO_LIMITATION_MARKERS and item in EVIDENCE_QUALITY_LABELS]
    if demo_labels:
        demo_label = demo_labels[0]
        if demo_label not in tags:
            if len(tags) >= 3:
                tags[-1] = demo_label
            else:
                tags.append(demo_label)
    return tags[:3]


def _quality_tags_html(control: dict[str, Any]) -> str:
    tags = _evidence_quality_tags(control)
    if not tags:
        return ""
    return '<span class="quality-tags">' + "".join(f'<span class="quality-tag">{escape(tag)}</span>' for tag in tags) + "</span>"


def _control_row(control: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    status = str(control.get("status") or "UNKNOWN")
    review_label, review_class = _review_badge(control)
    cause = str(control.get("status_cause") or "unknown")
    cause_meta = CAUSE_META.get(cause, CAUSE_META["unknown"])
    evidence_ids = [str(item) for item in (control.get("evidence_items_used") or [])]
    primary_evidence = evidence_ids[0] if evidence_ids else ""
    evidence_attr = " ".join(evidence_ids)
    finding_ids = " ".join(str(item.get("finding_id")) for item in findings if item.get("finding_id"))
    breadcrumbs = _display_breadcrumbs(control, findings)
    return f"""
    <button type=\"button\" class=\"control-row\" data-status=\"{escape(status)}\" data-cause=\"{escape(cause)}\" data-control-id=\"{escape(str(control.get('control_check_id')))}\" data-evidence-id=\"{escape(str(primary_evidence))}\" data-evidence-ids=\"{escape(evidence_attr)}\" data-finding-ids=\"{escape(finding_ids)}\">
      <span class=\"status-badge {review_class}\">{escape(review_label)}</span>
      <span class=\"control-main\">
        <span class=\"control-title\"><strong>{escape(str(control.get('control_check_id')))}</strong>{_action_chip_html(control, findings)}</span>
        <span><b>What the report found:</b> {escape(breadcrumbs['what_found'])}</span>
        <span><b>Why this appears:</b> {escape(breadcrumbs['why_this_appears'])}</span>
        <span><b>Why this matters:</b> {escape(breadcrumbs['why_it_matters'])}</span>
        <span><b>Next evidence step:</b> {escape(breadcrumbs['next_evidence_step'])}</span>
        {_quality_tags_html(control)}
        <small>Canonical status: {escape(status)} · Cause: <b>{escape(cause_meta['label'])}</b> · Evidence: {escape(str(control.get('evidence_completeness') or 'unknown'))} · Domain: {escape(_responsible_domain(control))}</small>
      </span>
    </button>
    """


def _findings_by_control(findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    mapped: dict[str, list[dict[str, Any]]] = {}
    for finding in findings:
        for control_id in finding.get("related_control_checks") or finding.get("affected_objects") or []:
            mapped.setdefault(str(control_id), []).append(finding)
    return mapped


def _action_chip_html(control: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    if findings:
        severity = str(findings[0].get("severity") or "low").lower()
        return f'<span class="action-chip severity-{escape(severity)}">Action linked</span>'
    if str(control.get("status") or "UNKNOWN") != "PASS":
        return '<span class="action-chip status-unverified">Needs follow-up</span>'
    return ""


def _display_breadcrumbs(control: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, str]:
    breadcrumbs = control_breadcrumbs(control)
    result = {
        "what_found": breadcrumbs.what_found,
        "why_this_appears": breadcrumbs.why_this_appears,
        "why_it_matters": breadcrumbs.why_it_matters,
        "next_evidence_step": breadcrumbs.next_evidence_step,
    }
    if not findings:
        return result
    finding = findings[0]
    if str(finding.get("condition") or "").strip():
        result["what_found"] = str(finding.get("condition")).strip()
    if str(finding.get("impact_or_risk") or "").strip():
        result["why_it_matters"] = str(finding.get("impact_or_risk")).strip()
    if str(finding.get("recommendation") or "").strip():
        result["next_evidence_step"] = str(finding.get("recommendation")).strip()
    return result


def _findings_list(findings: list[dict[str, Any]], controls: list[dict[str, Any]]) -> str:
    if not findings:
        return '<p class="muted">No critical actions required at this time.</p>'
    controls_by_id = {str(control.get("control_check_id")): control for control in controls}
    return "".join(_finding_item(finding, controls_by_id) for finding in findings)


def _finding_item(finding: dict[str, Any], controls_by_id: dict[str, dict[str, Any]]) -> str:
    evidence = finding.get("evidence_references") or []
    primary_evidence = evidence[0] if evidence else ""
    controls = finding.get("related_control_checks") or finding.get("affected_objects") or []
    controls_text = ", ".join(controls) or "No linked controls"
    title = _human_finding_title(finding, controls_by_id)
    severity = str(finding.get("severity", "low")).lower()
    return f"""
    <button type=\"button\" class=\"finding-card\" data-finding-id=\"{escape(str(finding.get('finding_id')))}\" data-evidence-id=\"{escape(str(primary_evidence))}\">
      <span class=\"severity severity-{escape(severity)}\">{escape(severity.upper())}</span>
      <span class=\"finding-content\">
        <strong>{escape(title)}</strong>
        <span><b>Issue:</b> {escape(str(finding.get('condition') or ''))}</span>
        <span><b>Why it matters:</b> {escape(str(finding.get('impact_or_risk') or 'Assessment confidence may be limited.'))}</span>
        <span><b>Recommended action:</b> {escape(str(finding.get('recommendation') or 'Review the linked control and evidence.'))}</span>
        <small>Linked controls: {escape(controls_text)}</small>
      </span>
    </button>
    """


def _human_finding_title(finding: dict[str, Any], controls_by_id: dict[str, dict[str, Any]] | None = None) -> str:
    title = str(finding.get("title") or finding.get("finding_id") or "Finding")
    controls = finding.get("related_control_checks") or finding.get("affected_objects") or []
    if controls:
        first = str(controls[0])
        if ":" in title:
            title_control, title_status = (part.strip() for part in title.split(":", 1))
            if title_control == first and title_status in STATUS_META:
                family = first.split("-", 1)[0]
                control = (controls_by_id or {}).get(first)
                review_label = _review_badge(control)[0] if control else STATUS_META[title_status]["label"]
                return f"{_family_meta(family)['name']}: {review_label}"
    return title


def _evidence_list(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return '<p class="muted">No evidence items.</p>'
    return "".join(
        f"<button type=\"button\" class=\"evidence-link\" data-evidence-id=\"{escape(str(item.get('evidence_id')))}\"><strong>{escape(str(item.get('evidence_id')))}</strong><span>{escape(str(item.get('source_system')))}</span></button>"
        for item in evidence
    )


def _domain_counts(counts: dict[str, int]) -> str:
    parts = []
    for status in STATUS_ORDER:
        value = counts.get(status, 0)
        if not value:
            continue
        meta = STATUS_META[status]
        parts.append(f'<span class="mini-status {meta["class"]}">{escape(meta["label"])}: {value}</span>')
    return "".join(parts) or '<span class="mini-status status-unverified">No checks</span>'


def _field(label: str, value: object, badge: str | None = None) -> str:
    shown = "(none)" if value in (None, "", []) else str(value)
    if badge:
        value_html = f'<span class="badge {badge}">{escape(shown)}</span>'
    else:
        value_html = f'<span>{escape(shown)}</span>'
    return f'<div class="field"><span>{escape(label)}</span>{value_html}</div>'


def _meta_pair(label: str, value: object) -> str:
    shown = "(unknown)" if value in (None, "", []) else str(value)
    return f'<div><dt>{escape(label)}</dt><dd>{escape(shown)}</dd></div>'


def _canonical_status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in STATUS_ORDER}
    for item in items:
        status = str(item.get("status") or "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _counts(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _coverage_sentence(counts: dict[str, int]) -> str:
    total = sum(counts.values()) or 0
    if not total:
        return "No control checks present."
    ordered = ["full", "partial", "none"]
    parts = [f"{counts.get(key, 0)} {key}" for key in ordered if counts.get(key, 0)]
    return f"{', '.join(parts)} across {total} checks."


def _filter_button(status: str) -> str:
    meta = STATUS_META[status]
    return f'<button type="button" class="filter" data-filter="{escape(status)}">{escape(meta["label"])}</button>'


def _fmt_time(value: object) -> str:
    if not value:
        return "(unknown)"
    return str(value).replace("T", " ").replace("Z", " UTC")


def _family_meta(family: str) -> dict[str, str]:
    return FAMILY_META.get(family, {"name": family or "Other", "summary": "Assessment controls outside the standard starter-kit domain taxonomy."})


def _family_sort_key(family: str) -> tuple[int, str]:
    order = ["LIC", "AUD", "LABEL", "DLP", "SAM", "EDISC", "PACK"]
    return (order.index(family) if family in order else 99, family)


def _control_review_sort_key(control: dict[str, Any]) -> tuple[int, str]:
    status = str(control.get("status") or "UNKNOWN")
    return (-STATUS_PRIORITY.get(status, 0), str(control.get("control_check_id") or ""))


def _domain_review_sort_key(family: str, grouped: dict[str, list[dict[str, Any]]]) -> tuple[int, tuple[int, str]]:
    dominant = _dominant_status(grouped.get(family, []))
    return (-STATUS_PRIORITY.get(dominant, 0), _family_sort_key(family))


def _dominant_status(items: list[dict[str, Any]]) -> str:
    if not items:
        return "UNKNOWN"
    return max((str(item.get("status") or "UNKNOWN") for item in items), key=lambda status: STATUS_PRIORITY.get(status, 0))


def _dominant_control(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not items:
        return None
    return max(items, key=lambda item: STATUS_PRIORITY.get(str(item.get("status") or "UNKNOWN"), 0))


def _css() -> str:
    return r'''
:root {
  color-scheme: light;
  --bg: #f9fafb;
  --surface: #ffffff;
  --surface-soft: #f3f4f6;
  --ink: #111827;
  --ink-soft: #1f2937;
  --ink-muted: #d1d5db;
  --line: #d1d5db;
  --line-strong: #9ca3af;
  --text: #111827;
  --muted: #4b5563;
  --verified: #15803d;
  --verified-bg: #dcfce7;
  --gap: #b45309;
  --gap-bg: #fef3c7;
  --unverified: #4b5563;
  --unverified-bg: #e5e7eb;
  --access: #1d4ed8;
  --access-bg: #dbeafe;
  --license: #7e22ce;
  --license-bg: #f3e8ff;
  --failed: #b91c1c;
  --failed-bg: #fee2e2;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.5;
}
button { font: inherit; color: inherit; }
.report-shell { max-width: 1480px; margin: 0 auto; padding: 24px; }
.report-header {
  display: grid;
  grid-template-columns: minmax(360px, 1fr) minmax(360px, 560px);
  gap: 24px;
  align-items: start;
  margin-bottom: 16px;
  padding: 24px;
  background: var(--ink);
  color: #f9fafb;
  border: 1px solid var(--ink);
  border-radius: 12px;
}
h1, h2, h3, p, dl, dd { margin: 0; }
h1 { font-size: 34px; line-height: 1.08; letter-spacing: -.03em; max-width: 780px; }
h2 { font-size: 18px; line-height: 1.25; }
h3 { font-size: 16px; line-height: 1.3; }
p, .muted { color: var(--muted); }
.report-header p { margin-top: 8px; max-width: 760px; color: var(--ink-muted); }
.value-prop { color: #ffffff !important; font-size: 18px; font-weight: 700; letter-spacing: -.01em; }
.assurance-disclaimer {
  display: inline-flex;
  width: fit-content;
  margin-top: 14px !important;
  padding: 8px 10px;
  border: 1px solid #374151;
  border-radius: 8px;
  color: #f9fafb !important;
  background: var(--ink-soft);
  font-weight: 700;
}
.proof-path {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 16px;
  max-width: 820px;
}
.proof-path div {
  border: 1px solid #374151;
  border-radius: 8px;
  padding: 10px;
  background: var(--ink-soft);
}
.proof-path strong { display: block; color: #ffffff; margin-bottom: 2px; }
.proof-path span { color: var(--ink-muted); }
.header-actions { display: flex; gap: 8px; margin-top: 14px; }
.header-actions button {
  border: 1px solid #4b5563;
  background: #f9fafb;
  color: var(--ink);
  border-radius: 8px;
  padding: 8px 11px;
  cursor: pointer;
  font-weight: 700;
}
.header-actions button:hover { border-color: #f9fafb; background: #ffffff; }
.run-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.run-meta div, .scope-note, .section, .evidence-panel, .posture-card, .posture-note {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
}
.run-meta div { padding: 10px 12px; }
.report-header .run-meta div {
  background: var(--ink-soft);
  border-color: #374151;
}
dt { color: var(--muted); font-size: 12px; }
.report-header dt { color: var(--ink-muted); }
dd { margin-top: 3px; word-break: break-word; font-weight: 600; }
.report-header dd { color: #ffffff; }
.posture-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(126px, 1fr)) minmax(220px, 1.2fr);
  gap: 10px;
  margin-bottom: 16px;
}
.posture-card {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto auto;
  gap: 3px 8px;
  padding: 12px;
  text-align: left;
  cursor: pointer;
}
.posture-card:hover, .posture-card.active { border-color: var(--line-strong); background: var(--surface-soft); }
.posture-card.status-verified { border-top: 4px solid var(--verified); }
.posture-card.status-gap { border-top: 4px solid var(--gap); }
.posture-card.status-unverified { border-top: 4px solid var(--unverified); }
.posture-card.status-access { border-top: 4px solid var(--access); }
.posture-card.status-license { border-top: 4px solid var(--license); }
.posture-card.status-failed { border-top: 4px solid var(--failed); }
.status-icon { grid-row: 1 / span 2; font-weight: 800; }
.posture-card.status-verified .status-icon { color: var(--verified); }
.posture-card.status-gap .status-icon { color: var(--gap); }
.posture-card.status-unverified .status-icon { color: var(--unverified); }
.posture-card.status-access .status-icon { color: var(--access); }
.posture-card.status-license .status-icon { color: var(--license); }
.posture-card.status-failed .status-icon { color: var(--failed); }
.posture-label { color: var(--muted); }
.posture-card strong { font-size: 24px; line-height: 1; }
.posture-card small { color: var(--muted); }
.posture-note { padding: 12px; display: grid; align-content: center; gap: 8px; }
.posture-note span { color: var(--muted); }
.posture-note b { color: var(--text); }
.reset-focus { width: fit-content; border: 1px solid var(--line); background: var(--surface); border-radius: 8px; padding: 6px 9px; cursor: pointer; }
.reset-focus:hover { border-color: var(--line-strong); background: var(--surface-soft); }
.demo-banner {
  background: #fff7ed;
  color: var(--text);
  border: 1px solid #fed7aa;
  border-left: 4px solid var(--gap);
  border-radius: 10px;
  padding: 13px 16px;
  margin-bottom: 16px;
}
.demo-banner strong { display: block; margin-bottom: 4px; }
.demo-banner p { color: var(--text); }
.scope-note {
  display: grid;
  grid-template-columns: minmax(320px, 1fr) minmax(360px, 520px);
  gap: 20px;
  padding: 16px;
  margin-bottom: 18px;
  border-left: 4px solid var(--gap);
}
.scope-note p { margin-top: 6px; }
.scope-facts { display: grid; gap: 8px; }
.field { display: grid; grid-template-columns: 120px 1fr; gap: 8px; }
.field > span:first-child { color: var(--muted); }
.content-grid { display: grid; grid-template-columns: minmax(620px, 1fr) 400px; gap: 18px; align-items: start; }
.main-content { display: grid; gap: 18px; }
.section, .evidence-panel { padding: 16px; }
.section-heading { display: flex; justify-content: space-between; align-items: start; gap: 20px; margin-bottom: 14px; }
.section-heading p { max-width: 620px; }
.finding-list, .domain-list, .evidence-list { display: grid; gap: 10px; }
.focus-summary { color: var(--muted); border: 1px solid var(--line); border-radius: 8px; padding: 6px 9px; background: var(--surface-soft); font-weight: 650; }
.finding-card {
  width: 100%;
  display: grid;
  grid-template-columns: 82px 1fr;
  gap: 12px;
  align-items: start;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface);
  text-align: left;
  cursor: pointer;
}
.finding-card:hover, .finding-card.active { border-color: var(--gap); background: #fffbeb; }
.finding-content { display: grid; gap: 5px; }
.finding-content span, .finding-content small { color: var(--muted); }
.finding-content b { color: var(--text); }
.severity, .status-badge, .mini-status, .badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  min-height: 22px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
}
.severity-medium { color: var(--gap); background: var(--gap-bg); }
.severity-low, .severity-informational { color: var(--unverified); background: var(--unverified-bg); }
.severity-high, .severity-critical { color: var(--failed); background: var(--failed-bg); }
.status-verified { color: var(--verified); background: var(--verified-bg); }
.status-gap { color: var(--gap); background: var(--gap-bg); }
.status-unverified { color: var(--unverified); background: var(--unverified-bg); }
.status-access { color: var(--access); background: var(--access-bg); }
.status-license { color: var(--license); background: var(--license-bg); }
.status-failed { color: var(--failed); background: var(--failed-bg); }
.filter-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.filter {
  border: 1px solid var(--line);
  background: var(--surface);
  border-radius: 8px;
  padding: 7px 10px;
  cursor: pointer;
}
.filter:hover, .filter.active { border-color: var(--line-strong); background: var(--surface-soft); }
.domain-card { border: 1px solid var(--line); border-radius: 10px; background: var(--surface); overflow: hidden; }
.domain-card.dimmed { opacity: .55; }
.domain-card.has-focus { border-color: var(--line-strong); }
.domain-card-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
  padding: 14px;
  background: var(--surface-soft);
  border-bottom: 1px solid var(--line);
}
.domain-card-header p { margin-top: 3px; color: var(--muted); font-size: 12px; }
.domain-summary { padding: 12px 14px 0; }
.domain-counts { display: flex; gap: 6px; flex-wrap: wrap; padding: 10px 14px 12px; }
details { border-top: 1px solid var(--line); }
summary { cursor: pointer; padding: 12px 14px; color: var(--muted); }
.control-list { display: grid; border-top: 1px solid var(--line); }
.control-row {
  width: 100%;
  display: grid;
  grid-template-columns: 134px 1fr;
  gap: 12px;
  align-items: start;
  padding: 12px 14px;
  border: 0;
  border-top: 1px solid var(--line);
  background: transparent;
  text-align: left;
  cursor: pointer;
}
.control-row:first-child { border-top: 0; }
.control-row:hover, .control-row.active { background: #f8fafc; }
.control-row.highlighted { border-left: 4px solid var(--gap); background: #fffbeb; }
.control-row.dimmed { opacity: .52; }
.control-main { display: grid; gap: 5px; }
.control-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.action-chip { display: inline-flex; width: fit-content; min-height: 20px; padding: 2px 7px; border-radius: 6px; font-size: 12px; font-weight: 700; }
.linked-action { color: var(--muted); }
.control-main span, .control-main small { color: var(--muted); }
.control-main b { color: var(--text); }
.quality-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 2px; }
.quality-tag {
  display: inline-flex;
  width: fit-content;
  padding: 2px 7px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface-soft);
  color: var(--muted);
  font-size: 12px;
  font-weight: 650;
}
.evidence-panel { position: sticky; top: 16px; max-height: calc(100vh - 32px); overflow: auto; }
.panel-heading { margin-bottom: 12px; }
.panel-heading p { margin-top: 4px; }
.evidence-detail { border: 1px solid var(--line); border-radius: 10px; padding: 14px; min-height: 220px; background: var(--surface); }
.control-context { display: grid; gap: 8px; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--line); }
.empty-state { color: var(--muted); padding: 14px; background: var(--surface-soft); border: 1px solid var(--line); border-radius: 8px; }
.evidence-actions { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0; }
.evidence-pill, .copy-button { border: 1px solid var(--line); background: var(--surface); border-radius: 8px; padding: 6px 9px; cursor: pointer; font-size: 12px; }
.evidence-pill:hover, .copy-button:hover { border-color: var(--line-strong); background: var(--surface-soft); }
.evidence-detail h3 { margin-bottom: 10px; }
.evidence-detail dl { margin: 0; display: grid; gap: 8px; }
.evidence-detail dt { color: var(--muted); }
.evidence-detail dd { margin: 0 0 8px; word-break: break-word; }
.evidence-detail pre {
  margin: 8px 0 0;
  padding: 10px;
  background: #111827;
  color: #f9fafb;
  border-radius: 8px;
  overflow: auto;
  max-height: 300px;
}
.evidence-index { margin-top: 14px; }
.evidence-index h3 { margin-bottom: 8px; }
.evidence-link {
  width: 100%;
  display: grid;
  gap: 2px;
  padding: 9px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  text-align: left;
  cursor: pointer;
}
.evidence-link span { color: var(--muted); font-size: 12px; }
.evidence-link:hover, .evidence-link.active { border-color: var(--line-strong); background: var(--surface-soft); }
[hidden] { display: none !important; }
@media (max-width: 1180px) {
  .report-header, .scope-note, .content-grid { grid-template-columns: 1fr; }
  .proof-path { grid-template-columns: 1fr; }
  .posture-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .evidence-panel { position: static; max-height: none; }
}
@media print {
  body { background: white; }
  .report-header { background: white; color: var(--text); border-color: var(--line); }
  .report-header p, .report-header dt, .report-header dd, .value-prop, .assurance-disclaimer, .proof-path span, .proof-path strong { color: var(--text) !important; }
  .assurance-disclaimer, .proof-path div, .report-header .run-meta div { background: white; border-color: var(--line); }
  .posture-card, .posture-note, .scope-note, .section, .evidence-panel { box-shadow: none; }
  .filter-row, .evidence-panel { display: none; }
  .content-grid { display: block; }
  details { break-inside: avoid; }
}
'''


def _js() -> str:
    return r'''
const PACK = JSON.parse(document.getElementById('pack-data').textContent);
const evidenceById = new Map((PACK.evidence_items || []).map(item => [item.evidence_id, item]));
const controlsById = new Map((PACK.control_checks || []).map(item => [item.control_check_id, item]));
const findingsById = new Map((PACK.findings || []).map(item => [item.finding_id, item]));
const findingsByControl = new Map();
for (const finding of PACK.findings || []) {
  for (const controlId of finding.related_control_checks || finding.affected_objects || []) {
    if (!findingsByControl.has(controlId)) findingsByControl.set(controlId, []);
    findingsByControl.get(controlId).push(finding);
  }
}
const statusLabels = {
  PASS: 'Verified', WARN: 'Needs Review', UNKNOWN: 'Unverified',
  NOT_ACCESSIBLE: 'Access Required', NOT_LICENSED: 'Not Licensed', FAIL: 'Failed'
};
const causeLabels = {
  verified: 'Verified evidence',
  tenant_gap: 'Tenant gap',
  assessment_limitation: 'Assessment limitation',
  permission_gap: 'Permission gap',
  not_licensed: 'Not licensed',
  unsupported_api: 'Unsupported API',
  usage_absence: 'No usage context',
  manual_evidence_required: 'Manual evidence required',
  demo_evidence: 'Demo evidence',
  unknown: 'Cause not specified'
};
const evidenceQualityLabels = {
  demo_evidence: 'Demo evidence attached',
  demo_only: 'Demo evidence attached',
  synthetic_fixture: 'Synthetic evidence',
  demo_evidence_in_full_check: 'Demo evidence attached',
  manual_evidence_linked: 'Manual evidence linked',
  manual_only: 'Manual evidence required',
  not_configured_for_assessment: 'Not collected in this run',
  partial_scope: 'Partial scope',
  sampled: 'Sampled evidence',
  stale: 'Stale evidence',
  stale_mapping: 'Stale mapping',
  license_limited: 'License mapping limited',
  permission_limited: 'Permission limited',
  no_export_validation: 'No export validation',
  no_positive_hit: 'No positive content hit',
  zero_result: 'Zero-result validation',
  api_unsupported: 'API limitation',
  unsupported_api: 'API limitation',
  raw_retention_unavailable: 'Raw artifact not retained'
};
const demoLimitationMarkers = ['demo_evidence', 'demo_only', 'synthetic_fixture', 'demo_evidence_in_full_check'];
const evidenceQualityPriority = {
  raw_retention_unavailable: 95,
  stale: 90,
  stale_mapping: 88,
  permission_limited: 85,
  license_limited: 82,
  api_unsupported: 80,
  unsupported_api: 80,
  not_configured_for_assessment: 75,
  manual_only: 70,
  no_export_validation: 65,
  no_positive_hit: 62,
  zero_result: 60,
  partial_scope: 55,
  sampled: 50,
  manual_evidence_linked: 30,
  demo_evidence: 10,
  demo_only: 10,
  synthetic_fixture: 10,
  demo_evidence_in_full_check: 10
};

function hasDemoMarker(control) {
  return (control.limitations || []).some(item => demoLimitationMarkers.includes(item));
}

function reviewLabel(control) {
  const status = control.status || 'UNKNOWN';
  const cause = control.status_cause || 'unknown';
  if (status === 'PASS' && hasDemoMarker(control)) return 'Demo evidence attached';
  if (status === 'PASS') return 'Verified';
  if (status === 'NOT_ACCESSIBLE' || cause === 'permission_gap') return 'Access required';
  if (status === 'NOT_LICENSED' || cause === 'not_licensed') return 'Licensing required';
  if (status === 'FAIL' || cause === 'tenant_gap') return 'Tenant action required';
  if (cause === 'unsupported_api') return 'Microsoft API limitation';
  if (cause === 'usage_absence') return 'No usage evidence';
  if (cause === 'manual_evidence_required') return 'Manual evidence required';
  if (cause === 'demo_evidence') return 'Demo evidence only';
  if (cause === 'assessment_limitation') return status === 'UNKNOWN' ? 'Not assessed' : 'Evidence incomplete';
  return 'Review required';
}

function meaningText(control) {
  const status = control.status || 'UNKNOWN';
  const cause = control.status_cause || 'unknown';
  if (status === 'PASS' && cause === 'verified') return 'Available evidence supports this control for the assessed scope.';
  if (status === 'FAIL' || cause === 'tenant_gap') return 'Collected evidence points to a tenant configuration or control gap that needs remediation.';
  if (status === 'NOT_ACCESSIBLE' || cause === 'permission_gap') return 'The control may exist, but the assessment identity could not read the required source.';
  if (status === 'NOT_LICENSED' || cause === 'not_licensed') return 'The required Microsoft capability appears unavailable or outside the current license baseline.';
  if (cause === 'unsupported_api') return 'The required evidence is not available through the supported Microsoft API path used by this assessment.';
  if (cause === 'usage_absence') return 'No relevant activity sample was available, so the control behavior cannot be assessed from usage evidence.';
  if (cause === 'manual_evidence_required') return 'This control depends on customer/assessor evidence or a separately approved collector.';
  if (cause === 'demo_evidence') return 'Only demo or synthetic evidence is attached; do not treat this as production assurance.';
  if (cause === 'assessment_limitation') return 'This does not prove the tenant is misconfigured; the assessment lacks enough supported evidence.';
  return 'The report cannot classify the reason confidently from the available evidence.';
}

function nextActionText(control) {
  const actions = (control.follow_up_required || []).filter(Boolean);
  if (actions.length) return actions[0];
  const status = control.status || 'UNKNOWN';
  const cause = control.status_cause || 'unknown';
  if (status === 'PASS' && cause === 'verified') return 'No action required; retain linked evidence for the audit trail.';
  if (cause === 'permission_gap') return 'Grant the least-privilege reader role/permission for this source, then rerun.';
  if (cause === 'not_licensed') return 'Confirm licensing or remove this control from the assessment baseline.';
  if (cause === 'unsupported_api') return 'Provide native Microsoft UI/export evidence for this control.';
  if (cause === 'usage_absence') return 'Provide a bounded usage sample or rerun after relevant activity exists.';
  if (cause === 'tenant_gap') return 'Remediate the Microsoft control configuration and rerun the assessment.';
  return 'Review the evidence manually, then decide whether a collector, export, permission, or tenant change is required.';
}

function responsibleDomain(control) {
  return ({
    LIC: 'Licensing',
    AUD: 'Audit / Purview',
    LABEL: 'Data protection',
    DLP: 'Data protection',
    SAM: 'SharePoint governance',
    EDISC: 'Compliance / eDiscovery',
    PACK: 'Assessment evidence'
  })[(control.control_family || '').toUpperCase()] || 'Governance review';
}

function evidenceQualityTags(control) {
  const limitations = control.limitations || [];
  const tags = [];
  if (control.evidence_completeness === 'partial') tags.push('Partial evidence');
  if (control.evidence_completeness === 'none') tags.push('No usable evidence');

  const orderedLimitations = [...limitations].sort((a, b) => (evidenceQualityPriority[b] || 0) - (evidenceQualityPriority[a] || 0));
  for (const limitation of orderedLimitations) {
    const label = evidenceQualityLabels[limitation];
    if (label && !tags.includes(label) && tags.length < 3) tags.push(label);
  }

  const demoMarker = limitations.find(item => demoLimitationMarkers.includes(item));
  const demoLabel = demoMarker ? evidenceQualityLabels[demoMarker] : null;
  if (demoLabel && !tags.includes(demoLabel)) {
    if (tags.length >= 3) tags[tags.length - 1] = demoLabel;
    else tags.push(demoLabel);
  }
  return tags.slice(0, 3);
}

function evidenceQualityHtml(control) {
  const tags = evidenceQualityTags(control);
  if (!tags.length) return '';
  return `<span class="quality-tags">${tags.map(tag => `<span class="quality-tag">${escapeHtml(tag)}</span>`).join('')}</span>`;
}

function evidenceDetailHtml(item) {
  if (!item) return '';
  return `
    <h3>${escapeHtml(item.evidence_id)}</h3>
    <div class="evidence-actions"><button type="button" class="copy-button" data-copy-value="${escapeHtml(item.evidence_id)}">Copy Evidence ID</button></div>
    <dl>
      <dt>Type</dt><dd>${escapeHtml(item.evidence_type)}</dd>
      <dt>Source</dt><dd>${escapeHtml(item.source_system)}</dd>
      <dt>Collected</dt><dd>${escapeHtml(item.collected_at_utc || '')}</dd>
      <dt>Hash</dt><dd><code>${escapeHtml(item.content_hash || '(none)')}</code></dd>
      <dt>Artifact</dt><dd><code>${escapeHtml(item.raw_artifact_path || '(not retained)')}</code></dd>
      <dt>Limitations</dt><dd>${escapeHtml((item.limitations || []).join(', ') || '(none)')}</dd>
    </dl>
    <h3>Normalized facts</h3>
    <pre>${escapeHtml(JSON.stringify(item.normalized_facts || {}, null, 2))}</pre>
  `;
}

function evidenceButtonsHtml(control) {
  const ids = control.evidence_items_used || [];
  if (!ids.length) return '';
  return `<div class="evidence-actions">${ids.map(id => `<button type="button" class="evidence-pill" data-evidence-id="${escapeHtml(id)}">${escapeHtml(id)}</button>`).join('')}</div>`;
}

function linkedFindingsHtml(control) {
  const findings = findingsByControl.get(control.control_check_id) || [];
  const first = findings[0] || {};
  const whatFound = first.condition || reviewLabel(control);
  const whyMatters = first.impact_or_risk || meaningText(control);
  const nextStep = first.recommendation || nextActionText(control);
  return `
    <p><b>What the report found:</b> ${escapeHtml(whatFound)}</p>
    <p><b>Why this appears:</b> ${escapeHtml(control.status_reason || 'No status reason was provided.')}</p>
    <p><b>Why this matters:</b> ${escapeHtml(whyMatters)}</p>
    <p><b>Next evidence step:</b> ${escapeHtml(nextStep)}</p>
  `;
}

function showEvidence(evidenceId, context) {
  const detail = document.getElementById('evidence-detail');
  const item = evidenceById.get(evidenceId);
  document.querySelectorAll('.active').forEach(el => el.classList.remove('active'));
  if (!item) {
    detail.innerHTML = `<h3>${context ? escapeHtml(context) : 'No automated evidence'}</h3><div class="empty-state">No automated evidence is linked to this item. Review the control's next action and provide manual evidence or approve the relevant collector.</div>`;
    return;
  }
  document.querySelectorAll(`[data-evidence-id="${CSS.escape(evidenceId)}"]`).forEach(el => el.classList.add('active'));
  detail.innerHTML = evidenceDetailHtml(item);
}

function showControl(controlId) {
  const control = controlsById.get(controlId);
  if (!control) return;
  document.querySelectorAll('.control-row.active, .evidence-link.active, .evidence-pill.active').forEach(el => el.classList.remove('active'));
  const row = document.querySelector(`[data-control-id="${CSS.escape(controlId)}"]`);
  if (row) row.classList.add('active');
  const evidenceIds = control.evidence_items_used || [];
  const firstEvidence = evidenceIds.length ? evidenceById.get(evidenceIds[0]) : null;
  const evidenceBlock = firstEvidence
    ? evidenceDetailHtml(firstEvidence)
    : `<div class="empty-state">No automated evidence is linked to this control. Use the next action below to provide manual evidence or approve the relevant read-only collector.</div>`;
  document.getElementById('evidence-detail').innerHTML = `
    <div class="control-context">
      <h3>${escapeHtml(control.control_check_id)} — ${escapeHtml(reviewLabel(control))}</h3>
      ${linkedFindingsHtml(control)}
      ${evidenceQualityHtml(control)}
      ${evidenceButtonsHtml(control)}
      <p class="muted">Canonical status: ${escapeHtml(control.status || '')} · Cause: ${escapeHtml(causeLabels[control.status_cause || 'unknown'] || 'Cause not specified')} · Evidence: ${escapeHtml(control.evidence_completeness || '')} · Domain: ${escapeHtml(responsibleDomain(control))}</p>
    </div>
    ${evidenceBlock}
  `;
}

function showFinding(findingId) {
  const finding = findingsById.get(findingId);
  if (!finding) return;
  const controlId = (finding.related_control_checks || finding.affected_objects || [])[0];
  if (controlId && controlsById.has(controlId)) {
    showControl(controlId);
    return;
  }
  const evidenceId = (finding.evidence_references || [])[0];
  showEvidence(evidenceId, findingId);
}

document.addEventListener('click', event => {
  const copy = event.target.closest('[data-copy-value]');
  if (copy) {
    navigator.clipboard?.writeText(copy.dataset.copyValue || '');
    copy.textContent = 'Copied';
    return;
  }
  const focus = event.target.closest('[data-focus-status]');
  if (focus) {
    applyFocusMode(focus.dataset.focusStatus, focus);
    return;
  }
  const control = event.target.closest('[data-control-id]');
  if (control) {
    showControl(control.dataset.controlId);
    return;
  }
  const finding = event.target.closest('[data-finding-id]');
  if (finding) {
    showFinding(finding.dataset.findingId);
    return;
  }
  const evidence = event.target.closest('[data-evidence-id]');
  if (evidence) showEvidence(evidence.dataset.evidenceId);
});

function applyFocusMode(status, button) {
  const summary = document.getElementById('focus-summary');
  document.querySelectorAll('[data-focus-status]').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.control-row').forEach(row => {
    row.classList.remove('highlighted', 'dimmed');
    row.style.order = '';
  });
  document.querySelectorAll('.domain-card').forEach(card => {
    card.classList.remove('has-focus', 'dimmed');
    card.style.order = '';
    const details = card.querySelector('details');
    if (details) details.open = true;
  });

  if (!status || status === 'ALL') {
    if (summary) summary.textContent = 'Showing all controls';
    return;
  }

  if (button) button.classList.add('active');
  const label = statusLabels[status] || status;
  let firstMatch = null;
  document.querySelectorAll('.control-row').forEach(row => {
    const match = row.dataset.status === status;
    row.classList.toggle('highlighted', match);
    row.classList.toggle('dimmed', !match);
    row.style.order = match ? '0' : '1';
    if (match && !firstMatch) firstMatch = row;
  });
  document.querySelectorAll('.domain-card').forEach(card => {
    const hasMatch = Array.from(card.querySelectorAll('.control-row')).some(row => row.dataset.status === status);
    card.classList.toggle('has-focus', hasMatch);
    card.classList.toggle('dimmed', !hasMatch);
    card.style.order = hasMatch ? '0' : '1';
    const details = card.querySelector('details');
    if (details) details.open = hasMatch;
  });
  if (summary) summary.textContent = `Focus: ${label} controls remain in context`;
  if (firstMatch) {
    firstMatch.scrollIntoView({behavior: 'smooth', block: 'center'});
    showControl(firstMatch.dataset.controlId);
  }
}

const downloadButton = document.getElementById('download-json');
if (downloadButton) {
  downloadButton.addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(PACK, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${PACK.evidence_pack_id || 'evidence_pack'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });
}
const printButton = document.getElementById('print-view');
if (printButton) printButton.addEventListener('click', () => window.print());

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
}

const defaultEvidence = document.getElementById('evidence-detail').dataset.defaultEvidence;
if (defaultEvidence) showEvidence(defaultEvidence);
'''
