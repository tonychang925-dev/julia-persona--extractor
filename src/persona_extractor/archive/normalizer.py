from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import uuid

SCHEMA_VERSION = "0.1.0"


@dataclass(frozen=True)
class Provenance:
    source_type: str
    source_path: str | None = None
    source_id: str | None = None
    source_offset: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        extra = data.pop("extra") or {}
        return {**data, **extra}


@dataclass(frozen=True)
class NormalizedMessage:
    message_id: str
    role: str
    content: str
    participant_id: str | None = None
    timestamp: str | None = None
    provenance: Provenance | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "role": self.role,
            "participant_id": self.participant_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "provenance": self.provenance.to_dict() if self.provenance else {"source_type": "unknown"},
        }


@dataclass(frozen=True)
class NormalizedConversationArchive:
    conversation_id: str
    participants: list[dict[str, Any]]
    messages: list[NormalizedMessage]
    provenance: Provenance
    title: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "conversation_id": self.conversation_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "participants": self.participants,
            "messages": [message.to_dict() for message in self.messages],
            "provenance": self.provenance.to_dict(),
        }


def stable_or_random_id(prefix: str, value: str | None = None) -> str:
    return str(value) if value else f"{prefix}_{uuid.uuid4().hex}"
