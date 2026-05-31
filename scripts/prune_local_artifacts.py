#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.retention import (
    DEFAULT_ARTIFACT_ROOTS,
    DEFAULT_LOCAL_ARTIFACT_RETENTION_DAYS,
    filter_unlocked_candidates,
    find_local_artifact_retention_candidates,
    locked_local_artifact_paths,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune local Tesrex assessment artifacts only. Does not touch Microsoft tenant-side searches or data.")
    parser.add_argument("--days", type=int, default=DEFAULT_LOCAL_ARTIFACT_RETENTION_DAYS, help="Local artifact retention window in days. Default: 30.")
    parser.add_argument("--root", action="append", dest="roots", help="Local artifact root to consider. May be repeated.")
    parser.add_argument("--execute", action="store_true", help="Actually delete candidates. Default is dry-run.")
    parser.add_argument("--ignore-locks", action="store_true", help="Allow deletion of artifacts referenced by evidence packs. Not recommended.")
    args = parser.parse_args()

    roots = tuple(args.roots) if args.roots else DEFAULT_ARTIFACT_ROOTS
    all_candidates = find_local_artifact_retention_candidates(roots, days=args.days)
    locked = locked_local_artifact_paths()
    candidates = all_candidates if args.ignore_locks else filter_unlocked_candidates(all_candidates, locked)
    mode = "EXECUTE" if args.execute else "DRY_RUN"
    print(f"LOCAL_ARTIFACT_RETENTION mode={mode} days={args.days} candidates={len(candidates)} locked_paths={len(locked)}")
    print("Tenant-side eDiscovery validation searches are not touched by this script.")
    if locked and not args.ignore_locks:
        print("Artifacts referenced by evidence packs or active findings are locked. Use --ignore-locks only after archive/supersession review.")
    for candidate in candidates:
        print(f"{candidate.path}\tage_days={candidate.age_days}\tcutoff={candidate.cutoff_utc}")
        if args.execute:
            shutil.rmtree(candidate.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
