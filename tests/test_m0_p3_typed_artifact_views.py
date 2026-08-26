"""M0-P3 typed-artifact views sabotage tests (contract §13.1)."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import jsonschema
import pytest

from persona_extractor.archive.adapters.chatgpt_evidence import build_chatgpt_source_evidence
from persona_extractor.archive.evidence.ids import artifact_id
from persona_extractor.archive.evidence.typed_artifacts import (
    ARTIFACT_PROFILE,
    build_chatgpt_typed_artifacts,
)

REPO = Path(__file__).resolve().parents[1]


def _schema() -> dict:
    return json.loads((REPO / "schemas" / "typed_artifact_view.schema.json").read_text())


def _node(sid: str, message: dict | None, projection: dict | None = None) -> dict:
    node: dict = {"source_node_id": sid, "source_payload": {"message": message}}
    if projection is not None:
        node["structural_projection"] = projection
    return node


def _content(content_type: str, parts: list | None = None) -> dict:
    c: dict = {"content_type": content_type}
    if parts is not None:
        c["parts"] = parts
    return c


def _sea(nodes: list[dict]) -> dict:
    return {"evidence_archive_id": "sea_" + "a" * 64, "nodes": nodes}


def _multimodal_fixture() -> dict:
    """The four-part multimodal fixture that kills node-vs-part ambiguity."""
    return {
        "content_type": "multimodal_text",
        "parts": [
            "hello",
            {"content_type": "audio_transcription", "direction": "out", "text": "hi"},
            {"content_type": "image_asset_pointer", "asset_pointer": "file-service://x"},
            {"content_type": "future_magic_type", "foo": 1},
        ],
    }


# --------------------------------------------------------------------------- #
# Authority + classification
# --------------------------------------------------------------------------- #

def test_s01_classification_reads_source_payload_not_projection():
    node = _node("n1", {"content": _content("text", parts=["hi"])}, projection={"content_type": "thoughts"})
    arts = build_chatgpt_typed_artifacts(_sea([node]))
    assert len(arts) == 1
    assert arts[0]["artifact_class"] == "visible_text"
    assert arts[0]["source_content_type"] == "text"


def test_s02_thoughts_produces_one_exported_decision_trace():
    node = _node("n1", {"content": _content("thoughts")})
    arts = build_chatgpt_typed_artifacts(_sea([node]))
    assert len(arts) == 1
    assert arts[0]["artifact_class"] == "exported_decision_trace"
    assert arts[0]["source_artifact_pointer"] == "/message/content"


def test_s03_reasoning_recap_produces_one_reasoning_execution_metadata():
    node = _node("n1", {"content": _content("reasoning_recap")})
    arts = build_chatgpt_typed_artifacts(_sea([node]))
    assert len(arts) == 1
    assert arts[0]["artifact_class"] == "reasoning_execution_metadata"


def test_s04_text_produces_one_visible_text():
    node = _node("n1", {"content": _content("text")})
    arts = build_chatgpt_typed_artifacts(_sea([node]))
    assert len(arts) == 1
    assert arts[0]["artifact_class"] == "visible_text"


def test_s05_multimodal_container_produces_no_container_artifact():
    node = _node("n1", {"content": _multimodal_fixture()})
    arts = build_chatgpt_typed_artifacts(_sea([node]))
    # 4 leaf parts, no 5th container artifact
    assert len(arts) == 4


def test_s06_multimodal_n_parts_produce_n_artifacts():
    node = _node("n1", {"content": _multimodal_fixture()})
    arts = build_chatgpt_typed_artifacts(_sea([node]))
    assert len(arts) == 4


def test_s07_audio_part_classified_audio_transcription():
    arts = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": _multimodal_fixture()})]))
    audio = [a for a in arts if a["source_artifact_pointer"] == "/message/content/parts/1"]
    assert len(audio) == 1
    assert audio[0]["artifact_class"] == "audio_transcription"
    assert audio[0]["source_content_type"] == "audio_transcription"


def test_s08_image_part_classified_image_asset_pointer():
    arts = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": _multimodal_fixture()})]))
    image = [a for a in arts if a["source_artifact_pointer"] == "/message/content/parts/2"]
    assert len(image) == 1
    assert image[0]["artifact_class"] == "image_asset_pointer"


def test_s09_plain_string_part_is_visible_text_with_exact_payload():
    arts = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": _multimodal_fixture()})]))
    s = [a for a in arts if a["source_artifact_pointer"] == "/message/content/parts/0"]
    assert len(s) == 1
    assert s[0]["artifact_class"] == "visible_text"
    assert s[0]["source_content_type"] == "multimodal_text"
    assert s[0]["payload"] == "hello"


def test_s10_unknown_top_level_content_type_is_not_dropped():
    node = _node("n1", {"content": _content("weird_unknown_type")})
    arts = build_chatgpt_typed_artifacts(_sea([node]))
    assert len(arts) == 1
    assert arts[0]["artifact_class"] == "unknown_typed_artifact"


def test_s11_unknown_multimodal_part_is_not_dropped():
    arts = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": _multimodal_fixture()})]))
    unknown = [a for a in arts if a["source_artifact_pointer"] == "/message/content/parts/3"]
    assert len(unknown) == 1
    assert unknown[0]["artifact_class"] == "unknown_typed_artifact"
    assert unknown[0]["source_content_type"] == "future_magic_type"


def test_s12_empty_text_payload_still_produces_artifact():
    node = _node("n1", {"content": _content("text", parts=[""])})
    arts = build_chatgpt_typed_artifacts(_sea([node]))
    assert len(arts) == 1


def test_s13_payload_equals_exact_value_at_pointer():
    content = _multimodal_fixture()
    arts = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": content})]))
    for a in arts:
        idx = int(a["source_artifact_pointer"].rsplit("/", 1)[1])
        assert a["payload"] == content["parts"][idx]


def test_s14_no_stringification_or_flattening():
    content = _multimodal_fixture()
    arts = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": content})]))
    audio = [a for a in arts if a["source_artifact_pointer"] == "/message/content/parts/1"][0]
    assert audio["payload"] == {"content_type": "audio_transcription", "direction": "out", "text": "hi"}


def test_s15_identical_parts_at_different_indices_have_different_ids():
    content = _content("multimodal_text", parts=["same", "same"])
    arts = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": content})]))
    assert len(arts) == 2
    assert arts[0]["artifact_id"] != arts[1]["artifact_id"]


def test_s16_same_source_same_id_across_runs():
    content = _multimodal_fixture()
    a1 = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": content})]))
    a2 = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": content})]))
    assert [x["artifact_id"] for x in a1] == [x["artifact_id"] for x in a2]


def test_s17_different_profile_different_id():
    content = _content("text")
    sea = _sea([_node("n1", {"content": content})])
    a1 = build_chatgpt_typed_artifacts(sea)[0]
    a2 = artifact_id(sea["evidence_archive_id"], "n1", "/message/content", "other-profile-v9.9")
    assert a1["artifact_id"] != a2


def test_s18_shuffled_nodes_same_artifact_order():
    c1 = _content("text")
    c2 = _content("thoughts")
    sea1 = _sea([_node("a", {"content": c1}), _node("b", {"content": c2})])
    sea2 = _sea([_node("b", {"content": c2}), _node("a", {"content": c1})])
    a1 = build_chatgpt_typed_artifacts(sea1)
    a2 = build_chatgpt_typed_artifacts(sea2)
    assert [x["artifact_id"] for x in a1] == [x["artifact_id"] for x in a2]


def test_s19_builder_never_mutates_sea():
    sea = _sea([_node("n1", {"content": _multimodal_fixture()})])
    before = copy.deepcopy(sea)
    build_chatgpt_typed_artifacts(sea)
    assert sea == before


def test_s20_message_null_produces_zero_artifacts():
    sea = _sea([_node("root", None)])
    assert build_chatgpt_typed_artifacts(sea) == []


def test_s21_missing_content_type_produces_no_invented_type():
    node = _node("n1", {"content": {"no_content_type_here": True}})
    assert build_chatgpt_typed_artifacts(_sea([node])) == []


def test_s22_malformed_multimodal_parts_produces_one_unknown_over_container():
    content = {"content_type": "multimodal_text", "parts": "not-a-list"}
    arts = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": content})]))
    assert len(arts) == 1
    assert arts[0]["artifact_class"] == "unknown_typed_artifact"
    assert arts[0]["payload"] == content


def test_s23_all_artifacts_have_observed_evidence_class():
    arts = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": _multimodal_fixture()})]))
    for a in arts:
        assert a["evidence_class"] == "observed_export_artifact"


def test_s24_no_interpretation_fields():
    arts = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": _multimodal_fixture()})]))
    forbidden = {"meaning", "persona_truth", "identity_change", "relationship_delta", "causal_claim"}
    for a in arts:
        assert forbidden.isdisjoint(a.keys())


def test_s25_every_artifact_schema_valid():
    arts = build_chatgpt_typed_artifacts(_sea([_node("n1", {"content": _multimodal_fixture()})]))
    schema = _schema()
    for a in arts:
        jsonschema.Draft202012Validator(schema).validate(a)


def test_s26_artifact_id_recomputes_from_frozen_inputs():
    sea = _sea([_node("n1", {"content": _multimodal_fixture()})])
    arts = build_chatgpt_typed_artifacts(sea)
    for a in arts:
        expected = artifact_id(
            a["evidence_archive_id"],
            a["source_node_ref"],
            a["source_artifact_pointer"],
            a["artifact_profile"],
        )
        assert a["artifact_id"] == expected


# --------------------------------------------------------------------------- #
# Golden private acceptance (only when GOLDEN_MIRA_FIXTURE_PATH is set)
# --------------------------------------------------------------------------- #

def test_golden_private_acceptance_4060():
    path = os.environ.get("GOLDEN_MIRA_FIXTURE_PATH")
    if not path:
        pytest.skip("GOLDEN_MIRA_FIXTURE_PATH not set")
    raw = Path(path).read_bytes()
    manifest, sea = build_chatgpt_source_evidence(raw, None, {"path": path, "uri": None})
    assert manifest["source_sha256"] == "564ef9b1aa5457b56751f550d80b0eaa24e144f8d08bd2f6b8c0ff870b8e9420"
    assert sea["source_native"]["conversation_id"] == "6a754a53-82c4-83e8-b9a2-610154053181"

    artifacts = build_chatgpt_typed_artifacts(sea)
    assert len(artifacts) == 4060

    from collections import Counter

    counts = Counter(a["artifact_class"] for a in artifacts)
    assert counts["visible_text"] == 1688
    assert counts["audio_transcription"] == 1361
    assert counts["image_asset_pointer"] == 2
    assert counts["exported_decision_trace"] == 154
    assert counts["reasoning_execution_metadata"] == 855
    assert counts["unknown_typed_artifact"] == 0

    assert len({a["artifact_id"] for a in artifacts}) == 4060
