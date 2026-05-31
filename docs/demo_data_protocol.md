# Demo Data Protocol

Purpose: create richer review/demo evidence packs without converting synthetic material into production assurance.

## Rules

- Prefix tenant-created demo artifacts with `TCA-DEMO`.
- Keep demo retention target at 30 days unless the assessor changes it.
- Do not inject or fabricate Microsoft Purview audit records.
- Do not treat synthetic chat transcripts as Teams messages, CopilotInteraction records, or production user evidence.
- Do not bulk-post Teams messages. Microsoft Graph Teams send-message APIs warn that Teams must not be used as a log file.
- Any report generated with demo evidence must show a visible demo-mode warning.

## Supported first demo dataset

The current seeder creates:

- local synthetic Copilot-style chat transcripts for UI depth only;
- local synthetic DLP policy evidence;
- local synthetic SAM/oversharing evidence;
- local synthetic retention evidence;
- local synthetic eDiscovery readiness evidence.

Public demo commands do not create tenant eDiscovery cases. Earlier internal validation supported rendering an approved tenant eDiscovery case as demo evidence, but that is not part of the public quick start and must not be treated as default demo behavior.

## Commands

Create local demo fixtures only. This is useful for inspecting the raw manual evidence bundle, but it is not the main public quick-start path:

```bash
scripts/create_demo_dataset.py
```

Generate the complete synthetic demo evidence pack and HTML report. This is the primary public demo entry point:

```bash
scripts/create_demo_report.py
```

Render UI from an existing evidence pack JSON:

```bash
scripts/render_evidence_pack_ui.py artifacts/evidence_packs/<run>/evidence_pack.json
```

Advanced: `scripts/run_assessment.py --manual-evidence ...` combines manual evidence with a live read-only probe. Do not describe that as synthetic-only demo mode because it attempts tenant-connected read operations.
