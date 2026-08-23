from __future__ import annotations

from persona_extractor.extraction.candidate_detector import CandidateExperienceDetector
from persona_extractor.segmentation.turn_window_segmenter import TurnWindowSegmenter

FORBIDDEN_FIELDS = {
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


def test_observable_signal_detector_does_not_emit_interpretation_fields():
    archive = {
        "archive_id": "archive_no_interpretation",
        "messages": [
            {
                "message_id": "m1",
                "content": "pattern pattern TODO_REVIEW",
                "immutable_ref": {"archive_id": "archive_no_interpretation"},
            }
        ],
    }
    segments = TurnWindowSegmenter(window_size=1).segment(archive)
    candidates = CandidateExperienceDetector().detect(archive, segments)

    for candidate in candidates:
        assert FORBIDDEN_FIELDS.isdisjoint(candidate.keys())
        for signal in candidate["detection_signals"]:
            assert FORBIDDEN_FIELDS.isdisjoint(signal.keys())
