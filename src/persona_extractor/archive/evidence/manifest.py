"""RawSourceManifest — the byte-level provenance root (M0 contract §7).

The manifest is derived from the EXACT physical source bytes, not from a parsed
or reserialized representation. The order is normative:

    read_bytes -> SHA256(exact bytes) -> RawSourceManifest -> strict parse

This is the forensic boundary: ``source_sha256`` proves byte identity, so any
whitespace/formatting change to the file (even with identical semantic JSON)
changes the manifest hash.
"""

from __future__ import annotations

from typing import Any

from .canonical_json import sha256_hex
from .ids import source_archive_id


def build_raw_source_manifest(
    *,
    source_bytes: bytes,
    source_type: str,
    source_locator: dict[str, Any] | None,
    adapter_name: str,
    adapter_version: str,
    ingested_at: str | None = None,
) -> dict[str, Any]:
    """Build a RawSourceManifest from exact source bytes.

    ``source_sha256`` is computed over ``source_bytes`` exactly as received; the
    caller MUST NOT pre-parse or reserialize before calling this.
    """
    source_sha256 = sha256_hex(source_bytes)
    locator = source_locator or {}
    return {
        "schema_version": "0.1.0",
        "source_archive_id": source_archive_id(source_type, source_sha256),
        "source_type": source_type,
        "source_sha256": source_sha256,
        "source_locator": {
            "path": locator.get("path"),
            "uri": locator.get("uri"),
        },
        "ingested_at": ingested_at,
        "adapter": {
            "name": adapter_name,
            "version": adapter_version,
        },
    }
