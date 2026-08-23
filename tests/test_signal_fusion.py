from persona_extractor.extraction.signal_fusion import SignalFusion


def make_candidate() -> dict:
    return {
        "schema_version": "0.2.0",
        "candidate_id": "candidate_0001",
        "source_segments": [
            {
                "segment_id": "segment_0001",
                "archive_id": "archive_001",
                "message_ids": ["m1"],
                "provenance_refs": ["archive_001:m1"],
            }
        ],
        "detection_signals": [
            {"signal_type": "repeated_reference", "strength": 0.5, "observed_on": ["segment_0001"]},
            {"signal_type": "manual_review_marker", "strength": 1.0, "observed_on": ["segment_0001"]},
        ],
        "confidence": {
            "review_worthiness": 1.0,
            "signal_strength": 1.0,
            "provenance_quality": 1.0,
        },
        "provenance_refs": ["archive_001:m1"],
        "created_by": {"component": "CandidateExperienceDetector", "version": "0.1.0"},
    }


def test_weighted_signal_fusion_outputs_schema_shape():
    fusion = SignalFusion().fuse(make_candidate())

    assert fusion["fusion_id"] == "fusion_0001"
    assert fusion["candidate_id"] == "candidate_0001"
    assert fusion["fusion_method"] == "weighted_observable_signal_average"
    assert 0 <= fusion["confidence"]["score"] <= 1
    assert fusion["provenance_refs"] == ["archive_001:m1"]


def test_max_signal_strength_method():
    fusion = SignalFusion(method="max_signal_strength").fuse(make_candidate())
    assert fusion["confidence"]["score"] == 1.0
    assert fusion["confidence"]["basis"] == ["signal_strength", "provenance_quality"]
