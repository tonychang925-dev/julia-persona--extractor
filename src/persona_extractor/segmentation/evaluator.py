"""M1.1 segmentation evaluation.

Evaluates container reliability only. Does not interpret segment meaning.
"""

from __future__ import annotations

from statistics import mean, median
from typing import Any
import hashlib
import json

FORBIDDEN_EVALUATION_FIELDS = {
    "meaning",
    "impact",
    "identity_change",
    "personality",
    "runtime_eligibility",
    "activation_weight",
    "governance_status",
    "causal_claim",
}


class SegmentationEvaluator:
    """Compute architecture-safe segmentation quality metrics."""

    component = "SegmentationEvaluator"
    version = "0.1.0"

    def evaluate(self, archive: dict[str, Any], segments: list[dict[str, Any]]) -> dict[str, Any]:
        report = {
            "schema_version": "0.2.0",
            "archive_id": archive["archive_id"],
            "metrics": {
                "coverage": self.coverage(archive, segments),
                "boundary_stability": self.boundary_stability(segments),
                "segment_size_distribution": self.segment_size_distribution(segments),
                "provenance_completeness": self.provenance_completeness(segments),
                "segmentation_neutrality": self.segmentation_neutrality(segments),
            },
            "created_by": {"component": self.component, "version": self.version},
        }
        forbidden = FORBIDDEN_EVALUATION_FIELDS.intersection(report.keys())
        if forbidden:
            raise AssertionError(f"evaluation emitted forbidden fields: {sorted(forbidden)}")
        return report

    @staticmethod
    def coverage(archive: dict[str, Any], segments: list[dict[str, Any]]) -> dict[str, Any]:
        archive_message_ids = [message["message_id"] for message in archive.get("messages", [])]
        segmented_message_ids = [
            ref["message_id"]
            for segment in segments
            for ref in segment.get("message_refs", [])
        ]
        archive_set = set(archive_message_ids)
        segmented_set = set(segmented_message_ids)
        duplicates = sorted({mid for mid in segmented_message_ids if segmented_message_ids.count(mid) > 1})
        unsegmented = [mid for mid in archive_message_ids if mid not in segmented_set]
        coverage_ratio = 1.0 if not archive_message_ids else len(segmented_set & archive_set) / len(archive_message_ids)
        return {
            "total_messages": len(archive_message_ids),
            "segmented_messages": len(segmented_message_ids),
            "unsegmented_messages": unsegmented,
            "duplicate_messages": duplicates,
            "coverage_ratio": coverage_ratio,
        }

    @staticmethod
    def boundary_stability(segments: list[dict[str, Any]]) -> dict[str, Any]:
        boundaries = [
            {
                "segment_id": segment["segment_id"],
                "start_message_id": segment["start_message_id"],
                "end_message_id": segment["end_message_id"],
                "strategy": segment["boundary"]["strategy"],
                "parameters": segment["boundary"].get("parameters", {}),
            }
            for segment in segments
        ]
        signature = hashlib.sha256(
            json.dumps(boundaries, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        deterministic = all(segment.get("boundary", {}).get("deterministic") is True for segment in segments)
        return {"deterministic": deterministic, "stable": deterministic, "signature": signature}

    @staticmethod
    def segment_size_distribution(segments: list[dict[str, Any]]) -> dict[str, Any]:
        sizes = [len(segment.get("message_refs", [])) for segment in segments]
        if not sizes:
            return {"count": 0, "min": 0, "max": 0, "mean": 0, "median": 0, "p95": 0}
        ordered = sorted(sizes)
        p95_index = min(len(ordered) - 1, int(0.95 * (len(ordered) - 1)))
        return {
            "count": len(sizes),
            "min": min(sizes),
            "max": max(sizes),
            "mean": mean(sizes),
            "median": median(sizes),
            "p95": ordered[p95_index],
        }

    @staticmethod
    def provenance_completeness(segments: list[dict[str, Any]]) -> dict[str, Any]:
        missing = [
            segment["segment_id"]
            for segment in segments
            if not segment.get("provenance_refs")
            or any(not ref.get("provenance_ref") for ref in segment.get("message_refs", []))
        ]
        return {
            "segments_with_provenance": len(segments) - len(missing),
            "segments_missing_provenance": missing,
            "complete": not missing,
        }

    @staticmethod
    def segmentation_neutrality(segments: list[dict[str, Any]]) -> dict[str, Any]:
        violations: list[dict[str, Any]] = []
        for segment in segments:
            forbidden = sorted(FORBIDDEN_EVALUATION_FIELDS.intersection(segment.keys()))
            if forbidden:
                violations.append({"segment_id": segment.get("segment_id"), "fields": forbidden})
        return {"neutral": not violations, "violations": violations}
