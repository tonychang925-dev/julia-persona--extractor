from __future__ import annotations

from persona_extractor.extraction.signal_fusion import SignalFusion
from tests.test_signal_fusion import make_candidate

FORBIDDEN_FIELDS = {
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


def test_signal_fusion_does_not_emit_interpretation_or_authority_fields():
    fusion = SignalFusion().fuse(make_candidate())
    assert FORBIDDEN_FIELDS.isdisjoint(fusion.keys())
    assert FORBIDDEN_FIELDS.isdisjoint(fusion["confidence"].keys())


def test_signal_fusion_references_candidate_signals_and_provenance():
    fusion = SignalFusion().fuse(make_candidate())
    assert fusion["candidate_id"] == "candidate_0001"
    assert fusion["signals"]
    assert fusion["provenance_refs"]
