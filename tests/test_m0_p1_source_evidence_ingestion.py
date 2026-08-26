"""M0-P1 source-evidence ingestion sabotage tests.

The standard here is: the correct implementation can pass, but a broken
implementation MUST NOT sneak through. Each S0x test pins one escape hatch shut.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from persona_extractor.archive.adapters.chatgpt_evidence import (
    build_chatgpt_source_evidence,
)
from persona_extractor.archive.evidence.canonical_json import (
    jcs_hash,
    parse_json_strict,
    sha256_hex,
)
from persona_extractor.archive.evidence.sea import rfc6901_escape

REPO = Path(__file__).resolve().parents[1]


def _manifest_schema() -> dict:
    return json.loads((REPO / "schemas" / "raw_source_manifest.schema.json").read_text())


def _sea_schema() -> dict:
    return json.loads((REPO / "schemas" / "source_evidence_archive.schema.json").read_text())


def _node(message: dict | None, parent: str | None = None) -> dict:
    return {"parent": parent, "message": message}


def _synthetic_conversation() -> dict:
    """A single-conversation export exercising every structural case."""
    return {
        "conversation_id": "conv_1",
        "current_node": "n7",
        "title": "Hi Mira",
        "mapping": {
            "root": _node(None, None),  # message = null
            "n1": _node({"id": "m1", "author": {"role": "user"}, "create_time": 1.0, "content": {"content_type": "text", "parts": ["hi"]}}, "root"),
            "n2": _node({"id": "m2", "author": {"role": "assistant"}, "create_time": 2.0, "content": {"content_type": "thoughts", "thoughts": []}}, "n1"),
            "n3": _node({"id": "m3", "author": {"role": "assistant"}, "create_time": 3.0, "content": {"content_type": "reasoning_recap", "content": "思考了 5s"}}, "n2"),
            "n4": _node({"id": "m4", "author": {"role": "assistant"}, "create_time": 4.0, "content": {"content_type": "text", "parts": ["hello"]}}, "n3"),
            "n5": _node({"id": "m5", "author": {"role": "assistant"}, "create_time": 5.0, "content": {"content_type": "weird_unknown_type", "parts": ["?"]}}, "n4"),
            "n6": _node({"id": "m6", "author": {"role": "assistant"}, "create_time": 6.0, "content": {"content_type": "text", "parts": []}}, "n5"),  # empty text
            "n7": _node({"id": "m7", "author": {"role": "assistant"}, "create_time": 7.0, "content": {"content_type": "multimodal_text", "parts": [{"content_type": "audio_transcription", "direction": "out", "text": "voice"}]}}, "n6"),
        },
    }


def _build(conversation: dict | None = None) -> tuple[dict, dict]:
    conv = conversation if conversation is not None else _synthetic_conversation()
    raw = json.dumps(conv, ensure_ascii=False).encode("utf-8")
    return build_chatgpt_source_evidence(raw, None, {"path": "synthetic.json", "uri": None})


# --------------------------------------------------------------------------- #
# Admission / conservation sabotage
# --------------------------------------------------------------------------- #

def test_s01_message_null_node_is_preserved():
    _, sea = _build()
    ids = {n["source_node_id"] for n in sea["nodes"]}
    assert "root" in ids


def test_s02_empty_text_node_is_preserved():
    _, sea = _build()
    ids = {n["source_node_id"] for n in sea["nodes"]}
    assert "n6" in ids


def test_s03_unknown_content_type_is_preserved():
    _, sea = _build()
    ids = {n["source_node_id"] for n in sea["nodes"]}
    assert "n5" in ids


def test_s04_mapping_size_equals_sea_node_count():
    conv = _synthetic_conversation()
    _, sea = _build(conv)
    assert len(conv["mapping"]) == len(sea["nodes"])
    assert sea["accounting"]["source_node_count"] == len(conv["mapping"])
    assert sea["accounting"]["preserved_node_count"] == len(conv["mapping"])
    assert sea["accounting"]["excluded_node_count"] == 0


def test_s05_no_duplicate_node_evidence_id():
    _, sea = _build()
    ids = [n["node_evidence_id"] for n in sea["nodes"]]
    assert len(ids) == len(set(ids))


# --------------------------------------------------------------------------- #
# Determinism sabotage
# --------------------------------------------------------------------------- #

def test_s06_node_ids_are_deterministic_across_runs():
    _, sea1 = _build()
    _, sea2 = _build()
    ids1 = [n["node_evidence_id"] for n in sea1["nodes"]]
    ids2 = [n["node_evidence_id"] for n in sea2["nodes"]]
    assert ids1 == ids2
    assert sea1["evidence_archive_id"] == sea2["evidence_archive_id"]


def test_s06b_manifest_id_is_deterministic_and_location_independent():
    conv = _synthetic_conversation()
    raw = json.dumps(conv).encode("utf-8")
    m1, _ = build_chatgpt_source_evidence(raw, None, {"path": "/a/b.json", "uri": None})
    m2, _ = build_chatgpt_source_evidence(raw, None, {"path": "/c/d.json", "uri": None})
    assert m1["source_archive_id"] == m2["source_archive_id"]


# --------------------------------------------------------------------------- #
# Payload fidelity sabotage
# --------------------------------------------------------------------------- #

def test_s07_source_payload_is_not_cropped():
    conv = _synthetic_conversation()
    _, sea = _build(conv)
    by_id = {n["source_node_id"]: n for n in sea["nodes"]}
    for source_node_id, source_node in conv["mapping"].items():
        assert by_id[source_node_id]["source_payload"] == source_node


def test_s08_canonical_node_hash_is_over_full_payload():
    conv = _synthetic_conversation()
    _, sea = _build(conv)
    by_id = {n["source_node_id"]: n for n in sea["nodes"]}
    for source_node_id, source_node in conv["mapping"].items():
        node = by_id[source_node_id]
        assert node["provenance"]["canonical_node_hash"] == jcs_hash(source_node)


# --------------------------------------------------------------------------- #
# Byte-level forensic boundary sabotage
# --------------------------------------------------------------------------- #

def test_s09_source_sha256_tracks_exact_bytes_not_semantic_json():
    conv = _synthetic_conversation()
    raw_compact = json.dumps(conv, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    raw_pretty = json.dumps(conv, ensure_ascii=False, indent=2).encode("utf-8")
    m1, _ = build_chatgpt_source_evidence(raw_compact, None, None)
    m2, _ = build_chatgpt_source_evidence(raw_pretty, None, None)
    assert m1["source_sha256"] == sha256_hex(raw_compact)
    assert m2["source_sha256"] == sha256_hex(raw_pretty)
    assert m1["source_sha256"] != m2["source_sha256"]


def test_s10_duplicate_json_key_is_rejected():
    with pytest.raises(ValueError):
        parse_json_strict(b'{"a": 1, "a": 2}')


@pytest.mark.parametrize("bad", [b'{"x": NaN}', b'{"x": Infinity}', b'{"x": -Infinity}'])
def test_s10bcd_non_standard_constants_are_rejected(bad):
    with pytest.raises(ValueError):
        parse_json_strict(bad)


def test_s10e_non_finite_number_is_rejected():
    with pytest.raises(ValueError):
        parse_json_strict(b'{"x": 1e400}')


def test_s11_json_pointer_applies_rfc6901_escaping():
    assert rfc6901_escape("a/b~c") == "a~1b~0c"


def test_s11b_negative_array_selector_is_rejected():
    raw = json.dumps([_synthetic_conversation()]).encode("utf-8")
    with pytest.raises(IndexError):
        build_chatgpt_source_evidence(raw, -1, None)


def test_s11c_out_of_range_array_selector_is_rejected():
    raw = json.dumps([_synthetic_conversation()]).encode("utf-8")
    with pytest.raises(IndexError):
        build_chatgpt_source_evidence(raw, 5, None)


# --------------------------------------------------------------------------- #
# API-shape sabotage: no caller-provided shrunk admission domain
# --------------------------------------------------------------------------- #

def test_s12_api_does_not_accept_caller_admitted_refs():
    import inspect

    sig = inspect.signature(build_chatgpt_source_evidence)
    params = list(sig.parameters)
    assert "admitted_refs" not in params
    assert "mapping" not in params


def test_h01_source_locator_is_canonicalized_to_path_and_uri():
    """A partial locator must be canonicalized to the schema shape {path, uri}."""
    conv = _synthetic_conversation()
    raw = json.dumps(conv).encode("utf-8")
    manifest, _ = build_chatgpt_source_evidence(raw, None, {"path": "foo.json"})
    assert set(manifest["source_locator"].keys()) == {"path", "uri"}
    assert manifest["source_locator"]["path"] == "foo.json"
    assert manifest["source_locator"]["uri"] is None


# --------------------------------------------------------------------------- #
# Schema conformance
# --------------------------------------------------------------------------- #

def test_manifest_and_sea_are_schema_valid():
    manifest, sea = _build()
    jsonschema.Draft202012Validator(_manifest_schema()).validate(manifest)
    jsonschema.Draft202012Validator(_sea_schema()).validate(sea)


# --------------------------------------------------------------------------- #
# Golden private acceptance (only when GOLDEN_MIRA_FIXTURE_PATH is set)
# --------------------------------------------------------------------------- #

def test_golden_private_acceptance_4059_4059_0():
    import os

    path = os.environ.get("GOLDEN_MIRA_FIXTURE_PATH")
    if not path:
        pytest.skip("GOLDEN_MIRA_FIXTURE_PATH not set")
    raw = Path(path).read_bytes()
    manifest, sea = build_chatgpt_source_evidence(raw, None, {"path": path, "uri": None})
    # identity binding: this MUST be the actual Golden source, not merely a
    # 4059-node file that happens to collide.
    assert manifest["source_sha256"] == "564ef9b1aa5457b56751f550d80b0eaa24e144f8d08bd2f6b8c0ff870b8e9420"
    assert sea["source_native"]["conversation_id"] == "6a754a53-82c4-83e8-b9a2-610154053181"
    assert sea["accounting"]["source_node_count"] == 4059
    assert sea["accounting"]["preserved_node_count"] == 4059
    assert sea["accounting"]["excluded_node_count"] == 0
    assert len(sea["nodes"]) == 4059
