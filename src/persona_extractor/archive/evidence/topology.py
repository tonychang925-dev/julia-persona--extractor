"""Source-native topology resolver (M0-P2, contract §11).

Topology authority is ``source_payload["parent"]`` — NOT
``structural_projection.parent_node_id``, NOT timestamps, NOT presentation
order. Source topology is evidence, not inference.

The resolver walks ``current_node -> parent -> ... -> root`` and returns a
resolution dict. It NEVER repairs, truncates, or falls back.
"""

from __future__ import annotations

from typing import Any

RESOLUTION_PROFILE = "chatgpt-official-export-canonical-lineage-v0.1"


class TopologyInputError(ValueError):
    """SEA precondition violation (NOT a §11 lineage resolution status).

    Raised when the SEA fed to P2 violates the P1 evidence-identity invariant
    (duplicate source_node_id, missing evidence_archive_id, non-object
    source_payload, etc.). This is distinct from a malformed source-native
    topology, which maps to the frozen six-status enum.
    """


def _index_sea(sea: dict[str, Any]) -> tuple[str, dict[str, dict[str, Any]]]:
    if not isinstance(sea, dict):
        raise TopologyInputError("SEA must be a dict")
    evidence_archive_id = sea.get("evidence_archive_id")
    if not evidence_archive_id:
        raise TopologyInputError("SEA missing evidence_archive_id")
    nodes = sea.get("nodes")
    if not isinstance(nodes, list):
        raise TopologyInputError("SEA missing nodes list")

    nodes_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise TopologyInputError("SEA node must be a dict")
        source_node_id = node.get("source_node_id")
        if not source_node_id:
            raise TopologyInputError("SEA node missing source_node_id")
        if source_node_id in nodes_by_id:
            raise TopologyInputError("duplicate source_node_id: %r" % source_node_id)
        if not isinstance(node.get("source_payload"), dict):
            raise TopologyInputError("source_payload not an object: %r" % source_node_id)
        nodes_by_id[source_node_id] = node

    return evidence_archive_id, nodes_by_id


def resolve_topology(sea: dict[str, Any]) -> dict[str, Any]:
    """Resolve the canonical lineage from ``source_payload.parent``.

    Returns a resolution dict:

    - resolved: ``{"resolution_status": "resolved", "current_node_id": ...,
      "node_refs": [root, ..., current]}``
    - invalid: ``{"resolution_status": "invalid_*", "current_node_id": ...,
      "offending_node_refs": [...], "offending_parent_refs": [...],
      "visited_node_refs": [...]}``
    """
    evidence_archive_id, nodes_by_id = _index_sea(sea)

    current = sea.get("source_native", {}).get("current_node")

    # Step 0 — missing current node selector.
    if current is None or current == "":
        return {
            "resolution_status": "invalid_missing_current_node",
            "current_node_id": current,
            "offending_node_refs": [],
            "offending_parent_refs": [],
            "visited_node_refs": [],
        }

    # Step 1 — current node not admitted.
    if current not in nodes_by_id:
        return {
            "resolution_status": "invalid_current_node_not_in_mapping",
            "current_node_id": current,
            "offending_node_refs": [current],
            "offending_parent_refs": [],
            "visited_node_refs": [],
        }

    # Step 2 — ancestry traversal (self-parent > missing-parent > cycle).
    visited: list[str] = []
    visited_set: set[str] = set()
    node_id: str = current
    while True:
        node = nodes_by_id[node_id]
        visited.append(node_id)
        visited_set.add(node_id)

        parent = node["source_payload"].get("parent")

        if parent == node_id:
            return {
                "resolution_status": "invalid_self_parent",
                "current_node_id": current,
                "offending_node_refs": [node_id],
                "offending_parent_refs": [node_id],
                "visited_node_refs": list(visited),
            }
        if parent is None:
            break  # reached root
        if parent not in nodes_by_id:
            return {
                "resolution_status": "invalid_missing_parent",
                "current_node_id": current,
                "offending_node_refs": [node_id],
                "offending_parent_refs": [parent],
                "visited_node_refs": list(visited),
            }
        if parent in visited_set:
            return {
                "resolution_status": "invalid_cycle",
                "current_node_id": current,
                "offending_node_refs": [node_id],
                "offending_parent_refs": [parent],
                "visited_node_refs": list(visited),
            }
        node_id = parent

    return {
        "resolution_status": "resolved",
        "current_node_id": current,
        "node_refs": list(reversed(visited)),  # root → current
    }
