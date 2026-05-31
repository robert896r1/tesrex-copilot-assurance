from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "serve_artifacts.py"

spec = importlib.util.spec_from_file_location("serve_artifacts", SCRIPT)
assert spec and spec.loader
serve_artifacts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(serve_artifacts)


class ServeArtifactsTests(unittest.TestCase):
    def test_artifact_url_removes_artifacts_prefix(self) -> None:
        url = serve_artifacts.artifact_url("artifacts/evidence_packs/run-demo/evidence_pack_ui.html", port=9999)
        self.assertEqual(url, "http://127.0.0.1:9999/evidence_packs/run-demo/evidence_pack_ui.html")

    def test_artifact_url_accepts_relative_artifact_path(self) -> None:
        url = serve_artifacts.artifact_url("evidence_packs/run-demo/evidence_pack_ui.html")
        self.assertEqual(url, "http://127.0.0.1:8766/evidence_packs/run-demo/evidence_pack_ui.html")


if __name__ == "__main__":
    unittest.main()
