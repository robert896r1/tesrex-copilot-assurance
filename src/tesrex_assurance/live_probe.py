"""Default read-only live probe orchestration.

Runs allowlisted local/Azure/Graph/Powershell capability checks and writes raw local artifacts plus a normalized summary. Default probes must not mutate the tenant."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .collectors.base import ProbeResult, ProbeStatus
from .collectors.graph import ReadOnlyGraphCollector
from .collectors.powershell import probe_powershell_modules
from .models import to_plain

AUDIT_QUERY_SCOPE_NAMES = {
    "AuditLogsQuery.Read.All",
    "AuditLogsQuery-Entra.Read.All",
    "AuditLogsQuery-Exchange.Read.All",
    "AuditLogsQuery-OneDrive.Read.All",
    "AuditLogsQuery-SharePoint.Read.All",
    "AuditLogsQuery-Endpoint.Read.All",
    "AuditLogsQuery-CRM.Read.All",
}


def run_live_readonly_probe(base_dir: str | Path = "artifacts/live_probe") -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outdir = Path(base_dir) / timestamp
    raw_dir = outdir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    account_payload, account_result = _run_json_command(["az", "account", "show", "--output", "json"], raw_dir / "az_account.json")
    cloud_payload, cloud_result = _run_json_command(["az", "cloud", "show", "--output", "json"], raw_dir / "az_cloud.json")
    environment_name = account_payload.get("environmentName") if isinstance(account_payload, dict) else None
    if not environment_name and isinstance(cloud_payload, dict):
        environment_name = cloud_payload.get("name")

    results: list[ProbeResult] = [account_result, cloud_result, _introspect_graph_token(raw_dir)]
    collector = ReadOnlyGraphCollector(environment_name=environment_name, artifact_dir=raw_dir)
    for probe_id in collector.specs:
        results.append(collector.run_probe(probe_id))
    results.extend(probe_powershell_modules(raw_dir))

    summary = {
        "generated_at_utc": timestamp,
        "environment_name": environment_name,
        "tenant_id": account_payload.get("tenantId") if isinstance(account_payload, dict) else None,
        "subscription_id": account_payload.get("id") if isinstance(account_payload, dict) else None,
        "user": (account_payload.get("user") or {}).get("name") if isinstance(account_payload, dict) else None,
        "boundary": {
            "mutation_methods_used": [],
            "broad_content_scan": False,
            "tenant_policy_changes": False,
            "permission_changes": False,
            "audit_query_created": False,
        },
        "probe_results": [to_plain(result) for result in results],
    }
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    (outdir / "summary.json").write_text(rendered + "\n", encoding="utf-8")
    (outdir / "summary.sha256").write_text(hashlib.sha256(rendered.encode("utf-8")).hexdigest() + "\n", encoding="utf-8")
    return outdir


def _run_json_command(command: list[str], raw_path: Path) -> tuple[dict[str, Any] | None, ProbeResult]:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    raw = completed.stdout if completed.returncode == 0 else completed.stderr
    raw_path.write_text(raw, encoding="utf-8")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    probe_id = raw_path.stem
    if completed.returncode != 0:
        return None, ProbeResult(probe_id, ProbeStatus.NOT_ACCESSIBLE if _looks_like_access_denial(raw) else ProbeStatus.UNKNOWN, ("PACK-002",), "Azure CLI", str(raw_path), digest, limitations=["local_auth_or_cli_failure"], status_reason=_compact(raw))
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None, ProbeResult(probe_id, ProbeStatus.UNKNOWN, ("PACK-002",), "Azure CLI", str(raw_path), digest, limitations=["malformed_response"], status_reason="Azure CLI returned non-JSON output for an expected JSON command.")
    return payload, ProbeResult(probe_id, ProbeStatus.OK, ("PACK-002",), "Azure CLI", str(raw_path), digest, {"keys": sorted(payload.keys())[:20] if isinstance(payload, dict) else []}, [], "Azure CLI context probe completed successfully.")


def _introspect_graph_token(raw_dir: Path) -> ProbeResult:
    completed = subprocess.run(["az", "account", "get-access-token", "--resource-type", "ms-graph", "--output", "json"], text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raw = completed.stderr
        path = raw_dir / "graph_token_error.json"
        path.write_text(raw, encoding="utf-8")
        return ProbeResult("graph.token_scopes", ProbeStatus.UNKNOWN, ("AUD-001", "PACK-002"), "Azure CLI token introspection", str(path), hashlib.sha256(raw.encode("utf-8")).hexdigest(), limitations=["token_introspection_failed"], status_reason=_compact(raw))
    try:
        token_payload = json.loads(completed.stdout)
        claims = _decode_jwt_claims(token_payload["accessToken"])
    except Exception as exc:  # noqa: BLE001
        raw = json.dumps({"error": str(exc)})
        path = raw_dir / "graph_token_claims_error.json"
        path.write_text(raw, encoding="utf-8")
        return ProbeResult("graph.token_scopes", ProbeStatus.UNKNOWN, ("AUD-001", "PACK-002"), "Azure CLI token introspection", str(path), hashlib.sha256(raw.encode("utf-8")).hexdigest(), limitations=["token_introspection_failed"], status_reason="Graph access token was obtained but claims could not be decoded locally.")
    scopes = set(str(claims.get("scp", "")).split())
    roles = set(claims.get("roles") or [])
    audit_scopes = sorted((scopes | roles).intersection(AUDIT_QUERY_SCOPE_NAMES))
    redacted_claims = {
        "aud": claims.get("aud"),
        "iss": claims.get("iss"),
        "tid": claims.get("tid"),
        "appid": claims.get("appid"),
        "scp": sorted(scopes),
        "roles": sorted(roles),
        "audit_query_scopes_present": audit_scopes,
        "raw_access_token_retained": False,
    }
    raw = json.dumps(redacted_claims, indent=2, sort_keys=True)
    path = raw_dir / "graph_token_claims_redacted.json"
    path.write_text(raw + "\n", encoding="utf-8")
    status = ProbeStatus.OK if audit_scopes else ProbeStatus.NOT_ACCESSIBLE
    limitations = [] if audit_scopes else ["permission_gap", "audit_query_scope_not_present"]
    return ProbeResult("graph.token_scopes", status, ("AUD-001",), "https://learn.microsoft.com/en-us/graph/api/security-auditcoreroot-post-auditlogqueries?view=graph-rest-1.0", str(path), hashlib.sha256(raw.encode("utf-8")).hexdigest(), {"audit_query_scopes_present": audit_scopes, "raw_access_token_retained": False}, limitations + ["raw_secret_not_retained"], "Decoded redacted Graph token claims locally; no audit query was created.")


def _decode_jwt_claims(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        raise ValueError("token is not a JWT")
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(payload.encode("ascii")))


def _looks_like_access_denial(raw: str) -> bool:
    text = raw.lower()
    return any(marker in text for marker in ["authorization", "forbidden", "unauthorized", "access denied", "403", "401"])


def _compact(raw: str) -> str:
    text = " ".join(raw.strip().split())
    return text[:500] if text else "No diagnostic text returned."
