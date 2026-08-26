"""M0-P2 source-native topology views sabotage tests (contract §11, §12).

The standard: the correct resolver must pass, but a resolver that guesses,
sorts, or repairs topology MUST NOT sneak through. Source topology is evidence,
not inference.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import jsonschema
import pytest

from persona_extractor.archive.adapters.chatgpt_evidence import (
    build_chatgpt_source_evidence,
)
from persona_extractor.archive.evidence.lineage_views import resolve_chatgpt_topology
from persona_extractor.archive.evidence.topology import TopologyInputError

REPO = Path(__file__).resolve().parents[1]

# Canonical tree: root -> u1 -> a1 -> a2 -> current, with an off-lineage
# branch u1 -> alt1 -> alt2.
PARENTS = {
    "root": None,
    "u1": "root",
    "a1": "u1",
    "a2": "a1",
    "current": "a2",
    "alt1": "u1",
    "alt2": "alt1",
}


def _sea(
    parents: dict[str, str | None] | None = None,
    *,
    current: str | None = "current",
    scramble_nodes: bool = False,
    wrong_projection: bool = False,
    scrambled_timestamps: bool = False,
) -> dict:
    parents = parents if parents is not None else PARENTS
    nodes = []
    for sid, parent in parents.items():
        node: dict = {
            "source_node_id": sid,
            "source_payload": {"parent": parent},
            "node_evidence_id": "node_" + "e" * 64,
        }
        if wrong_projection:
            node["structural_projection"] = {"parent_node_id": "WRONG_PARENT"}
        if scrambled_timestamps:
            node["source_payload"]["create_time"] = 1000 - len(nodes)
        nodes.append(node)
    if scramble_nodes:
        nodes = list(reversed(nodes))
    return {
        "evidence_archive_id": "sea_" + "a" * 64,
        "source_native": {"current_node": current},
        "nodes": nodes,
    }


def _lineage_schema() -> dict:
    return json.loads((REPO / "schemas" / "canonical_lineage_view.schema.json").read_text())


def _alternate_schema() -> dict:
    return json.loads((REPO / "schemas" / "alternate_evidence_view.schema.json").read_text())


# --------------------------------------------------------------------------- #
# Authority boundary
# --------------------------------------------------------------------------- #

def test_s01_resolved_lineage_uses_source_payload_parent_not_projection():
    sea = _sea(wrong_projection=True)
    canonical, _ = resolve_chatgpt_topology(sea)
    assert canonical["resolution_status"] == "resolved"
    assert canonical["node_refs"] == ["root", "u1", "a1", "a2", "current"]


def test_s02_scrambled_timestamps_do_not_change_lineage():
    sea = _sea(scrambled_timestamps=True)
    canonical, _ = resolve_chatgpt_topology(sea)
    assert canonical["node_refs"] == ["root", "u1", "a1", "a2", "current"]


def test_s03_shuffled_sea_nodes_do_not_change_lineage():
    sea = _sea(scramble_nodes=True)
    canonical, _ = resolve_chatgpt_topology(sea)
    assert canonical["node_refs"] == ["root", "u1", "a1", "a2", "current"]


def test_s04_resolved_node_refs_are_root_to_current():
    canonical, _ = resolve_chatgpt_topology(_sea())
    assert canonical["node_refs"][0] == "root"
    assert canonical["node_refs"][-1] == "current"


# --------------------------------------------------------------------------- #
# Failure semantics
# --------------------------------------------------------------------------- #

def test_s05_missing_current_node():
    canonical, alternates = resolve_chatgpt_topology(_sea(current=None))
    assert canonical["resolution_status"] == "invalid_missing_current_node"
    assert alternates == []


def test_s06_current_node_not_in_sea():
    canonical, _ = resolve_chatgpt_topology(_sea(current="ghost"))
    assert canonical["resolution_status"] == "invalid_current_node_not_in_mapping"


def test_s07_missing_parent():
    parents = dict(PARENTS)
    parents["a1"] = "ghost_parent"
    canonical, _ = resolve_chatgpt_topology(_sea(parents))
    assert canonical["resolution_status"] == "invalid_missing_parent"
    assert canonical["offending_node_refs"] == ["a1"]
    assert canonical["offending_parent_refs"] == ["ghost_parent"]


def test_s08_self_parent():
    parents = dict(PARENTS)
    parents["a2"] = "a2"
    canonical, _ = resolve_chatgpt_topology(_sea(parents))
    assert canonical["resolution_status"] == "invalid_self_parent"


def test_s09_self_parent_wins_over_cycle():
    parents = {"root": None, "n1": "root", "n2": "n1", "n3": "n2", "current": "n3"}
    parents["n2"] = "n2"  # n2 is self-parent; also would form a cycle n2->n2
    canonical, _ = resolve_chatgpt_topology(_sea(parents))
    assert canonical["resolution_status"] == "invalid_self_parent"


def test_s10_multi_node_cycle():
    parents = {"root": None, "n1": "root", "n2": "n1", "n3": "n2"}
    parents["n2"] = "n3"  # n1 -> n2 -> n3 -> n2 cycle
    canonical, _ = resolve_chatgpt_topology(_sea(parents, current="n3"))
    assert canonical["resolution_status"] == "invalid_cycle"


def test_t01_missing_parent_diagnostics_exact():
    parents = dict(PARENTS)
    parents["a1"] = "ghost_parent"
    canonical, _ = resolve_chatgpt_topology(_sea(parents))
    assert canonical["offending_node_refs"] == ["a1"]
    assert canonical["offending_parent_refs"] == ["ghost_parent"]
    assert canonical["visited_node_refs"] == ["current", "a2", "a1"]


def test_t02_self_parent_diagnostics_exact():
    parents = dict(PARENTS)
    parents["a2"] = "a2"
    canonical, _ = resolve_chatgpt_topology(_sea(parents))
    assert canonical["offending_node_refs"] == ["a2"]
    assert canonical["offending_parent_refs"] == ["a2"]
    assert canonical["visited_node_refs"] == ["current", "a2"]


def test_t03_cycle_diagnostics_exact():
    parents = {"root": None, "n1": "root", "n2": "n3", "n3": "n2"}
    canonical, _ = resolve_chatgpt_topology(_sea(parents, current="n3"))
    assert canonical["offending_node_refs"] == ["n2"]
    assert canonical["offending_parent_refs"] == ["n3"]
    assert canonical["visited_node_refs"] == ["n3", "n2"]


def test_s11_invalid_topology_emits_no_resolved_fields():
    canonical, _ = resolve_chatgpt_topology(_sea(current=None))
    assert "lineage_id" not in canonical
    assert "node_refs" not in canonical


def test_s12_invalid_topology_emits_zero_alternates():
    _, alternates = resolve_chatgpt_topology(_sea(current=None))
    assert alternates == []


# --------------------------------------------------------------------------- #
# Alternate evidence
# --------------------------------------------------------------------------- #

def test_s13_alternate_set_is_exact_complement():
    sea = _sea()
    canonical, alternates = resolve_chatgpt_topology(sea)
    alt_refs = {a["source_node_ref"] for a in alternates}
    assert alt_refs == {"alt1", "alt2"}


def test_s14_canonical_alternate_partition_is_exact():
    sea = _sea()
    canonical, alternates = resolve_chatgpt_topology(sea)
    canonical_set = set(canonical["node_refs"])
    alt_set = {a["source_node_ref"] for a in alternates}
    all_refs = {n["source_node_id"] for n in sea["nodes"]}
    assert canonical_set & alt_set == set()
    assert canonical_set | alt_set == all_refs


def test_s15_alternate_metadata_is_frozen():
    _, alternates = resolve_chatgpt_topology(_sea())
    for a in alternates:
        assert a["lineage_status"] == "alternate"
        assert a["active_context_membership"] is False
        assert a["historical_exposure"] == "unknown"


def test_s18_repeated_runs_are_deterministic():
    c1, a1 = resolve_chatgpt_topology(_sea())
    c2, a2 = resolve_chatgpt_topology(_sea())
    assert c1["lineage_id"] == c2["lineage_id"]
    assert [a["source_node_ref"] for a in a1] == [a["source_node_ref"] for a in a2]


# --------------------------------------------------------------------------- #
# SEA precondition / immutability
# --------------------------------------------------------------------------- #

def test_s16_duplicate_source_node_id_fails_closed():
    sea = _sea()
    dup = dict(sea["nodes"][0])
    sea["nodes"].append(dup)
    with pytest.raises(TopologyInputError):
        resolve_chatgpt_topology(sea)


def test_s17_resolver_never_mutates_sea():
    sea = _sea()
    before = copy.deepcopy(sea)
    resolve_chatgpt_topology(sea)
    assert sea == before

    # also under malformed topology
    sea2 = _sea(current=None)
    before2 = copy.deepcopy(sea2)
    resolve_chatgpt_topology(sea2)
    assert sea2 == before2


# --------------------------------------------------------------------------- #
# Schema conformance
# --------------------------------------------------------------------------- #

def test_resolved_view_is_schema_valid():
    canonical, _ = resolve_chatgpt_topology(_sea())
    jsonschema.Draft202012Validator(_lineage_schema()).validate(canonical)


@pytest.mark.parametrize("current", [None, "ghost"])
def test_failure_records_are_schema_valid(current):
    canonical, _ = resolve_chatgpt_topology(_sea(current=current))
    jsonschema.Draft202012Validator(_lineage_schema()).validate(canonical)


def _invalid_seas():
    return [
        ("missing_current", _sea(current=None)),
        ("current_not_mapping", _sea(current="ghost")),
        ("missing_parent", _sea(dict(PARENTS, a1="ghost_parent"))),
        ("self_parent", _sea(dict(PARENTS, a2="a2"))),
        ("cycle", _sea({"root": None, "n1": "root", "n2": "n3", "n3": "n2"}, current="n3")),
    ]


@pytest.mark.parametrize("name,sea", _invalid_seas(), ids=[n for n, _ in _invalid_seas()])
def test_t04_every_invalid_status_emits_zero_alternates(name, sea):
    _, alternates = resolve_chatgpt_topology(sea)
    assert alternates == []


@pytest.mark.parametrize("name,sea", _invalid_seas(), ids=[n for n, _ in _invalid_seas()])
def test_t05_every_invalid_status_is_schema_valid(name, sea):
    canonical, _ = resolve_chatgpt_topology(sea)
    jsonschema.Draft202012Validator(_lineage_schema()).validate(canonical)


def test_alternate_views_are_schema_valid():
    _, alternates = resolve_chatgpt_topology(_sea())
    schema = _alternate_schema()
    for a in alternates:
        jsonschema.Draft202012Validator(schema).validate(a)


# --------------------------------------------------------------------------- #
# Golden private acceptance (only when GOLDEN_MIRA_FIXTURE_PATH is set)
# --------------------------------------------------------------------------- #

def test_golden_private_acceptance_4026_33_4059():
    path = os.environ.get("GOLDEN_MIRA_FIXTURE_PATH")
    if not path:
        pytest.skip("GOLDEN_MIRA_FIXTURE_PATH not set")
    raw = Path(path).read_bytes()
    manifest, sea = build_chatgpt_source_evidence(raw, None, {"path": path, "uri": None})

    assert manifest["source_sha256"] == "564ef9b1aa5457b56751f550d80b0eaa24e144f8d08bd2f6b8c0ff870b8e9420"
    assert sea["source_native"]["conversation_id"] == "6a754a53-82c4-83e8-b9a2-610154053181"

    canonical, alternates = resolve_chatgpt_topology(sea)
    assert canonical["resolution_status"] == "resolved"
    assert canonical["current_node_id"] == "3fa39e74-2fd4-4177-9df3-a150ba168e8a"

    assert len(canonical["node_refs"]) == 4026
    assert len(alternates) == 33
    assert len(canonical["node_refs"]) + len(alternates) == 4059

    canonical_set = set(canonical["node_refs"])
    alt_set = {a["source_node_ref"] for a in alternates}
    assert canonical_set & alt_set == set()
    assert canonical_set | alt_set == {n["source_node_id"] for n in sea["nodes"]}

    assert len(canonical_set) == 4026
    assert len(alt_set) == 33

    # root is the node whose parent is None; current is the traversal start.
    assert canonical["node_refs"][-1] == "3fa39e74-2fd4-4177-9df3-a150ba168e8a"
    assert canonical["node_refs"][0] == "client-created-root"
    nodes_by_id = {n["source_node_id"]: n for n in sea["nodes"]}
    assert nodes_by_id[canonical["node_refs"][0]]["source_payload"].get("parent") is None
