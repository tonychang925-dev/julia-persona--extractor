from __future__ import annotations

from persona_extractor.review.review_queue import CandidateReviewQueue
from tests.test_candidate_review_queue import make_candidate, make_fusion

FORBIDDEN_FIELDS = {
    "identity_relevance",
    "causal_value",
    "importance",
    "meaning",
    "identity_change",
    "personality",
    "causal_claim",
    "relationship_delta",
    "behavioral_consequence",
    "runtime_eligibility",
    "activation_weight",
    "governance_status",
}


def test_review_queue_rejects_invalid_transition():
    queue = CandidateReviewQueue()
    record = queue.create_record(make_candidate(), make_fusion())
    try:
        queue.transition(record, "accepted_for_extraction", "invalid direct accept")
    except ValueError:
        return
    raise AssertionError("invalid transition was accepted")


def test_review_queue_preserves_candidate_fusion_and_provenance():
    queue = CandidateReviewQueue()
    record = queue.create_record(make_candidate(), make_fusion())
    updated = queue.transition(record, "scored", "fusion score available")

    assert updated["candidate_id"] == record["candidate_id"]
    assert updated["fusion_id"] == record["fusion_id"]
    assert updated["provenance_refs"] == record["provenance_refs"]


def test_review_queue_does_not_emit_identity_causal_importance_or_runtime_fields():
    record = CandidateReviewQueue().create_record(make_candidate(), make_fusion())
    assert FORBIDDEN_FIELDS.isdisjoint(record.keys())
