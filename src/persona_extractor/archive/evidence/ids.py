"""Frozen domain-separated logical ID derivation (M0 contract §7, §8, §9, §21.1).

Every logical ID is ``prefix + SHA256_HEX(JCS({domain, payload}))`` with a frozen
domain string, so it is deterministic across runs and independent of adapter
version, ingestion time, or filesystem location.

P1 uses ``rawsrc_``, ``sea_``, and ``node_``. The remaining domains are provided
as primitives for later phases (P2+).
"""

from __future__ import annotations

from .canonical_json import jcs_hash


def _derive(prefix: str, domain: str, payload: dict) -> str:
    return prefix + jcs_hash({"domain": domain, "payload": payload})


def source_archive_id(source_type: str, source_sha256: str) -> str:
    """``rawsrc_ + SHA256_HEX(JCS({domain: RAW-SOURCE-ID-v1, ...}))`` (§7)."""
    return _derive(
        "rawsrc_",
        "RAW-SOURCE-ID-v1",
        {"source_type": source_type, "source_sha256": source_sha256},
    )


def evidence_archive_id(
    source_archive_id: str, source_unit_pointer: str, source_native_id: str
) -> str:
    """``sea_ + SHA256_HEX(JCS({domain: SEA-ID-v1, ...}))`` (§8)."""
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
    """``node_ + SHA256_HEX(JCS({domain: SEA-NODE-ID-v1, ...}))`` (§9)."""
    return _derive(
        "node_",
        "SEA-NODE-ID-v1",
        {
            "evidence_archive_id": evidence_archive_id,
            "source_node_id": source_node_id,
            "json_pointer": json_pointer,
        },
    )


# --- Primitives for later phases (not used by P1) --------------------------- #

def lineage_id(
    evidence_archive_id: str,
    resolution_profile: str,
    current_node_id: str,
    ordered_node_refs: list[str],
) -> str:
    """``lineage_ + ...`` (§11)."""
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
    """``view_ + ...`` (§11)."""
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
    """``bundle_ + ...`` (§14)."""
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


def artifact_id(
    evidence_archive_id: str,
    source_node_ref: str,
    source_artifact_pointer: str,
    artifact_profile: str,
) -> str:
    """``artifact_ + ...`` (§13.1)."""
    return _derive(
        "artifact_",
        "TYPED-ARTIFACT-ID-v1",
        {
            "evidence_archive_id": evidence_archive_id,
            "source_node_ref": source_node_ref,
            "source_artifact_pointer": source_artifact_pointer,
            "artifact_profile": artifact_profile,
        },
    )


def normalized_archive_id(
    evidence_archive_id: str,
    normalization_profile: str,
) -> str:
    """``norm_ + ...`` (§15.5)."""
    return _derive(
        "norm_",
        "NORMALIZED-ARCHIVE-ID-v1",
        {
            "evidence_archive_id": evidence_archive_id,
            "normalization_profile": normalization_profile,
        },
    )


def normalized_message_id(
    archive_id: str,
    source_evidence_ref: str,
) -> str:
    """``normmsg_ + ...`` (§15.5)."""
    return _derive(
        "normmsg_",
        "NORMALIZED-MESSAGE-ID-v1",
        {
            "archive_id": archive_id,
            "source_evidence_ref": source_evidence_ref,
        },
    )
