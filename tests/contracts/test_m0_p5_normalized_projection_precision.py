"""M0-P5-FF-01 Normalized Projection Semantics precision tests (contract §15.5).

Locks the machine-enforced schema constraints and the frozen projection-profile
text. The standard: P5 is a faithful deterministic projection — canonical-only,
narrow text content, reused upstream IDs, no fabricated semantics.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[2]


def load_schema() -> dict:
    return json.loads((REPO / "schemas" / "normalized_archive.schema.json").read_text())


def assert_valid(instance: dict) -> None:
    jsonschema.Draft202012Validator(load_schema()).validate(instance)


def assert_invalid(instance: dict) -> None:
    errors = list(jsonschema.Draft202012Validator(load_schema()).iter_errors(instance))
    assert errors, "expected instance to be rejected by schema"


def _provenance() -> dict:
    return {
        "source_type": "chatgpt_official_export",
        "source_id": "conv_1",
        "source_offset": 0,
        "normalization_adapter": "chatgpt_official_export",
        "normalization_version": "0.3.0",
    }


def _message(**overrides: object) -> dict:
    m: dict = {
        "message_id": "normmsg_" + "c" * 64,
        "role": "user",
        "content": "hello",
        "source_evidence_ref": "node_" + "d" * 64,
        "lineage_state": "resolved",
        "lineage_ref": "lineage_" + "e" * 64,
        "bundle_eligibility": "not_eligible",
        "bundle_state": None,
        "bundle_ref": None,
        "provenance": _provenance(),
        "immutable_ref": {"archive_id": "norm_" + "a" * 64, "message_hash": "m" * 64},
    }
    m.update(overrides)
    return m


def _minimal_archive(**overrides: object) -> dict:
    a: dict = {
        "schema_version": "0.3.0",
        "archive_id": "norm_" + "a" * 64,
        "source_evidence_archive_ref": "sea_" + "b" * 64,
        "source_identity": {
            "source_type": "chatgpt_official_export",
            "source_id": "conv_1",
            "ingested_at": "2024-01-01T00:00:00.000000Z",
        },
        "provenance": _provenance(),
        "immutability": {
            "normalized_content_hash": "h" * 64,
            "raw_content_hash": "r" * 64,
            "normalization_adapter": "chatgpt_official_export",
            "normalization_version": "0.3.0",
        },
        "participants": [{"participant_id": "role:user", "role": "user", "display_name": None}],
        "messages": [_message()],
    }
    a.update(overrides)
    return a


# --------------------------------------------------------------------------- #
# C00-C02, C05-C09 — schema enforcement
# --------------------------------------------------------------------------- #

def test_c00_baseline_archive_is_schema_valid():
    assert_valid(_minimal_archive())


def test_c01_schema_version_must_be_0_3_0():
    a = _minimal_archive()
    a["schema_version"] = "0.2.0"
    assert_invalid(a)


def test_c02_ingested_at_null_is_valid():
    a = _minimal_archive()
    a["source_identity"]["ingested_at"] = None
    assert_valid(a)


def test_c05_source_evidence_ref_is_required():
    a = _minimal_archive()
    a["messages"][0].pop("source_evidence_ref")
    assert_invalid(a)


def test_c06_resolved_lineage_requires_lineage_ref():
    a = _minimal_archive()
    a["messages"][0]["lineage_state"] = "resolved"
    a["messages"][0].pop("lineage_ref")
    assert_invalid(a)


def test_c07_eligible_requires_bundle_state():
    a = _minimal_archive()
    a["messages"][0]["bundle_eligibility"] = "eligible"
    a["messages"][0].pop("bundle_state")
    assert_invalid(a)


def test_c08_resolved_bundle_requires_bundle_ref():
    a = _minimal_archive()
    a["messages"][0]["bundle_eligibility"] = "eligible"
    a["messages"][0]["bundle_state"] = "resolved"
    a["messages"][0].pop("bundle_ref")
    assert_invalid(a)


def test_c09_ambiguous_bundle_requires_bundle_ref():
    a = _minimal_archive()
    a["messages"][0]["bundle_eligibility"] = "eligible"
    a["messages"][0]["bundle_state"] = "ambiguous"
    a["messages"][0].pop("bundle_ref")
    assert_invalid(a)


# --------------------------------------------------------------------------- #
# C03-C04, C10-C17 — contract text conformance
# --------------------------------------------------------------------------- #

def _contract() -> str:
    return (REPO / "docs" / "M0_EVIDENCE_SUBSTRATE_CONTRACT.md").read_text()


def test_c03_archive_id_namespace_norm():
    c = _contract()
    assert '"norm_" + SHA256_HEX' in c


def test_c04_message_id_namespace_normmsg():
    c = _contract()
    assert '"normmsg_" + SHA256_HEX' in c


def test_c10_contract_says_canonical_only_projection():
    c = _contract()
    assert "canonical-only" in c
    assert "projected  : message is a dict" in c


def test_c11_contract_says_alternate_must_not_be_flattened():
    c = _contract()
    assert "MUST NOT be flattened into `messages[]`" in c


def test_c12_contract_says_typed_artifacts_not_content_authority():
    c = _contract()
    assert "TypedArtifactView is NOT the normalized-content authority" in c


def test_c13_content_textual_projection_table_frozen():
    c = _contract()
    assert "narrow textual projection" in c
    assert 'content_type == "text"' in c
    assert 'content_type == "multimodal_text"' in c
    assert 'content_type in {thoughts, reasoning_recap, image_asset_pointer}' in c


def test_c14_role_and_participant_semantics_frozen():
    c = _contract()
    assert 'participant_id = "role:" + normalized_role' in c
    assert '-> "unknown"' in c


def test_c15_id_formulas_frozen():
    c = _contract()
    assert "NORMALIZED-ARCHIVE-ID-v1" in c
    assert "NORMALIZED-MESSAGE-ID-v1" in c


def test_c16_hash_formulas_frozen():
    c = _contract()
    assert "NORMALIZED-MESSAGE-HASH-v1" in c
    assert "NORMALIZED-CONTENT-HASH-v1" in c


def test_c17_unknown_ingestion_time_must_remain_null():
    c = _contract()
    assert "Unknown ingestion time MUST remain `null`" in c
