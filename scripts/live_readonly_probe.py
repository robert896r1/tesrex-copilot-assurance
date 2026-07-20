#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.live_probe import LiveProbeSafetyError, run_live_readonly_probe


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run allowlisted, read-only Microsoft tenant probes after verifying the authenticated tenant."
    )
    parser.add_argument(
        "--expected-tenant-id",
        default=os.environ.get("AZURE_TENANT_ID"),
        help="Tenant ID that must match the active Azure CLI context. Defaults to AZURE_TENANT_ID.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/live_probe",
        help="Ignored local directory for probe evidence. Defaults to artifacts/live_probe.",
    )
    args = parser.parse_args()
    if not args.expected_tenant_id or not args.expected_tenant_id.strip():
        parser.error("set --expected-tenant-id or export AZURE_TENANT_ID before tenant access")

    try:
        output = run_live_readonly_probe(
            base_dir=args.output_dir,
            expected_tenant_id=args.expected_tenant_id,
        )
    except LiveProbeSafetyError as exc:
        print(f"TCA_LIVE_PROBE_BLOCKED={exc}", file=sys.stderr)
        return 2
    print(output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
