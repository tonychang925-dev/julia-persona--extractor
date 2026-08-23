from __future__ import annotations

from persona_extractor.segmentation.evaluator import SegmentationEvaluator
from persona_extractor.segmentation.turn_window_segmenter import TurnWindowSegmenter


def test_segmentation_evaluation_emits_no_semantic_claims():
    archive = {
        "archive_id": "archive_neutrality",
        "messages": [
            {"message_id": "m1", "immutable_ref": {"archive_id": "archive_neutrality"}},
            {"message_id": "m2", "immutable_ref": {"archive_id": "archive_neutrality"}},
        ],
    }
    segments = TurnWindowSegmenter(window_size=1).segment(archive)
    report = SegmentationEvaluator().evaluate(archive, segments)

    assert report["metrics"]["segmentation_neutrality"]["neutral"] is True
    assert report["metrics"]["segmentation_neutrality"]["violations"] == []
