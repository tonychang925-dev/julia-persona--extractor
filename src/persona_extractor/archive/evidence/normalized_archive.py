"""ChatGPT normalized archive projection (M0-P5, contract §15.5).

A faithful deterministic projection of already-proven facts (SEA / topology /
typed artifacts / response bundles) into a cross-source NormalizedConversationArchive
0.3.0. P5 has no fact-discovery authority: it never guesses chronology, meaning,
identity, or timestamps, and never fabricates bundle association.

Input authority boundaries (§15.5):

- ``manifest``           = source identity / locator / ingested_at / source_sha256
- ``SEA``                = content / source evidence
- ``CanonicalLineage``   = membership / order
- ``ResponseBundle``     = bundle association
"""

from __future__ import annotations

import datetime
import math
from typing import Any

from .canonical_json import jcs_hash
from .ids import normalized_archive_id, normalized_message_id
from .response_bundles import RESPONSE_BUNDLE_PROFILE

NORMALIZATION_PROFILE = "chatgpt-official-export-normalized-archive-v0.3"
NORMALIZATION_ADAPTER = "chatgpt_official_export_normalizer"
NORMALIZATION_VERSION = "0.3.0"


class NormalizedArchiveInputError(ValueError):
    """Precondition violation (fail closed)."""


def build_chatgpt_normalized_archive(
    manifest: dict[str, Any],
    sea: dict[str, Any],
    canonical_lineage: dict[str, Any],
    response_bundles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a NormalizedConversationArchive 0.3.0 (deterministic; never mutates inputs)."""
    source_type, source_sha256, source_path, source_uri, ingested_at = _validate_manifest(manifest)
    sea_id, conversation_id, title, nodes_by_id = _validate_sea(sea, manifest["source_archive_id"])
    lineage_id, node_refs = _validate_canonical(canonical_lineage, sea_id, nodes_by_id)
    member_to_bundle = _validate_bundles(response_bundles, sea_id, nodes_by_id, node_refs)

    archive_id = normalized_archive_id(sea_id, NORMALIZATION_PROFILE)

    participants: list[dict[str, Any]] = []
    seen_roles: set[str] = set()
    messages: list[dict[str, Any]] = []
    message_hashes: list[str] = []

    for ref in node_refs:
        node = nodes_by_id[ref]
        message = node["source_payload"].get("message")
        if not isinstance(message, dict):
            continue  # message = null or malformed -> omitted (canonical-only)

        role = _project_role(message)
        participant_id = "role:" + role
        if role not in seen_roles:
            seen_roles.add(role)
            participants.append({"participant_id": participant_id, "role": role, "display_name": None})

        bundle = member_to_bundle.get(ref)
        if bundle is not None:
            bundle_eligibility = "eligible"
            bundle_state = bundle["bundle_state"]
            bundle_ref = bundle["bundle_id"]
        else:
            bundle_eligibility = "not_eligible"
            bundle_state = None
            bundle_ref = None

        source_evidence_ref = node["node_evidence_id"]
        raw_message_id = _raw_message_id(message)

        normalized_message: dict[str, Any] = {
            "message_id": normalized_message_id(archive_id, source_evidence_ref),
            "role": role,
            "participant_id": participant_id,
            "content": _project_content(message.get("content")),
            "timestamp": _project_timestamp(message),
            "source_evidence_ref": source_evidence_ref,
            "lineage_ref": lineage_id,
            "lineage_state": "resolved",
            "bundle_state": bundle_state,
            "bundle_ref": bundle_ref,
            "bundle_eligibility": bundle_eligibility,
        }
        normalized_message["provenance"] = _provenance(source_type, source_path, source_uri, ref, raw_message_id)
        normalized_message["immutable_ref"] = {
            "archive_id": archive_id,
            "message_hash": _message_hash(normalized_message, raw_message_id),
            "raw_message_id": raw_message_id,
        }
        messages.append(normalized_message)
        message_hashes.append(normalized_message["immutable_ref"]["message_hash"])

    archive: dict[str, Any] = {
        "schema_version": "0.3.0",
        "archive_id": archive_id,
        "source_evidence_archive_ref": sea_id,
        "conversation_id": conversation_id,
        "title": title,
        "created_at": None,
        "updated_at": None,
        "source_identity": {
            "source_type": source_type,
            "source_id": conversation_id,
            "source_path": source_path,
            "source_uri": source_uri,
            "ingested_at": ingested_at,
            "content_hash": source_sha256,
        },
    }
    archive["provenance"] = _provenance(source_type, source_path, source_uri, conversation_id, None)
    archive["immutability"] = {
        "normalized_content_hash": _content_hash(archive, participants, message_hashes),
        "raw_content_hash": source_sha256,
        "normalization_adapter": NORMALIZATION_ADAPTER,
        "normalization_version": NORMALIZATION_VERSION,
    }
    archive["participants"] = participants
    archive["messages"] = messages
    return archive


# --------------------------------------------------------------------------- #
# Validation (fail closed)
# --------------------------------------------------------------------------- #

def _validate_manifest(manifest: Any) -> tuple[str, str, Any, Any, Any]:
    if not isinstance(manifest, dict):
        raise NormalizedArchiveInputError("manifest must be a dict")
    source_archive_id = manifest.get("source_archive_id")
    source_type = manifest.get("source_type")
    source_sha256 = manifest.get("source_sha256")
    if not source_archive_id or not source_type or not source_sha256:
        raise NormalizedArchiveInputError("manifest missing source_archive_id/source_type/source_sha256")
    locator = manifest.get("source_locator")
    source_path = locator.get("path") if isinstance(locator, dict) else None
    source_uri = locator.get("uri") if isinstance(locator, dict) else None
    return source_type, source_sha256, source_path, source_uri, manifest.get("ingested_at")


def _validate_sea(sea: Any, manifest_archive_id: str) -> tuple[str, Any, Any, dict[str, dict[str, Any]]]:
    if not isinstance(sea, dict):
        raise NormalizedArchiveInputError("SEA must be a dict")
    sea_id = sea.get("evidence_archive_id")
    if not sea_id:
        raise NormalizedArchiveInputError("SEA missing evidence_archive_id")
    if sea.get("source_manifest_ref") != manifest_archive_id:
        raise NormalizedArchiveInputError("SEA source_manifest_ref does not match manifest source_archive_id")
    source_native = sea.get("source_native")
    conversation_id = source_native.get("conversation_id") if isinstance(source_native, dict) else None
    title = source_native.get("title") if isinstance(source_native, dict) else None
    nodes = sea.get("nodes")
    if not isinstance(nodes, list):
        raise NormalizedArchiveInputError("SEA missing nodes list")
    nodes_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise NormalizedArchiveInputError("SEA node must be a dict")
        sid = node.get("source_node_id")
        if not sid:
            raise NormalizedArchiveInputError("SEA node missing source_node_id")
        if sid in nodes_by_id:
            raise NormalizedArchiveInputError("duplicate source_node_id: %r" % (sid,))
        if not isinstance(node.get("source_payload"), dict):
            raise NormalizedArchiveInputError("source_payload not an object: %r" % (sid,))
        nodes_by_id[sid] = node
    return sea_id, conversation_id, title, nodes_by_id


def _validate_canonical(
    canonical_lineage: Any,
    sea_id: str,
    nodes_by_id: dict[str, dict[str, Any]],
) -> tuple[str, list[str]]:
    if not isinstance(canonical_lineage, dict):
        raise NormalizedArchiveInputError("canonical_lineage must be a dict")
    if canonical_lineage.get("resolution_status") != "resolved":
        raise NormalizedArchiveInputError("canonical_lineage must be resolved")
    if canonical_lineage.get("evidence_archive_id") != sea_id:
        raise NormalizedArchiveInputError("canonical_lineage evidence_archive_id mismatch")
    lineage_id = canonical_lineage.get("lineage_id")
    if not lineage_id:
        raise NormalizedArchiveInputError("canonical_lineage missing lineage_id")
    node_refs = canonical_lineage.get("node_refs")
    if not isinstance(node_refs, list):
        raise NormalizedArchiveInputError("canonical_lineage missing node_refs")
    for ref in node_refs:
        if ref not in nodes_by_id:
            raise NormalizedArchiveInputError("canonical node_ref not in SEA: %r" % (ref,))
    return lineage_id, node_refs


def _validate_bundles(
    response_bundles: Any,
    sea_id: str,
    nodes_by_id: dict[str, dict[str, Any]],
    node_refs: list[str],
) -> dict[str, dict[str, Any]]:
    if not isinstance(response_bundles, list):
        raise NormalizedArchiveInputError("response_bundles must be a list")
    canonical_set = set(node_refs)
    canonical_assistant = {
        ref
        for ref in node_refs
        if _is_assistant(nodes_by_id[ref])
    }
    member_to_bundle: dict[str, dict[str, Any]] = {}
    for bundle in response_bundles:
        if not isinstance(bundle, dict):
            raise NormalizedArchiveInputError("bundle must be a dict")
        if bundle.get("evidence_archive_id") != sea_id:
            raise NormalizedArchiveInputError("bundle evidence_archive_id mismatch")
        if bundle.get("resolution_profile") != RESPONSE_BUNDLE_PROFILE:
            raise NormalizedArchiveInputError("bundle resolution_profile mismatch")
        bundle_id_value = bundle.get("bundle_id")
        if not bundle_id_value:
            raise NormalizedArchiveInputError("bundle missing bundle_id")
        if bundle.get("bundle_state") not in ("resolved", "ambiguous"):
            raise NormalizedArchiveInputError("bundle has invalid bundle_state")
        members = bundle.get("member_node_refs")
        if not isinstance(members, list):
            raise NormalizedArchiveInputError("bundle missing member_node_refs")
        for ref in members:
            if ref in member_to_bundle:
                raise NormalizedArchiveInputError("overlapping bundle members: %r" % (ref,))
            if ref not in canonical_set:
                raise NormalizedArchiveInputError("bundle member not in canonical lineage: %r" % (ref,))
            if ref not in canonical_assistant:
                raise NormalizedArchiveInputError("bundle member is not an assistant node: %r" % (ref,))
            member_to_bundle[ref] = bundle
    if set(member_to_bundle) != canonical_assistant:
        raise NormalizedArchiveInputError("bundle coverage does not match canonical assistant nodes")
    return member_to_bundle


def _is_assistant(node: dict[str, Any]) -> bool:
    message = node["source_payload"].get("message")
    if not isinstance(message, dict):
        return False
    return _project_role(message) == "assistant"


# --------------------------------------------------------------------------- #
# Projection primitives
# --------------------------------------------------------------------------- #

def _project_content(content: Any) -> str:
    """Narrow textual projection (§15.5). Never str(dict) / JSON dump / strip."""
    if not isinstance(content, dict):
        return ""
    content_type = content.get("content_type")
    if not isinstance(content_type, str) or content_type == "":
        return ""
    if content_type == "text":
        parts = content.get("parts")
        if isinstance(parts, list):
            return "\n".join(p for p in parts if isinstance(p, str))
        return ""
    if content_type == "multimodal_text":
        parts = content.get("parts")
        if not isinstance(parts, list):
            return ""
        fragments: list[str] = []
        for part in parts:
            if isinstance(part, str):
                fragments.append(part)
            elif isinstance(part, dict) and part.get("content_type") == "audio_transcription":
                text = part.get("text")
                if isinstance(text, str):
                    fragments.append(text)
        return "\n".join(fragments)
    if content_type == "audio_transcription":
        text = content.get("text")
        return text if isinstance(text, str) else ""
    # thoughts / reasoning_recap / image_asset_pointer / unknown -> ""
    return ""


def _project_role(message: dict[str, Any]) -> str:
    author = message.get("author")
    role = author.get("role") if isinstance(author, dict) else None
    if isinstance(role, str) and role != "":
        return role
    return "unknown"


def _project_timestamp(message: dict[str, Any]) -> str | None:
    create_time = message.get("create_time")
    if isinstance(create_time, bool):
        return None
    if isinstance(create_time, float):
        if not math.isfinite(create_time):
            return None
    elif not isinstance(create_time, int):
        return None
    # NOTE: do NOT run math.isfinite() on an arbitrary-precision int — the
    # implicit int->float conversion raises OverflowError for huge ints. Let
    # fromtimestamp raise (OverflowError/OSError/ValueError) instead -> null.
    try:
        dt = datetime.datetime.fromtimestamp(create_time, tz=datetime.timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _raw_message_id(message: dict[str, Any]) -> str | None:
    mid = message.get("id")
    return mid if isinstance(mid, str) and mid != "" else None


# --------------------------------------------------------------------------- #
# Records
# --------------------------------------------------------------------------- #

def _provenance(
    source_type: str,
    source_path: Any,
    source_uri: Any,
    source_id: str,
    raw_message_id: str | None,
) -> dict[str, Any]:
    return {
        "source_type": source_type,
        "source_path": source_path,
        "source_uri": source_uri,
        "source_id": source_id,
        "source_offset": None,
        "raw_message_id": raw_message_id,
        "normalization_adapter": NORMALIZATION_ADAPTER,
        "normalization_version": NORMALIZATION_VERSION,
    }


def _message_hash(message: dict[str, Any], raw_message_id: str | None) -> str:
    return jcs_hash(
        {
            "domain": "NORMALIZED-MESSAGE-HASH-v1",
            "payload": {
                "normalization_profile": NORMALIZATION_PROFILE,
                "message_id": message["message_id"],
                "role": message["role"],
                "participant_id": message["participant_id"],
                "content": message["content"],
                "timestamp": message["timestamp"],
                "source_evidence_ref": message["source_evidence_ref"],
                "lineage_ref": message["lineage_ref"],
                "lineage_state": message["lineage_state"],
                "bundle_state": message["bundle_state"],
                "bundle_ref": message["bundle_ref"],
                "bundle_eligibility": message["bundle_eligibility"],
                "raw_message_id": raw_message_id,
            },
        }
    )


def _content_hash(
    archive: dict[str, Any],
    participants: list[dict[str, Any]],
    ordered_message_hashes: list[str],
) -> str:
    return jcs_hash(
        {
            "domain": "NORMALIZED-CONTENT-HASH-v1",
            "payload": {
                "normalization_profile": NORMALIZATION_PROFILE,
                "archive_id": archive["archive_id"],
                "source_evidence_archive_ref": archive["source_evidence_archive_ref"],
                "conversation_id": archive["conversation_id"],
                "title": archive["title"],
                "created_at": archive["created_at"],
                "updated_at": archive["updated_at"],
                "participants": participants,
                "ordered_message_hashes": ordered_message_hashes,
            },
        }
    )
