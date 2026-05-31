from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
from pathlib import Path

from .base import ProbeResult, ProbeStatus

MODULES = {
    "powershell.exchange_online_management": {
        "module": "ExchangeOnlineManagement",
        "control_ids": ("DLP-001", "DLP-002", "EDISC-001"),
        "source_ref": "https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-dlpcompliancepolicy?view=exchange-ps",
    },
    "powershell.sharepoint_online": {
        "module": "Microsoft.Online.SharePoint.PowerShell",
        "control_ids": ("SAM-001",),
        "source_ref": "https://learn.microsoft.com/en-us/sharepoint/powershell-for-data-access-governance",
    },
}


def probe_powershell_modules(artifact_dir: str | Path | None = None) -> list[ProbeResult]:
    results: list[ProbeResult] = []
    pwsh = shutil.which("pwsh")
    if not pwsh:
        for probe_id, meta in MODULES.items():
            results.append(ProbeResult(probe_id, ProbeStatus.UNKNOWN, meta["control_ids"], meta["source_ref"], limitations=["local_tool_missing"], status_reason="PowerShell executable 'pwsh' is not available locally; tenant connection was not attempted."))
        return results
    for probe_id, meta in MODULES.items():
        module = meta["module"]
        command = f"$m = Get-Module -ListAvailable {json.dumps(module)} | Select-Object -First 1 Name,Version,Path; if ($null -eq $m) {{ '{{}}' }} else {{ $m | ConvertTo-Json -Compress }}"
        completed = subprocess.run([pwsh, "-NoLogo", "-NoProfile", "-Command", command], text=True, capture_output=True, check=False)
        raw = completed.stdout if completed.returncode == 0 else completed.stderr
        raw_path = None
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        if artifact_dir is not None:
            out = Path(artifact_dir)
            out.mkdir(parents=True, exist_ok=True)
            raw_path = str(out / f"{probe_id.replace('.', '_')}.json")
            Path(raw_path).write_text(raw, encoding="utf-8")
        if completed.returncode != 0:
            results.append(ProbeResult(probe_id, ProbeStatus.UNKNOWN, meta["control_ids"], meta["source_ref"], raw_artifact_path=raw_path, content_hash=digest, limitations=["local_tool_error"], status_reason="PowerShell module availability check failed locally; tenant connection was not attempted."))
            continue
        try:
            parsed = json.loads(raw or "{}")
        except json.JSONDecodeError:
            parsed = {}
        if parsed:
            results.append(ProbeResult(probe_id, ProbeStatus.OK, meta["control_ids"], meta["source_ref"], raw_artifact_path=raw_path, content_hash=digest, summary={"module": module, "available": True, "version": str(parsed.get("Version", ""))}, status_reason="Required PowerShell module is locally available. No tenant connection was attempted."))
        else:
            results.append(ProbeResult(probe_id, ProbeStatus.UNKNOWN, meta["control_ids"], meta["source_ref"], raw_artifact_path=raw_path, content_hash=digest, limitations=["local_module_missing"], status_reason=f"PowerShell module {module} is not installed locally; tenant connection was not attempted."))
    return results
