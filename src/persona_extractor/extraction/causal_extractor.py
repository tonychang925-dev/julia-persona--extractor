from __future__ import annotations

from typing import Any


def build_causal_experience_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {"experience_id": candidate.get("candidate_id", "candidate_unknown").replace("candidate", "experience"), "provenance": [candidate.get("evidence", {})], "trigger": "TBD_BY_REVIEW", "response": "TBD_BY_REVIEW", "transition": "TBD_BY_REVIEW", "relationship_delta": "TBD_BY_REVIEW", "behavioral_consequence": "TBD_BY_REVIEW", "activation_conditions": [], "causal_density": {"score": 0.0, "factors": {}}, "lifecycle_status": "extracted"}
