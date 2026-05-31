#!/usr/bin/env python3
"""Create local synthetic TCA demo evidence fixtures.

This public helper is tenant-free: it does not call Azure, Graph, Purview,
SharePoint, Audit, or eDiscovery. Use scripts/create_demo_report.py for the full
starter-kit demo report path.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.demo_dataset import create_demo_dataset, utc_timestamp


def main() -> int:
    parser = argparse.ArgumentParser(description="Create local synthetic TCA demo evidence fixtures.")
    parser.add_argument("--output-dir", default="artifacts/demo_dataset")
    parser.add_argument("--timestamp", default=utc_timestamp())
    parser.add_argument("--expiry-days", type=int, default=30)
    parser.add_argument("--tenant-id", default="TCA-DEMO-SYNTHETIC", help="Synthetic tenant identifier stamped into local demo fixtures.")
    parser.add_argument("--provided-by", default="TCA local demo mode", help="Provider label stamped into local demo fixtures.")
    args = parser.parse_args()

    out = create_demo_dataset(
        output_root=args.output_dir,
        timestamp=args.timestamp,
        tenant_id=args.tenant_id,
        provided_by=args.provided_by,
        expiry_days=args.expiry_days,
    )
    print("TCA_DEMO_MODE=SYNTHETIC_ONLY")
    print("TCA_DEMO_WARNING=No live Microsoft tenant, Graph, Purview, SharePoint, Audit, or eDiscovery data was read.")
    print(f"DEMO_DATASET={out}")
    print(f"MANUAL_EVIDENCE={out / 'manual_evidence_bundle.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
