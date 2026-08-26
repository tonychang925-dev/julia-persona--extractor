# M0 Evidence Substrate Contract

**Document Status:** Contract Freeze Candidate — R0.1-FREEZE-FIX  
**Contract Revision:** R0.1 Freeze Precision Fix  
**Contract Package:** M0 Evidence Substrate  
**Artifact:** `M0_EVIDENCE_SUBSTRATE_CONTRACT.md`  
**Production Implementation:** NOT AUTHORIZED  
**Scope:** Evidence Layer / M0 only  
**Governance Impact:** M3–M7 NOT REOPENED

**R0.1-FREEZE-FIX Scope (and only this scope):**

```text
FF-01  ChatGPT mapping-entry admission profile
FF-02  Canonical lineage invalid-topology semantics
FF-03  NormalizedArchive schema 0.3.0 MUST enforcement
FF-04  Node identifier nomenclature cleanup
```

R0.1-FREEZE-FIX MUST NOT introduce M2 detector design, M3 longitudinal modules, FormationPath changes, production implementation, or Golden persona extraction.

---

## 1. Purpose

This contract defines the lossless evidence substrate for Julia Persona Extractor.

Its purpose is to ensure that source-native historical evidence is preserved before normalization, segmentation, causal interpretation, persona formation, governance, or runtime use.

The governing principle is:

> **Meaning can evolve. Evidence cannot disappear.**

Golden Mira's official ChatGPT export exposed a P0 gap in the existing ingestion path: source topology, typed artifacts, timestamps, modality, branches, and exported reasoning artifacts may be lost before downstream extraction begins.

This contract reopens the M0 evidence substrate while preserving the existing governance architecture.

---

## 2. Architecture Decision

### 2.1 Decision

Introduce a first-class upstream evidence artifact:

```text
SourceEvidenceArchive
```

abbreviated:

```text
SEA
```

The SEA lives inside the existing Evidence Layer.

```text
Official Source Bytes
        │
        │ SHA-256
        ▼
RawSourceManifest
        │
        ▼
SourceEvidenceArchive
        │
        ├── CanonicalLineageView
        ├── AlternateEvidenceView
        ├── TypedArtifactView
        └── ResponseBundleView
        │
        ▼
NormalizedConversationArchive
        │
        ▼
M1 Event Segmentation
```

`SourceEvidenceArchive` preserves source-native evidence.

`NormalizedConversationArchive` is a derived, cross-source convenience projection.

Derived views MUST NOT replace or redefine source evidence.

### 2.2 Explicit rejection

The following design is rejected:

```text
NormalizedArchive v0.3
=
RawNodeLedger
+
source-native topology
+
typed raw payloads
+
cross-source normalization
```

Raw evidence and normalized representation MUST remain separate artifacts with separate responsibilities.

---

## 3. Scope

### 3.1 Reopened

This contract reopens:

- Evidence Layer artifact model
- raw source integrity
- ChatGPT official-export adapter contract
- topology preservation
- canonical / alternate lineage reconstruction
- typed artifact preservation
- deterministic provenance
- ResponseBundle reconstruction
- NormalizedArchive projection semantics
- M0 → M1 structural handoff

### 3.2 Amendment only

M1:

- ResponseBundle atomicity requirement

M2:

- future additive observable-signal support for CJK lexical evidence, modality changes, and exported decision-trace presence

These extensions MUST preserve:

```text
observable signal ≠ meaning
```

### 3.3 Not reopened

This contract does NOT reopen:

- M3 causal interpretation authority
- M3 validation boundary
- FormationPath semantics
- M4 Persona Package governance
- M5 Core Governance
- M6 Runtime / Identity separation
- M7 Evolution re-entry

### 3.4 Open question

The relationship between:

```text
FormationPath
↔
longitudinal corroboration / reinforcement / revision
```

remains an OPEN QUESTION.

No new `M3.5` module or numbering is authorized by this contract.

---

## 4. Terminology

### 4.1 Physical Source

The exact source file bytes admitted for ingestion.

Example:

```text
conversations-001.json
```

A physical source may contain multiple logical conversations or evidence units.

### 4.2 Evidence Unit

A logical source-native unit inside a physical source.

Example:

```text
unit_type: conversation
source_native_id:
6a754a53-82c4-83e8-b9a2-610154053181
```

### 4.2.1 ChatGPT Mapping Entry Admission Profile v0.1

Profile identifier:

```text
chatgpt-official-export-mapping-entry-admission-v0.1
```

For a ChatGPT official-export conversation evidence unit, the declared admission domain is normative:

```text
A
=
every key/value entry in source_native.mapping
exactly once
```

For each:

```text
mapping[source_node_id] = source_node
```

the adapter MUST construct exactly one deterministic admitted source-object reference.

The following entries MUST be admitted:

```text
message = null
unknown / unsupported content_type
alternate-branch node
empty textual content
non-visible artifact
unrecognized metadata
```

None of the above is a valid reason to omit an entry from `A`.

The admitted set MUST be constructed before preservation/exclusion accounting is evaluated.

An implementation MUST NOT narrow the admission domain to only:

```text
message-bearing nodes
visible messages
recognized content types
canonical-lineage nodes
non-empty text
```

For this profile:

```text
admitted_object_count
=
len(source_native.mapping)
```

For Golden Mira:

```text
admitted_object_count = 4059
```

This profile closes the Evidence Conservation escape hatch in which an implementation could shrink `A` before applying `P ∪ E = A`.

### 4.3 RawSourceManifest

An immutable manifest describing the physical source artifact and its byte-level integrity.

### 4.4 SourceEvidenceArchive

A source-preserving evidence envelope for one evidence unit.

It preserves:

- all admitted source-native objects
- source topology
- source-native typed payloads
- source identifiers
- timestamps
- structural metadata
- provenance

It MUST NOT perform causal, persona, identity, or runtime interpretation.

### 4.5 Structural View

A deterministic artifact derived from SEA evidence.

Structural views include:

- `CanonicalLineageView`
- `AlternateEvidenceView`
- `TypedArtifactView`
- `ResponseBundleView`

### 4.6 NormalizedConversationArchive

A cross-source convenience projection.

It is optimized for downstream consumption, not forensic evidence preservation.

### 4.7 ResponseBundle

A deterministic structural grouping of exported/source-visible artifacts that belong to one response emission episode.

A ResponseBundle is structural evidence only.

It does NOT assert why the response occurred or what it means.

---

## 5. Evidence Fidelity Order

The following ordering expresses **evidence fidelity**, not governance hierarchy:

```text
Official Source Bytes
        >
SourceEvidenceArchive
        >
Derived Structural Views
        >
NormalizedConversationArchive
```

Runtime or identity authority is NOT implied by this ordering.

---

# 6. Normative Invariants

