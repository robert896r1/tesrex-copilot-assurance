"""Versioned static Microsoft mapping loaders.

Mappings are advisory inputs, not proof by themselves. Staleness/completeness flags prevent hard conclusions from stale static data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .models import MappingVersion


class MappingValidationError(ValueError):
    pass


@dataclass(frozen=True)
class LoadedMapping:
    path: Path
    data: dict[str, Any]
    schema_version: str
    last_reviewed: date
    review_staleness_days_warn: int

    def is_stale(self, assessment_date: date) -> bool:
        return (assessment_date - self.last_reviewed).days > self.review_staleness_days_warn

    def version(self, assessment_date: date) -> MappingVersion:
        return MappingVersion(
            artifact_path=str(self.path),
            schema_version=self.schema_version,
            last_reviewed=self.last_reviewed.isoformat(),
            stale=self.is_stale(assessment_date),
        )


def parse_assessment_date(value: str | date | datetime | None) -> date:
    if value is None:
        return datetime.now(timezone.utc).date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return date.fromisoformat(value[:10])


def load_json_file(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_microsoft_capability_map(path: str | Path = "config/microsoft_capability_map.json") -> LoadedMapping:
    p = Path(path)
    data = load_json_file(p)
    _validate_common(data, p)
    _require_dict(data, "capabilities", p)
    _require_list(data, "global_classification_rules", p)
    _require_dict(data, "input_artifacts", p)
    _require_dict(data, "known_service_plans", p)
    completeness = _require_dict(data, "mapping_completeness", p)
    if completeness.get("claims_complete_coverage") is not False:
        raise MappingValidationError(f"{p}: mapping_completeness.claims_complete_coverage must be false until explicitly reviewed")
    for cap_key, cap in data["capabilities"].items():
        if not isinstance(cap, dict):
            raise MappingValidationError(f"{p}: capability {cap_key} must be an object")
        if "control_ids" not in cap:
            raise MappingValidationError(f"{p}: capability {cap_key} missing control_ids")
    return _loaded_mapping(p, data)


def load_dlp_copilot_location_map(path: str | Path = "config/dlp_copilot_location_map.json") -> LoadedMapping:
    p = Path(path)
    data = load_json_file(p)
    _validate_common(data, p)
    _require_list(data, "known_locations", p)
    _require_list(data, "recognition_rules", p)
    _require_dict(data, "status_rules", p)
    _require_list(data, "parser_safety_rules", p)
    completeness = _require_dict(data, "mapping_completeness", p)
    if completeness.get("claims_complete_guid_coverage") is not False:
        raise MappingValidationError(f"{p}: mapping_completeness.claims_complete_guid_coverage must be false until explicitly reviewed")
    for loc in data["known_locations"]:
        if not isinstance(loc, dict):
            raise MappingValidationError(f"{p}: known_locations entries must be objects")
        for key in ["canonical_id", "workload", "location_guid", "display_names"]:
            if key not in loc:
                raise MappingValidationError(f"{p}: known location missing {key}")
    return _loaded_mapping(p, data)


def _loaded_mapping(path: Path, data: dict[str, Any]) -> LoadedMapping:
    reviewed = parse_assessment_date(data["last_reviewed"])
    days = data["mapping_completeness"].get("review_staleness_days_warn")
    if not isinstance(days, int) or days < 1:
        raise MappingValidationError(f"{path}: review_staleness_days_warn must be a positive integer")
    return LoadedMapping(path=path, data=data, schema_version=str(data["schema_version"]), last_reviewed=reviewed, review_staleness_days_warn=days)


def _validate_common(data: dict[str, Any], path: Path) -> None:
    if not isinstance(data, dict):
        raise MappingValidationError(f"{path}: mapping root must be an object")
    for key in ["schema_version", "last_reviewed", "mapping_completeness", "source_refs", "evidence_contract"]:
        if key not in data:
            raise MappingValidationError(f"{path}: missing required key {key}")
    if data["evidence_contract"] != "docs/evidence_contract.md":
        raise MappingValidationError(f"{path}: evidence_contract must point to docs/evidence_contract.md")
    parse_assessment_date(data["last_reviewed"])
    _require_dict(data, "mapping_completeness", path)
    _require_dict(data, "source_refs", path)


def _require_dict(data: dict[str, Any], key: str, path: Path) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise MappingValidationError(f"{path}: {key} must be an object")
    return value


def _require_list(data: dict[str, Any], key: str, path: Path) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise MappingValidationError(f"{path}: {key} must be an array")
    return value
