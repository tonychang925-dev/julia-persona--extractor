from __future__ import annotations

FORBIDDEN_CANDIDATE_FIELDS = {
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

ALLOWED_SIGNAL_TYPES = {
    "conversation_length_change",
    "topic_transition",
    "emotional_intensity_change",
    "response_pattern_shift",
    "repeated_reference",
    "time_gap_proximity",
    "manual_review_marker",
}


def make_candidate() -> dict:
    return {
        "schema_version": "0.2.0",
        "candidate_id": "candidate_001",
        "source_segments": [
            {
                "segment_id": "segment_001",
                "archive_id": "archive_001",
                "message_ids": ["message_001", "message_002"],
                "provenance_refs": ["archive_001:message_001", "archive_001:message_002"],
            }
        ],
        "detection_signals": [
            {
                "signal_type": "repeated_reference",
                "strength": 0.5,
                "observed_on": ["segment_001"],
                "parameters": {"count": 2},
            }
        ],
        "confidence": {
            "review_worthiness": 0.5,
            "signal_strength": 0.5,
            "provenance_quality": 1.0,
        },
        "provenance_refs": ["archive_001:message_001", "archive_001:message_002"],
        "created_by": {"component": "CandidateExperienceDetector", "version": "0.1.0"},
    }


def test_candidate_references_segments_not_free_floating_claims():
    candidate = make_candidate()
    assert candidate["source_segments"]
    assert candidate["source_segments"][0]["segment_id"] == "segment_001"
    assert candidate["source_segments"][0]["message_ids"]


def test_candidate_preserves_provenance_to_segment_messages():
    candidate = make_candidate()
    segment_refs = set(candidate["source_segments"][0]["provenance_refs"])
    assert set(candidate["provenance_refs"]).issubset(segment_refs)


def test_candidate_detection_signals_are_allowed_and_non_semantic():
    candidate = make_candidate()
    for signal in candidate["detection_signals"]:
        assert signal["signal_type"] in ALLOWED_SIGNAL_TYPES
        assert 0 <= signal["strength"] <= 1
        assert signal["observed_on"]


def test_candidate_generates_no_causal_identity_persona_or_runtime_fields():
    candidate = make_candidate()
    assert FORBIDDEN_CANDIDATE_FIELDS.isdisjoint(candidate.keys())
