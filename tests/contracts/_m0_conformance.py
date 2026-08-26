"""M0 contract-conformance primitives.

These are reference implementations of the normative hash/canonicalization/ID
algorithms in the M0 Evidence Substrate contract (R0.1-FREEZE-FIX):

  - RFC 8785 JSON Canonicalization Scheme (JCS) serialization
  - SHA-256 hex digests
  - domain-separated logical ID derivation

This module lives under ``tests/contracts/`` as test infrastructure. It is NOT
the production evidence-substrate implementation and MUST NOT be imported by
``src/``. Its only purpose is to let contract tests verify the frozen vectors
and invariants machine-reproducibly.
"""

from __future__ import annotations

import hashlib
import math

# --------------------------------------------------------------------------- #
# Canonical JSON (RFC 8785 JCS)
# --------------------------------------------------------------------------- #

_ESCAPE_MAP = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
}


def _escape_string(value: str) -> str:
    """RFC 8785 string serialization: escape `"`, `\\`, and control chars."""
    out: list[str] = []
    for ch in value:
        if ch in _ESCAPE_MAP:
            out.append(_ESCAPE_MAP[ch])
        else:
            cp = ord(ch)
            if cp < 0x20:
                out.append("\\u%04x" % cp)
            else:
                out.append(ch)
    return "".join(out)


def _number_to_jcs(value: int | float) -> str:
    """Serialize a number with ECMAScript-style JSON number semantics.

    This reference covers the cases required by the contract vectors: integers
    and ordinary non-integral floats. Integral floats collapse to integer form
    (``1.0`` -> ``"1"``), matching RFC 8785 / ECMAScript, which differs from
    Python ``repr``.
    """
    if isinstance(value, bool):
        # bool is a subclass of int; guard explicitly (JSON has no bool-number).
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("NaN/Infinity cannot be canonically serialized")
        if value.is_integer():
            return str(int(value))
        return repr(value)
    raise TypeError("unsupported number type: %r" % type(value))


def canonicalize(value: object) -> str:
    """Return the RFC 8785 JCS canonical serialization of a JSON value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return _number_to_jcs(value)
    if isinstance(value, str):
        return '"' + _escape_string(value) + '"'
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(canonicalize(item) for item in value) + "]"
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda kv: kv[0])
        return "{" + ",".join(
            '"' + _escape_string(k) + '":' + canonicalize(v) for k, v in items
        ) + "}"
    raise TypeError("unsupported canonicalization type: %r" % type(value))


# --------------------------------------------------------------------------- #
# SHA-256 digests
# --------------------------------------------------------------------------- #

def sha256_hex(value: str) -> str:
    """SHA-256 over UTF-8 bytes, rendered as 64 lowercase hex characters."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def jcs_hash(value: object) -> str:
    """``SHA256_HEX(JCS(value))``."""
    return sha256_hex(canonicalize(value))


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
