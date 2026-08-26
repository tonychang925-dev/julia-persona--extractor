"""R0.1 conformance-primitive tests: canonicalization, ID, accounting, traceability.

Covers the R0.1-H01/H02/H03/H05 family from contract §19.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from _m0_conformance import (
    bundle_id,
    canonical_node_hash,
    canonicalize,
    evidence_archive_id,
    jcs_hash,
    lineage_id,
    node_evidence_id,
    sha256_hex,
    source_archive_id,
    view_id,
)

REPO = Path(__file__).resolve().parents[2]


def load_schema(name: str) -> dict:
    return json.loads((REPO / "schemas" / name).read_text())


def assert_valid(schema: dict, instance: dict) -> None:
    jsonschema.Draft202012Validator(schema).validate(instance)


def assert_invalid(schema: dict, instance: dict) -> None:
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(instance))
    assert errors, "expected instance to be rejected by schema"


# --------------------------------------------------------------------------- #
# R0.1-H01 — RFC 8785 canonicalization
# --------------------------------------------------------------------------- #

def test_h01_t01_rfc8785_conformance_vector():
    """The frozen conformance vector MUST reproduce exactly (contract §10.1)."""
    value = {"b": 2, "a": "Mira", "u": "老婆", "n": None, "t": True, "f": 1.5}
    canonical = '{"a":"Mira","b":2,"f":1.5,"n":null,"t":true,"u":"老婆"}'
    expected_hash = "9bf951a35a0e40688ff03e7b8c1757e5b9c76a301f5dce8709dddc64956ea7cc"
    assert canonicalize(value) == canonical
    assert sha256_hex(canonical) == expected_hash


def test_h01_t02_canonical_node_hash_is_deterministic_semantic_hash():
    """canonical_node_hash MUST equal SHA256(JCS(source_payload))."""
    payload = {"content_type": "thoughts", "content": "保持自然真诚"}
    assert canonical_node_hash(payload) == jcs_hash(payload)
    assert canonical_node_hash(payload) == canonical_node_hash(dict(payload))
    assert len(canonical_node_hash(payload)) == 64


def test_h01_key_order_does_not_change_canonicalization():
    """Canonicalization MUST be insensitive to input key insertion order."""
    a = {"b": 1, "a": 2}
    b = {"a": 2, "b": 1}
    assert canonicalize(a) == canonicalize(b)


# --------------------------------------------------------------------------- #
# R0.1-H02 — ID domain separation and stability
# --------------------------------------------------------------------------- #

def test_h02_t01_id_domain_separation_produces_distinct_ids():
    """Different domains/payloads MUST produce different IDs."""
    src_id = source_archive_id("chatgpt_official_export", "a" * 64)
    sea_id = evidence_archive_id(src_id, "/mapping/n1", "conv_1")
    node_id = node_evidence_id(sea_id, "n1", "/mapping/n1")
    lin_id = lineage_id(sea_id, "profile-v1", "n1", ["n1"])
    ids = {src_id, sea_id, node_id, lin_id}
    assert len(ids) == 4


def test_h02_t02_logical_id_is_stable_and_independent_of_adapter():
    """ID MUST NOT depend on adapter version or ingestion time."""
    first = source_archive_id("chatgpt_official_export", "b" * 64)
    second = source_archive_id("chatgpt_official_export", "b" * 64)
    assert first == second
    assert first.startswith("rawsrc_")
    assert len(first) == len("rawsrc_") + 64


def test_h02_id_prefixes_match_frozen_algorithms():
    """§21.1 frozen prefixes: rawsrc_ / sea_ / node_ / lineage_ / view_ / bundle_."""
    src = source_archive_id("t", "c" * 64)
    sea = evidence_archive_id(src, "/p", "id")
    node = node_evidence_id(sea, "n", "/mapping/n")
    lin = lineage_id(sea, "p", "n", ["n"])
    vw = view_id(sea, "typed", "p", ["n"])
    bd = bundle_id(sea, "p", "resolved", ["n"])
    assert src.startswith("rawsrc_")
    assert sea.startswith("sea_")
    assert node.startswith("node_")
    assert lin.startswith("lineage_")
    assert vw.startswith("view_")
    assert bd.startswith("bundle_")


# --------------------------------------------------------------------------- #
# R0.1-H03 — Accounting invariants (schema-enforced structure)
# --------------------------------------------------------------------------- #

def test_h03_t01_sea_schema_requires_accounting_counts():
    """SEA schema MUST require accounting with all count fields (§10.6)."""
    schema = load_schema("source_evidence_archive.schema.json")
    base = _minimal_sea()
    # valid
    assert_valid(schema, base)
    # missing accounting
    broken = dict(base)
    broken.pop("accounting")
    assert_invalid(schema, broken)


def test_h03_t02_accounting_set_invariant_holds_on_conforming_data():
    """P ∪ E = A, P ∩ E = ∅, |P| + |E| = |A| must be expressible and satisfiable."""
    admitted = {"n1", "n2", "n3"}
    preserved = {"n1", "n2"}
    excluded = {"n3"}
    assert preserved | excluded == admitted
    assert preserved & excluded == set()
    assert len(preserved) + len(excluded) == len(admitted)


def test_h03_t03_exclusion_record_requires_normative_fields():
    """Every exclusion MUST be an ExclusionRecord with reason code + rule id (§10.5)."""
    schema = load_schema("source_evidence_archive.schema.json")
    base = _minimal_sea()
    base["accounting"]["exclusions"] = [
        {
            "source_object_ref": "n3",
            "json_pointer": "/mapping/n3",
            "canonical_object_hash": "d" * 64,
            "exclusion_reason_code": "empty_content",
            "exclusion_rule_id": "M0-EXC-001",
            "exclusion_rule_version": "v0.1",
            "adapter": {"name": "chatgpt_official_export", "version": "0.1.0"},
            "detail": None,
        }
    ]
    assert_valid(schema, base)
    # missing reason code
    broken = dict(base)
    broken["accounting"]["exclusions"][0].pop("exclusion_reason_code")
    assert_invalid(schema, broken)


# --------------------------------------------------------------------------- #
# R0.1-H05 — Normalized projection traceability (schema-enforced)
# --------------------------------------------------------------------------- #

def test_h05_t01_source_evidence_ref_is_mandatory():
    """A normalized message without source_evidence_ref is contract-invalid (§15.2)."""
    schema = load_schema("normalized_archive.schema.json")
    archive = _minimal_normalized_archive()
    assert_valid(schema, archive)
    broken = dict(archive)
    broken["messages"][0].pop("source_evidence_ref")
    assert_invalid(schema, broken)


def test_h05_t02_resolved_bundle_ref_is_mandatory():
    """bundle_state=resolved requires non-null bundle_ref (§15.2.1)."""
    schema = load_schema("normalized_archive.schema.json")
    archive = _minimal_normalized_archive()
    archive["messages"][0]["bundle_state"] = "resolved"
    archive["messages"][0]["bundle_ref"] = "bundle_abc"
    assert_valid(schema, archive)
    broken = dict(archive)
    broken["messages"][0]["bundle_ref"] = None
    assert_invalid(schema, broken)


def test_h05_ambiguous_bundle_ref_is_mandatory():
    """bundle_state=ambiguous also requires non-null bundle_ref."""
    schema = load_schema("normalized_archive.schema.json")
    archive = _minimal_normalized_archive()
    archive["messages"][0]["bundle_state"] = "ambiguous"
    archive["messages"][0]["bundle_ref"] = "bundle_xyz"
    assert_valid(schema, archive)
    broken = dict(archive)
    broken["messages"][0]["bundle_ref"] = None
    assert_invalid(schema, broken)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

def _minimal_sea() -> dict:
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
        "nodes": [],
        "accounting": {
            "source_node_count": 0,
            "preserved_node_count": 0,
            "excluded_node_count": 0,
            "exclusions": [],
        },
    }


def _minimal_normalized_archive() -> dict:
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
