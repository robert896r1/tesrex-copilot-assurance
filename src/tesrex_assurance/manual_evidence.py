"""Manual/customer evidence bundle loader.

Manual artifacts are customer/assessor asserted unless independently verified elsewhere. The loader hashes artifacts and preserves limitations in the evidence pack."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import EvidenceItem, EvidenceType

SUPPORTED_SCHEMA_VERSION = "0.1.0"


class ManualEvidenceError(ValueError):
    pass


def load_manual_evidence_bundle(path: str | Path) -> dict[str, Any]:
    bundle_path = Path(path)
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManualEvidenceError(f"Manual evidence bundle is not valid JSON: {exc}") from exc
    validate_manual_evidence_bundle(bundle, base_dir=bundle_path.parent)
    return bundle


def validate_manual_evidence_bundle(bundle: dict[str, Any], *, base_dir: str | Path = ".") -> None:
    if not isinstance(bundle, dict):
        raise ManualEvidenceError("Manual evidence bundle must be a JSON object")
    if bundle.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise ManualEvidenceError(f"Manual evidence schema_version must be {SUPPORTED_SCHEMA_VERSION}")
    for key in ["assessment_run_id", "tenant_id", "provided_by", "provided_at_utc", "items"]:
        if key not in bundle:
            raise ManualEvidenceError(f"Manual evidence bundle missing {key}")
    if not isinstance(bundle["items"], list) or not bundle["items"]:
        raise ManualEvidenceError("Manual evidence bundle must contain at least one item")
    seen: set[str] = set()
    for item in bundle["items"]:
        if not isinstance(item, dict):
            raise ManualEvidenceError("Manual evidence item must be an object")
        for key in ["evidence_id", "control_ids", "evidence_type", "source_system", "artifact_path", "asserted_facts", "limitations"]:
            if key not in item:
                raise ManualEvidenceError(f"Manual evidence item missing {key}")
        if item["evidence_id"] in seen:
            raise ManualEvidenceError(f"Duplicate manual evidence_id {item['evidence_id']}")
        seen.add(item["evidence_id"])
        if item["evidence_type"] not in {kind.value for kind in EvidenceType}:
            raise ManualEvidenceError(f"Unsupported manual evidence_type {item['evidence_type']}")
        artifact = _resolve_artifact(base_dir, item["artifact_path"])
        if not artifact.exists() or not artifact.is_file():
            raise ManualEvidenceError(f"Manual evidence artifact does not exist: {artifact}")
        if not isinstance(item["control_ids"], list) or not item["control_ids"]:
            raise ManualEvidenceError(f"Manual evidence item {item['evidence_id']} must cite at least one control")
        if not isinstance(item["asserted_facts"], dict):
            raise ManualEvidenceError(f"Manual evidence item {item['evidence_id']} asserted_facts must be an object")
        if not isinstance(item["limitations"], list):
            raise ManualEvidenceError(f"Manual evidence item {item['evidence_id']} limitations must be an array")


def manual_evidence_items(bundle: dict[str, Any], *, base_dir: str | Path = ".") -> list[EvidenceItem]:
    validate_manual_evidence_bundle(bundle, base_dir=base_dir)
    items: list[EvidenceItem] = []
    for item in bundle["items"]:
        artifact = _resolve_artifact(base_dir, item["artifact_path"])
        asserted_facts = dict(item["asserted_facts"])
        asserted_facts.setdefault("trust_level", "customer_asserted")
        asserted_facts.setdefault("independently_verified_by_tool", False)
        limitations = sorted(set(list(item["limitations"]) + ["manual_only", "customer_asserted"]))
        evidence = EvidenceItem(
            evidence_id=item["evidence_id"],
            assessment_run_id=bundle["assessment_run_id"],
            evidence_type=EvidenceType(item["evidence_type"]),
            source_system=item["source_system"],
            source_endpoint_or_ui_path=item.get("source_endpoint_or_ui_path", "manual evidence"),
            collection_method="manual customer/assessor evidence",
            collected_at_utc=bundle["provided_at_utc"],
            tenant_id=bundle["tenant_id"],
            collector_identity=bundle["provided_by"],
            permission_context="manual/customer-provided",
            source_object_identifiers={"control_ids": item["control_ids"]},
            raw_artifact_path=str(artifact),
            content_hash=hashlib.sha256(artifact.read_bytes()).hexdigest(),
            normalized_facts=asserted_facts,
            relevance_rating=item.get("relevance_rating", "medium"),
            reliability_rating=item.get("reliability_rating", "medium"),
            limitations=limitations,
        )
        evidence.validate()
        items.append(evidence)
    return items


def _resolve_artifact(base_dir: str | Path, artifact_path: str) -> Path:
    path = Path(artifact_path)
    if path.is_absolute():
        return path
    return Path(base_dir) / path
