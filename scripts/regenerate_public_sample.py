#!/usr/bin/env python3
"""Regenerate the committed, tenant-free public sample from synthetic sources."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.demo_report import create_demo_report

SAMPLE_DIR = Path("samples/copilot-assurance")
SOURCE_DIR = SAMPLE_DIR / "generated-source"
SAMPLE_TIMESTAMP = "20260720T000000Z"
SAMPLE_GENERATED_AT = "2026-07-20T00:00:00Z"


def main() -> int:
    if Path.cwd().resolve() != ROOT.resolve():
        raise SystemExit("Run scripts/regenerate_public_sample.py from the repository root.")
    if SOURCE_DIR.exists():
        shutil.rmtree(SOURCE_DIR)
    paths = create_demo_report(
        output_root=SOURCE_DIR,
        timestamp=SAMPLE_TIMESTAMP,
        generated_at_utc=SAMPLE_GENERATED_AT,
    )
    shutil.copy2(paths.evidence_pack_json, SAMPLE_DIR / "evidence_pack.json")
    shutil.copy2(paths.evidence_pack_markdown, SAMPLE_DIR / "evidence_pack.md")
    print("TCA_PUBLIC_SAMPLE=REGENERATED")
    print(f"SAMPLE_JSON={SAMPLE_DIR / 'evidence_pack.json'}")
    print(f"SAMPLE_MARKDOWN={SAMPLE_DIR / 'evidence_pack.md'}")
    print(f"SYNTHETIC_SOURCE={SOURCE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