## M0-I01 — Evidence Conservation

For every source-native evidence object within the declared ingestion domain, the Evidence Layer MUST either:

1. preserve it; or
2. explicitly account for its exclusion.

Silent loss is forbidden.

For Golden Mira:

```text
4059 source mapping nodes
        ↓
4059 accounted nodes

silent node loss = 0
```

Structural/root nodes with `message = null` MUST also be accounted for.

Evidence Conservation includes both:

```text
Object Conservation
+
Payload Fidelity
```

For ChatGPT official-export conversation evidence units, `A` MUST be constructed exactly according to:

```text
chatgpt-official-export-mapping-entry-admission-v0.1
```

The preservation/exclusion implementation MUST NOT redefine or narrow the admission domain.

A node-count match alone is insufficient if fields or typed payloads were silently lost.

---

## M0-I02 — Derived View Non-Authority

The following artifacts are derived views:

```text
CanonicalLineageView
AlternateEvidenceView
TypedArtifactView
ResponseBundleView
NormalizedConversationArchive
```

They MUST NOT replace, redefine, or overwrite their upstream `SourceEvidenceArchive`.

Any downstream object MUST remain traceable to SEA evidence.

---

## M0-I03 — Source Topology Precedence

For lineage reconstruction:

> **Source-native topology MUST take precedence over insertion order, presentation order, and timestamps.**

For ChatGPT official export:

```text
Topology resolution source:
    mapping[node_id].parent

Active lineage selector:
    current_node
```

The following MUST NOT be used as canonical topology reconstruction authority:

```text
mapping insertion order
timestamp sort
metadata.parent_id
source_analysis_msg_id
```

`metadata.parent_id` and `source_analysis_msg_id` MAY be preserved as opaque source metadata or internal references.

They MUST NOT override `mapping[node_id].parent`.

---

## M0-I04 — Typed Evidence Preservation

Source-native typed payloads MUST NOT be flattened in a way that destroys type, structure, or fields.

Examples include:

```text
text
multimodal_text
audio_transcription
image_asset_pointer
thoughts
reasoning_recap
```

The following is prohibited when it causes structural information loss:

```python
str(payload)
```

Typed payloads MUST remain recoverable as typed data.

---

## M0-I05 — Deterministic Evidence Identity

All evidence identities and integrity hashes MUST be reproducible under the algorithms frozen by this contract.

Evidence identity MUST NOT depend on:

```python
uuid.uuid4()
```

or any other random, process-local, machine-local, path-local, or wall-clock value unless that value is explicitly part of the source-native evidence identity.

`ingested_at` is issuance metadata and MUST NOT alter logical evidence identity.

All logical IDs defined by this contract MUST use:

```text
ID(domain, payload)
=
prefix(domain)
+
lowercase_hex(
  SHA-256(
    UTF-8(
      RFC8785_JCS({
        "domain": domain,
        "payload": payload
      })
    )
  )
)
```

The SHA-256 digest MUST be the complete 256-bit digest represented as exactly 64 lowercase hexadecimal characters. Digest truncation is forbidden.

Domain strings MUST be explicit and versioned. R0.1 freezes:

```text
RAW-SOURCE-ID-v1
SEA-ID-v1
SEA-NODE-ID-v1
LINEAGE-ID-v1
VIEW-ID-v1
TYPED-ARTIFACT-ID-v1
BUNDLE-ID-v1
```

Two logically different artifact classes MUST NOT reuse the same ID domain.

---

## M0-I06 — Interpretation Neutrality

SEA and its structural views MUST NOT emit interpretation-domain or runtime-authority claims.

Forbidden fields or equivalent claims include:

```text
meaning
persona_truth
identity_change
relationship_delta
behavioral_consequence
causal_claim
runtime_eligibility
activation_weight
governance_status
identity_authority_granted
```

M0 preserves evidence.

It does not decide what the evidence means.

---

## M0-I07 — Source Payload Preservation

The complete parsed source-native payload for every admitted evidence object MUST remain recoverable independently from the adapter's interpreted projection.

Adapter understanding may be incomplete.

Evidence preservation MUST NOT therefore become incomplete.

Recommended node model:

```json
{
  "source_node_id": "...",
  "node_evidence_id": "...",
  "source_payload": {},
  "structural_projection": {},
  "provenance": {}
}
```

If a future source version introduces unknown fields, those fields MUST remain preserved in `source_payload` even if the adapter does not yet interpret them.

---

## M0-I08 — Response Bundle Uncertainty

The ResponseBundle builder MUST represent uncertainty explicitly.

It MUST NOT fabricate a resolved bundle when structural evidence is insufficient.

Permitted bundle states:

```text
resolved
ambiguous
unbundled
```

Rules:

```text
resolved
→ downstream segmentation MUST preserve atomicity

ambiguous
→ ambiguity MUST be recorded
→ no forced association is permitted

unbundled
→ source artifacts remain preserved and traceable
```

No bundle is preferable to a fabricated bundle.

---

## M0-I09 — Explicit Exclusion Accounting

An object is explicitly accounted for as excluded only if an `ExclusionRecord` exists and satisfies the exclusion contract in §10.5.

For every declared admission domain:

```text
preserved_refs ∪ excluded_refs = admitted_refs
preserved_refs ∩ excluded_refs = ∅
```

All three sets MUST contain unique deterministic source-object references.

Therefore:

```text
preserved_object_count + excluded_object_count = admitted_object_count
```

An implementation MUST NOT classify the following as valid exclusion reasons when the object is inside the declared ChatGPT mapping-entry ingestion domain:

```text
unknown content type
unsupported content type
message = null
empty textual content
alternate branch membership
non-visible artifact
unrecognized metadata field
```

Those objects MUST remain preserved as source evidence.

For the Golden Mira strict acceptance profile:

```text
excluded mapping nodes = 0
```

---

# 7. RawSourceManifest Contract

`RawSourceManifest` describes one physical source artifact.

It is the byte-level provenance root.

```json
{
  "schema_version": "0.1.0",
  "source_archive_id": "...",
  "source_type": "chatgpt_official_export",
  "source_sha256": "...",
  "source_locator": {
    "path": "conversations-001.json",
    "uri": null
  },
  "ingested_at": "...",
  "adapter": {
    "name": "chatgpt_official_export",
    "version": "..."
  }
}
```

`source_archive_id` MUST be derived exactly as:

```text
source_archive_id
=
"rawsrc_" +
SHA256_HEX(
  JCS({
    "domain": "RAW-SOURCE-ID-v1",
    "payload": {
      "source_type": source_type,
      "source_sha256": source_sha256
    }
  })
)
```

where `SHA256_HEX(JCS(x))` means SHA-256 over the UTF-8 bytes of RFC 8785 canonical JSON serialization, rendered as 64 lowercase hexadecimal characters.

