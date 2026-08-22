"""Candidate experience detection."""

from __future__ import annotations

from typing import Any


def detect_candidates(segments: list[Any]) -> list[dict[str, Any]]:
    """Return reviewable candidate shells for event segments."""
    return [
        {
            "candidate_id": f"candidate_{index + 1:04d}",
            "segment_id": getattr(segment, "segment_id", str(index)),
            "status": "detected",
            "evidence": getattr(segment, "evidence", {}),
        }
        for index, segment in enumerate(segments)
    ]
