"""M0 source-evidence ingestion primitives.

This package implements the lossless evidence substrate (SourceEvidenceArchive)
from the frozen M0 contract. It preserves source-native evidence BEFORE any
normalization, causal interpretation, or persona extraction.

Modules:
- canonical_json: RFC 8785 JCS + SHA-256 + duplicate-key-rejecting parser
- ids: frozen domain-separated logical IDs
- manifest: RawSourceManifest (byte-level provenance root)
- sea: SourceEvidenceArchive envelope + accounting
"""
