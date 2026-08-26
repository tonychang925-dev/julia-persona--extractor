# ADR — M0 Evidence Substrate Reopen

**Status:** APPROVED
**Date:** 2026-08-26
**Scope:** Evidence Layer / M0 only
**Governance impact:** M3–M7 NOT REOPENED

---

## Context

The `NormalizedConversationArchive` was implicitly serving two responsibilities:

1. forensic evidence preservation (what actually happened), and
2. a cross-source convenience representation for downstream consumption.

Golden Mira's official ChatGPT export exposed that these two responsibilities cannot
be safely collapsed. The existing ChatGPT adapter silently lost source topology,
typed artifacts (exported `thoughts`, `reasoning_recap`), timestamps, modality, and
alternate branches — before downstream extraction ever ran.

This was not a failure of the evidence philosophy; the Evidence Layer
("Preserve what happened. No interpretation.") had been defined but never given a
first-class artifact.

---

## Decision

Introduce a first-class, source-preserving upstream artifact inside the existing
Evidence Layer:

```text
SourceEvidenceArchive (SEA)
```

```text
Official Source Bytes
        │ SHA-256
        ▼
RawSourceManifest
        │
        ▼
SourceEvidenceArchive
        ├── CanonicalLineageView
        ├── AlternateEvidenceView
        ├── TypedArtifactView
        └── ResponseBundleView
        │
        ▼
NormalizedConversationArchive  (derived projection)
        │
        ▼
M1+
```

- `SourceEvidenceArchive` preserves source-native evidence.
- `NormalizedConversationArchive` is a derived, cross-source convenience projection.
- Derived views MUST NOT replace or redefine source evidence.

### Explicitly rejected

```text
NormalizedArchive v0.3 = RawNodeLedger + source-native topology + typed payloads + normalization
```

Raw evidence and normalized representation remain separate artifacts.

---

## Normative invariants

```text
M0-I01  Evidence Conservation      — preserve or explicitly account for exclusion; silent loss forbidden
M0-I02  Derived View Non-Authority — derived views never replace source evidence
M0-I03  Source Topology Precedence — mapping[node].parent outranks order and timestamps
M0-I04  Typed Evidence Preservation — no destructive payload flattening
M0-I05  Deterministic Evidence Identity — no random IDs
M0-I06  Interpretation Neutrality  — M0 emits no meaning/persona/runtime claims
M0-I07  Source Payload Preservation — complete payload survives independent of adapter interpretation
M0-I08  Response Bundle Uncertainty — ambiguity explicit; no fabricated bundles
M0-I09  Explicit Exclusion Accounting — exclusions require a normative ExclusionRecord
```

Governing statement:

> RAW history ≠ normalized representation ≠ causal interpretation ≠ persona.
> Every transition across those boundaries MUST preserve provenance.

---

## R0.1 Freeze-Fix closures

```text
FF-01  ChatGPT mapping-entry admission profile v0.1   — A = every mapping entry exactly once
FF-02  Canonical lineage invalid-topology semantics    — six deterministic resolution statuses
FF-03  NormalizedArchive schema 0.3.0 MUST enforcement — traceability conditionals machine-encoded
FF-04  SEA node identifier nomenclature                — source_node_id + node_evidence_id, no bare node_id
```

---

## Consequences

- Production implementation is NOT authorized by this decision; it is gated on
  Repository Artifact Freeze Audit PASS.
- `normalized_archive.schema.json` moves to semantic version `0.3.0` (derived
  projection with mandatory upstream traceability).
- Real Golden Mira RAW MUST NOT be committed to a public repository.