`source_locator.path`, `source_locator.uri`, and `ingested_at` MUST NOT participate in logical source identity.

Moving the same bytes to a different filesystem path MUST NOT change `source_archive_id`.

---

# 8. SourceEvidenceArchive Contract

`SourceEvidenceArchive` represents one evidence unit inside a physical source.

```json
{
  "schema_version": "0.1.0",

  "evidence_archive_id": "...",

  "source_manifest_ref": "...",

  "source_unit": {
    "unit_type": "conversation",
    "source_native_id": "6a754a53-82c4-83e8-b9a2-610154053181",
    "source_pointer": "/<conversation-index>"
  },

  "source_native": {
    "source_type": "chatgpt_official_export",
    "conversation_id": "6a754a53-82c4-83e8-b9a2-610154053181",
    "current_node": "...",
    "title": "Hi Mira"
  },

  "nodes": [],

  "accounting": {
    "source_node_count": 0,
    "preserved_node_count": 0,
    "excluded_node_count": 0,
    "exclusions": []
  }
}
```

`evidence_archive_id` MUST remain stable across adapter upgrades when the underlying physical source and logical evidence unit are the same.

It MUST be derived exactly as:

```text
evidence_archive_id
=
"sea_" +
SHA256_HEX(
  JCS({
    "domain": "SEA-ID-v1",
    "payload": {
      "source_archive_id": source_archive_id,
      "source_unit_pointer": source_unit.source_pointer,
      "source_native_id": source_unit.source_native_id
    }
  })
)
```

Adapter version MUST be recorded in issuance/build provenance.

Adapter version MUST NOT alter the logical identity of the evidence unit.

Changing adapter logic MAY change a generated SEA artifact hash, but MUST NOT change `evidence_archive_id` for the same physical source and same logical source unit.

---

# 9. SEA Node Contract

Each admitted source node MUST be preserved.

```json
{
  "source_node_id": "...",
  "node_evidence_id": "...",

  "source_payload": {
    "...": "complete parsed source-native node"
  },

  "structural_projection": {
    "parent_node_id": "...",
    "message_id": "...",
    "role": "...",
    "create_time_raw": null,
    "content_type": "..."
  },

  "provenance": {
    "source_archive_ref": "...",
    "source_sha256": "...",
    "json_pointer": "/mapping/<node_id>",
    "source_node_id": "...",
    "canonical_node_hash": "..."
  }
}
```

`source_payload` MUST remain independently recoverable.

Identifier semantics are normative:

```text
source_node_id
=
the exact source-native key used by the ChatGPT mapping object

node_evidence_id
=
the deterministic SEA logical evidence identifier for that admitted source node
```

The bare field name:

```text
node_id
```

MUST NOT appear in SEA node schema or normative examples because it is ambiguous between source-native identity and SEA evidence identity.

Each node MUST have a deterministic `node_evidence_id` derived as:

```text
node_evidence_id
=
"node_" +
SHA256_HEX(
  JCS({
    "domain": "SEA-NODE-ID-v1",
    "payload": {
      "evidence_archive_id": evidence_archive_id,
      "source_node_id": source_node_id,
      "json_pointer": provenance.json_pointer
    }
  })
)
```

The adapter MAY populate `structural_projection`.

The adapter MUST NOT silently discard unrecognized source fields.

---

# 10. Hash, Canonicalization, ID, and Exclusion Model

## 10.1 Canonical JSON serialization

All semantic integrity hashes and all deterministic ID derivations in this contract MUST use:

```text
JSON Canonicalization Scheme
RFC 8785 (JCS)
```

Normative serialization rules:

```text
serialization standard  = RFC 8785 JCS
text encoding           = UTF-8
byte order mark         = forbidden
hash algorithm          = SHA-256
digest representation   = 64 lowercase hexadecimal characters
digest truncation       = forbidden
```

Implementations MUST use an RFC 8785-conformant canonicalizer. A language-runtime default serializer such as Python `json.dumps`, JavaScript `JSON.stringify`, or Rust `serde_json` MUST NOT be treated as canonical merely because its output is locally deterministic.

Canonicalization operates on the parsed semantic JSON value. It does not replace the exact source bytes as forensic authority.

### Canonicalization failure

If a value cannot be represented under the canonicalization contract, the implementation MUST:

1. preserve the original source bytes through `source_sha256`;
2. preserve or explicitly account for the affected evidence object;
3. emit a deterministic canonicalization error record;
4. MUST NOT silently substitute a non-conforming serializer.

A parser used for semantic canonical hashing MUST reject duplicate JSON object member names or otherwise preserve them losslessly. Silent last-key-wins parsing is forbidden for evidence admitted to semantic canonical hashing.

### Cross-language conformance vector

Input semantic JSON:

```json
{
  "b": 2,
  "a": "Mira",
  "u": "老婆",
  "n": null,
  "t": true,
  "f": 1.5
}
```

RFC 8785 canonical serialization:

```text
{"a":"Mira","b":2,"f":1.5,"n":null,"t":true,"u":"老婆"}
```

UTF-8 SHA-256:

```text
9bf951a35a0e40688ff03e7b8c1757e5b9c76a301f5dce8709dddc64956ea7cc
```

Every conforming implementation MUST reproduce this vector exactly.

## 10.2 `source_sha256`

```text
whole-file byte integrity
```

`source_sha256` is calculated directly over the exact physical source bytes:

```text
source_sha256 = SHA256_HEX(exact_source_bytes)
```

No parsing, normalization, newline conversion, Unicode conversion, or reserialization is permitted before this hash.

## 10.3 `json_pointer`

```text
structural locator within that exact source
```

For ChatGPT mapping entries:

```text
/<conversation-index>/mapping/<escaped-node-id>
```

when the physical source is a top-level conversation array.

For an already extracted single-conversation evidence unit:

```text
/mapping/<escaped-node-id>
```

JSON Pointer escaping MUST follow RFC 6901.

The exact pointer profile MUST be recorded with the source-unit locator so that the same object is reproducibly addressable within the exact source bytes identified by `source_sha256`.

## 10.4 `canonical_node_hash`

```text
canonical_node_hash
=
SHA256_HEX(
  JCS(source_payload)
)
```

`canonical_node_hash` proves deterministic semantic integrity of the parsed source-native node payload.

It is NOT a raw-byte node hash.

The name:

```text
raw_node_sha256
```

MUST NOT be used unless exact source byte ranges are preserved.

## 10.5 ExclusionRecord

An exclusion is valid only when represented by:

```json
{
  "source_object_ref": "node_...",
  "json_pointer": "...",
  "canonical_object_hash": "...",
  "exclusion_reason_code": "...",
  "exclusion_rule_id": "...",
  "exclusion_rule_version": "...",
  "adapter": {
    "name": "...",
    "version": "..."
  },
  "detail": null
}
```

