#!/usr/bin/env python3
"""Serve generated TCA artifacts from localhost for review.

This helper serves the ignored local artifacts directory only. It is for local
review, not production hosting, and provides no authentication.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def artifact_url(path: str | Path, *, directory: str | Path = "artifacts", port: int = 8766) -> str:
    """Return the localhost URL for an artifact path served from ``directory``."""

    artifact_root = Path(directory)
    artifact_path = Path(path)
    try:
        relative = artifact_path.relative_to(artifact_root)
    except ValueError:
        relative = artifact_path
    return f"http://127.0.0.1:{port}/{relative.as_posix()}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve generated TCA artifacts from 127.0.0.1 for local report review.")
    parser.add_argument("--port", type=int, default=8766, help="Localhost port to bind. Default: 8766.")
    parser.add_argument("--directory", default="artifacts", help="Directory to serve. Default: artifacts.")
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists() or not directory.is_dir():
        raise SystemExit(f"Artifact directory does not exist: {directory}. Run scripts/create_demo_report.py first.")

    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print("TCA_ARTIFACT_SERVER=LOCAL_ONLY")
    print(f"SERVING_DIRECTORY={directory}")
    print(f"BASE_URL=http://127.0.0.1:{args.port}/")
    print("OPEN_REPORT_PATTERN=http://127.0.0.1:{}/evidence_packs/run-<timestamp>/evidence_pack_ui.html".format(args.port))
    print("WARNING=No authentication is provided. Do not expose this server beyond localhost.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nTCA_ARTIFACT_SERVER=STOPPED")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
