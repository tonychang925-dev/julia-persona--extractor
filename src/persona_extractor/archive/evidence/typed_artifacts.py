"""ChatGPT typed-artifact views (M0-P3, contract §13.1).

Derives TypedArtifactView[] from SEA source_payload WITHOUT interpreting meaning.
``thoughts`` / ``reasoning_recap`` are labeled structurally only; they are NOT
claims about internal reasoning, causal truth, persona, or identity.
"""

from __future__ import annotations

from typing import Any

from .ids import artifact_id

ARTIFACT_PROFILE = "chatgpt-official-export-typed-artifact-v0.1"

# Frozen classification table (contract §13.1). ``multimodal_text`` is handled
# specially (split into leaf parts), so it is NOT in this map.
_CLASS_BY_CONTENT_TYPE = {
    "thoughts": "exported_decision_trace",
    "reasoning_recap": "reasoning_execution_metadata",
    "text": "visible_text",
    "audio_transcription": "audio_transcription",
    "image_asset_pointer": "image_asset_pointer",
}


def build_chatgpt_typed_artifacts(sea: dict[str, Any]) -> list[dict[str, Any]]:
    """Build TypedArtifactView[] from a SEA (input only; does not mutate it).

    Output is deterministic: node order is ``source_node_ref`` lexical ascending,
    within-node order is source artifact order (node content, then multimodal
    parts in index order).
    """
    evidence_archive_id = sea["evidence_archive_id"]
    nodes_by_id = {n["source_node_id"]: n for n in sea.get("nodes", [])}

    artifacts: list[dict[str, Any]] = []
    for source_node_ref in sorted(nodes_by_id):
        source_payload = nodes_by_id[source_node_ref].get("source_payload", {})
        for pointer, content_type, artifact_class, payload in _classify_node(source_payload):
            artifacts.append(
                {
                    "schema_version": "0.1.0",
                    "artifact_id": artifact_id(
                        evidence_archive_id,
                        source_node_ref,
                        pointer,
                        ARTIFACT_PROFILE,
                    ),
                    "evidence_archive_id": evidence_archive_id,
                    "source_node_ref": source_node_ref,
                    "source_artifact_pointer": pointer,
                    "artifact_profile": ARTIFACT_PROFILE,
                    "source_content_type": content_type,
                    "artifact_class": artifact_class,
                    "evidence_class": "observed_export_artifact",
                    "payload": payload,
                }
            )
    return artifacts


def _classify_node(source_payload: dict[str, Any]) -> list[tuple[str, str, str, Any]]:
    """Return (pointer, source_content_type, artifact_class, payload) tuples.

    Reads source_payload.message.content only; never structural_projection.
    Returns [] when there is no usable typed content (no invented type).
    """
    message = source_payload.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, dict):
        return []
    content_type = content.get("content_type")
    if not isinstance(content_type, str) or content_type == "":
        return []

    if content_type == "multimodal_text":
        return _classify_multimodal(content)
    artifact_class = _CLASS_BY_CONTENT_TYPE.get(content_type, "unknown_typed_artifact")
    return [("/message/content", content_type, artifact_class, content)]


def _classify_multimodal(content: dict[str, Any]) -> list[tuple[str, str, str, Any]]:
    parts = content.get("parts")
    if not isinstance(parts, list):
        # Cannot safely decompose; preserve the exact container as one unknown artifact.
        return [("/message/content", "multimodal_text", "unknown_typed_artifact", content)]

    artifacts: list[tuple[str, str, str, Any]] = []
    for index, part in enumerate(parts):
        pointer = "/message/content/parts/" + str(index)
        if isinstance(part, str):
            artifacts.append((pointer, "multimodal_text", "visible_text", part))
        elif isinstance(part, dict):
            part_type = part.get("content_type")
            if isinstance(part_type, str) and part_type != "":
                artifact_class = _CLASS_BY_CONTENT_TYPE.get(part_type, "unknown_typed_artifact")
                artifacts.append((pointer, part_type, artifact_class, part))
            else:
                artifacts.append((pointer, "multimodal_text", "unknown_typed_artifact", part))
        else:
            # number, boolean, null, list -> multimodal_text + unknown
            artifacts.append((pointer, "multimodal_text", "unknown_typed_artifact", part))
    return artifacts
