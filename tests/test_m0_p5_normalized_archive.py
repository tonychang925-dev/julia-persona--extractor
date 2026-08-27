"""M0-P5 normalized archive projection sabotage tests (contract §15.5).

The standard: P5 is a faithful deterministic projection. A projection that
flattens alternate nodes, stringifies structured content, guesses timestamps,
mixes provenance namespaces, or recomputes bundle association MUST NOT sneak
through.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import jsonschema
import pytest

from persona_extractor.archive.adapters.chatgpt_evidence import build_chatgpt_source_evidence
from persona_extractor.archive.evidence.canonical_json import jcs_hash
from persona_extractor.archive.evidence.ids import normalized_archive_id, normalized_message_id
from persona_extractor.archive.evidence.lineage_views import resolve_chatgpt_topology
from persona_extractor.archive.evidence.normalized_archive import (
    NORMALIZATION_PROFILE,
    NormalizedArchiveInputError,
    build_chatgpt_normalized_archive,
)
from persona_extractor.archive.evidence.response_bundles import build_chatgpt_response_bundles

REPO = Path(__file__).resolve().parents[1]
SEA_ID = "sea_" + "b" * 64
RAW_ARCHIVE_ID = "rawsrc_" + "a" * 64
RESPONSE_BUNDLE_PROFILE = "chatgpt-official-export-response-bundle-v0.1"


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

def _evid(sid: str) -> str:
    return "node_" + ("%064x" % sum(ord(c) for c in sid))


def _content(content_type: str, parts=None, text=None) -> dict:
    c: dict = {"content_type": content_type}
    if parts is not None:
        c["parts"] = parts
    if text is not None:
        c["text"] = text
    return c


def _msg(role, content, create_time=None, mid=None) -> dict:
    m: dict = {"author": {"role": role}, "content": content}
    if create_time is not None:
        m["create_time"] = create_time
    if mid is not None:
        m["id"] = mid
    return m


def _node(sid: str, message, projection=None) -> dict:
    n: dict = {"source_node_id": sid, "node_evidence_id": _evid(sid), "source_payload": {"message": message}}
    if projection is not None:
        n["structural_projection"] = projection
    return n


def _structural(sid: str) -> dict:
    return {"source_node_id": sid, "node_evidence_id": _evid(sid), "source_payload": {"message": None}}


def _manifest(sha: str = "s" * 64, path: str = "/tmp/x.json") -> dict:
    return {
        "source_archive_id": RAW_ARCHIVE_ID,
        "source_type": "chatgpt_official_export",
        "source_sha256": sha,
        "source_locator": {"path": path, "uri": None},
        "ingested_at": None,
    }


def _sea(nodes, conv: str = "conv1", manifest_ref: str = RAW_ARCHIVE_ID) -> dict:
    return {
        "evidence_archive_id": SEA_ID,
        "source_manifest_ref": manifest_ref,
        "source_native": {"conversation_id": conv, "title": "T"},
        "nodes": nodes,
    }


def _canonical(node_refs, sea_id: str = SEA_ID, lineage: str = "lineage_" + "c" * 64) -> dict:
    return {"resolution_status": "resolved", "evidence_archive_id": sea_id, "lineage_id": lineage, "node_refs": node_refs}


def _bundle(members, state: str = "resolved", sea_id: str = SEA_ID, bid: str | None = None) -> dict:
    bid = bid if bid is not None else "bundle_" + ("%064x" % (sum(ord(c) for c in "".join(members))))
    return {
        "bundle_id": bid,
        "bundle_state": state,
        "evidence_archive_id": sea_id,
        "resolution_profile": RESPONSE_BUNDLE_PROFILE,
        "member_node_refs": members,
        "trigger_refs": [],
        "artifact_refs": [],
        "visible_response_refs": [],
        "provenance_refs": [],
    }


def _schema() -> dict:
    return json.loads((REPO / "schemas" / "normalized_archive.schema.json").read_text())


def _validate(archive: dict) -> None:
    jsonschema.Draft202012Validator(_schema()).validate(archive)


def _simple() -> tuple[dict, dict, dict, list]:
    """user text -> assistant text, one resolved bundle."""
    nodes = [
        _node("u1", _msg("user", _content("text", parts=["hi"]), mid="msg_u")),
        _node("a1", _msg("assistant", _content("text", parts=["hello"]), mid="msg_a")),
    ]
    sea = _sea(nodes)
    canonical = _canonical(["u1", "a1"])
    bundles = [_bundle(["a1"])]
    return _manifest(), sea, canonical, bundles


# --------------------------------------------------------------------------- #
# S01-S10 — fail closed
# --------------------------------------------------------------------------- #

def test_s01_manifest_sea_source_ref_mismatch_fails():
    manifest, sea, canonical, bundles = _simple()
    sea["source_manifest_ref"] = "rawsrc_" + "z" * 64
    with pytest.raises(NormalizedArchiveInputError):
        build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)


def test_s02_canonical_unresolved_fails():
    manifest, sea, canonical, bundles = _simple()
    canonical["resolution_status"] = "invalid_missing_current_node"
    with pytest.raises(NormalizedArchiveInputError):
        build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)


def test_s03_canonical_sea_mismatch_fails():
    manifest, sea, canonical, bundles = _simple()
    canonical["evidence_archive_id"] = "sea_" + "z" * 64
    with pytest.raises(NormalizedArchiveInputError):
        build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)


def test_s04_canonical_ref_missing_sea_fails():
    manifest, sea, canonical, bundles = _simple()
    canonical["node_refs"] = ["u1", "ghost"]
    with pytest.raises(NormalizedArchiveInputError):
        build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)


def test_s05_duplicate_sea_ref_fails():
    manifest, _, canonical, bundles = _simple()
    node = _node("u1", _msg("user", _content("text", parts=["hi"])))
    sea = _sea([_node("u1", _msg("user", _content("text", parts=["hi"]))), node])
    with pytest.raises(NormalizedArchiveInputError):
        build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)


def test_s06_bundle_sea_mismatch_fails():
    manifest, sea, canonical, bundles = _simple()
    bundles[0]["evidence_archive_id"] = "sea_" + "z" * 64
    with pytest.raises(NormalizedArchiveInputError):
        build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)


def test_s07_wrong_bundle_profile_fails():
    manifest, sea, canonical, bundles = _simple()
    bundles[0]["resolution_profile"] = "some-other-profile"
    with pytest.raises(NormalizedArchiveInputError):
        build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)


def test_s08_overlapping_bundle_members_fail():
    manifest, sea, canonical, _ = _simple()
    bundles = [_bundle(["a1"]), _bundle(["a1"], bid="bundle_" + "e" * 64)]
    with pytest.raises(NormalizedArchiveInputError):
        build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)


def test_s09_bundle_member_non_canonical_fails():
    manifest, sea, canonical, _ = _simple()
    bundles = [_bundle(["alt1"])]  # alt1 is not in canonical node_refs
    with pytest.raises(NormalizedArchiveInputError):
        build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)


def test_s10_assistant_bundle_coverage_not_exact_fails():
    manifest, sea, canonical, _ = _simple()
    bundles: list = []  # assistant a1 has no bundle
    with pytest.raises(NormalizedArchiveInputError):
        build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)


# --------------------------------------------------------------------------- #
# S11-S15 — projection scope + order
# --------------------------------------------------------------------------- #

def test_s11_null_message_omitted():
    manifest = _manifest()
    sea = _sea([_node("u1", _msg("user", _content("text", parts=["hi"]))), _structural("null1"), _node("a1", _msg("assistant", _content("text", parts=["x"])))])
    canonical = _canonical(["u1", "null1", "a1"])
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, [_bundle(["a1"])])
    assert [m["source_evidence_ref"] for m in arc["messages"]] == [_evid("u1"), _evid("a1")]


def test_s12_malformed_non_dict_message_omitted():
    manifest = _manifest()
    broken = {"source_node_id": "broken", "node_evidence_id": _evid("broken"), "source_payload": {"message": "broken"}}
    sea = _sea([_node("a1", _msg("assistant", _content("text", parts=["x"]))), broken])
    canonical = _canonical(["a1", "broken"])
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, [_bundle(["a1"])])
    assert [m["source_evidence_ref"] for m in arc["messages"]] == [_evid("a1")]


def test_s13_alternate_node_omitted():
    manifest = _manifest()
    sea = _sea([_node("u1", _msg("user", _content("text", parts=["hi"]))), _node("a1", _msg("assistant", _content("text", parts=["x"]))), _node("alt1", _msg("assistant", _content("text", parts=["alt"])))])
    canonical = _canonical(["u1", "a1"])  # alt1 not in canonical
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, [_bundle(["a1"])])
    refs = [m["source_evidence_ref"] for m in arc["messages"]]
    assert _evid("alt1") not in refs


def test_s14_canonical_order_preserved():
    manifest = _manifest()
    sea = _sea([
        _node("u1", _msg("user", _content("text", parts=["1"]))),
        _node("a1", _msg("assistant", _content("text", parts=["2"]))),
        _node("u2", _msg("user", _content("text", parts=["3"]))),
        _node("a2", _msg("assistant", _content("text", parts=["4"]))),
    ])
    canonical = _canonical(["u1", "a1", "u2", "a2"])
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, [_bundle(["a1"]), _bundle(["a2"], bid="bundle_" + "e" * 64)])
    assert [m["source_evidence_ref"] for m in arc["messages"]] == [_evid("u1"), _evid("a1"), _evid("u2"), _evid("a2")]


def test_s15_sea_nodes_shuffle_changes_nothing():
    manifest = _manifest()
    nodes = [_node("u1", _msg("user", _content("text", parts=["hi"]))), _node("a1", _msg("assistant", _content("text", parts=["x"])))]
    canonical = _canonical(["u1", "a1"])
    bundles = [_bundle(["a1"])]
    a1 = build_chatgpt_normalized_archive(manifest, _sea(nodes), canonical, bundles)
    a2 = build_chatgpt_normalized_archive(manifest, _sea(list(reversed(nodes))), canonical, bundles)
    assert a1 == a2


# --------------------------------------------------------------------------- #
# S16-S19 — role + participants
# --------------------------------------------------------------------------- #

def test_s16_source_payload_role_wins_over_projection():
    manifest = _manifest()
    node = _node("a1", _msg("assistant", _content("text", parts=["x"])), projection={"role": "user"})
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [_bundle(["a1"])])
    assert arc["messages"][0]["role"] == "assistant"


def test_s17_exact_non_empty_role_passthrough():
    manifest = _manifest()
    node = _node("a1", _msg("developer", _content("text", parts=["x"])))
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [])
    assert arc["messages"][0]["role"] == "developer"


def test_s18_missing_role_is_unknown():
    manifest = _manifest()
    node = _node("a1", {"author": {}, "content": _content("text", parts=["x"])})
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [])
    assert arc["messages"][0]["role"] == "unknown"


def test_s19_role_bucket_participants_deterministic():
    manifest = _manifest()
    sea = _sea([
        _node("u1", _msg("user", _content("text", parts=["1"]))),
        _node("a1", _msg("assistant", _content("text", parts=["2"]))),
        _node("s1", _msg("system", _content("text", parts=["3"]))),
    ])
    arc = build_chatgpt_normalized_archive(manifest, sea, _canonical(["u1", "a1", "s1"]), [_bundle(["a1"])])
    assert arc["participants"] == [
        {"participant_id": "role:user", "role": "user", "display_name": None},
        {"participant_id": "role:assistant", "role": "assistant", "display_name": None},
        {"participant_id": "role:system", "role": "system", "display_name": None},
    ]


# --------------------------------------------------------------------------- #
# S20-S28 — content projection
# --------------------------------------------------------------------------- #

def test_s20_text_string_parts_exact_order():
    manifest = _manifest()
    node = _node("a1", _msg("assistant", _content("text", parts=["a", "b", "c"])))
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [_bundle(["a1"])])
    assert arc["messages"][0]["content"] == "a\nb\nc"


def test_s21_no_strip_of_text_parts():
    manifest = _manifest()
    node = _node("a1", _msg("assistant", _content("text", parts=["  hi  ", "", "  "])))
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [_bundle(["a1"])])
    assert arc["messages"][0]["content"] == "  hi  \n\n  "


def test_s22_non_string_text_parts_not_stringified():
    manifest = _manifest()
    node = _node("a1", _msg("assistant", _content("text", parts=["ok", 123, {"x": 1}, None])))
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [_bundle(["a1"])])
    assert arc["messages"][0]["content"] == "ok"


def test_s23_multimodal_plain_string_preserved():
    manifest = _manifest()
    node = _node("a1", _msg("assistant", _content("multimodal_text", parts=["hello", "world"])))
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [_bundle(["a1"])])
    assert arc["messages"][0]["content"] == "hello\nworld"


def test_s24_audio_transcription_text_preserved():
    manifest = _manifest()
    node = _node("a1", _msg("assistant", _content("multimodal_text", parts=[{"content_type": "audio_transcription", "text": "hi there", "direction": "out"}])))
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [_bundle(["a1"])])
    assert arc["messages"][0]["content"] == "hi there"


def test_s25_image_and_unknown_omitted_from_content():
    manifest = _manifest()
    node = _node("a1", _msg("assistant", _content("multimodal_text", parts=["keep", {"content_type": "image_asset_pointer", "asset_pointer": "x"}, {"content_type": "future_type", "foo": 1}])))
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [_bundle(["a1"])])
    assert arc["messages"][0]["content"] == "keep"


def test_s26_thoughts_projects_to_empty():
    manifest = _manifest()
    node = _node("a1", _msg("assistant", _content("thoughts", parts=["secret reasoning"])))
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [_bundle(["a1"])])
    assert arc["messages"][0]["content"] == ""


def test_s27_reasoning_recap_projects_to_empty():
    manifest = _manifest()
    node = _node("a1", _msg("assistant", _content("reasoning_recap", parts=["recap"])))
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [_bundle(["a1"])])
    assert arc["messages"][0]["content"] == ""


def test_s28_missing_or_unknown_content_type_projects_to_empty():
    manifest = _manifest()
    nodes = [
        _node("a1", _msg("assistant", _content("weird_type", parts=["x"]))),
        _node("a2", _msg("assistant", {"author": {"role": "assistant"}})),
    ]
    arc = build_chatgpt_normalized_archive(manifest, _sea(nodes), _canonical(["a1", "a2"]), [_bundle(["a1"]), _bundle(["a2"], state="ambiguous", bid="bundle_" + "e" * 64)])
    assert arc["messages"][0]["content"] == ""
    assert arc["messages"][1]["content"] == ""


# --------------------------------------------------------------------------- #
# S29-S30 — timestamp
# --------------------------------------------------------------------------- #

def test_s29_finite_epoch_projects_to_frozen_rfc3339():
    manifest = _manifest()
    node = _node("a1", _msg("assistant", _content("text", parts=["x"]), create_time=1700000000.5))
    arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a1"]), [_bundle(["a1"])])
    assert arc["messages"][0]["timestamp"] == "2023-11-14T22:13:20.500000Z"


def test_s30_malformed_timestamp_projects_to_null():
    manifest = _manifest()
    cases = [None, "not-a-number", True, float("nan"), float("inf")]
    for i, create_time in enumerate(cases):
        node = _node("a%d" % i, _msg("assistant", _content("text", parts=["x"]), create_time=create_time))
        arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a%d" % i]), [_bundle(["a%d" % i], bid="bundle_" + ("%064x" % i))])
        assert arc["messages"][0]["timestamp"] is None


# --------------------------------------------------------------------------- #
# S31-S32 — traceability refs
# --------------------------------------------------------------------------- #

def test_s31_source_evidence_ref_is_node_evidence_id():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    assert arc["messages"][1]["source_evidence_ref"] == _evid("a1")


def test_s32_lineage_ref_is_canonical_lineage_id():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    assert arc["messages"][0]["lineage_ref"] == "lineage_" + "c" * 64
    assert arc["messages"][0]["lineage_state"] == "resolved"


# --------------------------------------------------------------------------- #
# S33-S36 — bundle projection
# --------------------------------------------------------------------------- #

def test_s33_assistant_resolved_state_and_ref_copied_exactly():
    manifest, sea, canonical, _ = _simple()
    bundles = [_bundle(["a1"], state="resolved", bid="bundle_" + "f" * 64)]
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    m = arc["messages"][1]
    assert m["bundle_eligibility"] == "eligible"
    assert m["bundle_state"] == "resolved"
    assert m["bundle_ref"] == "bundle_" + "f" * 64


def test_s34_assistant_ambiguous_preserved():
    manifest, sea, canonical, _ = _simple()
    bundles = [_bundle(["a1"], state="ambiguous", bid="bundle_" + "f" * 64)]
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    m = arc["messages"][1]
    assert m["bundle_state"] == "ambiguous"
    assert m["bundle_ref"] == "bundle_" + "f" * 64


def test_s35_non_assistant_bundle_state_and_ref_null():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    m = arc["messages"][0]
    assert m["bundle_eligibility"] == "not_eligible"
    assert m["bundle_state"] is None
    assert m["bundle_ref"] is None


def test_s36_never_recomputes_bundle():
    manifest, sea, canonical, _ = _simple()
    # bundle_id is exactly what P4 produced; P5 must not derive its own.
    bundles = [_bundle(["a1"], bid="bundle_" + "9" * 64)]
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    assert arc["messages"][1]["bundle_ref"] == "bundle_" + "9" * 64


# --------------------------------------------------------------------------- #
# S37-S42 — IDs + hashes
# --------------------------------------------------------------------------- #

def test_s37_archive_id_exact_recomputation():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    assert arc["archive_id"] == normalized_archive_id(SEA_ID, NORMALIZATION_PROFILE)


def test_s38_message_id_exact_recomputation():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    m = arc["messages"][1]
    assert m["message_id"] == normalized_message_id(arc["archive_id"], _evid("a1"))


def test_s39_raw_message_id_exact_source_id_or_null():
    manifest = _manifest()
    nodes = [
        _node("a1", _msg("assistant", _content("text", parts=["x"]), mid="msg_a")),
        _node("a2", _msg("assistant", _content("text", parts=["y"]))),
    ]
    arc = build_chatgpt_normalized_archive(manifest, _sea(nodes), _canonical(["a1", "a2"]), [_bundle(["a1"]), _bundle(["a2"], bid="bundle_" + "e" * 64)])
    assert arc["messages"][0]["immutable_ref"]["raw_message_id"] == "msg_a"
    assert arc["messages"][1]["immutable_ref"]["raw_message_id"] is None


def test_s40_message_hash_exact_recomputation():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    m = arc["messages"][0]
    expected = jcs_hash({
        "domain": "NORMALIZED-MESSAGE-HASH-v1",
        "payload": {
            "normalization_profile": NORMALIZATION_PROFILE,
            "message_id": m["message_id"],
            "role": m["role"],
            "participant_id": m["participant_id"],
            "content": m["content"],
            "timestamp": m["timestamp"],
            "source_evidence_ref": m["source_evidence_ref"],
            "lineage_ref": m["lineage_ref"],
            "lineage_state": m["lineage_state"],
            "bundle_state": m["bundle_state"],
            "bundle_ref": m["bundle_ref"],
            "bundle_eligibility": m["bundle_eligibility"],
            "raw_message_id": m["immutable_ref"]["raw_message_id"],
        },
    })
    assert m["immutable_ref"]["message_hash"] == expected


def test_s41_normalized_content_hash_exact_recomputation():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    expected = jcs_hash({
        "domain": "NORMALIZED-CONTENT-HASH-v1",
        "payload": {
            "normalization_profile": NORMALIZATION_PROFILE,
            "archive_id": arc["archive_id"],
            "source_evidence_archive_ref": arc["source_evidence_archive_ref"],
            "conversation_id": arc["conversation_id"],
            "title": arc["title"],
            "created_at": arc["created_at"],
            "updated_at": arc["updated_at"],
            "participants": arc["participants"],
            "ordered_message_hashes": [m["immutable_ref"]["message_hash"] for m in arc["messages"]],
        },
    })
    assert arc["immutability"]["normalized_content_hash"] == expected


def test_s42_raw_content_hash_equals_manifest_sha():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    assert arc["immutability"]["raw_content_hash"] == "s" * 64


# --------------------------------------------------------------------------- #
# S43-S45 — identity stability / immutability / determinism
# --------------------------------------------------------------------------- #

def test_s43_path_uri_ingested_at_do_not_alter_ids_or_hashes():
    nodes = [_node("u1", _msg("user", _content("text", parts=["hi"]))), _node("a1", _msg("assistant", _content("text", parts=["x"])))]
    sea = _sea(nodes)
    canonical = _canonical(["u1", "a1"])
    bundles = [_bundle(["a1"])]
    m1 = _manifest(path="/tmp/a.json")
    m2 = _manifest(path="/other/b.json")
    m2["ingested_at"] = "2024-01-01T00:00:00.000000Z"
    m2["source_locator"]["uri"] = "file:///other/b.json"
    a1 = build_chatgpt_normalized_archive(m1, sea, canonical, bundles)
    a2 = build_chatgpt_normalized_archive(m2, sea, canonical, bundles)
    assert a1["archive_id"] == a2["archive_id"]
    assert [m["message_id"] for m in a1["messages"]] == [m["message_id"] for m in a2["messages"]]
    assert a1["immutability"]["normalized_content_hash"] == a2["immutability"]["normalized_content_hash"]


def test_s44_inputs_immutable():
    manifest, sea, canonical, bundles = _simple()
    before = (copy.deepcopy(manifest), copy.deepcopy(sea), copy.deepcopy(canonical), copy.deepcopy(bundles))
    build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    assert (manifest, sea, canonical, bundles) == before


def test_s45_repeated_build_entire_archive_equal():
    manifest, sea, canonical, bundles = _simple()
    a1 = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    a2 = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    assert a1 == a2


# --------------------------------------------------------------------------- #
# S46-S47 — schema + no fabricated semantics
# --------------------------------------------------------------------------- #

def test_s46_archive_is_schema_valid():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    _validate(arc)


def test_s47_no_causal_persona_identity_fields():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    forbidden = {"caused_by", "meaning", "policy", "identity_effect", "relationship_delta", "persona"}
    for m in arc["messages"]:
        assert forbidden.isdisjoint(m.keys())
    assert forbidden.isdisjoint(arc.keys())


# --------------------------------------------------------------------------- #
# S48-S51 — R1 closure (huge-int timestamp + provenance behavior)
# --------------------------------------------------------------------------- #

def test_s48_huge_finite_int_timestamp_projects_to_null():
    manifest = _manifest()
    cases = [10**1000, -(10**1000), 10**19]
    for i, ct in enumerate(cases):
        node = _node("a%d" % i, _msg("assistant", _content("text", parts=["x"]), create_time=ct))
        arc = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a%d" % i]), [_bundle(["a%d" % i], bid="bundle_" + ("%064x" % i))])
        assert arc["messages"][0]["timestamp"] is None


def test_s49_archive_provenance_mapping():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    p = arc["provenance"]
    assert p["source_id"] == "conv1"  # conversation_id, not source_node_id
    assert p["source_offset"] is None
    assert p["raw_message_id"] is None
    assert p["source_type"] == "chatgpt_official_export"
    assert p["source_path"] == "/tmp/x.json"
    assert p["source_uri"] is None


def test_s50_message_provenance_mapping():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    m = arc["messages"][1]  # assistant a1
    p = m["provenance"]
    assert p["source_id"] == "a1"  # source_node_id, not conversation_id
    assert p["source_offset"] is None
    assert p["raw_message_id"] == "msg_a"  # source message.id
    assert m["immutable_ref"]["raw_message_id"] == p["raw_message_id"]

    # null path: no source message.id -> both raw_message_id fields null,
    # and never fall back to source_node_id.
    node = _node("a2", _msg("assistant", _content("text", parts=["x"])))
    arc2 = build_chatgpt_normalized_archive(manifest, _sea([node]), _canonical(["a2"]), [_bundle(["a2"], bid="bundle_" + "e" * 64)])
    m2 = arc2["messages"][0]
    assert m2["provenance"]["raw_message_id"] is None
    assert m2["immutable_ref"]["raw_message_id"] is None
    assert m2["provenance"]["raw_message_id"] != m2["provenance"]["source_id"]


def test_s51_normalization_adapter_version_exact():
    manifest, sea, canonical, bundles = _simple()
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    assert arc["provenance"]["normalization_adapter"] == "chatgpt_official_export_normalizer"
    assert arc["provenance"]["normalization_version"] == "0.3.0"
    assert arc["immutability"]["normalization_adapter"] == "chatgpt_official_export_normalizer"
    assert arc["immutability"]["normalization_version"] == "0.3.0"
    assert arc["messages"][0]["provenance"]["normalization_adapter"] == "chatgpt_official_export_normalizer"
    assert arc["messages"][0]["provenance"]["normalization_version"] == "0.3.0"


# --------------------------------------------------------------------------- #
# Golden private acceptance (only when GOLDEN_MIRA_FIXTURE_PATH is set)
# --------------------------------------------------------------------------- #

def test_golden_private_acceptance_frozen_hard_values():
    path = os.environ.get("GOLDEN_MIRA_FIXTURE_PATH")
    if not path:
        pytest.skip("GOLDEN_MIRA_FIXTURE_PATH not set")
    raw = Path(path).read_bytes()
    manifest, sea = build_chatgpt_source_evidence(raw, None, {"path": path, "uri": None})

    assert manifest["source_sha256"] == "564ef9b1aa5457b56751f550d80b0eaa24e144f8d08bd2f6b8c0ff870b8e9420"
    assert sea["source_native"]["conversation_id"] == "6a754a53-82c4-83e8-b9a2-610154053181"

    canonical, _ = resolve_chatgpt_topology(sea)
    assert canonical["resolution_status"] == "resolved"
    assert len(canonical["node_refs"]) == 4026

    bundles = build_chatgpt_response_bundles(sea, canonical, [])
    arc = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)

    assert len(arc["messages"]) == 4025

    eligible = [m for m in arc["messages"] if m["bundle_eligibility"] == "eligible"]
    not_eligible = [m for m in arc["messages"] if m["bundle_eligibility"] == "not_eligible"]
    assert len(eligible) == 2504
    assert len(not_eligible) == 1521

    assert len({m["bundle_ref"] for m in eligible}) == 1508
    assert arc["immutability"]["raw_content_hash"] == manifest["source_sha256"]

    # alternate nodes are never projected: every message's provenance.source_id
    # is a canonical node id.
    canonical_ids = set(canonical["node_refs"])
    for m in arc["messages"]:
        assert m["provenance"]["source_id"] in canonical_ids

    # Frozen P5 Golden signature (exact).
    assert arc["archive_id"] == "norm_ad478095fc8985d8e0433f3dc0b3c984cc0471e7463f3694e4590b6a9d727dd3"
    assert arc["immutability"]["normalized_content_hash"] == "c2a94f0250b8aa4dcf2bf58ecb76204a1ef84f482f5ac27b54b6cb3b8d5b1960"
    role_counts: dict[str, int] = {}
    for m in arc["messages"]:
        role_counts[m["role"]] = role_counts.get(m["role"], 0) + 1
    assert role_counts == {"user": 1521, "assistant": 2504}
    assert [p["participant_id"] for p in arc["participants"]] == ["role:user", "role:assistant"]
    assert sum(1 for m in arc["messages"] if m["bundle_state"] == "resolved") == 2390
    assert sum(1 for m in arc["messages"] if m["bundle_state"] == "ambiguous") == 114
    assert sum(1 for m in arc["messages"] if m["content"] != "") == 3016
    assert sum(1 for m in arc["messages"] if m["content"] == "") == 1009

    _validate(arc)
