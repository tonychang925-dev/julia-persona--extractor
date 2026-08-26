"""M0-P4 response-bundle views sabotage tests (contract §14, §14.6).

The standard: canonical lineage is the EXCLUSIVE membership/order authority; SEA
is dereference-only; typed artifacts are join-only. A resolver that recomputes
topology from SEA, guesses unknown content into a resolved bundle, truncates
members, or emits unbundled MUST NOT sneak through.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import jsonschema
import pytest

from persona_extractor.archive.adapters.chatgpt_evidence import build_chatgpt_source_evidence
from persona_extractor.archive.evidence.ids import bundle_id
from persona_extractor.archive.evidence.lineage_views import resolve_chatgpt_topology
from persona_extractor.archive.evidence.response_bundles import (
    RESPONSE_BUNDLE_PROFILE,
    BundleInputError,
    build_chatgpt_response_bundles,
)
from persona_extractor.archive.evidence.typed_artifacts import build_chatgpt_typed_artifacts

REPO = Path(__file__).resolve().parents[1]
SEA_ID = "sea_" + "a" * 64


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

def _evid(sid: str) -> str:
    """Deterministic node_evidence_id for a fixture node id."""
    return "node_" + ("%064x" % sum(ord(c) for c in sid))


def _aid(ref: str, i: int = 0) -> str:
    """Deterministic artifact_id for a fixture node ref."""
    return "artifact_" + ("%064x" % (sum(ord(c) for c in ref) + i + 1))


def _msg(role: str | None, content_type: str | None) -> dict:
    m: dict = {"author": {"role": role}}
    if content_type is not None:
        m["content"] = {"content_type": content_type}
    return m


def _node(sid: str, role: str | None, content_type: str | None, projection: dict | None = None) -> dict:
    node: dict = {
        "source_node_id": sid,
        "node_evidence_id": _evid(sid),
        "source_payload": {"message": _msg(role, content_type)},
    }
    if projection is not None:
        node["structural_projection"] = projection
    return node


def _structural(sid: str) -> dict:
    """A ``message = null`` structural node (transparent for grouping)."""
    return {"source_node_id": sid, "node_evidence_id": _evid(sid), "source_payload": {"message": None}}


def _sea(nodes: list[dict], evidence_archive_id: str = SEA_ID) -> dict:
    return {"evidence_archive_id": evidence_archive_id, "nodes": nodes}


def _canonical(node_refs: list[str], evidence_archive_id: str = SEA_ID) -> dict:
    return {
        "resolution_status": "resolved",
        "evidence_archive_id": evidence_archive_id,
        "node_refs": node_refs,
    }


def _art(artifact_id_value: str, source_node_ref: str, evidence_archive_id: str = SEA_ID, pointer: str = "/message/content") -> dict:
    return {
        "artifact_id": artifact_id_value,
        "evidence_archive_id": evidence_archive_id,
        "source_node_ref": source_node_ref,
        "artifact_profile": "chatgpt-official-export-typed-artifact-v0.1",
        "source_artifact_pointer": pointer,
    }


def _schema() -> dict:
    return json.loads((REPO / "schemas" / "response_bundle_view.schema.json").read_text())


def _validate(bundle: dict) -> None:
    jsonschema.Draft202012Validator(_schema()).validate(bundle)


# --------------------------------------------------------------------------- #
# S01-S08 — grouping + authority
# --------------------------------------------------------------------------- #

def test_s01_single_assistant_run_resolves_to_one_bundle():
    sea = _sea([_node("u1", "user", "text"), _node("x1", "assistant", "text")])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["u1", "x1"]), [])
    assert len(bundles) == 1
    assert bundles[0]["bundle_state"] == "resolved"


def test_s02_trigger_is_preceding_user_not_member():
    sea = _sea([
        _node("u1", "user", "text"),
        _node("t1", "assistant", "thoughts"),
        _node("x1", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["u1", "t1", "x1"]), [])
    b = bundles[0]
    assert b["trigger_refs"] == ["u1"]
    assert b["member_node_refs"] == ["t1", "x1"]
    assert "u1" not in b["member_node_refs"]


def test_s03_null_structural_node_does_not_break_run():
    sea = _sea([
        _node("u1", "user", "text"),
        _structural("null1"),
        _node("t1", "assistant", "thoughts"),
        _node("r1", "assistant", "reasoning_recap"),
        _node("x1", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["u1", "null1", "t1", "r1", "x1"]), [])
    assert len(bundles) == 1
    b = bundles[0]
    assert b["trigger_refs"] == ["u1"]
    assert b["member_node_refs"] == ["t1", "r1", "x1"]
    assert b["visible_response_refs"] == ["x1"]


def test_s04_null_structural_node_is_not_member_or_trigger():
    sea = _sea([
        _structural("null1"),
        _node("x1", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["null1", "x1"]), [])
    b = bundles[0]
    assert "null1" not in b["member_node_refs"]
    assert "null1" not in b["trigger_refs"]


def test_s05_members_preserve_canonical_order_not_lexical():
    # canonical order is x1 -> a1 -> m1; lexical ascending would be a1, m1, x1.
    sea = _sea([
        _node("x1", "assistant", "thoughts"),
        _node("a1", "assistant", "reasoning_recap"),
        _node("m1", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["x1", "a1", "m1"]), [])
    assert bundles[0]["member_node_refs"] == ["x1", "a1", "m1"]


def test_s06_multiple_assistant_runs_produce_multiple_bundles_in_order():
    sea = _sea([
        _node("u1", "user", "text"),
        _node("a1", "assistant", "text"),
        _node("u2", "user", "text"),
        _node("a2", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["u1", "a1", "u2", "a2"]), [])
    assert len(bundles) == 2
    assert bundles[0]["member_node_refs"] == ["a1"]
    assert bundles[1]["member_node_refs"] == ["a2"]
    assert bundles[0]["trigger_refs"] == ["u1"]
    assert bundles[1]["trigger_refs"] == ["u2"]


def test_s07_non_assistant_non_user_message_node_breaks_run():
    # a "system" message-bearing node is neither member nor trigger, and it
    # breaks contiguity, so a1 and a2 are two separate runs.
    sea = _sea([
        _node("a1", "assistant", "text"),
        _node("s1", "system", "text"),
        _node("a2", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["a1", "s1", "a2"]), [])
    assert len(bundles) == 2
    assert bundles[0]["member_node_refs"] == ["a1"]
    assert bundles[1]["member_node_refs"] == ["a2"]


def test_s08_classification_reads_source_payload_not_projection():
    # structural_projection lies (claims "thoughts"); production must read
    # source_payload.message.content.content_type = "text".
    sea = _sea([
        _node("x1", "assistant", "text", projection={"content_type": "thoughts"}),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["x1"]), [])
    assert bundles[0]["bundle_state"] == "resolved"
    assert bundles[0]["visible_response_refs"] == ["x1"]


# --------------------------------------------------------------------------- #
# S09-S18 — resolved / ambiguous classification
# --------------------------------------------------------------------------- #

def _run(cts):
    nodes = [_node("n%d" % i, "assistant", ct) for i, ct in enumerate(cts)]
    bundles = build_chatgpt_response_bundles(_sea(nodes), _canonical(["n%d" % i for i in range(len(cts))]), [])
    assert len(bundles) == 1
    return bundles[0]


def test_s09_text_resolves():
    assert _run(["text"])["bundle_state"] == "resolved"


def test_s10_multimodal_text_resolves():
    assert _run(["multimodal_text"])["bundle_state"] == "resolved"


def test_s11_thoughts_recap_text_resolves():
    assert _run(["thoughts", "reasoning_recap", "text"])["bundle_state"] == "resolved"


def test_s12_repeated_auxiliary_resolves():
    assert _run(["thoughts", "thoughts", "reasoning_recap", "text"])["bundle_state"] == "resolved"


def test_s13_zero_terminal_is_ambiguous():
    assert _run(["thoughts"])["bundle_state"] == "ambiguous"


def test_s14_two_terminals_is_ambiguous():
    assert _run(["text", "text"])["bundle_state"] == "ambiguous"


def test_s15_auxiliary_after_terminal_is_ambiguous():
    assert _run(["text", "thoughts"])["bundle_state"] == "ambiguous"


def test_s16_terminal_between_auxiliary_is_ambiguous():
    assert _run(["thoughts", "text", "thoughts"])["bundle_state"] == "ambiguous"


def test_s17_unknown_content_is_ambiguous():
    assert _run(["thoughts", "unknown_thing", "text"])["bundle_state"] == "ambiguous"


def test_s18_missing_content_type_is_ambiguous():
    assert _run([None])["bundle_state"] == "ambiguous"


# --------------------------------------------------------------------------- #
# S19-S22 — visible_response_refs
# --------------------------------------------------------------------------- #

def test_s19_resolved_visible_is_final_member():
    sea = _sea([
        _node("t1", "assistant", "thoughts"),
        _node("x1", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["t1", "x1"]), [])
    assert bundles[0]["visible_response_refs"] == ["x1"]


def test_s20_ambiguous_zero_terminal_visible_is_empty():
    sea = _sea([_node("t1", "assistant", "thoughts")])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["t1"]), [])
    assert bundles[0]["bundle_state"] == "ambiguous"
    assert bundles[0]["visible_response_refs"] == []


def test_s21_ambiguous_multiple_terminals_lists_all_recognized():
    sea = _sea([
        _node("x1", "assistant", "text"),
        _node("x2", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["x1", "x2"]), [])
    assert bundles[0]["bundle_state"] == "ambiguous"
    assert bundles[0]["visible_response_refs"] == ["x1", "x2"]


def test_s22_visible_refs_are_source_node_ids_not_artifact_ids():
    sea = _sea([_node("x1", "assistant", "text")])
    arts = [_art(_aid("x1"), "x1")]
    bundles = build_chatgpt_response_bundles(sea, _canonical(["x1"]), arts)
    assert bundles[0]["visible_response_refs"] == ["x1"]
    assert bundles[0]["visible_response_refs"] != [_aid("x1")]


# --------------------------------------------------------------------------- #
# S23-S27 — artifact_refs join
# --------------------------------------------------------------------------- #

def test_s23_artifact_refs_only_contains_member_artifacts():
    sea = _sea([
        _node("u1", "user", "text"),
        _node("x1", "assistant", "text"),
    ])
    arts = [_art(_aid("x1"), "x1"), _art(_aid("u1"), "u1")]
    bundles = build_chatgpt_response_bundles(sea, _canonical(["u1", "x1"]), arts)
    assert bundles[0]["artifact_refs"] == [_aid("x1")]


def test_s24_multimodal_member_contributes_multiple_leaf_artifacts():
    sea = _sea([_node("x1", "assistant", "multimodal_text")])
    arts = [_art(_aid("x1", 0), "x1"), _art(_aid("x1", 1), "x1"), _art(_aid("x1", 2), "x1")]
    bundles = build_chatgpt_response_bundles(sea, _canonical(["x1"]), arts)
    assert bundles[0]["artifact_refs"] == [_aid("x1", 0), _aid("x1", 1), _aid("x1", 2)]


def test_s25_artifact_order_is_canonical_member_then_source_order():
    sea = _sea([
        _node("a1", "assistant", "thoughts"),
        _node("x1", "assistant", "text"),
    ])
    # typed_artifacts delivered lexically sorted (x1 before a1); production must
    # reorder by canonical member order (a1 first).
    arts = [_art(_aid("x1"), "x1"), _art(_aid("a1"), "a1")]
    bundles = build_chatgpt_response_bundles(sea, _canonical(["a1", "x1"]), arts)
    assert bundles[0]["artifact_refs"] == [_aid("a1"), _aid("x1")]


def test_s26_member_without_artifact_has_no_artifact_ref():
    sea = _sea([_node("x1", "assistant", "text")])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["x1"]), [])
    assert bundles[0]["artifact_refs"] == []


def test_s27_artifact_refs_use_pointer_numeric_order_not_caller_order():
    # caller delivers parts/10 before parts/2; production must order by pointer
    # numeric index (parts/2 before parts/10), not by caller list order.
    sea = _sea([_node("x1", "assistant", "multimodal_text")])
    arts = [
        _art("artifact_" + "b" * 64, "x1", pointer="/message/content/parts/10"),
        _art("artifact_" + "a" * 64, "x1", pointer="/message/content/parts/2"),
    ]
    bundles = build_chatgpt_response_bundles(sea, _canonical(["x1"]), arts)
    assert bundles[0]["artifact_refs"] == ["artifact_" + "a" * 64, "artifact_" + "b" * 64]


# --------------------------------------------------------------------------- #
# S28-S30 — provenance_refs
# --------------------------------------------------------------------------- #

def test_s28_provenance_is_trigger_then_member_evidence_ids():
    sea = _sea([
        _node("u1", "user", "text"),
        _node("x1", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["u1", "x1"]), [])
    assert bundles[0]["provenance_refs"] == [_evid("u1"), _evid("x1")]


def test_s29_provenance_preserves_canonical_order():
    sea = _sea([
        _node("u2", "user", "text"),
        _node("u1", "user", "text"),
        _node("a1", "assistant", "thoughts"),
        _node("x1", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["u2", "u1", "a1", "x1"]), [])
    assert bundles[0]["provenance_refs"] == [_evid("u2"), _evid("u1"), _evid("a1"), _evid("x1")]


def test_s30_provenance_uses_node_evidence_id_not_source_node_id():
    sea = _sea([_node("x1", "assistant", "text")])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["x1"]), [])
    assert bundles[0]["provenance_refs"] == [_evid("x1")]
    assert bundles[0]["provenance_refs"] != ["x1"]


# --------------------------------------------------------------------------- #
# S31-S33 — conservation + no unbundled
# --------------------------------------------------------------------------- #

def test_s31_every_assistant_node_lands_in_exactly_one_bundle():
    sea = _sea([
        _node("a1", "assistant", "thoughts"),
        _node("a2", "assistant", "text"),
        _node("u1", "user", "text"),
        _node("a3", "assistant", "unknown_thing"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["a1", "a2", "u1", "a3"]), [])
    covered = [m for b in bundles for m in b["member_node_refs"]]
    assert covered == ["a1", "a2", "a3"]
    assert len(covered) == len(set(covered)) == 3


def test_s32_bundle_members_do_not_overlap():
    sea = _sea([
        _node("u1", "user", "text"),
        _node("a1", "assistant", "text"),
        _node("u2", "user", "text"),
        _node("a2", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["u1", "a1", "u2", "a2"]), [])
    s0 = set(bundles[0]["member_node_refs"])
    s1 = set(bundles[1]["member_node_refs"])
    assert s0 & s1 == set()


def test_s33_never_emits_unbundled():
    # even a lone unknown assistant node becomes ambiguous, never unbundled.
    sea = _sea([_node("a1", "assistant", "weird_type")])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["a1"]), [])
    assert bundles[0]["bundle_state"] != "unbundled"
    assert bundles[0]["bundle_state"] == "ambiguous"


# --------------------------------------------------------------------------- #
# S34-S40 — fail closed (BundleInputError)
# --------------------------------------------------------------------------- #

def test_s34_non_resolved_canonical_fails_closed():
    sea = _sea([_node("x1", "assistant", "text")])
    canonical = {"resolution_status": "invalid_missing_current_node", "evidence_archive_id": SEA_ID}
    with pytest.raises(BundleInputError):
        build_chatgpt_response_bundles(sea, canonical, [])


def test_s35_canonical_evidence_archive_mismatch_fails_closed():
    sea = _sea([_node("x1", "assistant", "text")])
    canonical = _canonical(["x1"], evidence_archive_id="sea_" + "b" * 64)
    with pytest.raises(BundleInputError):
        build_chatgpt_response_bundles(sea, canonical, [])


def test_s36_duplicate_source_node_id_fails_closed():
    sea = _sea([_node("x1", "assistant", "text"), _node("x1", "assistant", "text")])
    with pytest.raises(BundleInputError):
        build_chatgpt_response_bundles(sea, _canonical(["x1"]), [])


def test_s37_canonical_ref_not_in_sea_fails_closed():
    sea = _sea([_node("x1", "assistant", "text")])
    with pytest.raises(BundleInputError):
        build_chatgpt_response_bundles(sea, _canonical(["ghost"]), [])


def test_s38_artifact_evidence_archive_mismatch_fails_closed():
    sea = _sea([_node("x1", "assistant", "text")])
    arts = [_art(_aid("x1"), "x1", evidence_archive_id="sea_" + "b" * 64)]
    with pytest.raises(BundleInputError):
        build_chatgpt_response_bundles(sea, _canonical(["x1"]), arts)


def test_s39_duplicate_artifact_id_fails_closed():
    sea = _sea([_node("x1", "assistant", "text")])
    arts = [_art(_aid("x1"), "x1"), _art(_aid("x1"), "x1")]
    with pytest.raises(BundleInputError):
        build_chatgpt_response_bundles(sea, _canonical(["x1"]), arts)


def test_s40_missing_evidence_archive_id_fails_closed():
    with pytest.raises(BundleInputError):
        build_chatgpt_response_bundles({"nodes": [_node("x1", "assistant", "text")]}, _canonical(["x1"]), [])


# --------------------------------------------------------------------------- #
# S41-S42 — immutability + determinism
# --------------------------------------------------------------------------- #

def test_s41_never_mutates_inputs():
    sea = _sea([_node("u1", "user", "text"), _node("x1", "assistant", "text")])
    canonical = _canonical(["u1", "x1"])
    arts = [_art(_aid("x1"), "x1")]
    before = (copy.deepcopy(sea), copy.deepcopy(canonical), copy.deepcopy(arts))
    build_chatgpt_response_bundles(sea, canonical, arts)
    assert (sea, canonical, arts) == before


def test_s42_repeated_runs_are_deterministic():
    sea = _sea([_node("u1", "user", "text"), _node("x1", "assistant", "text")])
    canonical = _canonical(["u1", "x1"])
    b1 = build_chatgpt_response_bundles(sea, canonical, [])
    b2 = build_chatgpt_response_bundles(sea, canonical, [])
    assert b1 == b2
    assert b1[0]["bundle_id"] == b2[0]["bundle_id"]


# --------------------------------------------------------------------------- #
# S43-S45 — schema conformance + bundle identity
# --------------------------------------------------------------------------- #

def test_s43_resolved_bundle_is_schema_valid():
    sea = _sea([_node("u1", "user", "text"), _node("x1", "assistant", "text")])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["u1", "x1"]), [])
    _validate(bundles[0])


def test_s44_ambiguous_bundle_is_schema_valid():
    sea = _sea([_node("x1", "assistant", "thoughts")])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["x1"]), [])
    assert bundles[0]["bundle_state"] == "ambiguous"
    _validate(bundles[0])


def test_s45_bundle_id_is_frozen_domain_derivation():
    sea = _sea([_node("x1", "assistant", "text")])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["x1"]), [])
    b = bundles[0]
    assert b["bundle_id"].startswith("bundle_")
    assert b["bundle_id"] == bundle_id(SEA_ID, RESPONSE_BUNDLE_PROFILE, "resolved", ["x1"])


# --------------------------------------------------------------------------- #
# S46-S49 — R1 escape-hatch closure
# --------------------------------------------------------------------------- #

def test_s46_malformed_non_null_message_is_boundary_not_transparent():
    # assistant A -> malformed non-null message -> assistant B: the malformed
    # node breaks the run (A and B are two bundles). It is NOT skipped like null.
    sea = _sea([
        _node("a1", "assistant", "text"),
        {"source_node_id": "broken", "node_evidence_id": _evid("broken"), "source_payload": {"message": "broken"}},
        _node("a2", "assistant", "text"),
    ])
    bundles = build_chatgpt_response_bundles(sea, _canonical(["a1", "broken", "a2"]), [])
    assert len(bundles) == 2
    assert bundles[0]["member_node_refs"] == ["a1"]
    assert bundles[1]["member_node_refs"] == ["a2"]


def test_s47_artifact_profile_mismatch_fails_closed():
    sea = _sea([_node("x1", "assistant", "text")])
    art = _art(_aid("x1"), "x1")
    art["artifact_profile"] = "some-other-profile"
    with pytest.raises(BundleInputError):
        build_chatgpt_response_bundles(sea, _canonical(["x1"]), [art])


def test_s48_artifact_source_ref_not_in_sea_fails_closed():
    sea = _sea([_node("x1", "assistant", "text")])
    art = _art(_aid("ghost"), "ghost")
    with pytest.raises(BundleInputError):
        build_chatgpt_response_bundles(sea, _canonical(["x1"]), [art])


def test_s49_shuffled_typed_artifacts_produce_identical_bundles():
    sea = _sea([_node("x1", "assistant", "multimodal_text")])
    arts = [
        _art("artifact_" + "c" * 64, "x1", pointer="/message/content/parts/0"),
        _art("artifact_" + "a" * 64, "x1", pointer="/message/content/parts/10"),
        _art("artifact_" + "b" * 64, "x1", pointer="/message/content/parts/2"),
    ]
    shuffled = [arts[1], arts[2], arts[0]]
    b1 = build_chatgpt_response_bundles(sea, _canonical(["x1"]), arts)
    b2 = build_chatgpt_response_bundles(sea, _canonical(["x1"]), shuffled)
    assert b1 == b2
    assert b1[0]["artifact_refs"] == [
        "artifact_" + "c" * 64,  # parts/0
        "artifact_" + "b" * 64,  # parts/2
        "artifact_" + "a" * 64,  # parts/10
    ]


# --------------------------------------------------------------------------- #
# Golden private acceptance (only when GOLDEN_MIRA_FIXTURE_PATH is set)
# --------------------------------------------------------------------------- #

def test_golden_private_acceptance_conservation_and_signature():
    path = os.environ.get("GOLDEN_MIRA_FIXTURE_PATH")
    if not path:
        pytest.skip("GOLDEN_MIRA_FIXTURE_PATH not set")
    raw = Path(path).read_bytes()
    _, sea = build_chatgpt_source_evidence(raw, None, {"path": path, "uri": None})

    canonical, _ = resolve_chatgpt_topology(sea)
    assert canonical["resolution_status"] == "resolved"

    artifacts = build_chatgpt_typed_artifacts(sea)
    sea_before = copy.deepcopy(sea)
    canonical_before = copy.deepcopy(canonical)
    artifacts_before = copy.deepcopy(artifacts)

    bundles = build_chatgpt_response_bundles(sea, canonical, artifacts)

    # Frozen Golden signature (exact P4 counts).
    resolved = [b for b in bundles if b["bundle_state"] == "resolved"]
    ambiguous = [b for b in bundles if b["bundle_state"] == "ambiguous"]
    assert len(bundles) == 1508
    assert len(resolved) == 1461
    assert len(ambiguous) == 47
    assert sum(len(b["member_node_refs"]) for b in bundles) == 2504
    assert sum(len(b["trigger_refs"]) for b in bundles) == 1520
    assert sum(len(b["visible_response_refs"]) for b in bundles) == 1506
    assert sum(len(b["provenance_refs"]) for b in bundles) == 4024
    assert all(b["bundle_state"] != "unbundled" for b in bundles)

    # Conservation: every eligible canonical assistant message-bearing node is
    # covered by exactly one bundle.
    nodes_by_id = {n["source_node_id"]: n for n in sea["nodes"]}
    assistant_refs = []
    for ref in canonical["node_refs"]:
        message = nodes_by_id[ref]["source_payload"].get("message")
        if not isinstance(message, dict):
            continue
        role = (message.get("author") or {}).get("role")
        if role == "assistant":
            assistant_refs.append(ref)
    covered = [m for b in bundles for m in b["member_node_refs"]]
    assert covered == assistant_refs
    assert len(covered) == len(set(covered)) == len(assistant_refs)

    # Schema + reference namespace integrity.
    artifacts_by_id = {a["artifact_id"]: a for a in artifacts}
    bundle_ids = [b["bundle_id"] for b in bundles]
    assert len(bundle_ids) == len(set(bundle_ids))
    for b in bundles:
        _validate(b)
        member_set = set(b["member_node_refs"])
        for aid in b["artifact_refs"]:
            assert aid in artifacts_by_id
            assert artifacts_by_id[aid]["source_node_ref"] in member_set
        assert b["bundle_id"] == bundle_id(
            sea["evidence_archive_id"], RESPONSE_BUNDLE_PROFILE, b["bundle_state"], b["member_node_refs"]
        )
    for b in resolved:
        assert b["visible_response_refs"] == [b["member_node_refs"][-1]]

    # Immutability + determinism on the real Golden inputs.
    assert (sea, canonical, artifacts) == (sea_before, canonical_before, artifacts_before)
    assert build_chatgpt_response_bundles(sea, canonical, artifacts) == bundles
