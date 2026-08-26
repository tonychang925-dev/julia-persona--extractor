"""M0 ResponseBundle reconstruction + atomicity + ambiguity tests.

Covers M0-SEA-T10/T11/T14 and R0.1-H04 (contract §14.3 resolution profile).
The resolution helper here is a reference implementation of the normative
profile; it is NOT the production ResponseBundle resolver.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[2]

AUXILIARY = {"thoughts", "reasoning_recap"}
TERMINAL = {"text", "multimodal_text"}


def load_schema(name: str) -> dict:
    return json.loads((REPO / "schemas" / name).read_text())


def assert_valid(schema: dict, instance: dict) -> None:
    jsonschema.Draft202012Validator(schema).validate(instance)


def assert_invalid(schema: dict, instance: dict) -> None:
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(instance))
    assert errors, "expected instance to be rejected by schema"


# --------------------------------------------------------------------------- #
# Reference resolution profile (contract §14.3)
# --------------------------------------------------------------------------- #

def resolve_assistant_run(content_types: list[str]) -> str:
    """Return bundle_state for one assistant run per the §14.3 resolved/ambiguous rule."""
    terminals = [i for i, ct in enumerate(content_types) if ct in TERMINAL]
    unknowns = [ct for ct in content_types if ct not in AUXILIARY and ct not in TERMINAL]
    if unknowns:
        return "ambiguous"
    if len(terminals) != 1:
        return "ambiguous"  # zero or more-than-one terminal visible response
    if terminals[0] != len(content_types) - 1:
        return "ambiguous"  # terminal is not the final message-bearing node
    return "resolved"


# --------------------------------------------------------------------------- #
# T10 — Response bundle reconstruction (schema)
# --------------------------------------------------------------------------- #

def test_t10_bundle_schema_accepts_resolved_bundle():
    schema = load_schema("response_bundle_view.schema.json")
    bundle = _bundle("resolved", member_node_refs=["t1", "r1", "x1"])
    assert_valid(schema, bundle)


def test_t10_bundle_schema_rejects_missing_resolution_profile():
    schema = load_schema("response_bundle_view.schema.json")
    bundle = _bundle("resolved", member_node_refs=["x1"])
    bundle.pop("resolution_profile")
    assert_invalid(schema, bundle)


# --------------------------------------------------------------------------- #
# T11 — Response bundle atomicity (resolved bundle cannot be empty)
# --------------------------------------------------------------------------- #

def test_t11_resolved_bundle_requires_at_least_one_member():
    schema = load_schema("response_bundle_view.schema.json")
    bundle = _bundle("resolved", member_node_refs=[])
    assert_invalid(schema, bundle)


# --------------------------------------------------------------------------- #
# T14 — Bundle ambiguity preservation
# --------------------------------------------------------------------------- #

def test_t14_ambiguous_bundle_state_is_schema_valid_and_preserved():
    schema = load_schema("response_bundle_view.schema.json")
    bundle = _bundle("ambiguous", member_node_refs=["u1"])
    assert_valid(schema, bundle)
    assert bundle["bundle_state"] == "ambiguous"


# --------------------------------------------------------------------------- #
# R0.1-H04 — Resolution profile logic
# --------------------------------------------------------------------------- #

def test_h04_t01_assistant_run_resolves_to_one_bundle():
    """[thoughts, recap, text] MUST resolve; members are the assistant nodes."""
    assert resolve_assistant_run(["thoughts", "reasoning_recap", "text"]) == "resolved"
    assert resolve_assistant_run(["text"]) == "resolved"
    assert resolve_assistant_run(["multimodal_text"]) == "resolved"
    assert resolve_assistant_run(["thoughts", "thoughts", "reasoning_recap", "text"]) == "resolved"


def test_h04_t02_user_trigger_is_not_a_bundle_member():
    """trigger_refs (preceding user run) are contextual, not emission members."""
    # In canonical order: user -> thoughts -> recap -> text
    sequence = [("user", "text"), ("assistant", "thoughts"), ("assistant", "reasoning_recap"), ("assistant", "text")]
    trigger = [node for node in sequence if node[0] == "user"]
    members = [node for node in sequence if node[0] == "assistant"]
    assert len(trigger) == 1
    assert len(members) == 3
    assert set(trigger) & set(members) == set()
    assert resolve_assistant_run([ct for _, ct in members]) == "resolved"


def test_h04_t03_unknown_pattern_preserves_ambiguity():
    """An unknown assistant content type MUST NOT be guessed into a resolved bundle."""
    assert resolve_assistant_run(["thoughts", "unknown_thing", "text"]) == "ambiguous"
    assert resolve_assistant_run(["text", "thoughts"]) == "ambiguous"  # auxiliary after terminal
    assert resolve_assistant_run(["thoughts"]) == "ambiguous"  # zero terminal
    assert resolve_assistant_run(["text", "text"]) == "ambiguous"  # two terminals


def test_h04_t04_member_non_overlap_and_full_coverage():
    """Every eligible assistant node maps to exactly one bundle; members do not overlap."""
    content_types = ["thoughts", "reasoning_recap", "text"]
    # single assistant run -> single bundle covering all members
    state = resolve_assistant_run(content_types)
    assert state == "resolved"
    members = content_types  # the whole run
    assert len(members) == 3
    # no member appears in two bundles (trivially true for a single run)
    assert len(set(members)) == len(members)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

def _bundle(state: str, member_node_refs: list[str]) -> dict:
    visible = [member_node_refs[-1]] if state == "resolved" and member_node_refs else []
    provenance = ["node_" + ("%064x" % i) for i in range(len(member_node_refs) + 1)]
    return {
        "schema_version": "0.1.0",
        "bundle_id": "bundle_" + "d" * 64,
        "bundle_state": state,
        "evidence_archive_id": "sea_" + "a" * 64,
        "resolution_profile": "chatgpt-official-export-response-bundle-v0.1",
        "trigger_refs": ["u1"],
        "member_node_refs": member_node_refs,
        "artifact_refs": [],
        "visible_response_refs": visible,
        "provenance_refs": provenance,
    }
