# Configuration Mapping Artifacts

These files are versioned evidence-classification aids for the read-only assessment collectors.

They are deliberately conservative. A missing or unrecognized mapping should usually produce `UNKNOWN`, not `FAIL` or `NOT_LICENSED`.

## Files

- `microsoft_capability_map.json`
  - Maps Microsoft Graph `subscribedSkUs` and service-plan evidence to first-slice capability assumptions.
  - Used by `LIC-001`, `LIC-002`, `LABEL-001`, `AUD-*`, `DLP-*`, `SAM-001`, and `EDISC-*` control checks.

- `dlp_copilot_location_map.json`
  - Maps known DLP policy location identifiers/names/actions for Microsoft 365 Copilot and Copilot Chat.
  - Used by `DLP-001` and `DLP-002`.

## Operating rules

1. Keep source URLs and `last_reviewed` current.
2. Do not hardcode Microsoft SKU, service-plan, or DLP location assumptions in collector code.
3. If Microsoft changes naming or output structure, update these files and record a decision.
4. If mapping is ambiguous, classify as `UNKNOWN` with a clear limitation.
5. If access is denied, classify as `NOT_ACCESSIBLE`, not `UNKNOWN`.
6. If mapping freshness exceeds the file threshold, add `stale_mapping` and avoid hard `NOT_LICENSED`/`FAIL` unless the run independently verifies the claim.
7. Treat fallback Copilot-like SKU/service-plan or DLP-location matches as `WARN`/manual-review evidence, not `PASS`.
