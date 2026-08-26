"""R0.1-FREEZE-FIX closure tests (FF-01..FF-04).

Reference implementations here are contract-conformance primitives only; they
are NOT the production ChatGPT adapter or lineage resolver.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[2]


def load_schema(name: str) -> dict:
    return json.loads((REPO / "schemas" / name).read_text())


def assert_valid(schema: dict, instance: dict) -> None:
    jsonschema.Draft202012Validator(schema).validate(instance)


def assert_invalid(schema: dict, instance: dict) -> None:
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(instance))
    assert errors, "expected instance to be rejected by schema"


# --------------------------------------------------------------------------- #
# Reference: admission profile (contract §4.2.1)
# --------------------------------------------------------------------------- #

def admission_set(mapping: dict) -> set[str]:
    """Every key/value entry in source_native.mapping, exactly once."""
    return set(mapping.keys())


# --------------------------------------------------------------------------- #
# Reference: lineage resolution (contract §11.3-11.5)
# --------------------------------------------------------------------------- #

def resolve_lineage(mapping: dict, current_node: str | None) -> tuple[str, list[str]]:
    """Return (resolution_status, ordered refs).

    Frozen ordering (contract §11 / AF-06):

    - resolved: node_refs = root → current (conversational forward order);
    - invalid_*: visited_node_refs = current → root (traversal order).
    """
    if current_node is None or current_node == "":
        return "invalid_missing_current_node", []
    if current_node not in mapping:
        return "invalid_current_node_not_in_mapping", [current_node]
    visited: list[str] = []
    node_id = current_node
    while True:
        if node_id in visited:
            return "invalid_cycle", visited + [node_id]
        visited.append(node_id)
        node = mapping[node_id]
        parent = (node or {}).get("parent")
        if parent == node_id:
            return "invalid_self_parent", visited + [node_id]
        if parent is None:
            return "resolved", list(reversed(visited))
        if parent not in mapping:
            return "invalid_missing_parent", visited + [parent]
        node_id = parent


# --------------------------------------------------------------------------- #
# FF-01 — Admission profile
# --------------------------------------------------------------------------- #

def test_ff01_t01_admission_set_is_every_mapping_entry_exactly_once():
    mapping = {"n1": {}, "n2": {}, "n3": {}}
    assert admission_set(mapping) == {"n1", "n2", "n3"}
    assert len(admission_set(mapping)) == 3


def test_ff01_t02_null_unknown_alternate_empty_entries_are_admitted():
    mapping = {
        "root": {"message": None},
        "unknown_ct": {"message": {"content": {"content_type": "weird_thing"}}},
        "alt": {"message": {"content": {"content_type": "text"}}},
        "empty": {"message": {"content": {"content_type": "text", "parts": []}}},
    }
    admitted = admission_set(mapping)
    assert admitted == {"root", "unknown_ct", "alt", "empty"}
    assert len(admitted) == 4


# --------------------------------------------------------------------------- #
# FF-02 — Lineage failure semantics
# --------------------------------------------------------------------------- #

def test_ff02_t01_missing_current_node_produces_invalid_status():
    mapping = {"n1": {"parent": None}}
    status, _ = resolve_lineage(mapping, None)
    assert status == "invalid_missing_current_node"


def test_ff02_t02_current_node_outside_mapping_produces_invalid_status():
    mapping = {"n1": {"parent": None}}
    status, refs = resolve_lineage(mapping, "n999")
    assert status == "invalid_current_node_not_in_mapping"
    assert refs == ["n999"]


def test_ff02_t03_missing_parent_produces_invalid_status():
    mapping = {"n2": {"parent": "ghost"}}
    status, refs = resolve_lineage(mapping, "n2")
    assert status == "invalid_missing_parent"
    assert refs == ["n2", "ghost"]


def test_ff02_t04_self_parent_and_cycle_never_resolve():
    self_parent = {"n1": {"parent": "n1"}}
    status, _ = resolve_lineage(self_parent, "n1")
    assert status == "invalid_self_parent"

    cycle = {"a": {"parent": "b"}, "b": {"parent": "a"}}
    status, _ = resolve_lineage(cycle, "a")
    assert status == "invalid_cycle"


def test_ff02_resolved_lineage_terminates_at_root():
    mapping = {"n3": {"parent": "n2"}, "n2": {"parent": "n1"}, "n1": {"parent": None}}
    status, refs = resolve_lineage(mapping, "n3")
    assert status == "resolved"
    # Frozen: node_refs = root → current
    assert refs == ["n1", "n2", "n3"]


def test_ff02_missing_current_node_sea_valid_and_invalid_status():
    """A conforming SEA with missing current_node MUST validate AND resolve to invalid_missing_current_node."""
    sea_schema = load_schema("source_evidence_archive.schema.json")
    sea = _sea(_node())
    sea["source_native"]["current_node"] = None  # missing/unusable selector
    assert_valid(sea_schema, sea)  # evidence preserved, not rejected by SEA schema
    status, _ = resolve_lineage({}, sea["source_native"]["current_node"])
    assert status == "invalid_missing_current_node"


# --------------------------------------------------------------------------- #
# FF-03 — Normalized schema 0.3.0 enforcement
# --------------------------------------------------------------------------- #

def test_ff03_t01_normalized_schema_const_is_0_3_0():
    schema = load_schema("normalized_archive.schema.json")
    assert schema["properties"]["schema_version"]["const"] == "0.3.0"


def test_ff03_t02_normalized_schema_machine_enforces_traceability_conditionals():
    schema = load_schema("normalized_archive.schema.json")
    # 0.2.x is rejected by const
    broken_version = _normalized()
    broken_version["schema_version"] = "0.2.0"
    assert_invalid(schema, broken_version)
    # missing archive-level SEA ref is rejected
    missing_ref = _normalized()
    missing_ref.pop("source_evidence_archive_ref")
    assert_invalid(schema, missing_ref)


def test_ff03_t03_resolved_bundle_requires_bundle_ref_present():
    """bundle_state=resolved with bundle_ref ABSENT (not merely null) is rejected."""
    schema = load_schema("normalized_archive.schema.json")
    archive = _normalized()
    archive["messages"][0]["bundle_state"] = "resolved"
    archive["messages"][0].pop("bundle_ref")
    assert_invalid(schema, archive)


def test_ff03_t04_resolved_lineage_requires_lineage_ref_present():
    """lineage_state=resolved with lineage_ref ABSENT is rejected."""
    schema = load_schema("normalized_archive.schema.json")
    archive = _normalized()
    archive["messages"][0]["lineage_state"] = "resolved"
    archive["messages"][0].pop("lineage_ref")
    assert_invalid(schema, archive)


# --------------------------------------------------------------------------- #
# FF-04 — SEA node identifier nomenclature
# --------------------------------------------------------------------------- #

def test_ff04_t01_sea_node_forbids_bare_node_id():
    schema = load_schema("source_evidence_archive.schema.json")
    node = _node()
    # bare "node_id" field is forbidden by the "not" constraint
    node["node_id"] = "ambiguous"
    sea = _sea(node)
    assert_invalid(schema, sea)


def test_ff04_t02_sea_node_requires_source_node_id_and_node_evidence_id():
    schema = load_schema("source_evidence_archive.schema.json")
    sea = _sea(_node())
    assert_valid(schema, sea)
    broken = _sea(_node())
    broken["nodes"][0].pop("source_node_id")
    assert_invalid(schema, broken)
    broken2 = _sea(_node())
    broken2["nodes"][0].pop("node_evidence_id")
    assert_invalid(schema, broken2)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

def _node() -> dict:
    return {
        "source_node_id": "n2",
        "node_evidence_id": "node_" + "b" * 64,
        "source_payload": {"message": None},
        "provenance": {
            "source_archive_ref": "rawsrc_" + "f" * 64,
            "source_sha256": "a" * 64,
            "json_pointer": "/mapping/n2",
            "source_node_id": "n2",
            "canonical_node_hash": "c" * 64,
        },
    }


def _sea(node: dict) -> dict:
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
        "nodes": [node],
        "accounting": {
            "source_node_count": 1,
            "preserved_node_count": 1,
            "excluded_node_count": 0,
            "exclusions": [],
        },
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
