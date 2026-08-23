"""Observable signal detection for M2.0.

Signals are non-semantic evidence markers. They do not assert causality,
identity change, personality, or runtime authority.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable
import re

ALLOWED_SIGNAL_TYPES = {
    "conversation_length_change",
    "topic_transition",
    "emotional_intensity_change",
    "response_pattern_shift",
    "repeated_reference",
    "time_gap_proximity",
    "manual_review_marker",
}

FORBIDDEN_SIGNAL_FIELDS = {
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


@dataclass(frozen=True)
class DetectionSignal:
    signal_type: str
    strength: float
    observed_on: list[str]
    parameters: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        if self.signal_type not in ALLOWED_SIGNAL_TYPES:
            raise ValueError(f"unsupported signal_type: {self.signal_type}")
        data = {
            "signal_type": self.signal_type,
            "strength": max(0.0, min(1.0, self.strength)),
            "observed_on": self.observed_on,
            "parameters": self.parameters,
        }
        forbidden = FORBIDDEN_SIGNAL_FIELDS.intersection(data.keys())
        if forbidden:
            raise AssertionError(f"signal emitted forbidden fields: {sorted(forbidden)}")
        return data


class RepeatedReferenceDetector:
    """Detect repeated lexical references within segment text.

    This is a baseline observable signal detector. It counts repeated tokens only;
    it does not infer what those tokens mean.
    """

    signal_type = "repeated_reference"

    def __init__(self, min_token_length: int = 4, min_count: int = 2) -> None:
        self.min_token_length = min_token_length
        self.min_count = min_count

    def detect(self, segment: dict[str, Any], messages_by_id: dict[str, dict[str, Any]]) -> list[DetectionSignal]:
        tokens = list(self._tokens_for_segment(segment, messages_by_id))
        counts = Counter(tokens)
        repeated = {token: count for token, count in counts.items() if count >= self.min_count}
        if not repeated:
            return []
        max_count = max(repeated.values())
        strength = min(1.0, max_count / max(1, len(tokens)))
        return [
            DetectionSignal(
                signal_type=self.signal_type,
                strength=strength,
                observed_on=[segment["segment_id"]],
                parameters={"terms": repeated, "min_count": self.min_count},
            )
        ]

    def _tokens_for_segment(self, segment: dict[str, Any], messages_by_id: dict[str, dict[str, Any]]) -> Iterable[str]:
        for ref in segment.get("message_refs", []):
            content = messages_by_id.get(ref["message_id"], {}).get("content", "")
            for token in re.findall(r"[A-Za-z0-9_]+", content.lower()):
                if len(token) >= self.min_token_length:
                    yield token


class ManualReviewMarkerDetector:
    """Detect explicit manual review markers in message content."""

    signal_type = "manual_review_marker"

    def __init__(self, markers: tuple[str, ...] = ("TODO_REVIEW", "REVIEW_MARKER")) -> None:
        self.markers = markers

    def detect(self, segment: dict[str, Any], messages_by_id: dict[str, dict[str, Any]]) -> list[DetectionSignal]:
        hits: list[str] = []
        for ref in segment.get("message_refs", []):
            content = messages_by_id.get(ref["message_id"], {}).get("content", "")
            if any(marker in content for marker in self.markers):
                hits.append(ref["message_id"])
        if not hits:
            return []
        return [
            DetectionSignal(
                signal_type=self.signal_type,
                strength=1.0,
                observed_on=[segment["segment_id"]],
                parameters={"message_ids": hits, "markers": list(self.markers)},
            )
        ]
