"""M0 contract-conformance primitives.

Reference implementations of the normative hash/canonicalization/ID algorithms
in the M0 Evidence Substrate contract (R0.1-FREEZE-FIX):

  - RFC 8785 JSON Canonicalization Scheme (JCS) serialization
  - SHA-256 hex digests
  - domain-separated logical ID derivation

Canonical JSON serialization is delegated to the ``jcs`` package, a known RFC 8785
conformant implementation. This means number serialization follows ECMAScript
semantics (e.g. ``1e-6`` -> ``"0.000001"``, ``-0.0`` -> ``"0"``) rather than a
hand-rolled approximation of ``repr``.

This module lives under ``tests/contracts/`` as test infrastructure. It is NOT
the production evidence-substrate implementation and MUST NOT be imported by
``src/``. Its only purpose is to let contract tests verify the frozen vectors
and invariants machine-reproducibly.
"""

from __future__ import annotations

import hashlib

import jcs


def canonicalize(value: object) -> str:
    """Return the RFC 8785 JCS canonical serialization as a UTF-8 string."""
    return jcs.canonicalize(value).decode("utf-8")


# --------------------------------------------------------------------------- #
# SHA-256 digests
# --------------------------------------------------------------------------- #

def sha256_hex(value: str) -> str:
    """SHA-256 over UTF-8 bytes, rendered as 64 lowercase hex characters."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def jcs_hash(value: object) -> str:
    """``SHA256_HEX(JCS(value))`` — hash over the canonical UTF-8 bytes directly."""
    return hashlib.sha256(jcs.canonicalize(value)).hexdigest()


# --------------------------------------------------------------------------- #
# Domain-separated logical IDs (contract §7, §8, §9, §11, §14, §21.1)
# --------------------------------------------------------------------------- #

def _derive(prefix: str, domain: str, payload: dict) -> str:
    return prefix + jcs_hash({"domain": domain, "payload": payload})


def source_archive_id(source_type: str, source_sha256: str) -> str:
    """``rawsrc_ + SHA256_HEX(JCS({domain: RAW-SOURCE-ID-v1, payload: ...}))``."""
    return _derive(
        "rawsrc_",
        "RAW-SOURCE-ID-v1",
        {"source_type": source_type, "source_sha256": source_sha256},
    )


def evidence_archive_id(
    source_archive_id: str, source_unit_pointer: str, source_native_id: str
) -> str:
    """``sea_ + SHA256_HEX(JCS({domain: SEA-ID-v1, payload: ...}))``."""
    return _derive(
        "sea_",
        "SEA-ID-v1",
        {
            "source_archive_id": source_archive_id,
            "source_unit_pointer": source_unit_pointer,
            "source_native_id": source_native_id,
        },
    )


def node_evidence_id(
    evidence_archive_id: str, source_node_id: str, json_pointer: str
) -> str:
    """``node_ + SHA256_HEX(JCS({domain: SEA-NODE-ID-v1, payload: ...}))``."""
    return _derive(
        "node_",
        "SEA-NODE-ID-v1",
        {
            "evidence_archive_id": evidence_archive_id,
            "source_node_id": source_node_id,
            "json_pointer": json_pointer,
        },
    )


def lineage_id(
    evidence_archive_id: str,
    resolution_profile: str,
    current_node_id: str,
    ordered_node_refs: list[str],
) -> str:
    """``lineage_ + SHA256_HEX(JCS({domain: LINEAGE-ID-v1, payload: ...}))``."""
    return _derive(
        "lineage_",
        "LINEAGE-ID-v1",
        {
            "evidence_archive_id": evidence_archive_id,
            "resolution_profile": resolution_profile,
            "current_node_id": current_node_id,
            "ordered_node_refs": ordered_node_refs,
        },
    )


def view_id(
    evidence_archive_id: str,
    view_type: str,
    view_profile: str,
    ordered_source_refs: list[str],
) -> str:
    """``view_ + SHA256_HEX(JCS({domain: VIEW-ID-v1, payload: ...}))``."""
    return _derive(
        "view_",
        "VIEW-ID-v1",
        {
            "evidence_archive_id": evidence_archive_id,
            "view_type": view_type,
            "view_profile": view_profile,
            "ordered_source_refs": ordered_source_refs,
        },
    )


def bundle_id(
    evidence_archive_id: str,
    resolution_profile: str,
    bundle_state: str,
    ordered_member_node_refs: list[str],
) -> str:
    """``bundle_ + SHA256_HEX(JCS({domain: BUNDLE-ID-v1, payload: ...}))``."""
    return _derive(
        "bundle_",
        "BUNDLE-ID-v1",
        {
            "evidence_archive_id": evidence_archive_id,
            "resolution_profile": resolution_profile,
            "bundle_state": bundle_state,
            "ordered_member_node_refs": ordered_member_node_refs,
        },
    )


def canonical_node_hash(source_payload: dict) -> str:
    """``SHA256_HEX(JCS(source_payload))`` — semantic node integrity, not raw bytes."""
    return jcs_hash(source_payload)
