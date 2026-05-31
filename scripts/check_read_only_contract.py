#!/usr/bin/env python3
"""Guard the public starter kit's read-only Microsoft-tenant contract.

This is intentionally conservative. The public starter kit may write local
artifacts under ``artifacts/``, but default collectors and tenant-connected
scripts must not contain Microsoft Graph/Purview write operations.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.collectors.graph import graph_probe_specs  # noqa: E402

SCAN_PATHS = [
    ROOT / "src",
    ROOT / "scripts",
]

BANNED_PATTERNS = [
    re.compile(r"\baz\s+rest\b[^\n]*(?:--method|-m)\s+(?!get\b)(post|put|patch|delete)\b", re.IGNORECASE),
    re.compile(r"\brequests\.(post|put|patch|delete)\s*\(", re.IGNORECASE),
    re.compile(r"\bhttpx\.(post|put|patch|delete)\s*\(", re.IGNORECASE),
    re.compile(r"\bmethod\s*=\s*['\"](POST|PUT|PATCH|DELETE)['\"]", re.IGNORECASE),
    re.compile(r"\b(New|Set|Remove|Update|Add)-(?:ComplianceSearch|DlpCompliance|RetentionCompliance|Label|RoleGroupMember|ServicePrincipal)\b", re.IGNORECASE),
]


def iter_files(path: Path):
    if path.is_file():
        yield path
    elif path.is_dir():
        for child in path.rglob("*"):
            if child.is_file() and child.suffix in {".py", ".ps1", ".sh"}:
                yield child


def main() -> int:
    failures: list[str] = []

    for probe_id, spec in graph_probe_specs().items():
        if spec.method.upper() != "GET":
            failures.append(f"Graph probe {probe_id} uses non-GET method {spec.method!r}")

    for path in SCAN_PATHS:
        for file_path in iter_files(path):
            text = file_path.read_text(encoding="utf-8")
            for pattern in BANNED_PATTERNS:
                for match in pattern.finditer(text):
                    line_no = text.count("\n", 0, match.start()) + 1
                    try:
                        display_path = file_path.relative_to(ROOT)
                    except ValueError:
                        display_path = file_path
                    failures.append(f"{display_path}:{line_no}: banned write-like operation: {match.group(0)}")

    if failures:
        print("Read-only contract check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Read-only contract check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
