#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys

FORBIDDEN_PREFIXES = (
    "artifacts/live_probe/",
    "artifacts/evidence_packs/",
    "artifacts/demo_dataset/",
    "artifacts/ediscovery_functional/",
)

ALLOWED = {"artifacts/.gitkeep"}


def main() -> int:
    result = subprocess.run(["git", "ls-files"], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        print(result.stderr.strip() or "git ls-files failed", file=sys.stderr)
        return result.returncode
    blocked = []
    for line in result.stdout.splitlines():
        if line in ALLOWED:
            continue
        if any(line.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            blocked.append(line)
    if blocked:
        print("Committed evidence artifact guard failed.", file=sys.stderr)
        print("Do not commit generated tenant/demo evidence outputs:", file=sys.stderr)
        for path in blocked:
            print(f"- {path}", file=sys.stderr)
        print("\nKeep generated reports local or publish sanitized samples through an explicit launch-assets decision.", file=sys.stderr)
        return 1
    print("Committed evidence artifact guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
