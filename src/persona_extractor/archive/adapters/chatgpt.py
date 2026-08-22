from __future__ import annotations

from typing import Any

from persona_extractor.archive.normalizer import NormalizedConversationArchive, NormalizedMessage, Provenance, stable_or_random_id


def normalize_chatgpt_conversation(raw: dict[str, Any], source_path: str | None = None) -> NormalizedConversationArchive:
    conversation_id = stable_or_random_id("conversation", raw.get("id"))
    messages: list[NormalizedMessage] = []
    for offset, (node_id, node) in enumerate((raw.get("mapping") or {}).items()):
        message = (node or {}).get("message") or {}
        author = message.get("author") or {}
        content = message.get("content") or {}
        parts = content.get("parts") or []
        text = "\n".join(str(part) for part in parts if part is not None).strip()
        if not text:
            continue
        role = author.get("role") or "unknown"
        messages.append(NormalizedMessage(
            message_id=stable_or_random_id("message", message.get("id") or node_id),
            role=role,
            participant_id=role,
            content=text,
            provenance=Provenance(source_type="chatgpt", source_path=source_path, source_id=node_id, source_offset=offset),
        ))
    return NormalizedConversationArchive(
        conversation_id=conversation_id,
        title=raw.get("title"),
        participants=[{"participant_id": "user", "role": "user", "display_name": None}, {"participant_id": "assistant", "role": "assistant", "display_name": None}],
        messages=messages,
        provenance=Provenance(source_type="chatgpt", source_path=source_path, source_id=conversation_id),
    )
