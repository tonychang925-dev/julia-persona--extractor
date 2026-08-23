from persona_extractor.review.review_queue import CandidateReviewQueue


def make_candidate() -> dict:
    return {
        "candidate_id": "candidate_0001",
        "provenance_refs": ["archive_001:m1"],
    }


def make_fusion() -> dict:
    return {
        "fusion_id": "fusion_0001",
        "candidate_id": "candidate_0001",
        "provenance_refs": ["archive_001:m1"],
    }


def test_review_queue_creates_detected_record():
    record = CandidateReviewQueue().create_record(make_candidate(), make_fusion())

    assert record["review_id"] == "review_0001"
    assert record["candidate_id"] == "candidate_0001"
    assert record["fusion_id"] == "fusion_0001"
    assert record["review_state"] == "detected"
    assert record["provenance_refs"] == ["archive_001:m1"]


def test_review_queue_transitions_valid_path():
    queue = CandidateReviewQueue()
    record = queue.create_record(make_candidate(), make_fusion())
    record = queue.transition(record, "scored", "fusion score available")
    record = queue.transition(record, "review_pending", "queued for review")

    assert record["review_state"] == "review_pending"
    assert [item["to"] for item in record["history"]] == ["detected", "scored", "review_pending"]
