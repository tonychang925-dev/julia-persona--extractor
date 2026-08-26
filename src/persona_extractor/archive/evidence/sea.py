"""SourceEvidenceArchive envelope + accounting (M0 contract §8, §9, §10.6).

The SEA is a source-preserving evidence envelope. Every admitted source node is
preserved unconditionally; the complete ``source_payload`` is the life-line and
MUST NOT be cropped, and ``structural_projection`` is a derived convenience that
must never mutate or substitute for the payload.
"""

from __future__ import annotations

from typing import Any

from .canonical_json import jcs_hash
from .ids import evidence_archive_id, node_evidence_id


def rfc6901_escape(segment: str) -> str:
    """RFC 6901 JSON Pointer segment escaping: ``~`` -> ``~0``, ``/`` -> ``~1``."""
    return segment.replace("~", "~0").replace("/", "~1")


def build_sea_node(
    *,
    source_node_id: str,
    source_node: dict[str, Any],
    evidence_archive_id: str,
    json_pointer: str,
    source_archive_id: str,
    source_sha256: str,
    structural_projection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one SEA node, preserving the complete source node as payload.

    ``source_payload`` is the entire parsed source-native node, uncropped. The
    ``canonical_node_hash`` is over ``source_payload``, NOT over the projection.
    """
    return {
        "source_node_id": source_node_id,
        "node_evidence_id": node_evidence_id(evidence_archive_id, source_node_id, json_pointer),
        "source_payload": source_node,
        "structural_projection": structural_projection,
        "provenance": {
            "source_archive_ref": source_archive_id,
            "source_sha256": source_sha256,
            "json_pointer": json_pointer,
            "source_node_id": source_node_id,
            "canonical_node_hash": jcs_hash(source_node),
        },
    }


def build_accounting(
    *,
    source_node_count: int,
    preserved_node_count: int,
    excluded_node_count: int,
    exclusions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the SEA accounting block (§10.6)."""
    return {
        "source_node_count": source_node_count,
        "preserved_node_count": preserved_node_count,
        "excluded_node_count": excluded_node_count,
        "exclusions": exclusions,
    }


def build_source_evidence_archive(
    *,
    source_archive_id: str,
    source_unit: dict[str, Any],
    source_native: dict[str, Any],
    nodes: list[dict[str, Any]],
    accounting: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the SourceEvidenceArchive envelope (§8)."""
    evidence_archive_id_value = evidence_archive_id(
        source_archive_id,
        source_unit["source_pointer"],
        source_unit["source_native_id"],
    )
    return {
        "schema_version": "0.1.0",
        "evidence_archive_id": evidence_archive_id_value,
        "source_manifest_ref": source_archive_id,
        "source_unit": source_unit,
        "source_native": source_native,
        "nodes": nodes,
        "accounting": accounting,
    }
