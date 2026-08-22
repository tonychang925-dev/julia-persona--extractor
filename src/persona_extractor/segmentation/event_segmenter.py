from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EventSegment:
    segment_id: str
    message_ids: list[str]
    boundary_reason: str
    evidence: dict[str, Any]


def segment_by_turn_window(messages: list[dict[str, Any]], window_size: int = 8) -> list[EventSegment]:
    segments: list[EventSegment] = []
    for index in range(0, len(messages), window_size):
        chunk = messages[index:index + window_size]
        segments.append(EventSegment(f"segment_{len(segments)+1:04d}", [m["message_id"] for m in chunk], "fixed_turn_window_v0", {"start_offset": index, "end_offset": index + len(chunk) - 1}))
    return segments
