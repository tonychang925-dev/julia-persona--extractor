"""Backward-compatible event segmentation entry points."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from persona_extractor.segmentation.turn_window_segmenter import TurnWindowSegmenter


@dataclass(frozen=True)
class EventSegment:
    segment_id: str
    message_ids: list[str]
    boundary_reason: str
    evidence: dict[str, Any]


def segment_archive_by_turn_window(
    archive: dict[str, Any],
    window_size: int = 8,
) -> list[dict[str, Any]]:
    """Return Event Segment schema-compatible dictionaries."""
    return TurnWindowSegmenter(window_size=window_size).segment(archive)


def segment_by_turn_window(messages: list[dict[str, Any]], window_size: int = 8) -> list[EventSegment]:
    """Legacy prototype API retained for early tests.

    Prefer `TurnWindowSegmenter.segment(archive)` for M1 schema-compatible output.
    """
    segments: list[EventSegment] = []
    for index in range(0, len(messages), window_size):
        chunk = messages[index : index + window_size]
        segments.append(
            EventSegment(
                segment_id=f"segment_{len(segments) + 1:04d}",
                message_ids=[message["message_id"] for message in chunk],
                boundary_reason="fixed_turn_window_v0",
                evidence={"start_offset": index, "end_offset": index + len(chunk) - 1},
            )
        )
    return segments
