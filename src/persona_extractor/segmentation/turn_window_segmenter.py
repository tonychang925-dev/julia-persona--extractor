"""Deterministic fixed-turn segmentation strategy."""

from __future__ import annotations

from typing import Any

from persona_extractor.segmentation.base import Segmenter

FORBIDDEN_SEGMENT_FIELDS = {
    "meaning",
    "impact",
    "identity_change",
    "personality",
    "runtime_eligibility",
    "activation_weight",
    "governance_status",
}


class TurnWindowSegmenter(Segmenter):
    """Baseline segmentation strategy.

    Purpose:
        Produce reproducible event segments from fixed-size message windows.

    Not responsible for:
        - semantic interpretation;
        - importance scoring;
        - causal inference;
        - identity or persona judgment.
    """

    component = "TurnWindowSegmenter"
    version = "0.1.0"

    def __init__(self, window_size: int = 8) -> None:
        if window_size < 1:
            raise ValueError("window_size must be >= 1")
        self.window_size = window_size

    def segment(self, archive: dict[str, Any]) -> list[dict[str, Any]]:
        archive_id = archive["archive_id"]
        messages = archive.get("messages", [])
        segments: list[dict[str, Any]] = []

        for start in range(0, len(messages), self.window_size):
            chunk = messages[start : start + self.window_size]
            if not chunk:
                continue
            segment = self._build_segment(
                archive_id=archive_id,
                chunk=chunk,
                segment_index=len(segments) + 1,
            )
            forbidden = FORBIDDEN_SEGMENT_FIELDS.intersection(segment.keys())
            if forbidden:
                raise AssertionError(f"segment emitted forbidden fields: {sorted(forbidden)}")
            segments.append(segment)

        return segments

    def _build_segment(
        self,
        archive_id: str,
        chunk: list[dict[str, Any]],
        segment_index: int,
    ) -> dict[str, Any]:
        message_refs = [self._message_ref(archive_id, message) for message in chunk]
        provenance_refs = [item["provenance_ref"] for item in message_refs]
        return {
            "schema_version": "0.2.0",
            "segment_id": f"segment_{segment_index:04d}",
            "archive_id": archive_id,
            "message_refs": message_refs,
            "start_message_id": chunk[0]["message_id"],
            "end_message_id": chunk[-1]["message_id"],
            "boundary": {
                "strategy": "turn_window",
                "reason_codes": ["fixed_turn_window"],
                "deterministic": True,
                "parameters": {"window_size": self.window_size},
            },
            "provenance_refs": provenance_refs,
            "created_by": {"component": self.component, "version": self.version},
        }

    @staticmethod
    def _message_ref(archive_id: str, message: dict[str, Any]) -> dict[str, str]:
        message_archive_id = message.get("immutable_ref", {}).get("archive_id") or archive_id
        message_id = message["message_id"]
        return {
            "archive_id": message_archive_id,
            "message_id": message_id,
            "provenance_ref": f"{message_archive_id}:{message_id}",
        }
