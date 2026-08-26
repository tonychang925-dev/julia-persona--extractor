"""ChatGPT response-bundle views (M0-P4, contract §14, §14.6).

Groups each assistant response-emission episode from the canonical lineage into a
ResponseBundleView. Authority boundaries are frozen (§14.6):

- ``CanonicalLineageView`` is the EXCLUSIVE membership + ordering authority.
- ``SEA`` is a dereference input only (source-native message / role /
  content_type / node_evidence_id). P4 never recomputes topology from SEA.
- ``TypedArtifactView[]`` is a join input only (fills ``artifact_refs``).

v0.1 never emits ``unbundled``: an unresolved assistant run MUST be ``ambiguous``.
"""

from __future__ import annotations

from typing import Any

from .ids import bundle_id

RESPONSE_BUNDLE_PROFILE = "chatgpt-official-export-response-bundle-v0.1"

# Frozen classification table (contract §14.3). ``multimodal_text`` is a
# recognized terminal visible response content type (the container itself is not
# an artifact; P3 already split it into leaf artifacts).
AUXILIARY_CONTENT_TYPES = frozenset({"thoughts", "reasoning_recap"})
TERMINAL_VISIBLE_CONTENT_TYPES = frozenset({"text", "multimodal_text"})


class BundleInputError(ValueError):
    """SEA / canonical-lineage / typed-artifact precondition violation.

    Raised fail-closed before any grouping. Distinct from the bundle
    ``resolved``/``ambiguous`` states, which are legitimate outcomes.
    """


