"""Local artifact retention helpers.

Retention applies to local generated artifacts only. It does not clean up Microsoft tenant-side eDiscovery or Purview objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

DEFAULT_LOCAL_ARTIFACT_RETENTION_DAYS = 30
DEFAULT_ARTIFACT_ROOTS = (
    "artifacts/live_probe",
    "artifacts/evidence_packs",
    "artifacts/review_sidecar",
)


@dataclass(frozen=True)
class RetentionCandidate:
    path: Path
    age_days: int
    cutoff_utc: str


def retention_cutoff(now: datetime | None = None, days: int = DEFAULT_LOCAL_ARTIFACT_RETENTION_DAYS) -> datetime:
    if days < 1:
        raise ValueError("retention days must be positive")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current - timedelta(days=days)


def find_local_artifact_retention_candidates(
    roots: list[str | Path] | tuple[str | Path, ...] = DEFAULT_ARTIFACT_ROOTS,
    *,
    now: datetime | None = None,
    days: int = DEFAULT_LOCAL_ARTIFACT_RETENTION_DAYS,
) -> list[RetentionCandidate]:
    """Return local artifact directories older than the retention window.

    This intentionally operates only on local filesystem artifacts. It never calls
    Microsoft tenant APIs and never deletes tenant-side validation searches.
    """

    cutoff = retention_cutoff(now, days)
    candidates: list[RetentionCandidate] = []
    for root_value in roots:
        root = Path(root_value)
        if not root.exists() or not root.is_dir():
            continue
        for child in root.iterdir():
            if not child.is_dir():
                continue
            mtime = datetime.fromtimestamp(child.stat().st_mtime, timezone.utc)
            if mtime < cutoff:
                candidates.append(
                    RetentionCandidate(
                        path=child,
                        age_days=max(0, (cutoff - mtime).days + days),
                        cutoff_utc=cutoff.isoformat().replace("+00:00", "Z"),
                    )
                )
    return sorted(candidates, key=lambda item: str(item.path))


def locked_local_artifact_paths(evidence_pack_root: str | Path = "artifacts/evidence_packs") -> set[Path]:
    """Return local artifact paths referenced by active evidence packs.

    Locks are conservative: PASS/WARN evidence, packs with findings, and pack
    directories themselves are preserved. This function never calls tenant APIs.
    """

    root = Path(evidence_pack_root)
    locked: set[Path] = set()
    if not root.exists():
        return locked
    for pack_file in root.glob("*/evidence_pack.json"):
        try:
            pack = json.loads(pack_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        pack_dir = pack_file.parent.resolve()
        checks = pack.get("control_checks") or []
        evidence_by_id = {item.get("evidence_id"): item for item in pack.get("evidence_items") or [] if isinstance(item, dict)}
        if pack.get("findings"):
            locked.add(pack_dir)
            for evidence in evidence_by_id.values():
                raw_path = evidence.get("raw_artifact_path")
                if raw_path:
                    locked.add(Path(raw_path).resolve())
                    locked.add(Path(raw_path).resolve().parent)
        for check in checks:
            if not isinstance(check, dict) or check.get("status") not in {"PASS", "WARN"}:
                continue
            for evidence_id in check.get("evidence_items_used") or []:
                evidence = evidence_by_id.get(evidence_id)
                if not evidence:
                    continue
                raw_path = evidence.get("raw_artifact_path")
                if raw_path:
                    locked.add(Path(raw_path).resolve())
                    locked.add(Path(raw_path).resolve().parent)
    return locked


def filter_unlocked_candidates(candidates: list[RetentionCandidate], locked_paths: set[Path]) -> list[RetentionCandidate]:
    filtered: list[RetentionCandidate] = []
    resolved_locks = {path.resolve() for path in locked_paths}
    for candidate in candidates:
        candidate_path = candidate.path.resolve()
        if any(candidate_path == locked or locked.is_relative_to(candidate_path) or candidate_path.is_relative_to(locked) for locked in resolved_locks):
            continue
        filtered.append(candidate)
    return filtered
