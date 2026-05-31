from __future__ import annotations

import contextlib
import importlib.util
import io
import unittest
from pathlib import Path


def _load_guard_module():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("check_read_only_contract", root / "scripts" / "check_read_only_contract.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReadOnlyContractGuardTests(unittest.TestCase):
    def test_read_only_contract_guard_rejects_write_like_http_call(self) -> None:
        guard = _load_guard_module()
        tmp_dir = Path(self._testMethodName)
        tmp_dir.mkdir(exist_ok=True)
        bad = tmp_dir / "bad_collector.py"
        bad.write_text("import requests\nrequests.post('https://graph.microsoft.com/v1.0/test')\n")
        original_scan_paths = guard.SCAN_PATHS
        try:
            guard.SCAN_PATHS = [bad]
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(guard.main(), 1)
        finally:
            guard.SCAN_PATHS = original_scan_paths
            bad.unlink(missing_ok=True)
            tmp_dir.rmdir()
