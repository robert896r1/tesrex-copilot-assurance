#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.pack_builder import build_evidence_pack_from_live_probe, latest_live_probe_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Tesrex Copilot Governance Evidence Pack from live probe summary.")
    parser.add_argument("--summary", help="Path to artifacts/live_probe/<timestamp>/summary.json. Defaults to latest.")
    parser.add_argument("--output-dir", default="artifacts/evidence_packs")
    parser.add_argument("--manual-evidence", action="append", default=[], help="Manual evidence bundle JSON. May be repeated.")
    args = parser.parse_args()

    summary = Path(args.summary) if args.summary else latest_live_probe_summary()
    json_path, md_path, _pack = build_evidence_pack_from_live_probe(summary, output_dir=args.output_dir, manual_evidence_paths=args.manual_evidence)
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
