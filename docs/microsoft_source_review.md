# Microsoft Source Review

Review date: 2026-07-20  
Mapping schema: `0.1.0`  
Scope: official Microsoft sources used by the starter-kit collectors and advisory capability mappings.

## Outcome

The implemented read-only endpoints and documented least-privilege permission names remain supported by the official sources reviewed below. The known Microsoft 365 Copilot service-plan IDs in `config/microsoft_capability_map.json` were present in Microsoft's current service-plan reference.

This was a source review, not a tenant validation. The capability map still sets `claims_complete_coverage` to `false`; absence of a known SKU or plan must not be treated as proof of `NOT_LICENSED` unless the stricter classification conditions in the mapping are met.

## Reviewed sources

| Surface | Official source | Review result |
|---|---|---|
| Subscribed SKUs | [List subscribedSkus](https://learn.microsoft.com/en-us/graph/api/subscribedsku-list?view=graph-rest-1.0) | `GET /subscribedSkus` remains available. Least application permission is `LicenseAssignment.Read.All`; `Directory.Read.All` and `Organization.Read.All` are higher-privileged alternatives. |
| Service plans | [Product names and service plan identifiers](https://learn.microsoft.com/en-us/entra/identity/users/licensing-service-plan-reference) | All service-plan IDs currently listed in `known_service_plans` were found. The mapping remains intentionally incomplete. |
| Sensitivity labels | [List sensitivityLabels](https://learn.microsoft.com/en-us/graph/api/tenantdatasecurityandgovernance-list-sensitivitylabels?view=graph-rest-1.0) | `GET /security/dataSecurityAndGovernance/sensitivityLabels` remains available. Least application permission is `SensitivityLabel.Read`; `SensitivityLabels.Read.All` is a higher-privileged alternative. |
| eDiscovery cases | [List eDiscoveryCases](https://learn.microsoft.com/en-us/graph/api/security-casesroot-list-ediscoverycases?view=graph-rest-1.0) | `GET /security/cases/ediscoveryCases` remains available with `eDiscovery.Read.All`; Microsoft also documents Purview eDiscovery RBAC requirements. Endpoint visibility alone remains partial evidence. |
| Audit search | [Create auditLogQuery](https://learn.microsoft.com/en-us/graph/api/security-auditcoreroot-post-auditlogqueries?view=graph-rest-1.0) | Query creation remains a `POST` operation and is outside the default read-only collector. The configured audit permissions remain source-aligned for capability/scope inspection only. |
| DLP for Copilot | [Learn about DLP for Microsoft 365 Copilot](https://learn.microsoft.com/en-us/purview/dlp-microsoft365-copilot-location-learn-about) | Copilot remains an Applications location for DLP. Static recognition continues to be advisory and conservative. |
| SharePoint Advanced Management | [SAM features for Copilot licensing](https://learn.microsoft.com/en-us/sharepoint/sharepoint-advanced-management-features-copilot-license) | The prior licensing URL was replaced with the current official page. The standalone SAM SKU/service-plan mapping remains unverified and therefore cannot independently produce `NOT_LICENSED`. |

## Retained limitations

- Microsoft licensing, APIs, UI names, roles, and preview features can change after this date.
- Tenant licensing and RBAC determine what a particular assessment identity can read.
- PowerShell/UI export schemas may differ by module version and tenant rollout.
- No source reviewed here establishes complete coverage for every Microsoft 365 Copilot or SharePoint Advanced Management entitlement.
- A successful list/read operation proves visibility for the assessed identity and scope, not policy effectiveness.
