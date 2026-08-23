from persona_extractor.segmentation.turn_window_segmenter import TurnWindowSegmenter


def make_archive(count: int = 5) -> dict:
    return {
        "schema_version": "0.2.0",
        "archive_id": "archive_001",
        "messages": [
            {
                "message_id": f"message_{index:03d}",
                "content": f"message {index}",
                "immutable_ref": {"archive_id": "archive_001"},
            }
            for index in range(1, count + 1)
        ],
    }


def test_turn_window_segmenter_emits_schema_shape():
    segments = TurnWindowSegmenter(window_size=2).segment(make_archive(3))

    assert [segment["segment_id"] for segment in segments] == ["segment_0001", "segment_0002"]
    assert segments[0]["start_message_id"] == "message_001"
    assert segments[0]["end_message_id"] == "message_002"
    assert segments[0]["boundary"]["strategy"] == "turn_window"
    assert segments[0]["provenance_refs"] == ["archive_001:message_001", "archive_001:message_002"]


def test_turn_window_segmenter_is_reproducible():
    archive = make_archive(5)
    first = TurnWindowSegmenter(window_size=2).segment(archive)
    second = TurnWindowSegmenter(window_size=2).segment(archive)
    assert first == second
