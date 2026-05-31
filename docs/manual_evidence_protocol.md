# Manual Evidence Protocol

Status: starter kit protocol baseline
Last reviewed: 2026-04-30

## Purpose

Some Microsoft Copilot governance controls cannot be safely proven through automated read-only probes in the starter kit.

Manual evidence is the approved path for those controls when automation would require:

- tenant mutation;
- content export;
- sensitive content handling;
- long-running Microsoft reports;
- UI-only or preview surfaces;
- customer-specific approval.

## Supported manual evidence examples

- Purview eDiscovery export/readiness evidence.
- Purview retention policy screenshot/export for Copilot or AI apps.
- DLP policy/rule export when PowerShell/API access is unavailable.
- SharePoint Advanced Management / DAG report export.
- Auditor/customer attestation with supporting screenshot or report.

## Rules

1. Manual evidence must cite one or more control IDs.
2. Manual evidence must preserve an artifact path and content hash.
3. Manual evidence must state asserted facts separately from limitations.
4. Manual evidence is lower-repeatability evidence unless the artifact is an official export with stable metadata.
5. Manual evidence cannot silently convert an automated `UNKNOWN` into `PASS`; the control check must explain why the manual artifact is sufficient.
6. Content exports are customer-controlled artifacts. The starter kit does not create them automatically.
7. Manual evidence is tagged `trust_level=customer_asserted` and `independently_verified_by_tool=false` unless a later verifier proves otherwise.
8. Manual evidence cannot override an automated `NOT_ACCESSIBLE` result without an explicit customer or assessor statement in the evidence bundle and a clear pack limitation.

## Bundle format

Machine-readable bundles use:

`config/manual_evidence_schema.json`

Minimal example:

```json
{
  "schema_version": "0.1.0",
  "assessment_run_id": "run-20260430",
  "tenant_id": "tenant-guid",
  "provided_by": "customer.admin@example.com",
  "provided_at_utc": "2026-04-30T13:00:00Z",
  "items": [
    {
      "evidence_id": "manual-edisc-export-001",
      "control_ids": ["EDISC-002"],
      "evidence_type": "report_export",
      "source_system": "Microsoft Purview eDiscovery",
      "source_endpoint_or_ui_path": "Purview > eDiscovery > Exports",
      "artifact_path": "manual/edisc-export-summary.pdf",
      "asserted_facts": {
        "customer_provided_purview_export": true,
        "export_performed_by_customer": true
      },
      "limitations": ["manual_only"],
      "relevance_rating": "high",
      "reliability_rating": "medium"
    }
  ]
}
```

## Product implication

Manual evidence is a first-class evidence source in the pack, not a side note. It lets the product remain Microsoft-native and minimally invasive while still giving auditors a defensible place for customer-controlled proof.
