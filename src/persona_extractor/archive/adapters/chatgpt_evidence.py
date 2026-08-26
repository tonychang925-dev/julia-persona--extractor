"""ChatGPT official-export M0 evidence ingestion (P1).

Turns exact source bytes + a conversation selector into a
(RawSourceManifest, SourceEvidenceArchive) pair with zero silent loss.

This is the NEW M0 ingestion path. The legacy ``chatgpt.py`` normalization path
remains untouched (it is the counter-example the sabotage tests target).
"""

from __future__ import annotations

from typing import Any

from ..evidence.canonical_json import parse_json_strict
from ..evidence.ids import evidence_archive_id
from ..evidence.manifest import build_raw_source_manifest
from ..evidence.sea import (
    build_accounting,
    build_sea_node,
    build_source_evidence_archive,
    rfc6901_escape,
)

ADAPTER_NAME = "chatgpt_official_export"
ADAPTER_VERSION = "0.1.0"


def build_chatgpt_source_evidence(
    source_bytes: bytes,
    conversation_selector: int | str | None = None,
    source_locator: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build (RawSourceManifest, SourceEvidenceArchive) from exact source bytes.

    The admission domain ``A`` is derived internally from ``mapping`` — every key
    exactly once. The API does NOT accept a caller-provided admitted-refs list.
    """
    manifest = build_raw_source_manifest(
        source_bytes=source_bytes,
        source_type=ADAPTER_NAME,
        source_locator=source_locator,
        adapter_name=ADAPTER_NAME,
        adapter_version=ADAPTER_VERSION,
    )

    parsed = parse_json_strict(source_bytes)
    conversation, source_pointer = _select_conversation(parsed, conversation_selector)

    sea = _build_sea(
        conversation=conversation,
        source_pointer=source_pointer,
        manifest=manifest,
    )
    return manifest, sea


def _select_conversation(
    parsed: Any, selector: int | str | None
) -> tuple[dict[str, Any], str]:
    """Return (conversation, source_pointer).

    - single-conversation export (dict with ``mapping``): source_pointer ``"/"``
    - array export (list of conversations): source_pointer ``"/<index>"``
    """
    if isinstance(parsed, dict) and "mapping" in parsed:
        return parsed, "/"
    if isinstance(parsed, list):
        index = _resolve_index(parsed, selector)
        return parsed[index], "/" + str(index)
    raise ValueError("unrecognized ChatGPT official-export shape")


def _resolve_index(conversations: list[Any], selector: int | str | None) -> int:
    if isinstance(selector, int):
        return selector
    if isinstance(selector, str):
        for index, conversation in enumerate(conversations):
            if not isinstance(conversation, dict):
                continue
            native_id = conversation.get("conversation_id") or conversation.get("id")
            if native_id == selector:
                return index
        raise ValueError("conversation not found by selector: %r" % selector)
    raise TypeError("conversation_selector must be an int index or a str conversation_id")


def _build_sea(
    *,
    conversation: dict[str, Any],
    source_pointer: str,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    mapping = conversation.get("mapping") or {}
    source_native_id = conversation.get("conversation_id") or conversation.get("id") or ""

    source_unit = {
        "unit_type": "conversation",
        "source_native_id": source_native_id,
        "source_pointer": source_pointer,
    }
    source_native = {
        "source_type": ADAPTER_NAME,
        "conversation_id": source_native_id,
        "current_node": conversation.get("current_node"),
        "title": conversation.get("title") or "",
    }

    sea_id = evidence_archive_id(
        manifest["source_archive_id"],
        source_pointer,
        source_native_id,
    )

    nodes: list[dict[str, Any]] = []
    for source_node_id in sorted(mapping.keys()):
        json_pointer = _node_json_pointer(source_pointer, source_node_id)
        nodes.append(
            build_sea_node(
                source_node_id=source_node_id,
                source_node=mapping[source_node_id],
                evidence_archive_id=sea_id,
                json_pointer=json_pointer,
                source_archive_id=manifest["source_archive_id"],
                source_sha256=manifest["source_sha256"],
                structural_projection=_structural_projection(mapping[source_node_id]),
            )
        )

    accounting = build_accounting(
        source_node_count=len(mapping),
        preserved_node_count=len(nodes),
        excluded_node_count=0,
        exclusions=[],
    )

    return build_source_evidence_archive(
        source_archive_id=manifest["source_archive_id"],
        source_unit=source_unit,
        source_native=source_native,
        nodes=nodes,
        accounting=accounting,
    )


def _node_json_pointer(source_pointer: str, source_node_id: str) -> str:
    prefix = "" if source_pointer == "/" else source_pointer
    return prefix + "/mapping/" + rfc6901_escape(source_node_id)


def _structural_projection(source_node: Any) -> dict[str, Any]:
    """Derive a ChatGPT structural projection (never mutates source_payload)."""
    if not isinstance(source_node, dict):
        return {
            "parent_node_id": None,
            "message_id": None,
            "role": None,
            "create_time_raw": None,
            "content_type": None,
        }
    message = source_node.get("message") or {}
    author = message.get("author") or {}
    content = message.get("content") or {}
    content_type = content.get("content_type") if isinstance(content, dict) else None
    return {
        "parent_node_id": source_node.get("parent"),
        "message_id": message.get("id"),
        "role": author.get("role"),
        "create_time_raw": message.get("create_time"),
        "content_type": content_type,
    }
