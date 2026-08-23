from persona_extractor.segmentation.evaluator import SegmentationEvaluator
from persona_extractor.segmentation.turn_window_segmenter import TurnWindowSegmenter


def make_archive(count: int = 7) -> dict:
    return {
        "archive_id": "archive_eval",
        "messages": [
            {"message_id": f"m{i}", "immutable_ref": {"archive_id": "archive_eval"}}
            for i in range(count)
        ],
    }


def test_evaluator_reports_coverage_and_distribution():
    archive = make_archive(7)
    segments = TurnWindowSegmenter(window_size=3).segment(archive)
    report = SegmentationEvaluator().evaluate(archive, segments)

    assert report["metrics"]["coverage"]["coverage_ratio"] == 1.0
    assert report["metrics"]["coverage"]["unsegmented_messages"] == []
    assert report["metrics"]["segment_size_distribution"]["count"] == 3
    assert report["metrics"]["segment_size_distribution"]["max"] == 3


def test_evaluator_boundary_signature_is_stable():
    archive = make_archive(5)
    segments = TurnWindowSegmenter(window_size=2).segment(archive)
    evaluator = SegmentationEvaluator()

    first = evaluator.evaluate(archive, segments)
    second = evaluator.evaluate(archive, segments)

    assert first["metrics"]["boundary_stability"]["signature"] == second["metrics"]["boundary_stability"]["signature"]
    assert first["metrics"]["boundary_stability"]["stable"] is True
