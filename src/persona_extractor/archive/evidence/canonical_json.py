"""Canonical JSON (RFC 8785), SHA-256, and strict JSON parsing.

M0 contract §10.1 requires RFC 8785 JSON Canonicalization Scheme (JCS) for all
semantic integrity hashes and ID derivations, and forbids silent last-key-wins
parsing for evidence admitted to semantic canonical hashing.

Canonicalization is delegated to the ``jcs`` package (a frozen RFC 8785
conformant implementation); we do NOT reimplement number serialization here.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import jcs


def canonical_json(value: Any) -> bytes:
    """Return the RFC 8785 JCS canonical serialization as UTF-8 bytes."""
    return jcs.canonicalize(value)


def canonical_json_str(value: Any) -> str:
    """Return the RFC 8785 JCS canonical serialization as a UTF-8 string."""
    return jcs.canonicalize(value).decode("utf-8")


def sha256_hex(data: bytes) -> str:
    """SHA-256 over exact bytes, rendered as 64 lowercase hex characters."""
    return hashlib.sha256(data).hexdigest()


def jcs_hash(value: Any) -> str:
    """``SHA256_HEX(JCS(value))`` — hash over the canonical UTF-8 bytes directly."""
    return hashlib.sha256(jcs.canonicalize(value)).hexdigest()


def parse_json_strict(raw: bytes) -> Any:
    """Parse UTF-8 JSON bytes, rejecting duplicate object member names.

    Contract §10.1: a parser used for semantic canonical hashing MUST reject
    duplicate JSON object member names (or preserve them losslessly). Python's
    default ``json.loads`` silently last-key-wins, which is forbidden here.
    """
    def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON object member: %r" % key)
            result[key] = value
        return result

    return json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicates)
