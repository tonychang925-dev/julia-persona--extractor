from __future__ import annotations

from typing import Any


def detect_candidates(segments: list[Any]) -> list[dict[str, Any]]:
    return [{"candidate_id": f"candidate_{i+1:04d}", "segment_id": getattr(s, "segment_id", str(i)), "status": "detected", "evidence": getattr(s, "evidence", {})} for i, s in enumerate(segments)]
