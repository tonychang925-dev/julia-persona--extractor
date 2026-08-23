from __future__ import annotations

VALID_TRANSITIONS = {
    None: {"detected"},
    "detected": {"scored"},
    "scored": {"review_pending"},
    "review_pending": {"accepted_for_extraction", "rejected"},
    "accepted_for_extraction": set(),
    "rejected": set(),
}

FORBIDDEN_REVIEW_FIELDS = {
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


def make_review_record() -> dict:
    return {
        "schema_version": "0.2.0",
        "review_id": "review_001",
        "candidate_id": "candidate_001",
        "fusion_id": "fusion_001",
        "review_state": "review_pending",
        "decision_reason": "candidate has fused observable signals and is queued for review",
        "provenance_refs": ["archive_001:message_001"],
        "history": [
            {"from": None, "to": "detected", "actor": "CandidateExperienceDetector", "timestamp": "2026-08-23T00:00:00Z", "reason": "observable signals detected", "provenance_refs": ["archive_001:message_001"]},
            {"from": "detected", "to": "scored", "actor": "SignalFusion", "timestamp": "2026-08-23T00:01:00Z", "reason": "signal fusion record created", "provenance_refs": ["archive_001:message_001"]},
            {"from": "scored", "to": "review_pending", "actor": "CandidateReviewQueue", "timestamp": "2026-08-23T00:02:00Z", "reason": "queued for review", "provenance_refs": ["archive_001:message_001"]},
        ],
        "created_by": {"component": "CandidateReviewQueue", "version": "0.1.0"},
    }


def is_valid_transition(source: str | None, target: str) -> bool:
    return target in VALID_TRANSITIONS[source]


def test_review_state_machine_allows_expected_path():
    path = [(None, "detected"), ("detected", "scored"), ("scored", "review_pending")]
    assert all(is_valid_transition(source, target) for source, target in path)


def test_review_state_machine_rejects_direct_detected_to_accepted():
    assert not is_valid_transition("detected", "accepted_for_extraction")


def test_review_record_references_candidate_fusion_and_provenance():
    record = make_review_record()
    assert record["candidate_id"] == "candidate_001"
    assert record["fusion_id"] == "fusion_001"
    assert record["provenance_refs"]
    assert record["history"]


def test_review_record_generates_no_identity_causal_importance_or_runtime_fields():
    record = make_review_record()
    assert FORBIDDEN_REVIEW_FIELDS.isdisjoint(record.keys())