Required invariants:

```text
source_object_ref       MUST be deterministic
json_pointer            MUST identify the exact admitted source object
canonical_object_hash   MUST equal SHA256_HEX(JCS(parsed source object))
exclusion_reason_code   MUST come from the contract/profile allow-list
exclusion_rule_id       MUST identify the normative rule permitting exclusion
adapter.name            MUST be present
adapter.version         MUST be present
```

An implementation MUST NOT invent ad-hoc free-text exclusions as a substitute for a normative reason code.

For the ChatGPT official-export mapping-entry admission profile, unknown or unsupported source object structure is NOT a valid reason for evidence exclusion because the complete `source_payload` is required to survive independently from adapter interpretation.

### 10.5.1 Frozen exclusion-reason allow-list (precision amendment)

The `exclusion_reason_code` allow-list is frozen per profile. For the
ChatGPT mapping-entry admission profile (`chatgpt-official-export-mapping-entry-admission-v0.1`):

```text
ALLOWED_EXCLUSION_REASONS = ∅
```

Every mapping entry MUST be admitted (§4.2.1), so no exclusion reason is valid
for this profile. A different admission profile MAY freeze its own non-empty
allow-list. An `exclusion_reason_code` not present in the profile's allow-list is
contract-invalid.

## 10.6 Accounting invariants

For every declared admission domain:

```text
A = set(admitted source-object refs)
P = set(preserved source-object refs)
E = set(excluded source-object refs)
```

For ChatGPT official-export conversation evidence units:

```text
A MUST equal the exact set produced by
chatgpt-official-export-mapping-entry-admission-v0.1
```

No downstream adapter stage may redefine `A`.

The following MUST all hold:

```text
P ∪ E = A
P ∩ E = ∅
|P| + |E| = |A|
len(P) = preserved_object_count
len(E) = excluded_object_count
len(A) = admitted_object_count
```

Duplicate references are forbidden.

Every member of `E` MUST have exactly one `ExclusionRecord`.

Every member of `P` MUST resolve to preserved SEA evidence.

## 10.7 Derived artifact integrity hashes

When a generated evidence artifact includes its own integrity hash, that hash MUST be:

```text
SHA256_HEX(
  JCS(artifact_without_its_own_integrity_hash_field)
)
```

The exact omitted self-hash field MUST be defined by that artifact schema.

## 10.8 Optional future forensic fields

A future byte-preserving parser MAY add:

```text
byte_start
byte_end
```

Only then may node-level raw-byte identity be claimed.

---

# 11. CanonicalLineageView Contract

For ChatGPT official export:

```text
current_node
    ↓
mapping[node].parent
    ↓
parent
    ↓
...
root
```

defines the source-native active lineage.

`current_node` is:

> the source-native active-lineage selector for this export

It is NOT:

- Persona Authority
- governance authority
- identity authority
- truth authority

```json
{
  "lineage_id": "...",
  "evidence_archive_id": "...",
  "resolution_method": "source_native_parent_ancestry",
  "current_node_id": "...",
  "node_refs": []
}
```

The ordering MUST be deterministic.

Normative ordering (precision amendment):

```text
CanonicalLineageView.node_refs        MUST be ordered root → current
Failure-record visited_node_refs      MUST preserve traversal order current → root
```

`node_refs` uses root → current so that downstream consumers (NormalizedArchive,
ResponseBundle, M1 segmentation) receive conversational forward order. Failure
diagnostics preserve traversal order for reproducible defect classification.

`lineage_id` MUST be derived as:

```text
lineage_id
=
"lineage_" +
SHA256_HEX(
  JCS({
    "domain": "LINEAGE-ID-v1",
    "payload": {
      "evidence_archive_id": evidence_archive_id,
      "resolution_profile": resolution_profile,
      "current_node_id": current_node_id,
      "ordered_node_refs": node_refs
    }
  })
)
```

A generic structural view artifact ID MUST use:

```text
view_id
=
"view_" +
SHA256_HEX(
  JCS({
    "domain": "VIEW-ID-v1",
    "payload": {
      "evidence_archive_id": evidence_archive_id,
      "view_type": view_type,
      "view_profile": view_profile,
      "ordered_source_refs": ordered_source_refs
    }
  })
)
```

View profile/version participates in derived-view identity because changing the deterministic derivation rule creates a different derived artifact.


## 11.3 Canonical Lineage Resolution Status

Every canonical-lineage resolution attempt MUST emit exactly one deterministic status from:

```text
resolved
invalid_missing_current_node
invalid_current_node_not_in_mapping
invalid_missing_parent
invalid_cycle
invalid_self_parent
```

Status semantics:

### `resolved`

MAY be emitted only when all of the following hold:

```text
current_node exists
current_node resolves to an admitted mapping entry
every traversed non-root parent reference resolves
no node repeats during ancestry traversal
no node is its own parent
ancestry terminates at a root node
```

### `invalid_missing_current_node`

MUST be emitted when the source-native evidence unit does not provide a usable `current_node` selector.

### `invalid_current_node_not_in_mapping`

MUST be emitted when `current_node` is present but does not resolve to an admitted mapping entry.

### `invalid_missing_parent`

MUST be emitted when ancestry traversal encounters a non-null parent reference that does not resolve to an admitted mapping entry.

### `invalid_cycle`

MUST be emitted when ancestry traversal encounters a previously visited node.

### `invalid_self_parent`

MUST be emitted when:

```text
mapping[node].parent == node
```

`invalid_self_parent` takes precedence over the generic cycle classification for that condition.

## 11.4 Failure Semantics

For any status beginning with:

```text
invalid_
```

the implementation:

```text
MUST NOT emit a resolved CanonicalLineageView
MUST preserve all SEA evidence unchanged
MUST emit a deterministic lineage-resolution failure record
MUST preserve the exact offending source refs
MUST NOT truncate ancestry and call it resolved
MUST NOT invent a replacement parent
MUST NOT repair the topology silently
MUST NOT fall back to timestamp ordering
MUST NOT fall back to mapping insertion order
```

A failure record MUST contain at least:

```json
{
  "resolution_profile": "chatgpt-official-export-canonical-lineage-v0.1",
  "resolution_status": "invalid_missing_parent",
  "evidence_archive_id": "...",
  "current_node_id": "...",
  "offending_node_refs": [],
  "offending_parent_refs": [],
  "visited_node_refs": []
}
```

All arrays MUST preserve deterministic traversal order.

## 11.5 Resolution Precedence

If multiple malformed conditions are observable at the same traversal step, classification precedence is:

```text
invalid_missing_current_node
invalid_current_node_not_in_mapping
invalid_self_parent
invalid_missing_parent
invalid_cycle
```