def build_chatgpt_response_bundles(
    sea: dict[str, Any],
    canonical_lineage: dict[str, Any],
    typed_artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build ResponseBundleView[] from resolved canonical lineage.

    Deterministic: bundles follow canonical lineage order; members, triggers,
    visible refs, artifact refs, and provenance refs all preserve canonical order.
    Never mutates any input.
    """
    evidence_archive_id, nodes_by_id = _validate_sea(sea)
    node_refs = _validate_canonical(canonical_lineage, evidence_archive_id, nodes_by_id)
    artifacts_by_node = _validate_artifacts(typed_artifacts, evidence_archive_id)

    seq = _message_bearing_sequence(node_refs, nodes_by_id)
    return _group_bundles(evidence_archive_id, nodes_by_id, artifacts_by_node, seq)


# --------------------------------------------------------------------------- #
# Precondition validation (fail closed)
# --------------------------------------------------------------------------- #

def _validate_sea(sea: Any) -> tuple[str, dict[str, dict[str, Any]]]:
    if not isinstance(sea, dict):
        raise BundleInputError("SEA must be a dict")
    evidence_archive_id = sea.get("evidence_archive_id")
    if not evidence_archive_id:
        raise BundleInputError("SEA missing evidence_archive_id")
    nodes = sea.get("nodes")
    if not isinstance(nodes, list):
        raise BundleInputError("SEA missing nodes list")

    nodes_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise BundleInputError("SEA node must be a dict")
        source_node_id = node.get("source_node_id")
        if not source_node_id:
            raise BundleInputError("SEA node missing source_node_id")
        if source_node_id in nodes_by_id:
            raise BundleInputError("duplicate source_node_id: %r" % source_node_id)
        if not isinstance(node.get("source_payload"), dict):
            raise BundleInputError("source_payload not an object: %r" % source_node_id)
        nodes_by_id[source_node_id] = node
    return evidence_archive_id, nodes_by_id


def _validate_canonical(
    canonical_lineage: Any,
    evidence_archive_id: str,
    nodes_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    if not isinstance(canonical_lineage, dict):
        raise BundleInputError("canonical_lineage must be a dict")
    status = canonical_lineage.get("resolution_status")
    if status != "resolved":
        raise BundleInputError("canonical_lineage must be resolved, got %r" % (status,))
    if canonical_lineage.get("evidence_archive_id") != evidence_archive_id:
        raise BundleInputError("canonical_lineage evidence_archive_id mismatch")
    node_refs = canonical_lineage.get("node_refs")
    if not isinstance(node_refs, list):
        raise BundleInputError("canonical_lineage missing node_refs")
    for ref in node_refs:
        if ref not in nodes_by_id:
            raise BundleInputError("canonical node_ref not in SEA: %r" % (ref,))
    return node_refs


def _validate_artifacts(
    typed_artifacts: Any,
    evidence_archive_id: str,
) -> dict[str, list[str]]:
    if not isinstance(typed_artifacts, list):
        raise BundleInputError("typed_artifacts must be a list")
    artifacts_by_node: dict[str, list[str]] = {}
    seen: set[str] = set()
    for art in typed_artifacts:
        if not isinstance(art, dict):
            raise BundleInputError("typed artifact must be a dict")
        if art.get("evidence_archive_id") != evidence_archive_id:
            raise BundleInputError("typed artifact evidence_archive_id mismatch")
        artifact_id_value = art.get("artifact_id")
        if not artifact_id_value:
            raise BundleInputError("typed artifact missing artifact_id")
        if artifact_id_value in seen:
            raise BundleInputError("duplicate artifact_id: %r" % (artifact_id_value,))
        seen.add(artifact_id_value)
        source_node_ref = art.get("source_node_ref")
        if not source_node_ref:
            raise BundleInputError("typed artifact missing source_node_ref")
        artifacts_by_node.setdefault(source_node_ref, []).append(artifact_id_value)
    return artifacts_by_node


# --------------------------------------------------------------------------- #
# Grouping
# --------------------------------------------------------------------------- #

def _message_bearing_sequence(
    node_refs: list[str],
    nodes_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Walk canonical order, skipping ``message = null`` structural nodes.

    Structural nodes are transparent for role-run grouping (§14.3): they do not
    break an assistant run, and never become members or triggers.
    """
    seq: list[dict[str, Any]] = []
    for ref in node_refs:
        payload = nodes_by_id[ref]["source_payload"]
        message = payload.get("message")
        if not isinstance(message, dict):
            continue
        author = message.get("author")
        role = author.get("role") if isinstance(author, dict) else None
        content = message.get("content")
        content_type = content.get("content_type") if isinstance(content, dict) else None
        seq.append({"source_node_id": ref, "role": role, "content_type": content_type})
    return seq


def _preceding_user_run(seq: list[dict[str, Any]], start: int) -> list[str]:
    refs: list[str] = []
    j = start - 1
    while j >= 0 and seq[j]["role"] == "user":
        refs.append(seq[j]["source_node_id"])
        j -= 1
    refs.reverse()  # canonical order
    return refs


def _group_bundles(
    evidence_archive_id: str,
    nodes_by_id: dict[str, dict[str, Any]],
    artifacts_by_node: dict[str, list[str]],
    seq: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    bundles: list[dict[str, Any]] = []
    n = len(seq)
    i = 0
    while i < n:
        if seq[i]["role"] != "assistant":
            i += 1
            continue
        start = i
        while i < n and seq[i]["role"] == "assistant":
            i += 1
        end = i

        member_refs = [seq[j]["source_node_id"] for j in range(start, end)]
        trigger_refs = _preceding_user_run(seq, start)
        content_types = [seq[j]["content_type"] for j in range(start, end)]
        bundles.append(
            _build_bundle(
                evidence_archive_id,
                nodes_by_id,
                artifacts_by_node,
                trigger_refs,
                member_refs,
                content_types,
            )
        )
    return bundles


def _resolve_state(content_types: list[Any]) -> str:
    """Resolved/ambiguous per §14.3. Never returns ``unbundled`` for v0.1."""
    terminals = [i for i, ct in enumerate(content_types) if ct in TERMINAL_VISIBLE_CONTENT_TYPES]
    unknowns = [
        ct
        for ct in content_types
        if ct not in AUXILIARY_CONTENT_TYPES and ct not in TERMINAL_VISIBLE_CONTENT_TYPES
    ]
    if unknowns:
        return "ambiguous"
    if len(terminals) != 1:
        return "ambiguous"  # zero or more-than-one terminal visible
    if terminals[0] != len(content_types) - 1:
        return "ambiguous"  # terminal is not the final message-bearing node
    return "resolved"


def _build_bundle(
    evidence_archive_id: str,
    nodes_by_id: dict[str, dict[str, Any]],
    artifacts_by_node: dict[str, list[str]],
    trigger_refs: list[str],
    member_refs: list[str],
    content_types: list[Any],
) -> dict[str, Any]:
    bundle_state = _resolve_state(content_types)

    # §14.6: visible_response_refs = recognized terminal visible response nodes.
    # For a resolved bundle this is exactly [member_refs[-1]].
    visible_refs = [
        ref for ref, ct in zip(member_refs, content_types) if ct in TERMINAL_VISIBLE_CONTENT_TYPES
    ]

    artifact_refs: list[str] = []
    for ref in member_refs:
        artifact_refs.extend(artifacts_by_node.get(ref, []))

    provenance_refs = [
        nodes_by_id[ref]["node_evidence_id"] for ref in trigger_refs
    ] + [nodes_by_id[ref]["node_evidence_id"] for ref in member_refs]

    return {
        "schema_version": "0.1.0",
        "bundle_id": bundle_id(
            evidence_archive_id,
            RESPONSE_BUNDLE_PROFILE,
            bundle_state,
            member_refs,
        ),
        "bundle_state": bundle_state,
        "evidence_archive_id": evidence_archive_id,
        "resolution_profile": RESPONSE_BUNDLE_PROFILE,
        "trigger_refs": trigger_refs,
        "member_node_refs": member_refs,
        "artifact_refs": artifact_refs,
        "visible_response_refs": visible_refs,
        "provenance_refs": provenance_refs,
    }
