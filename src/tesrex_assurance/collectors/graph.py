from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .base import ProbeResult, ProbeSpec, ProbeStatus

GRAPH_BASE_URLS = {
    "AzureCloud": "https://graph.microsoft.com",
    "AzureUSGovernment": "https://graph.microsoft.us",
    "AzureChinaCloud": "https://microsoftgraph.chinacloudapi.cn",
}


def graph_base_url_for_cloud(environment_name: str | None) -> tuple[str | None, list[str]]:
    if not environment_name:
        return GRAPH_BASE_URLS["AzureCloud"], ["cloud_context_unknown"]
    if environment_name not in GRAPH_BASE_URLS:
        return None, ["national_cloud_limited", "unsupported_cloud_environment"]
    return GRAPH_BASE_URLS[environment_name], []


def graph_probe_specs() -> dict[str, ProbeSpec]:
    return {
        "graph.organization": ProbeSpec(
            "graph.organization", ("LIC-001", "PACK-002"), "GET",
            "/v1.0/organization?$select=id,displayName,verifiedDomains",
            "Read tenant organization metadata to confirm Graph tenant context.",
            "https://learn.microsoft.com/en-us/graph/api/organization-get",
            ("Organization.Read.All", "Directory.Read.All"),
        ),
        "graph.subscribed_skus": ProbeSpec(
            "graph.subscribed_skus", ("LIC-001", "LIC-002", "SAM-001"), "GET",
            "/v1.0/subscribedSkus",
            "Read tenant commercial subscriptions and service plans.",
            "https://learn.microsoft.com/en-us/graph/api/subscribedsku-list?view=graph-rest-1.0",
            ("LicenseAssignment.Read.All", "Directory.Read.All", "Organization.Read.All"),
        ),
        "graph.sensitivity_labels": ProbeSpec(
            "graph.sensitivity_labels", ("LABEL-001",), "GET",
            "/v1.0/security/dataSecurityAndGovernance/sensitivityLabels?$top=1",
            "Probe ability to list tenant sensitivity labels without enumerating full taxonomy.",
            "https://learn.microsoft.com/en-us/graph/api/tenantdatasecurityandgovernance-list-sensitivitylabels?view=graph-rest-1.0",
            ("SensitivityLabel.Read", "SensitivityLabels.Read.All"),
        ),
        "graph.ediscovery_cases": ProbeSpec(
            "graph.ediscovery_cases", ("EDISC-002",), "GET",
            "/v1.0/security/cases/ediscoveryCases?$top=1",
            "Probe ability to list eDiscovery cases without creating or changing cases.",
            "https://learn.microsoft.com/en-us/graph/api/security-casesroot-list-ediscoverycases?view=graph-rest-1.0",
            ("eDiscovery.Read.All",),
            (
                "Purview app-only service principal",
                "eDiscovery Manager role group",
                "eDiscovery Administrator case-admin assignment",
            ),
        ),
    }


class ReadOnlyGraphCollector:
    """Allowlisted GET-only Microsoft Graph probe runner using Azure CLI auth."""

    def __init__(self, environment_name: str | None = "AzureCloud", artifact_dir: str | Path | None = None) -> None:
        self.environment_name = environment_name
        self.base_url, self.cloud_limitations = graph_base_url_for_cloud(environment_name)
        self.artifact_dir = Path(artifact_dir) if artifact_dir else None
        self._specs = graph_probe_specs()

    @property
    def specs(self) -> dict[str, ProbeSpec]:
        return dict(self._specs)

    def run_probe(self, probe_id: str) -> ProbeResult:
        if probe_id not in self._specs:
            return ProbeResult(probe_id, ProbeStatus.UNKNOWN, (), "", limitations=["probe_not_allowlisted"], status_reason="Probe is not allowlisted for the read-only Graph collector.")
        spec = self._specs[probe_id]
        if self.base_url is None:
            return ProbeResult(probe_id, ProbeStatus.UNKNOWN, spec.control_ids, spec.source_ref, limitations=list(self.cloud_limitations), status_reason=f"No supported Microsoft Graph base URL for cloud environment {self.environment_name!r}.")
        url = f"{self.base_url}{spec.path}"
        completed = subprocess.run(["az", "rest", "--method", "get", "--url", url, "--output", "json"], text=True, capture_output=True, check=False)
        raw = completed.stdout if completed.returncode == 0 else completed.stderr
        artifact_text = _redact_raw_artifact(raw)
        raw_path, digest = self._write_raw(probe_id, artifact_text)
        if completed.returncode != 0:
            status = ProbeStatus.NOT_ACCESSIBLE if _looks_like_access_denial(raw) else ProbeStatus.UNKNOWN
            limitations = ["permission_gap"] if status == ProbeStatus.NOT_ACCESSIBLE else ["probe_failed"]
            if probe_id == "graph.ediscovery_cases" and status == ProbeStatus.NOT_ACCESSIBLE:
                limitations.extend(["purview_rbac_gap", "prerequisite_missing"])
            return ProbeResult(probe_id, status, spec.control_ids, spec.source_ref, raw_path, digest, limitations=limitations + list(self.cloud_limitations), status_reason=_compact_reason(artifact_text))
        return ProbeResult(probe_id, ProbeStatus.OK, spec.control_ids, spec.source_ref, raw_path, digest, _summarize_json_payload(raw), list(self.cloud_limitations), "GET probe completed successfully.")

    def _write_raw(self, probe_id: str, raw: str) -> tuple[str | None, str | None]:
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        if self.artifact_dir is None:
            return None, digest
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        path = self.artifact_dir / f"{probe_id.replace('.', '_')}.json"
        path.write_text(raw, encoding="utf-8")
        return str(path), digest


def _looks_like_access_denial(raw: str) -> bool:
    parsed = _try_parse_error_payload(raw)
    if parsed:
        code = str(parsed.get("code", "")).lower()
        message = str(parsed.get("message", "")).lower()
        if any(marker in f"{code} {message}" for marker in ["authorization_requestdenied", "insufficient", "forbidden", "unauthorized", "access denied", "403", "401"]):
            return True
    text = raw.lower()
    return any(marker in text for marker in ["authorization_requestdenied", "insufficient privileges", "forbidden", "unauthorized", "access denied", "403", "401"])


def _try_parse_error_payload(raw: str) -> dict[str, Any] | None:
    candidates = [raw.strip()]
    if "(" in raw and raw.rstrip().endswith(")"):
        candidates.append(raw[raw.find("(") + 1: raw.rfind(")")])
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                return error
            return payload
    return None


def _redact_raw_artifact(raw: str) -> str:
    """Remove obvious bearer-token or secret-shaped values before local artifact retention."""

    redacted = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", raw)
    redacted = re.sub(r"(?i)(\"(?:access_token|refresh_token|client_secret|secret)\"\s*:\s*\")[^\"]+(\")", r"\1[REDACTED]\2", redacted)
    redacted = re.sub(r"(?i)((?:access_token|refresh_token|client_secret|secret)=)[^\s&]+", r"\1[REDACTED]", redacted)
    return redacted


def _compact_reason(raw: str) -> str:
    text = " ".join(raw.strip().split())
    return text[:500] if text else "Probe failed without returned error text."


def _summarize_json_payload(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"payload_shape": "non_json"}
    if isinstance(payload, dict) and isinstance(payload.get("value"), list):
        return {"payload_shape": "collection", "count_returned": len(payload["value"])}
    if isinstance(payload, dict):
        return {"payload_shape": "object", "keys": sorted(payload.keys())[:20]}
    return {"payload_shape": type(payload).__name__}