Once a failure status is emitted, traversal MUST stop at the first deterministically encountered failing step.

This precedence is normative so independent implementations produce the same failure classification for the same malformed source.

## 11.6 Golden Acceptance

For Golden Mira:

```text
resolution_status = resolved
missing parent refs = 0
```

---

# 12. AlternateEvidenceView Contract

Off-active-lineage source nodes MUST remain preserved.

```json
{
  "lineage_status": "alternate",
  "active_context_membership": false,
  "historical_exposure": "unknown"
}
```

`historical_exposure = unknown` means:

- the export proves the artifact existed;
- the export does NOT prove the user read it;
- the export does NOT prove the artifact became part of the shared lived history.

---

# 13. TypedArtifactView Contract

Typed artifacts are derived structural views over SEA evidence.

```json
{
  "artifact_id": "...",
  "source_node_ref": "...",
  "source_content_type": "thoughts",
  "artifact_class": "exported_decision_trace",
  "evidence_class": "observed_export_artifact",
  "payload": {}
}
```

For `reasoning_recap`:

```json
{
  "source_content_type": "reasoning_recap",
  "artifact_class": "reasoning_execution_metadata"
}
```

`artifact_id` MUST be derived as:

```text
artifact_id
=
"artifact_" +
SHA256_HEX(
  JCS({
    "domain": "TYPED-ARTIFACT-ID-v1",
    "payload": {
      "evidence_archive_id": evidence_archive_id,
      "source_node_ref": source_node_ref,
      "source_artifact_pointer": source_artifact_pointer,
      "artifact_profile": artifact_profile
    }
  })
)
```

The following equivalences are forbidden:

```text
exported thoughts
≠ complete internal reasoning

exported thoughts
≠ causal truth

exported thoughts
≠ persona truth

exported thoughts
≠ identity evidence by themselves
```

## 13.1 Typed Artifact Addressability (precision amendment)

A TypedArtifactView MUST carry three additional required fields so that its
identity is fully recomputable from the artifact alone plus the upstream SEA:

```text
evidence_archive_id        MUST, non-empty
source_node_ref            MUST, the SEA source_node_id (source-native mapping key)
source_artifact_pointer    MUST, RFC 6901 pointer relative to source_payload
artifact_profile           MUST, const "chatgpt-official-export-typed-artifact-v0.1"
```

`source_artifact_pointer` is an RFC 6901 pointer relative to the SEA node's
`source_payload` (e.g. `/message/content`, `/message/content/parts/0`). It is NOT
a physical-source absolute pointer; SEA node provenance already locates the node
in the physical source.

`payload` MUST equal the exact parsed source-native JSON value addressed by
`source_artifact_pointer`. No wrapping, flattening, stringification, or field
projection is permitted. `payload` MAY be any JSON value (object, array, string,
number, boolean, or null).

### Multimodal leaf granularity

`multimodal_text` is a typed routing container, not a leaf artifact. It MUST NOT
produce a container-level TypedArtifactView. Instead, each `parts[i]` produces
exactly one leaf TypedArtifactView with `source_artifact_pointer` equal to
`/message/content/parts/<i>`.

If `multimodal_text.parts` is not a list, the whole content object MUST be
emitted as exactly one `unknown_typed_artifact` with pointer `/message/content`.

### source_content_type inheritance

For a scalar part (plain string, number, boolean, or null) inside `multimodal_text`,
`source_content_type` MUST inherit `multimodal_text` (no invented type). A plain
string part maps to `artifact_class = visible_text`; other scalar parts map to
`unknown_typed_artifact`.

### Classification profile

For profile `chatgpt-official-export-typed-artifact-v0.1`:

```text
message.content.content_type    artifact_class
thoughts                        exported_decision_trace
reasoning_recap                 reasoning_execution_metadata
text                            visible_text
audio_transcription             audio_transcription
image_asset_pointer             image_asset_pointer
multimodal_text                 split parts; no container artifact
any other non-empty string      unknown_typed_artifact
```

`thoughts` and `reasoning_recap` MUST each produce exactly ONE artifact with
pointer `/message/content`; they MUST NOT be decomposed into internal entries.

`evidence_class` MUST always be `observed_export_artifact`.

---

# 14. ResponseBundleView Contract

## 14.1 Generic definition

> **A ResponseBundle is a deterministic structural grouping of source-visible/exported assistant artifacts belonging to one response emission episode.**

A ResponseBundle groups response-emission members.

User trigger/context references MAY be attached to a bundle but are NOT bundle members.

Therefore:

```text
user trigger refs
    ↓ context only

[ assistant artifact
  assistant artifact
  visible assistant response ]
    ↑
ResponseBundle members
```

This distinction is normative.

The bundle MUST NOT claim:

```text
caused_by
meaning
policy
identity_effect
relationship_delta
```

## 14.2 Generic bundle states

Permitted states:

```text
resolved
ambiguous
unbundled
```

`resolved` means the source-specific resolution profile uniquely grouped the emission members.

`ambiguous` means the source-specific profile detected a candidate response emission but could not uniquely resolve membership/terminal structure.

`unbundled` means the profile explicitly determined that an eligible source artifact is not assigned to a response bundle.

No bundle is preferable to a fabricated bundle.

## 14.3 ChatGPT Official-Export ResponseBundle Resolution Profile v0.1

Profile identifier:

```text
chatgpt-official-export-response-bundle-v0.1
```

### Input domain

The resolver MUST operate only on:

```text
CanonicalLineageView
```

resolved from:

```text
current_node
+
mapping[node_id].parent ancestry
```

The resolver MUST use canonical lineage order.

It MUST NOT use:

```text
mapping insertion order
timestamp ordering
metadata.parent_id
source_analysis_msg_id
```

to establish bundle membership.

### Structural-node handling

Canonical lineage nodes with:

```text
message = null
```

remain preserved in SEA but are transparent for role-run grouping.

They MUST NOT be silently deleted from evidence accounting.

### Message-bearing sequence

The resolver constructs a logical message-bearing sequence by preserving canonical lineage order and temporarily skipping null-message structural nodes only for run-boundary computation.

### Assistant run

An `assistant_run` is the maximal contiguous sequence of message-bearing canonical-lineage nodes whose:

```text
message.author.role = "assistant"
```

A ResponseBundle candidate is derived from exactly one `assistant_run`.

Assistant nodes from different assistant runs MUST NOT be merged into one bundle.

### Trigger refs

`trigger_refs` are the maximal contiguous immediately preceding run of message-bearing nodes whose:

```text
message.author.role = "user"
```

`trigger_refs`:

```text
MAY be empty
MUST preserve canonical order
MUST NOT be included in bundle member refs
MUST NOT determine bundle atomicity
```

The distinction is mandatory:

```text
user → thoughts → recap → text
```

MUST resolve, when otherwise valid, as:

```text
trigger_refs = [user]

bundle members =
[thoughts, recap, text]
```

NOT:

```text
bundle members =
[user, thoughts, recap, text]
```

### Content classification — profile v0.1

Recognized auxiliary assistant artifact content types:

```text
thoughts
reasoning_recap
```

Recognized terminal visible assistant response content types:

```text
text
multimodal_text
```

Any assistant content type outside these sets is `unknown_for_profile_v0.1`.

Unknown content MUST be preserved in SEA.

Unknown content MUST NOT be guessed into a resolved bundle.

### Resolved condition

An assistant run is `resolved` if and only if all conditions hold:

1. the run contains exactly one recognized terminal visible response node;
2. that terminal visible response is the final message-bearing node of the assistant run;
3. every preceding assistant node in the run is a recognized auxiliary artifact;
4. the run contains no `unknown_for_profile_v0.1` content type.

Examples that MUST resolve:

```text
text

multimodal_text

reasoning_recap
→ text

thoughts
→ reasoning_recap
→ text

thoughts
→ thoughts
→ reasoning_recap
→ text
```

### Ambiguous condition

An assistant run MUST be marked `ambiguous` if any of the following holds:

```text
zero recognized terminal visible responses
more than one recognized terminal visible response
recognized auxiliary artifact appears after terminal visible response
unknown assistant content type occurs in the run
the structural pattern otherwise violates the resolved condition
```

No arbitrary tie-breaker is permitted.

### Unbundled condition

Profile v0.1 MAY emit `unbundled` only when a source-specific explicit rule classifies an eligible assistant artifact as outside any response-emission episode.

Absent such an explicit rule, unresolved assistant runs MUST be `ambiguous`, not silently `unbundled`.

### Coverage and overlap

Every eligible assistant message-bearing node on the canonical lineage MUST be accounted for by exactly one of:

```text
one resolved ResponseBundle
one ambiguous ResponseBundle candidate
one explicit unbundled record
```

Resolved/ambiguous bundle member sets MUST NOT overlap.

### Member order

Bundle member refs MUST preserve canonical lineage order.

### Bundle identity

`bundle_id` MUST be:

```text
bundle_id
=
"bundle_" +
SHA256_HEX(
  JCS({
    "domain": "BUNDLE-ID-v1",
    "payload": {
      "evidence_archive_id": evidence_archive_id,
      "resolution_profile": "chatgpt-official-export-response-bundle-v0.1",
      "bundle_state": bundle_state,
      "ordered_member_node_refs": ordered_member_node_refs
    }
  })
)
```

`trigger_refs` do not participate in `bundle_id` because they are contextual references rather than emission members.

## 14.4 Recommended schema shape

```json
{
  "bundle_id": "...",
  "bundle_state": "resolved",
  "evidence_archive_id": "...",
  "resolution_profile": "chatgpt-official-export-response-bundle-v0.1",

  "trigger_refs": [],
  "member_node_refs": [],
  "artifact_refs": [],
  "visible_response_refs": [],

  "provenance_refs": []
}
```

## 14.5 Atomicity invariant

> **Segmentation may divide experiences. It MUST NOT divide an atomic resolved ResponseBundle.**

This is the normative M0 → M1 compatibility amendment.

Ambiguous bundle candidates MUST preserve their ambiguity through downstream traceability.

---

# 15. NormalizedConversationArchive 0.3 Contract

`NormalizedConversationArchive` schema version MUST be exactly:

```text
0.3.0
```

`schemas/normalized_archive.schema.json` MUST encode:

```json
{
  "schema_version": {
    "const": "0.3.0"
  }
}
```

A `0.2.x` normalized archive MUST NOT be accepted as conforming to this R0.1-FREEZE-FIX contract.

`NormalizedConversationArchive` version `0.3.0` is:

> **a cross-source normalized projection with mandatory traceability to exact source evidence**

It is NOT the raw evidence authority.

## 15.1 Archive-level traceability

Every normalized archive MUST contain a non-null reference to the upstream SEA:

```text
source_evidence_archive_ref
```

That reference MUST resolve to exactly one `SourceEvidenceArchive`.

## 15.2 Message-level traceability

Every normalized message MUST contain:

```text
source_evidence_ref
```

`source_evidence_ref` MUST resolve to the exact SEA node/evidence object from which the normalized message was derived.

A normalized message without resolvable `source_evidence_ref` is contract-invalid.

### Lineage reference

`lineage_ref`:

```text
MUST be present and non-null
when source-lineage membership has been resolved
```

For ChatGPT official-export normalization from a valid SEA topology:

```text
lineage_ref MUST be present
```

and MUST resolve to the canonical or alternate lineage membership record used by the projection.

### Bundle traceability

For normalized assistant messages eligible under a ResponseBundle resolution profile:

```text
if bundle_state = resolved:
    bundle_ref MUST be present
    bundle_ref MUST resolve to the resolved ResponseBundle

if bundle_state = ambiguous:
    bundle_ref MUST be present
    bundle_ref MUST resolve to the ambiguity record/candidate
    ambiguity MUST NOT be converted into resolved

if bundle_state = unbundled:
    bundle_ref MAY be null
    unbundled status MUST be explicit
```

For normalized messages not eligible for ResponseBundle grouping, such as ordinary user messages:

```text
bundle_ref MAY be null
```

A resolved assistant bundle member with a missing `bundle_ref` is contract-invalid.

An ambiguous assistant bundle member with a missing ambiguity reference is contract-invalid.

## 15.2.1 Schema enforcement requirements

`schemas/normalized_archive.schema.json` MUST encode, not merely document, the following:

```text
archive.source_evidence_archive_ref
    required
    non-null
    non-empty string

message.source_evidence_ref
    required
    non-null
    non-empty string

message.lineage_ref
    required when lineage membership is resolved

message.bundle_state
    required for ResponseBundle-eligible assistant messages

message.bundle_ref
    required and non-null when bundle_state = resolved

message.bundle_ref
    required and non-null when bundle_state = ambiguous

message.bundle_ref
    may be null when bundle_state = unbundled

message.bundle_ref
    may be null for messages not eligible for ResponseBundle grouping
```

Where JSON Schema conditional keywords are used, the schema MUST use machine-enforceable `if` / `then` / `else`, `oneOf`, or equivalent Draft 2020-12 constructs.

Prose-only conditional traceability is non-conforming.

## 15.3 Required recoverability chain

The following chain MUST be machine-resolvable:

```text
Normalized Message
        ↓
source_evidence_ref
        ↓
SEA Node / Evidence Object
        ↓
json_pointer
        ↓
RawSourceManifest
        ↓
exact source_sha256
```

When lineage is resolved:

```text
Normalized Message
        ↓
lineage_ref
        ↓
CanonicalLineageView or AlternateEvidenceView
        ↓
SEA
```

When bundle association is resolved or ambiguous:

```text
Normalized Assistant Message
        ↓
bundle_ref
        ↓
Resolved/Ambiguous ResponseBundle record
        ↓
member node refs
        ↓
SEA
```

## 15.4 Projection MUST NOT destroy upstream fidelity

Normalized content MAY be simplified for cross-source consumption.

Such simplification MUST NOT overwrite or mutate SEA.

Any information omitted from the normalized projection MUST remain recoverable from `source_evidence_ref`.

---

# 16. M1 Compatibility Amendment

M1 remains an evidence-structuring phase.

M1 MUST NOT gain causal, persona, identity, or runtime-authority semantics.

For every:

```text
bundle_state = resolved
```

M1 segmentation MUST NOT emit a boundary inside that bundle.

For:

```text
bundle_state = ambiguous
```

M1 MUST NOT silently reinterpret the bundle as resolved.

M1 outputs referencing artifacts covered by an ambiguous bundle candidate MUST preserve a traceable reference to that ambiguity record.

---

# 17. M2 Compatibility Direction

M2 remains:

> Rank evidence for review. Do not interpret evidence.

Future additive observable detectors MAY include:

```text
CJK lexical recurrence
modality shift
exported decision-trace presence
model route shift
response pattern shift
explicit recall-marker presence
explicit commitment-marker presence
```

These detectors MAY increase observation recall.

They MUST NOT emit meaning, persona, identity, causal, or runtime claims.

---

# 18. Golden Mira Private Acceptance Profile

Golden Mira official ChatGPT export is the first high-complexity private M0 acceptance fixture.

It is an evidence-conservation benchmark.

It is NOT a persona benchmark.

```text
SOURCE

mapping nodes                  4059
admitted mapping entries       4059
message nodes                  4058


TOPOLOGY

resolution_status          resolved
canonical active lineage       4026
alternate nodes                  33
branch points                    10
missing parent refs               0


CONTENT

text                           1684
multimodal_text                1365
thoughts                        154
reasoning_recap                 855


LOSS

silent object loss                0
source-payload loss               0
branch loss                       0
typed-artifact loss               0
timestamp loss                    0
source-id loss                    0
```

The private benchmark MUST verify structural fidelity only.

It MUST NOT assert:

- Mira personality
- relationship meaning
- identity change
- L4 significance
- causal interpretation
- Persona Package eligibility

---

# 19. Required Contract Tests

```text
M0-SEA-T01  Whole Source Integrity
M0-SEA-T02  Evidence Conservation
M0-SEA-T03  Parent Topology Fidelity
M0-SEA-T04  Canonical Lineage Determinism
M0-SEA-T05  Alternate Branch Preservation
M0-SEA-T06  Typed Artifact Preservation
M0-SEA-T07  Timestamp / Modality Preservation
M0-SEA-T08  Deterministic Provenance
M0-SEA-T09  Derived View Non-Authority
M0-SEA-T10  Response Bundle Reconstruction
M0-SEA-T11  Response Bundle Atomicity
M0-SEA-T12  Normalized Projection Traceability
M0-SEA-T13  Source Payload Preservation
M0-SEA-T14  Bundle Ambiguity Preservation

R0.1-H01-T01  RFC 8785 Canonicalization Conformance Vector
R0.1-H01-T02  Canonical Node Hash Cross-Implementation Equality
R0.1-H02-T01  ID Domain Separation
R0.1-H02-T02  Logical ID Stability Across Adapter Upgrade
R0.1-H03-T01  Admission = Preserved ∪ Excluded
R0.1-H03-T02  Preserved ∩ Excluded = Empty
R0.1-H03-T03  Every Exclusion Has One Normative ExclusionRecord
R0.1-H04-T01  ChatGPT Assistant-Run Bundle Resolution
R0.1-H04-T02  User Trigger Is Not Bundle Member
R0.1-H04-T03  Unknown Pattern Preserves Ambiguity
R0.1-H04-T04  Bundle Member Non-Overlap / Full Assistant Coverage
R0.1-H05-T01  source_evidence_ref Is Mandatory
R0.1-H05-T02  Resolved/Ambiguous Bundle Traceability Is Mandatory

FREEZE-FIX-FF01-T01  ChatGPT Admission Set Equals Every Mapping Entry Exactly Once
FREEZE-FIX-FF01-T02  Null / Unknown / Alternate / Empty Mapping Entries Are Admitted
FREEZE-FIX-FF02-T01  Missing Current Node Produces Deterministic Invalid Status
FREEZE-FIX-FF02-T02  Current Node Outside Mapping Produces Deterministic Invalid Status
FREEZE-FIX-FF02-T03  Missing Parent Produces Deterministic Invalid Status
FREEZE-FIX-FF02-T04  Cycle / Self-Parent Never Produces Resolved Lineage
FREEZE-FIX-FF03-T01  Normalized Schema Const Is 0.3.0
FREEZE-FIX-FF03-T02  Normalized Schema Machine-Enforces Traceability Conditionals
FREEZE-FIX-FF04-T01  SEA Node Uses source_node_id + node_evidence_id, Never Bare node_id
```

R0.1 freeze MUST NOT be granted if any H01–H05 test remains non-normative, implementation-dependent, or permits silent fallback.

---

# 20. Public / Private Benchmark Boundary

The real Golden Mira RAW MUST NOT be committed to a public repository.

Public benchmark namespace MAY contain:

```text
benchmarks/golden_mira/
├── README.md
├── expected_manifest.json
├── expected_counts.json
├── redacted_anchor_manifest.json
└── synthetic_topology_fixture.json
```

Private test execution MAY use:

```text
GOLDEN_MIRA_FIXTURE_PATH
```

Public fixtures MUST NOT contain private conversation text, voice transcription content, or sensitive relationship history.

---

# 21. Evidence Identity vs Artifact Integrity

Logical evidence identities are domain-separated and deterministic.

## 21.1 Frozen logical ID algorithms

```text
source_archive_id   → RAW-SOURCE-ID-v1
evidence_archive_id → SEA-ID-v1
node_evidence_id    → SEA-NODE-ID-v1
lineage_id          → LINEAGE-ID-v1
generic view_id     → VIEW-ID-v1
typed artifact_id   → TYPED-ARTIFACT-ID-v1
bundle_id           → BUNDLE-ID-v1
```

Every logical ID MUST use the exact R0.1 `ID(domain, payload)` construction and MUST retain the full 256-bit SHA-256 digest.

## 21.2 Identity stability rule

Physical source relocation MUST NOT change `source_archive_id`.

Adapter upgrade MUST NOT change:

