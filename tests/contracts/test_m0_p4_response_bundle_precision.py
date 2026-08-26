"""M0-P4-FF-01 Bundle Reference Semantics precision tests (contract §14.6).

Proves the reference namespaces are machine-enforced in the schema, and that the
contract text unambiguously freezes canonical-lineage authority + namespace rules.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[2]


def load_schema() -> dict:
    return json.loads((REPO / "schemas" / "response_bundle_view.schema.json").read_text())


def assert_valid(schema: dict, instance: dict) -> None:
    jsonschema.Draft202012Validator(schema).validate(instance)


def assert_invalid(schema: dict, instance: dict) -> None:
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(instance))
    assert errors, "expected instance to be rejected by schema"


def _minimal_bundle() -> dict:
    return {
        "schema_version": "0.1.0",
        "bundle_id": "bundle_" + "d" * 64,
        "bundle_state": "resolved",
        "evidence_archive_id": "sea_" + "a" * 64,
        "resolution_profile": "chatgpt-official-export-response-bundle-v0.1",
        "trigger_refs": ["u1"],
        "member_node_refs": ["a1"],
        "artifact_refs": ["artifact_" + "e" * 64],
        "visible_response_refs": ["a1"],
        "provenance_refs": ["node_" + "f" * 64, "node_" + "e" * 64],
    }


# --------------------------------------------------------------------------- #
# Schema enforcement (C01-C06)
# --------------------------------------------------------------------------- #

def test_c00_minimal_bundle_is_valid():
    """Baseline: the shared fixture MUST itself be schema-valid, so the
    negative tests below fail only for the field they intend to mutate."""
    schema = load_schema()
    assert_valid(schema, _minimal_bundle())


def test_c01_missing_artifact_refs_is_rejected():
    schema = load_schema()
    b = _minimal_bundle()
    b.pop("artifact_refs")
    assert_invalid(schema, b)


def test_c02_missing_visible_response_refs_is_rejected():
    schema = load_schema()
    b = _minimal_bundle()
    b.pop("visible_response_refs")
    assert_invalid(schema, b)


def test_c03_artifact_refs_requires_artifact_id_namespace():
    schema = load_schema()
    b = _minimal_bundle()
    b["artifact_refs"] = ["a1"]  # source-node-id, not artifact_<64hex>
    assert_invalid(schema, b)


def test_c04_provenance_refs_requires_node_evidence_id_namespace():
    schema = load_schema()
    b = _minimal_bundle()
    b["provenance_refs"] = ["a1"]  # source-node-id, not node_<64hex>
    assert_invalid(schema, b)


def test_c05_resolved_with_zero_visible_response_refs_is_rejected():
    schema = load_schema()
    b = _minimal_bundle()
    b["visible_response_refs"] = []
    assert_invalid(schema, b)


def test_c06_resolved_with_multiple_visible_response_refs_is_rejected():
    schema = load_schema()
    b = _minimal_bundle()
    b["visible_response_refs"] = ["a1", "a2"]
    assert_invalid(schema, b)


# --------------------------------------------------------------------------- #
# Contract text conformance (C07-C12)
# --------------------------------------------------------------------------- #

def _contract() -> str:
    return (REPO / "docs" / "M0_EVIDENCE_SUBSTRATE_CONTRACT.md").read_text()


def test_c07_canonical_lineage_is_exclusive_membership_authority():
    c = _contract()
    assert "EXCLUSIVE membership domain and ordering authority" in c


def test_c08_sea_is_dereference_support_only():
    c = _contract()
    assert "is a dereference input only" in c


def test_c09_artifact_refs_is_p3_artifact_id():
    c = _contract()
    assert "artifact_refs          = TypedArtifactView.artifact_id[]" in c


def test_c10_visible_response_refs_is_terminal_source_node_id():
    c = _contract()
    assert "visible_response_refs  = SEA source_node_id[]" in c
    assert "NOT artifact-level" in c


def test_c11_trigger_refs_are_context_only():
    c = _contract()
    assert "NOT bundle members" in c
    assert "NOT determine atomicity" in c


def test_c12_provenance_refs_is_node_evidence_id():
    c = _contract()
    assert "provenance_refs        = SEA node_evidence_id[]" in c
