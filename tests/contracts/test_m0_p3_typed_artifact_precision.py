"""M0 P3-FF-01 Typed Artifact Addressability precision tests (contract §13.1).

These tests prove the precision amendment is machine-enforced: the schema MUST
require the three addressability fields, MUST accept arbitrary-JSON payload, and
MUST reject interpretation fields.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[2]


def load_schema() -> dict:
    return json.loads((REPO / "schemas" / "typed_artifact_view.schema.json").read_text())


def assert_valid(schema: dict, instance: dict) -> None:
    jsonschema.Draft202012Validator(schema).validate(instance)


def assert_invalid(schema: dict, instance: dict) -> None:
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(instance))
    assert errors, "expected instance to be rejected by schema"


def _minimal_artifact() -> dict:
    return {
        "schema_version": "0.1.0",
        "artifact_id": "artifact_" + "a" * 64,
        "evidence_archive_id": "sea_" + "b" * 64,
        "source_node_ref": "n1",
        "source_artifact_pointer": "/message/content",
        "artifact_profile": "chatgpt-official-export-typed-artifact-v0.1",
        "source_content_type": "text",
        "artifact_class": "visible_text",
        "evidence_class": "observed_export_artifact",
        "payload": "hello",
    }


def test_c01_missing_evidence_archive_id_is_rejected():
    schema = load_schema()
    a = _minimal_artifact()
    a.pop("evidence_archive_id")
    assert_invalid(schema, a)


def test_c02_missing_source_artifact_pointer_is_rejected():
    schema = load_schema()
    a = _minimal_artifact()
    a.pop("source_artifact_pointer")
    assert_invalid(schema, a)


def test_c03_missing_artifact_profile_is_rejected():
    schema = load_schema()
    a = _minimal_artifact()
    a.pop("artifact_profile")
    assert_invalid(schema, a)


def test_c04_non_frozen_artifact_profile_is_rejected():
    schema = load_schema()
    a = _minimal_artifact()
    a["artifact_profile"] = "some-other-profile-v9.9"
    assert_invalid(schema, a)


def test_c05_plain_string_payload_is_accepted():
    schema = load_schema()
    a = _minimal_artifact()
    a["payload"] = "plain string"
    assert_valid(schema, a)
    a["payload"] = 42
    assert_valid(schema, a)
    a["payload"] = None
    assert_valid(schema, a)
    a["payload"] = ["list", "of", "strings"]
    assert_valid(schema, a)


def test_c06_interpretation_field_is_rejected():
    schema = load_schema()
    for field in ["meaning", "persona_truth", "identity_change", "causal_claim", "relationship_delta"]:
        a = _minimal_artifact()
        a[field] = "not allowed"
        assert_invalid(schema, a)
