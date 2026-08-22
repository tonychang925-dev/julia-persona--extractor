"""Causal density scoring prototype."""

from __future__ import annotations

from typing import Any


def score_density(experience: dict[str, Any]) -> dict[str, Any]:
    """Attach a transparent placeholder density score."""
    provenance_count = len(experience.get("provenance", []))
    score = min(1.0, provenance_count / 10)
    updated = dict(experience)
    updated["causal_density"] = {
        "score": score,
        "factors": {
            "provenance_count": float(provenance_count),
            "prototype_weight": 0.1,
        },
    }
    return updated
