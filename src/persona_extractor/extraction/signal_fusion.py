"""Signal fusion for M2.2.

Combines observable signals into review confidence records only. Does not
produce importance, identity relevance, causal interpretation, or runtime
authority.
"""

from __future__ import annotations

from statistics import mean
from typing import Any

FORBIDDEN_FUSION_FIELDS = {
    "importance",
    "identity_relevance",
    "meaning",
    "impact",
    "identity_change",
    "personality",
    "causal_claim",
    "relationship_delta",
    "behavioral_consequence",
    "runtime_eligibility",
    "activation_weight",
    "governance_status",
}

ALLOWED_METHODS = {
    "weighted_observable_signal_average",
    "max_signal_strength",
}


class SignalFusion:
    """Build signal_fusion.schema.json-compatible records."""

    component = "SignalFusion"
    version = "0.1.0"

    def __init__(self, method: str = "weighted_observable_signal_average") -> None:
        if method not in ALLOWED_METHODS:
            raise ValueError(f"unsupported fusion method: {method}")
        self.method = method

    def fuse(self, candidate: dict[str, Any]) -> dict[str, Any]:
        signals = candidate.get("detection_signals", [])
        if not signals:
            raise ValueError("candidate must contain at least one detection signal")

        strengths = [float(signal["strength"]) for signal in signals]
        signal_count_factor = min(1.0, len(signals) / 5)
        mean_strength = mean(strengths)
        max_strength = max(strengths)
        provenance_quality = float(candidate.get("confidence", {}).get("provenance_quality", 0.0))
        source_segment_coverage = self._source_segment_coverage(candidate)

        if self.method == "max_signal_strength":
            score = max_strength
            basis = ["signal_strength", "provenance_quality"]
        else:
            score = (
                0.30 * signal_count_factor
                + 0.35 * mean_strength
                + 0.20 * provenance_quality
                + 0.15 * source_segment_coverage
            )
            basis = [
                "signal_count",
                "signal_strength",
                "provenance_quality",
                "source_segment_coverage",
            ]

        record = {
            "schema_version": "0.2.0",
            "fusion_id": candidate["candidate_id"].replace("candidate", "fusion", 1),
            "candidate_id": candidate["candidate_id"],
            "signals": [self._signal_ref(signal) for signal in signals],
            "fusion_method": self.method,
            "confidence": {
                "score": max(0.0, min(1.0, score)),
                "basis": basis,
                "factors": {
                    "signal_count": len(signals),
                    "mean_signal_strength": mean_strength,
                    "max_signal_strength": max_strength,
                    "provenance_quality": provenance_quality,
                    "source_segment_coverage": source_segment_coverage,
                },
            },
            "provenance_refs": candidate["provenance_refs"],
            "created_by": {"component": self.component, "version": self.version},
        }
        forbidden = FORBIDDEN_FUSION_FIELDS.intersection(record.keys())
        if forbidden:
            raise AssertionError(f"fusion emitted forbidden fields: {sorted(forbidden)}")
        return record

    @staticmethod
    def _signal_ref(signal: dict[str, Any]) -> dict[str, Any]:
        return {
            "signal_type": signal["signal_type"],
            "strength": signal["strength"],
            "observed_on": signal["observed_on"],
        }

    @staticmethod
    def _source_segment_coverage(candidate: dict[str, Any]) -> float:
        source_segments = candidate.get("source_segments", [])
        if not source_segments:
            return 0.0
        with_messages = [segment for segment in source_segments if segment.get("message_ids")]
        return len(with_messages) / len(source_segments)
