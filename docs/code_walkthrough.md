# Code Walkthrough

This document is for external readers who want to understand how the starter kit works before changing it.

## High-level data flow

```text
Synthetic demo path
scripts/create_demo_report.py
  -> tesrex_assurance.demo_report
  -> tesrex_assurance.demo_dataset
  -> tesrex_assurance.pack_builder
  -> tesrex_assurance.evidence_pack
  -> tesrex_assurance.ui_renderer
  -> artifacts/evidence_packs/run-*/evidence_pack_ui.html

Tenant-connected read-only path
scripts/live_readonly_probe.py or scripts/run_assessment.py
  -> tesrex_assurance.live_probe
  -> tesrex_assurance.collectors.*
  -> artifacts/live_probe/*/summary.json
  -> tesrex_assurance.pack_builder
  -> tesrex_assurance.evidence_pack
  -> tesrex_assurance.ui_renderer
```

## Repository layout

| Path | Purpose |
|---|---|
| `README.md` | Public entry point and quick start. |
| `Justfile` | Convenience commands for validation, demo generation, and local serving. |
| `scripts/` | Thin command-line wrappers around package code. |
| `src/tesrex_assurance/` | Starter-kit implementation. |
| `config/` | Versioned advisory Microsoft mapping files. |
| `docs/` | Evidence contract, operating boundaries, source review, code guide, and release-readiness record. |
| `tests/` | Fixture/unit tests for conservative status logic and report generation. |
| `artifacts/` | Ignored local generated reports and probe evidence. Do not commit real artifacts. |

## Core modules

| Module | Role |
|---|---|
| `models.py` | Dataclasses/enums defining the evidence-pack contract. |
| `live_probe.py` | Default read-only live probe orchestration. |
| `collectors/` | Allowlisted collector implementations. |
| `demo_report.py` | Tenant-free synthetic demo report flow. |
| `demo_dataset.py` | Synthetic/manual evidence fixture creation. |
| `manual_evidence.py` | Customer/assessor artifact ingestion and hashing. |
| `mappings.py` | Static mapping loaders with staleness/completeness checks. |
| `classifiers.py` | Conservative classifiers that avoid false hard failures. |
| `pack_builder.py` | Converts probe/manual evidence into control checks and findings. |
| `evidence_pack.py` | Validates evidence-pack invariants and renders JSON/Markdown. |
| `breadcrumbs.py` | Human explanation text for report controls. |
| `ui_renderer.py` | Static HTML report renderer. |

## Demo mode versus tenant-connected mode

Demo mode is intentionally synthetic and tenant-free. It proves the report shape and review experience, not tenant posture. Public demo commands do not call Azure, Graph, Purview, SharePoint, Audit, or eDiscovery. `scripts/create_demo_dataset.py` creates local fixture files only; `scripts/create_demo_report.py` is the public quick-start command that creates fixtures, builds the evidence pack, and renders the HTML report.

Tenant-connected mode requires Microsoft identity, Graph/Purview/SharePoint/Audit/eDiscovery access, an explicit expected tenant ID, and customer-approved evidence boundaries. Before any token or Graph request, the CLI checks the active Azure CLI tenant against that exact expected tenant and stops on a mismatch. Default live probes are read-only and must not mutate a tenant.

## Safety invariants

Do not weaken these without updating tests and docs:

1. Demo evidence must be marked synthetic/example and must not be treated as production assurance.
2. Default tenant-connected probes must be read-only.
3. Permission failures are `NOT_ACCESSIBLE`, not customer control failures.
4. Stale or incomplete static mappings must not produce hard `NOT_LICENSED` or hard DLP `FAIL` by themselves.
5. eDiscovery endpoint visibility is not proof of Copilot data export readiness.
6. Generated evidence artifacts stay local/ignored unless deliberately sanitized for a public sample.
7. TCA is not a chatbot, Copilot runtime interceptor, auto-remediation engine, or certification product.

## Adding a collector or control

1. Add or confirm the control semantics in `docs/evidence_contract.md`.
2. Add or update the least-privilege entry in `docs/least_privilege_matrix.md` and config where appropriate.
3. Keep the collector read-only by default.
4. Add fixture tests for `PASS`, `WARN`, `UNKNOWN`, `NOT_ACCESSIBLE`, and any downgrade/limitation behavior affected by the change.
5. Ensure `pack_builder.py` links evidence IDs to control checks and findings.
6. Run `just check`.

## Common extension points

- Report wording: `breadcrumbs.py` and `ui_renderer.py`.
- Control classification: `classifiers.py` and `pack_builder.py`.
- Manual evidence shape: `manual_evidence.py` and `config/manual_evidence_schema.json`.
- Mapping freshness/completeness: `mappings.py` and files under `config/`.
- Demo depth: `demo_dataset.py` and `demo_report.py`.

## Local commands

```bash
# Validate repository boundaries, configs, Python code, tests, and whitespace.
just check

# Create a synthetic local report without Microsoft tenant access.
just demo

# Deterministically regenerate and verify the committed synthetic sample.
just sample

# Serve generated artifacts locally on 127.0.0.1.
just serve
```

Without `just`, use the equivalent script commands documented in `README.md`.
