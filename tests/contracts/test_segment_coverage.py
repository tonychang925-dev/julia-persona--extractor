from __future__ import annotations

from persona_extractor.segmentation.turn_window_segmenter import TurnWindowSegmenter


def test_all_messages_are_segmented_once_by_turn_window():
    archive = {
        "archive_id": "archive_coverage",
        "messages": [
            {"message_id": f"m{i}", "immutable_ref": {"archive_id": "archive_coverage"}}
            for i in range(7)
        ],
    }

    segments = TurnWindowSegmenter(window_size=3).segment(archive)
    segmented_message_ids = [
        message_ref["message_id"]
        for segment in segments
        for message_ref in segment["message_refs"]
    ]

    assert segmented_message_ids == [message["message_id"] for message in archive["messages"]]
    assert len(segmented_message_ids) == len(set(segmented_message_ids))
