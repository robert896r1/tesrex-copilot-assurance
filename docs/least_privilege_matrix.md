# Least-Privilege Collector Matrix

Status: starter kit baseline
Last reviewed: 2026-04-30

Machine-readable source: `config/collector_permission_matrix.json`

## Policy

The starter kit uses read-only collectors by default. Permissions that can create queries, validation searches, exports, holds, or tenant artifacts are not default permissions; they require an explicit bounded-validation approval for that run.

## Collector groups

| Collector | Controls | Least-privilege posture | Default? |
|---|---:|---|---|
| Graph organization | LIC-001, PACK-002 | `Organization.Read.All` or equivalent directory read | Yes |
| Graph subscribed SKUs | LIC-001, LIC-002, SAM-001 | license/subscription read only | Yes |
| Graph sensitivity labels | LABEL-001 | sensitivity-label taxonomy read | Yes |
| Graph audit token-scope check | AUD-001 | scope/role presence only; no audit query creation | Yes |
| Graph eDiscovery case visibility | EDISC-002 | `eDiscovery.Read.All` plus Purview app-only RBAC prerequisite | Yes |
| Purview DLP policy inventory | DLP-001, DLP-002 | policy/rule read only or manual export | Planned/read-only |
| Purview retention stance | EDISC-001 | retention policy read only or manual export | Planned/read-only |
| SharePoint SAM capability | SAM-001 | SharePoint admin read/capability evidence; no DAG report creation by default | Planned/read-only |
| eDiscovery bounded validation | EDISC-002 | `eDiscovery.ReadWrite.All` plus Purview role; explicit approval only | No |

If `eDiscovery.ReadWrite.All` is present in a default run without a bounded-validation flag, the evidence pack should flag the assessment identity as broader than starter kit default requirements. If a run is explicitly marked as bounded validation, that permission is expected for the bounded validation scope but still must not be used by default collectors.

## Over-privilege handling

If the current assessment identity has broader permissions than the default collector requires, the pack should disclose that as assessment context. Over-privilege is not automatically a tenant control failure, but it is relevant to product deployment hardening.

## Rule

A collector cannot be considered starter kit-stable until its required permissions and side-effect boundary are listed here and in `config/collector_permission_matrix.json`.
