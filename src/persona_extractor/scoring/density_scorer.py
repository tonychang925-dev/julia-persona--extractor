from __future__ import annotations

from typing import Any


def score_density(experience: dict[str, Any]) -> dict[str, Any]:
    updated = dict(experience)
    count = len(updated.get("provenance", []))
    updated["causal_density"] = {"score": min(1.0, count / 10), "factors": {"provenance_count": float(count)}}
    return updated
