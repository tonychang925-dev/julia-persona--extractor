"""M0 evidence-substrate schema enforcement tests.

Covers the M0-SEA-T01..T09, T12, T13 family from contract §19: whole-source
integrity, evidence conservation, topology, lineage determinism, branch and
typed-artifact preservation, provenance determinism, derived-view non-authority,
projection traceability, and source-payload preservation.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[2]

FORBIDDEN_INTERPRETATION_FIELDS = [
    "meaning",
    "persona_truth",
    "identity_change",
    "relationship_delta",
    "behavioral_consequence",
    "causal_claim",
    "runtime_eligibility",
    "activation_weight",
    "governance_status",
    "identity_authority_granted",
]


def load_schema(name: str) -> dict:
    return json.loads((REPO / "schemas" / name).read_text())


def assert_valid(schema: dict, instance: dict) -> None:
    jsonschema.Draft202012Validator(schema).validate(instance)


def assert_invalid(schema: dict, instance: dict) -> None:
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(instance))
    assert errors, "expected instance to be rejected by schema"


# --------------------------------------------------------------------------- #
# T01 — Whole source integrity
# --------------------------------------------------------------------------- #

def test_t01_source_manifest_requires_byte_level_sha256():
    schema = load_schema("raw_source_manifest.schema.json")
    manifest = _manifest()
    assert_valid(schema, manifest)
    # wrong-length hash is rejected
    broken = dict(manifest)
    broken["source_sha256"] = "abc"
    assert_invalid(schema, broken)
    # missing hash is rejected
    broken2 = dict(manifest)
    broken2.pop("source_sha256")
    assert_invalid(schema, broken2)


# --------------------------------------------------------------------------- #
# T02 — Evidence conservation
# --------------------------------------------------------------------------- #

def test_t02_sea_requires_nodes_and_accounting():
    schema = load_schema("source_evidence_archive.schema.json")
    sea = _sea_with_node()
    assert_valid(schema, sea)
    broken = dict(sea)
    broken.pop("accounting")
    assert_invalid(schema, broken)


# --------------------------------------------------------------------------- #
# T03 — Parent topology fidelity
# --------------------------------------------------------------------------- #

def test_t03_sea_node_structural_projection_preserves_parent():
    schema = load_schema("source_evidence_archive.schema.json")
    sea = _sea_with_node()
    node = sea["nodes"][0]
    node["structural_projection"] = {
        "parent_node_id": "n1",
        "message_id": "m2",
        "role": "assistant",
        "create_time_raw": 1786071638.0,
        "content_type": "text",
    }
    assert_valid(schema, sea)


# --------------------------------------------------------------------------- #
# T04 — Canonical lineage determinism
# --------------------------------------------------------------------------- #

def test_t04_lineage_view_requires_deterministic_resolution():
    schema = load_schema("canonical_lineage_view.schema.json")
    view = {
        "schema_version": "0.1.0",
        "resolution_status": "resolved",
        "evidence_archive_id": "sea_" + "a" * 64,
        "current_node_id": "n3",
        "resolution_method": "source_native_parent_ancestry",
        "resolution_profile": "chatgpt-official-export-canonical-lineage-v0.1",
        "lineage_id": "lineage_" + "b" * 64,
        "node_refs": ["n1", "n2", "n3"],
    }
    assert_valid(schema, view)
    # resolved without lineage_id is invalid
    broken = dict(view)
    broken.pop("lineage_id")
    assert_invalid(schema, broken)


# --------------------------------------------------------------------------- #
# T05 — Alternate branch preservation
# --------------------------------------------------------------------------- #

def test_t05_alternate_view_preserves_off_chain_evidence():
    schema = load_schema("alternate_evidence_view.schema.json")
    alt = {
        "schema_version": "0.1.0",
        "evidence_archive_id": "sea_" + "a" * 64,
        "source_node_ref": "n4",
        "lineage_status": "alternate",
        "active_context_membership": False,
        "historical_exposure": "unknown",
    }
    assert_valid(schema, alt)
    # alternate view must not claim context authority
    broken = dict(alt)
    broken["active_context_membership"] = True
    assert_invalid(schema, broken)


# --------------------------------------------------------------------------- #
# T06 — Typed artifact preservation
# --------------------------------------------------------------------------- #

def test_t06_typed_artifact_view_preserves_typed_payload():
    schema = load_schema("typed_artifact_view.schema.json")
    artifact = {
        "schema_version": "0.1.0",
        "artifact_id": "artifact_" + "c" * 64,
        "source_node_ref": "n5",
        "source_content_type": "thoughts",
        "artifact_class": "exported_decision_trace",
        "evidence_class": "observed_export_artifact",
        "payload": {"content": "保持自然真诚"},
    }
    assert_valid(schema, artifact)
    broken = dict(artifact)
    broken.pop("payload")
    assert_invalid(schema, broken)


# --------------------------------------------------------------------------- #
# T07 — Timestamp / modality preservation
# --------------------------------------------------------------------------- #

def test_t07_structural_projection_preserves_raw_timestamp_and_content_type():
    schema = load_schema("source_evidence_archive.schema.json")
    sea = _sea_with_node()
    sea["nodes"][0]["structural_projection"] = {
        "parent_node_id": "n1",
        "message_id": "m2",
        "role": "assistant",
        "create_time_raw": 1786071638.29659,
        "content_type": "multimodal_text",
    }
    assert_valid(schema, sea)


# --------------------------------------------------------------------------- #
# T08 — Deterministic provenance (no random IDs)
# --------------------------------------------------------------------------- #

def test_t08_node_evidence_id_must_be_deterministic_hex_derived():
    schema = load_schema("source_evidence_archive.schema.json")
    sea = _sea_with_node()
    assert_valid(schema, sea)
    # a UUID-like (non hex, non node_ prefix) evidence id is rejected
    broken = dict(sea)
    broken["nodes"][0]["node_evidence_id"] = "node_9b2b5e0e-1234-5678-9abc-def012345678"
    assert_invalid(schema, broken)


# --------------------------------------------------------------------------- #
# T09 — Derived view non-authority
# --------------------------------------------------------------------------- #

def test_t09_derived_views_reject_interpretation_and_authority_fields():
    sea_schema = load_schema("source_evidence_archive.schema.json")
    alt_schema = load_schema("alternate_evidence_view.schema.json")
    typed_schema = load_schema("typed_artifact_view.schema.json")
    bundle_schema = load_schema("response_bundle_view.schema.json")
    for field in FORBIDDEN_INTERPRETATION_FIELDS:
        sea = _sea_with_node()
        sea[field] = "not allowed"
        assert_invalid(sea_schema, sea)

        alt = _alternate()
        alt[field] = "not allowed"
        assert_invalid(alt_schema, alt)

        typed = _typed()
        typed[field] = "not allowed"
        assert_invalid(typed_schema, typed)

        bundle = _bundle()
        bundle[field] = "not allowed"
        assert_invalid(bundle_schema, bundle)


# --------------------------------------------------------------------------- #
# T12 — Normalized projection traceability
# --------------------------------------------------------------------------- #

def test_t12_normalized_archive_requires_source_evidence_archive_ref():
    schema = load_schema("normalized_archive.schema.json")
    archive = _normalized()
    assert_valid(schema, archive)
    broken = dict(archive)
    broken.pop("source_evidence_archive_ref")
    assert_invalid(schema, broken)


# --------------------------------------------------------------------------- #
# T13 — Source payload preservation
# --------------------------------------------------------------------------- #

def test_t13_sea_node_requires_independently_recoverable_source_payload():
    schema = load_schema("source_evidence_archive.schema.json")
    sea = _sea_with_node()
    assert_valid(schema, sea)
    broken = dict(sea)
    broken["nodes"][0].pop("source_payload")
    assert_invalid(schema, broken)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

def _manifest() -> dict:
    return {
        "schema_version": "0.1.0",
        "source_archive_id": "rawsrc_" + "f" * 64,
        "source_type": "chatgpt_official_export",
        "source_sha256": "a" * 64,
        "source_locator": {"path": "conversations-001.json", "uri": None},
        "ingested_at": "2026-08-26T00:00:00Z",
        "adapter": {"name": "chatgpt_official_export", "version": "0.1.0"},
    }


def _sea_with_node() -> dict:
    return {
        "schema_version": "0.1.0",
        "evidence_archive_id": "sea_" + "e" * 64,
        "source_manifest_ref": "rawsrc_" + "f" * 64,
        "source_unit": {
            "unit_type": "conversation",
            "source_native_id": "conv_1",
            "source_pointer": "/mapping",
        },
        "source_native": {
            "source_type": "chatgpt_official_export",
            "conversation_id": "conv_1",
            "current_node": "n2",
            "title": "Hi Mira",
        },
        "nodes": [
            {
                "source_node_id": "n2",
                "node_evidence_id": "node_" + "b" * 64,
                "source_payload": {"message": None},
                "structural_projection": {
                    "parent_node_id": "n1",
                    "message_id": None,
                    "role": None,
                    "create_time_raw": None,
                    "content_type": None,
                },
                "provenance": {
                    "source_archive_ref": "rawsrc_" + "f" * 64,
                    "source_sha256": "a" * 64,
                    "json_pointer": "/mapping/n2",
                    "source_node_id": "n2",
                    "canonical_node_hash": "c" * 64,
                },
            }
        ],
        "accounting": {
            "source_node_count": 1,
            "preserved_node_count": 1,
            "excluded_node_count": 0,
            "exclusions": [],
        },
    }


def _alternate() -> dict:
    return {
        "schema_version": "0.1.0",
        "evidence_archive_id": "sea_" + "a" * 64,
        "source_node_ref": "n4",
        "lineage_status": "alternate",
        "active_context_membership": False,
        "historical_exposure": "unknown",
    }


def _typed() -> dict:
    return {
        "schema_version": "0.1.0",
        "artifact_id": "artifact_" + "c" * 64,
        "source_node_ref": "n5",
        "source_content_type": "thoughts",
        "artifact_class": "exported_decision_trace",
        "evidence_class": "observed_export_artifact",
        "payload": {},
    }


def _bundle() -> dict:
    return {
        "schema_version": "0.1.0",
        "bundle_id": "bundle_" + "d" * 64,
        "bundle_state": "resolved",
        "evidence_archive_id": "sea_" + "a" * 64,
        "resolution_profile": "chatgpt-official-export-response-bundle-v0.1",
        "trigger_refs": ["u1"],
        "member_node_refs": ["n2"],
        "provenance_refs": ["n2"],
    }


def _normalized() -> dict:
    return {
        "schema_version": "0.3.0",
        "archive_id": "archive_1",
        "source_evidence_archive_ref": "sea_" + "a" * 64,
        "source_identity": {
            "source_type": "chatgpt_official_export",
            "source_id": "conv_1",
            "ingested_at": "2026-08-26T00:00:00Z",
        },
        "provenance": {
            "source_type": "chatgpt",
            "source_id": "conv_1",
            "source_offset": 0,
            "normalization_adapter": "chatgpt",
            "normalization_version": "0.3.0",
        },
        "immutability": {
            "normalized_content_hash": None,
            "raw_content_hash": None,
            "normalization_adapter": "chatgpt",
            "normalization_version": "0.3.0",
        },
        "participants": [{"participant_id": "user", "role": "user"}],
        "messages": [
            {
                "message_id": "m1",
                "role": "assistant",
                "content": "hi",
                "timestamp": None,
                "source_evidence_ref": "node_" + "b" * 64,
                "lineage_ref": None,
                "bundle_state": None,
                "bundle_ref": None,
                "provenance": {
                    "source_type": "chatgpt",
                    "source_id": "conv_1",
                    "source_offset": 0,
                    "normalization_adapter": "chatgpt",
                    "normalization_version": "0.3.0",
                },
                "immutable_ref": {"archive_id": "archive_1", "message_hash": None},
            }
        ],
    }