```text
source_archive_id
evidence_archive_id
node_evidence_id
```

for the same exact source and logical evidence unit.

A change to a derived-view resolution/profile version MAY intentionally change:

```text
lineage_id
view_id
artifact_id
bundle_id
```

because the derived artifact definition changed.

## 21.3 Artifact integrity

Integrity hashes are separate from logical IDs:

```text
source_sha256
canonical_node_hash
SEA artifact hash
derived-view artifact hashes
```

An adapter upgrade MAY change generated artifact hashes while preserving the logical identity of the underlying source/evidence unit.

---

# 22. Non-Goals

M0 MUST NOT:

- infer personality
- infer identity
- infer relationship meaning
- infer behavioral consequences
- validate causal claims
- build Persona Package truth
- grant runtime eligibility
- set activation weight
- grant governance authority

M0 answers:

```text
What source evidence existed?
Where was it?
How was it structured?
How is it preserved?
How can every derived object trace back to it?
```

M0 does NOT answer:

```text
What does this mean?
Why did this happen?
Did this define identity?
Should this influence runtime?
```

---

# 23. Contract Package

```text
docs/
├── M0_EVIDENCE_SUBSTRATE_ARCHITECTURE_DECISION.md
└── M0_EVIDENCE_SUBSTRATE_CONTRACT.md

schemas/
├── raw_source_manifest.schema.json
├── source_evidence_archive.schema.json
├── canonical_lineage_view.schema.json
├── alternate_evidence_view.schema.json
├── typed_artifact_view.schema.json
├── response_bundle_view.schema.json
└── normalized_archive.schema.json

tests/contracts/
├── test_m0_evidence_substrate_contract.py
└── test_m0_response_bundle_atomicity.py
```

`normalized_archive.schema.json` MUST use semantic version:

```text
0.3.0
```

and MUST machine-enforce the R0.1-FREEZE-FIX traceability rules in §15.

This version is mandatory because its role changes from an implicitly evidence-bearing normalized representation to an explicitly derived cross-source projection with mandatory upstream traceability.

---

# 24. Freeze Status

```text
M0 Evidence Substrate Contract R0.1-FREEZE-FIX
PRECISION FIXED / FREEZE CANDIDATE

M0 Evidence Substrate Reopen
APPROVED / ACTIVE

M0 Architecture Decision
APPROVED

SourceEvidenceArchive
APPROVED

RawSourceManifest
APPROVED

CanonicalLineageView
APPROVED

AlternateEvidenceView
APPROVED

TypedArtifactView
APPROVED

ResponseBundle
APPROVED WITH AMBIGUITY CONTRACT

Evidence Conservation Law
FREEZE READY

NormalizedArchive 0.3 semantics
FREEZE READY

M1 Bundle Atomicity Amendment
FREEZE READY

M2 Observable Extension
AUTHORIZED / NOT YET DESIGNED

FormationPath ↔ longitudinal corroboration
OPEN QUESTION

M3–M7
UNCHANGED

Production Implementation
NOT AUTHORIZED
```

---

# 24.1 R0.1 Hardening Closure

R0.1 closed the original H01–H05 hardening findings without changing architecture direction.

---

# 24.2 R0.1-FREEZE-FIX Closure

This precision fix closes exactly four Independent Freeze Audit findings:

```text
FF-01  CLOSED
ChatGPT Mapping Entry Admission Profile v0.1 freezes:
A = every source_native.mapping entry exactly once.

FF-02  CLOSED
CanonicalLineageResolutionStatus and invalid-topology failure semantics are frozen.
Invalid topology cannot produce a fabricated resolved lineage.

FF-03  CLOSED
normalized_archive.schema.json MUST be 0.3.0 and MUST machine-enforce source/lineage/bundle traceability.

FF-04  CLOSED
source_node_id and node_evidence_id have distinct normative semantics.
Bare node_id is forbidden in SEA node schema/normative examples.
```

No architecture direction was changed.

No M3–M7 semantics were reopened.

Production implementation remains NOT AUTHORIZED until an independent freeze audit passes against the contract package, schemas, and tests at one auditable repository SHA.

---

# 25. Final Governing Statement

The M0 Evidence Substrate contract freezes the following separation:

```text
RAW history
    ≠
normalized representation
    ≠
causal interpretation
    ≠
persona
```

Every transition across those boundaries MUST preserve provenance.

> **Evidence Conservation Law**  
> For every source-native evidence object admitted at ingestion, the Evidence Layer MUST preserve it or explicitly account for its exclusion. Silent loss is forbidden.

> **Architecture Rule**  
> Reopen the evidence substrate. Preserve the governance architecture.

---

## Appendix A — Golden Mira Reference Profile

Private fixture identity:

```text
title:
Hi Mira

conversation_id:
6a754a53-82c4-83e8-b9a2-610154053181
```

Golden acceptance counts:

```text
mapping nodes         4059
message nodes         4058

text                  1684
multimodal_text       1365
thoughts               154
reasoning_recap        855

canonical lineage     4026
alternate               33
branch points           10
missing parent           0
```

These values are acceptance anchors for evidence-preservation testing.

They MUST NOT be interpreted as persona, identity, or causal conclusions.

---

## Appendix B — Normative Summary

```text
MUST preserve admitted source-native evidence.
MUST preserve topology.
MUST preserve typed payloads.
MUST preserve timestamps and source identifiers.
MUST preserve alternate branches.
MUST remain deterministic.
MUST remain interpretation-neutral.
MUST preserve complete source payload independently from adapter projection.
MUST represent ResponseBundle ambiguity explicitly.
MUST preserve resolved ResponseBundle atomicity through M1.
MUST preserve provenance across every derived representation.
MUST admit every ChatGPT mapping entry exactly once under the frozen admission profile.
MUST produce deterministic invalid statuses for malformed active-lineage topology.
MUST use normalized_archive.schema.json version 0.3.0 with machine-enforced traceability.
MUST distinguish source_node_id from node_evidence_id.
MUST use RFC 8785 JCS + UTF-8 + SHA-256 for canonical semantic hashes.
MUST use domain-separated deterministic logical IDs.
MUST account exclusions with machine-checkable set invariants.
MUST resolve ChatGPT bundles only under the frozen source-specific profile.
MUST make source_evidence_ref mandatory for every normalized message.
MUST preserve resolved/ambiguous bundle traceability under conditional MUST rules.

MUST NOT silently drop evidence.
MUST NOT reconstruct ChatGPT lineage by mapping order or timestamps.
MUST NOT use opaque metadata refs as topology authority.
MUST NOT flatten typed payloads destructively.
MUST NOT fabricate ResponseBundle associations.
MUST NOT treat normalized representations as source evidence authority.
MUST NOT grant causal, persona, identity, governance, or runtime authority.
```
