from __future__ import annotations

FORBIDDEN_FUSION_FIELDS = {
    "importance",
    "identity_relevance",
    "meaning",
    "impact",
    "identity_change",
    "personality",
    "causal_claim",
    "relationship_delta",
    "behavioral_consequence",
    "runtime_eligibility",
    "activation_weight",
    "governance_status",
}

ALLOWED_BASIS = {
    "signal_count",
    "signal_strength",
    "signal_consistency",
    "provenance_quality",
    "source_segment_coverage",
}


def make_fusion() -> dict:
    return {
        "schema_version": "0.2.0",
        "fusion_id": "fusion_001",
        "candidate_id": "candidate_001",
        "signals": [
            {"signal_type": "repeated_reference", "strength": 0.5, "observed_on": ["segment_001"]},
            {"signal_type": "manual_review_marker", "strength": 1.0, "observed_on": ["segment_001"]},
        ],
        "fusion_method": "weighted_observable_signal_average",
        "confidence": {
            "score": 0.75,
            "basis": ["signal_count", "signal_strength", "provenance_quality"],
            "factors": {
                "signal_count": 2,
                "mean_signal_strength": 0.75,
                "max_signal_strength": 1.0,
                "provenance_quality": 1.0,
                "source_segment_coverage": 1.0,
            },
        },
        "provenance_refs": ["archive_001:message_001"],
        "created_by": {"component": "SignalFusion", "version": "0.1.0"},
    }


def test_fusion_references_candidate_and_signals():
    fusion = make_fusion()
    assert fusion["candidate_id"] == "candidate_001"
    assert fusion["signals"]
    assert all(signal["observed_on"] for signal in fusion["signals"])


def test_fusion_confidence_uses_allowed_basis_only():
    fusion = make_fusion()
    assert set(fusion["confidence"]["basis"]).issubset(ALLOWED_BASIS)
    assert 0 <= fusion["confidence"]["score"] <= 1


def test_fusion_preserves_provenance():
    fusion = make_fusion()
    assert fusion["provenance_refs"] == ["archive_001:message_001"]


def test_fusion_generates_no_importance_identity_causal_or_runtime_fields():
    fusion = make_fusion()
    assert FORBIDDEN_FUSION_FIELDS.isdisjoint(fusion.keys())
