"""Canonical lineage and alternate-evidence artifact builders (M0-P2, §11, §12).

Builds schema-valid CanonicalLineageView / failure record and
AlternateEvidenceView[] from a topology resolution. Does NOT mutate the SEA.
"""

from __future__ import annotations

from typing import Any

from .ids import lineage_id
from .topology import RESOLUTION_PROFILE, resolve_topology


def resolve_chatgpt_topology(
    sea: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Resolve canonical lineage + alternate evidence views from a SEA.

    Returns ``(canonical_view_or_failure_record, alternate_views)``.

    - resolved: canonical view is a CanonicalLineageView; alternate_views holds
      every off-lineage source node.
    - invalid: canonical view is a deterministic failure record; alternate_views
      is ``[]`` (never fabricate alternate membership when the active lineage
      did not resolve).
    """
    resolution = resolve_topology(sea)
    canonical = _build_canonical(sea, resolution)
    alternates = _build_alternates(sea, resolution)
    return canonical, alternates


def _build_canonical(sea: dict[str, Any], resolution: dict[str, Any]) -> dict[str, Any]:
    evidence_archive_id = sea["evidence_archive_id"]
    base: dict[str, Any] = {
        "schema_version": "0.1.0",
        "resolution_status": resolution["resolution_status"],
        "evidence_archive_id": evidence_archive_id,
        "current_node_id": resolution["current_node_id"],
        "resolution_profile": RESOLUTION_PROFILE,
    }
    if resolution["resolution_status"] == "resolved":
        node_refs = resolution["node_refs"]
        base["resolution_method"] = "source_native_parent_ancestry"
        base["lineage_id"] = lineage_id(
            evidence_archive_id=evidence_archive_id,
            resolution_profile=RESOLUTION_PROFILE,
            current_node_id=resolution["current_node_id"],
            ordered_node_refs=node_refs,
        )
        base["node_refs"] = node_refs
    else:
        base["offending_node_refs"] = resolution["offending_node_refs"]
        base["offending_parent_refs"] = resolution["offending_parent_refs"]
        base["visited_node_refs"] = resolution["visited_node_refs"]
    return base


def _build_alternates(sea: dict[str, Any], resolution: dict[str, Any]) -> list[dict[str, Any]]:
    if resolution["resolution_status"] != "resolved":
        return []

    evidence_archive_id = sea["evidence_archive_id"]
    canonical_set = set(resolution["node_refs"])
    all_refs = {node["source_node_id"] for node in sea["nodes"]}
    alternate_refs = sorted(all_refs - canonical_set)

    return [
        {
            "schema_version": "0.1.0",
            "evidence_archive_id": evidence_archive_id,
            "source_node_ref": ref,
            "lineage_status": "alternate",
            "active_context_membership": False,
            "historical_exposure": "unknown",
        }
        for ref in alternate_refs
    ]
