from persona_extractor.segmentation.event_segmenter import segment_by_turn_window


def test_segment_by_turn_window():
    messages = [{"message_id": f"m{i}"} for i in range(9)]
    segments = segment_by_turn_window(messages, window_size=4)
    assert len(segments) == 3
