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
import math
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
    """Parse UTF-8 JSON bytes strictly.

    Rejects, at parse time:

    - duplicate JSON object member names (§10.1, no silent last-key-wins);
    - non-standard constants ``NaN`` / ``Infinity`` / ``-Infinity``;
    - non-finite numbers (e.g. ``1e400`` overflowing to ``inf``), which cannot be
      represented under RFC 8785/JCS and MUST take a deterministic failure path.
    """
    def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON object member: %r" % key)
            result[key] = value
        return result

    def _reject_constant(value: str) -> Any:
        raise ValueError("non-standard JSON constant: %s" % value)

    def _parse_float(value: str) -> float:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("non-finite JSON number: %s" % value)
        return result

    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicates,
        parse_constant=_reject_constant,
        parse_float=_parse_float,
    )
