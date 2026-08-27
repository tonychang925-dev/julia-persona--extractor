"""M0-P6 end-to-end acceptance gate.

Runs the entire frozen M0 chain once from exact source bytes:

    exact bytes -> manifest -> SEA -> topology -> typed artifacts
                -> response bundles -> normalized archive

and proves three things: nothing is lost (conservation), nothing is crossed
(namespace/reference consistency), and a rerun does not drift (determinism).
P6 adds NO production semantics and NO new derived representation.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from persona_extractor.archive.adapters.chatgpt_evidence import build_chatgpt_source_evidence
from persona_extractor.archive.evidence.lineage_views import resolve_chatgpt_topology
from persona_extractor.archive.evidence.normalized_archive import build_chatgpt_normalized_archive
from persona_extractor.archive.evidence.response_bundles import build_chatgpt_response_bundles
from persona_extractor.archive.evidence.typed_artifacts import build_chatgpt_typed_artifacts

RAW_SHA = "564ef9b1aa5457b56751f550d80b0eaa24e144f8d08bd2f6b8c0ff870b8e9420"
CONVERSATION_ID = "6a754a53-82c4-83e8-b9a2-610154053181"


def _fixture_path() -> str | None:
    return os.environ.get("GOLDEN_MIRA_FIXTURE_PATH")


def _build_full_chain(raw: bytes, path: str):
    manifest, sea = build_chatgpt_source_evidence(raw, None, {"path": path, "uri": None})
    canonical, alternates = resolve_chatgpt_topology(sea)
    artifacts = build_chatgpt_typed_artifacts(sea)
    bundles = build_chatgpt_response_bundles(sea, canonical, artifacts)
    archive = build_chatgpt_normalized_archive(manifest, sea, canonical, bundles)
    return manifest, sea, canonical, alternates, artifacts, bundles, archive


def _role(node: dict) -> str | None:
    message = node["source_payload"].get("message")
    if not isinstance(message, dict):
        return None
    author = message.get("author")
    return author.get("role") if isinstance(author, dict) else None


# --------------------------------------------------------------------------- #
# E2E-01 — full chain runs and every layer matches its frozen Golden signature
# --------------------------------------------------------------------------- #

def test_e2e_full_chain_golden_signatures():
    path = _fixture_path()
    if not path:
        pytest.skip("GOLDEN_MIRA_FIXTURE_PATH not set")
    raw = Path(path).read_bytes()
    manifest, sea, canonical, alternates, artifacts, bundles, archive = _build_full_chain(raw, path)

    assert manifest["source_sha256"] == RAW_SHA
    assert sea["source_native"]["conversation_id"] == CONVERSATION_ID
    assert len(sea["nodes"]) == 4059
    assert len(canonical["node_refs"]) == 4026
    assert len(alternates) == 33
    assert len(artifacts) == 4060
    assert len(bundles) == 1508
    assert sum(1 for b in bundles if b["bundle_state"] == "resolved") == 1461
    assert sum(1 for b in bundles if b["bundle_state"] == "ambiguous") == 47
    assert len(archive["messages"]) == 4025


# --------------------------------------------------------------------------- #
# E2E-02 — conservation (nothing lost across layer boundaries)
# --------------------------------------------------------------------------- #

def test_e2e_conservation_no_loss():
    path = _fixture_path()
    if not path:
        pytest.skip("GOLDEN_MIRA_FIXTURE_PATH not set")
    raw = Path(path).read_bytes()
    manifest, sea, canonical, alternates, artifacts, bundles, archive = _build_full_chain(raw, path)

    # P1: every admitted source node is preserved, none excluded.
    acc = sea["accounting"]
    assert acc["source_node_count"] == 4059
    assert acc["preserved_node_count"] == 4059
    assert acc["excluded_node_count"] == 0

    # P2: canonical + alternate partition the full SEA exactly, no overlap.
    canonical_set = set(canonical["node_refs"])
    alt_set = {a["source_node_ref"] for a in alternates}
    all_set = {n["source_node_id"] for n in sea["nodes"]}
    assert canonical_set & alt_set == set()
    assert canonical_set | alt_set == all_set
    assert len(canonical_set) == 4026 and len(alt_set) == 33

    # P4: bundle members are exactly the canonical assistant message-bearing nodes.
    nodes_by_id = {n["source_node_id"]: n for n in sea["nodes"]}
    assistant = {ref for ref in canonical["node_refs"] if _role(nodes_by_id[ref]) == "assistant"}
    members = {m for b in bundles for m in b["member_node_refs"]}
    assert members == assistant
    assert len(members) == 2504

    # P5: 4025 messages = canonical message-bearing nodes (4026 minus the one
    # null structural root).
    message_refs = {m["provenance"]["source_id"] for m in archive["messages"]}
    message_bearing = {ref for ref in canonical["node_refs"] if isinstance(nodes_by_id[ref]["source_payload"].get("message"), dict)}
    assert message_refs == message_bearing
    assert len(message_refs) == 4025


# --------------------------------------------------------------------------- #
# E2E-03 — reference consistency (nothing crossed across layers)
# --------------------------------------------------------------------------- #

def test_e2e_reference_consistency():
    path = _fixture_path()
    if not path:
        pytest.skip("GOLDEN_MIRA_FIXTURE_PATH not set")
    raw = Path(path).read_bytes()
    manifest, sea, canonical, alternates, artifacts, bundles, archive = _build_full_chain(raw, path)

    sea_id = sea["evidence_archive_id"]
    # archive-level binding chain.
    assert manifest["source_archive_id"] == sea["source_manifest_ref"]
    assert canonical["evidence_archive_id"] == sea_id
    assert all(a["evidence_archive_id"] == sea_id for a in artifacts)
    assert all(b["evidence_archive_id"] == sea_id for b in bundles)
    assert archive["source_evidence_archive_ref"] == sea_id

    # message-level binding: lineage_ref -> canonical lineage, source_evidence_ref
    # -> a real SEA node evidence id, bundle_ref -> a real P4 bundle id.
    node_evidence_ids = {n["node_evidence_id"] for n in sea["nodes"]}
    bundle_ids = {b["bundle_id"] for b in bundles}
    for m in archive["messages"]:
        assert m["lineage_ref"] == canonical["lineage_id"]
        assert m["source_evidence_ref"] in node_evidence_ids
        if m["bundle_ref"] is not None:
            assert m["bundle_ref"] in bundle_ids


# --------------------------------------------------------------------------- #
# E2E-04 — namespace audit (each layer uses its frozen ID domain)
# --------------------------------------------------------------------------- #

def test_e2e_namespace_audit():
    path = _fixture_path()
    if not path:
        pytest.skip("GOLDEN_MIRA_FIXTURE_PATH not set")
    raw = Path(path).read_bytes()
    manifest, sea, canonical, alternates, artifacts, bundles, archive = _build_full_chain(raw, path)

    assert manifest["source_archive_id"].startswith("rawsrc_")
    assert sea["evidence_archive_id"].startswith("sea_")
    assert all(n["node_evidence_id"].startswith("node_") for n in sea["nodes"])
    assert canonical["lineage_id"].startswith("lineage_")
    assert all(a["artifact_id"].startswith("artifact_") for a in artifacts)
    assert all(b["bundle_id"].startswith("bundle_") for b in bundles)
    assert archive["archive_id"].startswith("norm_")
    assert all(m["message_id"].startswith("normmsg_") for m in archive["messages"])
    assert all(m["source_evidence_ref"].startswith("node_") for m in archive["messages"])


# --------------------------------------------------------------------------- #
# E2E-05 — full-chain determinism (rerun does not drift)
# --------------------------------------------------------------------------- #

def test_e2e_full_determinism():
    path = _fixture_path()
    if not path:
        pytest.skip("GOLDEN_MIRA_FIXTURE_PATH not set")
    raw = Path(path).read_bytes()
    first = _build_full_chain(raw, path)
    second = _build_full_chain(raw, path)
    for a, b in zip(first, second):
        assert a == b
