#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.live_probe import run_live_readonly_probe
from tesrex_assurance.pack_builder import build_evidence_pack_from_live_probe


def main() -> int:
    parser = argparse.ArgumentParser(description="Run starter-kit read-only live probes and generate an evidence pack.")
    parser.add_argument("--manual-evidence", action="append", default=[], help="Manual evidence bundle JSON. May be repeated.")
    args = parser.parse_args()
    probe_dir = run_live_readonly_probe()
    summary = probe_dir / "summary.json"
    json_path, md_path, _pack = build_evidence_pack_from_live_probe(summary, manual_evidence_paths=args.manual_evidence)
    print(f"LIVE_PROBE={probe_dir}")
    print(f"EVIDENCE_PACK_JSON={json_path}")
    print(f"EVIDENCE_PACK_MD={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
