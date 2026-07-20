from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LiveProbeCliTests(unittest.TestCase):
    def _environment_with_fake_az(self, base: Path) -> tuple[dict[str, str], Path]:
        marker = base / "az-invocations.txt"
        fake_bin = base / "bin"
        fake_bin.mkdir()
        fake_az = fake_bin / "az"
        fake_az.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "marker = Path(os.environ['TCA_AZ_MARKER'])\n"
            "marker.write_text((marker.read_text() if marker.exists() else '') + ' '.join(sys.argv[1:]) + '\\n')\n"
            "if sys.argv[1:3] == ['account', 'show']:\n"
            "    print(json.dumps({'tenantId': 'actual-tenant', 'environmentName': 'AzureCloud', 'user': {'name': 'tester'}}))\n"
            "    raise SystemExit(0)\n"
            "raise SystemExit(91)\n",
            encoding="utf-8",
        )
        fake_az.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"
        env["PYTHONPATH"] = str(ROOT / "src")
        env["TCA_AZ_MARKER"] = str(marker)
        env.pop("AZURE_TENANT_ID", None)
        return env, marker

    def test_help_never_invokes_azure_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            env, marker = self._environment_with_fake_az(Path(tmp))
            result = subprocess.run(
                [sys.executable, "scripts/live_readonly_probe.py", "--help"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--expected-tenant-id", result.stdout)
        self.assertFalse(marker.exists())

    def test_missing_expected_tenant_fails_before_azure_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            env, marker = self._environment_with_fake_az(Path(tmp))
            result = subprocess.run(
                [sys.executable, "scripts/live_readonly_probe.py"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("expected-tenant-id", result.stderr)
        self.assertFalse(marker.exists())

    def test_tenant_mismatch_stops_after_account_context_check(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            env, marker = self._environment_with_fake_az(base)
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/live_readonly_probe.py",
                    "--expected-tenant-id",
                    "different-tenant",
                    "--output-dir",
                    str(base / "artifacts"),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            invocations = marker.read_text(encoding="utf-8").splitlines()
        self.assertEqual(result.returncode, 2)
        self.assertIn("does not match expected tenant", result.stderr)
        self.assertEqual(invocations, ["account show --output json"])


if __name__ == "__main__":
    unittest.main()
