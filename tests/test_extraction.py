from persona_extractor.extraction.candidate_detector import detect_candidates
from persona_extractor.extraction.causal_extractor import build_causal_experience_candidate
from persona_extractor.segmentation.event_segmenter import EventSegment


def test_build_causal_experience_candidate():
    segment = EventSegment("s1", ["m1"], "fixture", {"source_id": "m1"})
    candidate = detect_candidates([segment])[0]
    experience = build_causal_experience_candidate(candidate)
    assert experience["lifecycle_status"] == "extracted"
    assert experience["experience_id"] == "experience_0001"
