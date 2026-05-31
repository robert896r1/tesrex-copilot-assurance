#!/usr/bin/env python3
"""Verify committed public sample assets remain synthetic and safe to publish."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "samples" / "copilot-assurance"
REQUIRED = [
    SAMPLE_DIR / "README.md",
    SAMPLE_DIR / "evidence_pack.md",
    SAMPLE_DIR / "evidence_pack.json",
    ROOT / "docs" / "assets" / "sample-report-overview.png",
]
FORBIDDEN_MARKERS = [
    "/tmp/tca-public-sample",
    "/home/robert",
    "@tesrex.com",
]


def fail(message: str) -> int:
    print(f"Sample asset verification failed: {message}", file=sys.stderr)
    return 1


def main() -> int:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        return fail("missing required sample assets: " + ", ".join(missing))

    pack = json.loads((SAMPLE_DIR / "evidence_pack.json").read_text(encoding="utf-8"))
    notice = pack.get("sample_notice") or {}
    run = pack.get("assessment_run") or {}
    if run.get("tenant_id") != "TCA-DEMO-SYNTHETIC":
        return fail("sample evidence pack tenant_id is not TCA-DEMO-SYNTHETIC")
    if notice.get("synthetic_only") is not True or notice.get("not_customer_evidence") is not True:
        return fail("sample_notice must mark the pack as synthetic-only and not customer evidence")
    if "demo_evidence_present" not in set(run.get("limitations") or []):
        return fail("assessment run must disclose demo evidence")

    for rel in ["README.md", "evidence_pack.md", "evidence_pack.json"]:
        text = (SAMPLE_DIR / rel).read_text(encoding="utf-8")
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                return fail(f"forbidden marker {marker!r} found in samples/copilot-assurance/{rel}")

    print("Sample asset verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
