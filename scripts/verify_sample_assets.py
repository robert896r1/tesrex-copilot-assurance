#!/usr/bin/env python3
"""Verify committed public sample assets remain synthetic and safe to publish."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
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
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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

    evidence_items = pack.get("evidence_items") or []
    if not evidence_items:
        return fail("sample evidence inventory is empty")
    source_root = (SAMPLE_DIR / "generated-source").resolve()
    for item in evidence_items:
        evidence_id = item.get("evidence_id") or "(unknown evidence)"
        raw_path = item.get("raw_artifact_path")
        expected_hash = item.get("content_hash")
        if not raw_path or Path(raw_path).is_absolute():
            return fail(f"{evidence_id} must use a repository-relative raw_artifact_path")
        artifact = (ROOT / raw_path).resolve()
        try:
            artifact.relative_to(source_root)
        except ValueError:
            return fail(f"{evidence_id} artifact path escapes samples/copilot-assurance/generated-source")
        if not artifact.is_file():
            return fail(f"{evidence_id} artifact does not exist: {raw_path}")
        if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
            return fail(f"{evidence_id} does not contain a valid SHA-256 hash")
        actual_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            return fail(f"{evidence_id} artifact hash mismatch: {raw_path}")
        artifact_text = artifact.read_text(encoding="utf-8")
        if '"is_synthetic": true' not in artifact_text or '"demo_mode": true' not in artifact_text:
            return fail(f"{evidence_id} artifact lacks synthetic/demo markers: {raw_path}")

    pack002 = next(
        (item for item in pack.get("control_checks") or [] if item.get("control_check_id") == "PACK-002"),
        None,
    )
    if not pack002 or pack002.get("status") != "PASS":
        return fail("PACK-002 must PASS after verifying every committed sample artifact")
    if "Verified the existence and SHA-256 hash" not in str(pack002.get("status_reason") or ""):
        return fail("PACK-002 status reason must describe artifact existence and hash verification")

    for rel in ["README.md", "evidence_pack.md", "evidence_pack.json"]:
        text = (SAMPLE_DIR / rel).read_text(encoding="utf-8")
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                return fail(f"forbidden marker {marker!r} found in samples/copilot-assurance/{rel}")

    print("Sample asset verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
