from __future__ import annotations

FORBIDDEN_SEGMENT_FIELDS = {
    "meaning",
    "impact",
    "identity_change",
    "personality",
    "runtime_eligibility",
    "activation_weight",
    "governance_status",
}


def make_segment() -> dict:
    return {
        "schema_version": "0.2.0",
        "segment_id": "segment_001",
        "archive_id": "archive_001",
        "message_refs": [
            {
                "archive_id": "archive_001",
                "message_id": "message_001",
                "provenance_ref": "archive_001:message_001",
            }
        ],
        "start_message_id": "message_001",
        "end_message_id": "message_001",
        "boundary": {
            "strategy": "turn_window",
            "reason_codes": ["fixed_turn_window"],
            "deterministic": True,
            "parameters": {"window_size": 1},
        },
        "provenance_refs": ["archive_001:message_001"],
        "created_by": {"component": "TurnWindowSegmenter", "version": "0.1.0"},
    }


def test_segment_provenance_preserved():
    segment = make_segment()
    assert segment["archive_id"] == segment["message_refs"][0]["archive_id"]
    assert segment["provenance_refs"]
    assert segment["message_refs"][0]["provenance_ref"] in segment["provenance_refs"]


def test_segment_has_reproducible_boundary_metadata():
    segment = make_segment()
    assert segment["boundary"]["strategy"] == "turn_window"
    assert segment["boundary"]["deterministic"] is True
    assert segment["boundary"]["parameters"]["window_size"] == 1


def test_segment_generates_no_semantic_claims_or_persona_fields():
    segment = make_segment()
    assert FORBIDDEN_SEGMENT_FIELDS.isdisjoint(segment.keys())
