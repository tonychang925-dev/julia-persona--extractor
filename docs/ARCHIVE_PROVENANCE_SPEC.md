# Archive Provenance Specification

Status: v0.2 architecture-freeze draft

## Purpose

Archive provenance defines how raw historical evidence remains traceable through every downstream extractor artifact.

The extractor may transform structure, but it must preserve lineage.

```text
Raw Source
↓
Normalized Message
↓
Event Segment
↓
Candidate Experience
↓
Causal Experience Node
↓
Persona Package Element
```

## Core rule

Meaning can evolve. Evidence cannot disappear.

Every derived object must retain enough provenance to reconstruct why it exists.

## Provenance levels

### 1. Raw Source Provenance

Identifies the original archive artifact.

Required fields:

- `source_type`
- `source_path` or `source_uri`
- `source_id`
- `ingested_at`
- `content_hash`

### 2. Normalized Message Provenance

Links each normalized message to raw archive location.

Required fields:

- `source_type`
- `source_id`
- `source_path`
- `source_offset`
- `raw_message_id`
- `normalization_adapter`
- `normalization_version`

### 3. Segment Provenance

Links an event segment to the normalized message range or selected message set.

Required fields:

- `segment_id`
- `message_ids`
- `boundary_strategy`
- `boundary_reason`
- `created_at`

### 4. Candidate Experience Provenance

Links a candidate to segment-level evidence.

Required fields:

- `candidate_id`
- `segment_ids`
- `detection_strategy`
- `detection_reason`
- `supporting_message_ids`

### 5. Causal Experience Provenance

Links causal claims to candidate evidence.

Required fields:

- `experience_id`
- `candidate_ids`
- `supporting_message_ids`
- `claim_fields_supported`
- `claim_fields_uncertain`
- `review_status`

### 6. Persona Package Element Provenance

Links exported package elements to experience nodes and graph edges.

Required fields:

- `package_id`
- `element_id`
- `experience_ids`
- `graph_edge_ids`
- `exported_at`
- `generator`

## Non-goals

Provenance does not decide whether a structure is true, stable, or runtime-eligible.

It only answers:

- where did this come from?
- which evidence supports it?
- which transform created it?
- what remains uncertain?
