from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class ProbeStatus(StrEnum):
    OK = "OK"
    WARN = "WARN"
    UNKNOWN = "UNKNOWN"
    NOT_ACCESSIBLE = "NOT_ACCESSIBLE"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class ProbeSpec:
    probe_id: str
    control_ids: tuple[str, ...]
    method: str
    path: str
    description: str
    source_ref: str
    expected_permissions: tuple[str, ...] = ()
    expected_roles: tuple[str, ...] = ()
    no_side_effects: bool = True

    def __post_init__(self) -> None:
        if self.method.upper() != "GET":
            raise ValueError(f"ProbeSpec {self.probe_id} is not read-only: method={self.method}")


@dataclass
class ProbeResult:
    probe_id: str
    status: ProbeStatus
    control_ids: tuple[str, ...]
    source_ref: str
    raw_artifact_path: str | None = None
    content_hash: str | None = None
    summary: dict[str, object] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    status_reason: str = ""


class ReadOnlyCollector(Protocol):
    def run_probe(self, probe_id: str) -> ProbeResult:
        """Run an allowlisted read-only probe."""
        ...
