from __future__ import annotations

from datetime import datetime, timezone
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tesrex_assurance.retention import find_local_artifact_retention_candidates, filter_unlocked_candidates, locked_local_artifact_paths


class RetentionTests(unittest.TestCase):
    def test_find_local_artifact_retention_candidates_only_returns_old_directories(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "artifacts"
            old = root / "old"
            new = root / "new"
            old.mkdir(parents=True)
            new.mkdir()
            now = datetime(2026, 4, 30, tzinfo=timezone.utc)
            old_time = datetime(2026, 3, 1, tzinfo=timezone.utc).timestamp()
            new_time = datetime(2026, 4, 25, tzinfo=timezone.utc).timestamp()
            os.utime(old, (old_time, old_time))
            os.utime(new, (new_time, new_time))
            candidates = find_local_artifact_retention_candidates([root], now=now, days=30)
        self.assertEqual([candidate.path.name for candidate in candidates], ["old"])


    def test_evidence_pack_references_lock_local_artifact_directories(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            live = base / "artifacts" / "live_probe" / "old"
            live.mkdir(parents=True)
            raw = live / "raw.json"
            raw.write_text("{}", encoding="utf-8")
            pack_dir = base / "artifacts" / "evidence_packs" / "run1"
            pack_dir.mkdir(parents=True)
            (pack_dir / "evidence_pack.json").write_text(
                '{"findings":[{"finding_id":"f1"}],"evidence_items":[{"evidence_id":"ev1","raw_artifact_path":"' + str(raw) + '"}],"control_checks":[{"status":"WARN","evidence_items_used":["ev1"]}]}',
                encoding="utf-8",
            )
            now = datetime(2026, 4, 30, tzinfo=timezone.utc)
            old_time = datetime(2026, 3, 1, tzinfo=timezone.utc).timestamp()
            os.utime(live, (old_time, old_time))
            candidates = find_local_artifact_retention_candidates([live.parent], now=now, days=30)
            locks = locked_local_artifact_paths(base / "artifacts" / "evidence_packs")
            filtered = filter_unlocked_candidates(candidates, locks)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(filtered, [])


if __name__ == "__main__":
    unittest.main()
