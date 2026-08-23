from persona_extractor.extraction.candidate_detector import CandidateExperienceDetector
from persona_extractor.segmentation.turn_window_segmenter import TurnWindowSegmenter


def make_archive() -> dict:
    return {
        "archive_id": "archive_candidate",
        "messages": [
            {
                "message_id": "m1",
                "content": "coffee planning coffee",
                "immutable_ref": {"archive_id": "archive_candidate"},
            },
            {
                "message_id": "m2",
                "content": "ordinary note",
                "immutable_ref": {"archive_id": "archive_candidate"},
            },
            {
                "message_id": "m3",
                "content": "TODO_REVIEW explicit marker",
                "immutable_ref": {"archive_id": "archive_candidate"},
            },
        ],
    }


def test_candidate_detector_emits_candidates_from_observable_signals():
    archive = make_archive()
    segments = TurnWindowSegmenter(window_size=1).segment(archive)
    candidates = CandidateExperienceDetector().detect(archive, segments)

    assert [candidate["candidate_id"] for candidate in candidates] == ["candidate_0001", "candidate_0002"]
    assert candidates[0]["detection_signals"][0]["signal_type"] == "repeated_reference"
    assert candidates[1]["detection_signals"][0]["signal_type"] == "manual_review_marker"


def test_candidate_detector_preserves_segment_provenance():
    archive = make_archive()
    segments = TurnWindowSegmenter(window_size=1).segment(archive)
    candidate = CandidateExperienceDetector().detect(archive, segments)[0]

    assert candidate["source_segments"][0]["segment_id"] == "segment_0001"
    assert candidate["provenance_refs"] == ["archive_candidate:m1"]
