#!/usr/bin/env python3
"""Fail if known legacy gateway/chat runtime paths are introduced into TCA.

This guard is intentionally path-based. Documentation may discuss old work for
lessons learned, but the canonical TCA repo must not absorb the old runtime,
Teams bot, Copilot Studio, ADX, or gateway implementation trees by accident.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PATHS = [
    "artifacts/teams",
    "db/governance_store",
    "services/teams-adapter",
    "services/teams-sdk-agent",
    "src/gateway",
    "src/workflows",
    "src/audit/adx_writer.ts",
    "scripts/copilot_studio_apply_runtime_profile.cjs",
    "scripts/deploy_gatewaypilot.sh",
    "scripts/deploy_gatewaypilot_adapter.sh",
    "scripts/deploy_teams_sdk_agent.sh",
    "tesrex_gateway_contracts.schema.json",
]


def exists_forbidden(rel: str) -> bool:
    candidate = ROOT / rel
    if candidate.exists():
        return True
    if rel.endswith(".sh") or rel.endswith(".cjs") or rel.endswith(".ts") or rel.endswith(".json"):
        return False
    return any(ROOT.glob(f"{rel}/**/*"))


def main() -> int:
    found = [rel for rel in FORBIDDEN_PATHS if exists_forbidden(rel)]
    if found:
        print("Repository boundary check failed.", file=sys.stderr)
        print("The canonical TCA repo must not contain legacy gateway/chat runtime paths:", file=sys.stderr)
        for rel in found:
            print(f"- {rel}", file=sys.stderr)
        print("\nIf a file is intentionally salvaged, document the decision first in a reviewed pull request and update this guard in the same patch.", file=sys.stderr)
        return 1
    print("Repository boundary check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
