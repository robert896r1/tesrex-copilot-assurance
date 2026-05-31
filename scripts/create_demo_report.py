#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.demo_report import create_demo_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a tenant-free synthetic TCA demo evidence pack and HTML report.")
    parser.add_argument("--output-root", default="artifacts", help="Root output directory. Defaults to ignored local artifacts/.")
    parser.add_argument("--timestamp", help="Optional timestamp for reproducible demo output, e.g. 20260519T120000Z.")
    args = parser.parse_args()

    paths = create_demo_report(output_root=args.output_root, timestamp=args.timestamp)
    print("TCA_DEMO_MODE=SYNTHETIC_ONLY")
    print("TCA_DEMO_WARNING=No live Microsoft tenant, Graph, Purview, SharePoint, Audit, or eDiscovery data was read.")
    print(f"DEMO_DATASET={paths.demo_dataset_dir}")
    print(f"LIVE_PROBE_SUMMARY={paths.summary}")
    print(f"EVIDENCE_PACK_JSON={paths.evidence_pack_json}")
    print(f"EVIDENCE_PACK_MD={paths.evidence_pack_markdown}")
    print(f"EVIDENCE_PACK_UI={paths.evidence_pack_ui}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
