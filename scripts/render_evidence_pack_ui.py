#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.ui_renderer import render_evidence_pack_html


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a human-friendly static UI for a Tesrex evidence pack.")
    parser.add_argument("pack", help="Path to evidence_pack.json")
    parser.add_argument("--output", help="Output HTML path. Defaults to evidence_pack_ui.html beside the pack.")
    args = parser.parse_args()
    print(render_evidence_pack_html(args.pack, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
