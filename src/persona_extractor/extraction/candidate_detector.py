"""Candidate experience detection.

M2.0 detects review-worthy evidence regions from observable signals only.
It does not perform causal interpretation.
"""

from __future__ import annotations

from typing import Any

from persona_extractor.extraction.observable_signals import (
    FORBIDDEN_SIGNAL_FIELDS,
    ManualReviewMarkerDetector,
    RepeatedReferenceDetector,
)


class CandidateExperienceDetector:
    """Build Candidate Experience schema-compatible dictionaries."""

    component = "CandidateExperienceDetector"
    version = "0.1.0"

    def __init__(self, signal_detectors: list[Any] | None = None) -> None:
        self.signal_detectors = signal_detectors or [
            RepeatedReferenceDetector(),
            ManualReviewMarkerDetector(),
        ]

    def detect(self, archive: dict[str, Any], segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        messages_by_id = {message["message_id"]: message for message in archive.get("messages", [])}
        candidates: list[dict[str, Any]] = []
        for segment in segments:
            signals = []
            for detector in self.signal_detectors:
                signals.extend(signal.to_dict() for signal in detector.detect(segment, messages_by_id))
            if not signals:
                continue
            candidate = self._build_candidate(segment, signals, len(candidates) + 1)
            forbidden = FORBIDDEN_SIGNAL_FIELDS.intersection(candidate.keys())
            if forbidden:
                raise AssertionError(f"candidate emitted forbidden fields: {sorted(forbidden)}")
            candidates.append(candidate)
        return candidates

    def _build_candidate(
        self,
        segment: dict[str, Any],
        signals: list[dict[str, Any]],
        candidate_index: int,
    ) -> dict[str, Any]:
        provenance_refs = segment["provenance_refs"]
        signal_strength = max(signal["strength"] for signal in signals)
        return {
            "schema_version": "0.2.0",
            "candidate_id": f"candidate_{candidate_index:04d}",
            "source_segments": [
                {
                    "segment_id": segment["segment_id"],
                    "archive_id": segment["archive_id"],
                    "message_ids": [ref["message_id"] for ref in segment["message_refs"]],
                    "provenance_refs": provenance_refs,
                }
            ],
            "detection_signals": signals,
            "confidence": {
                "review_worthiness": signal_strength,
                "signal_strength": signal_strength,
                "provenance_quality": 1.0 if provenance_refs else 0.0,
            },
            "provenance_refs": provenance_refs,
            "created_by": {"component": self.component, "version": self.version},
        }


def detect_candidates(segments: list[Any]) -> list[dict[str, Any]]:
    """Legacy shell detector retained for pre-M2 tests."""
    return [
        {
            "candidate_id": f"candidate_{index + 1:04d}",
            "segment_id": getattr(segment, "segment_id", str(index)),
            "status": "detected",
            "evidence": getattr(segment, "evidence", {}),
        }
        for index, segment in enumerate(segments)
    ]
