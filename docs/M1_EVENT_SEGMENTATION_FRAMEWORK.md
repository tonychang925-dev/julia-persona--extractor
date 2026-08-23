# M1 Event Segmentation Framework

Status: M1 scope contract

## Purpose

M1 converts a `Normalized Conversation Archive v0.2` into an `Event Segment Collection`.

M1 is evidence structuring, not semantic extraction.

```text
Normalized Conversation Archive
↓
Segmentation Framework
↓
Event Segment Collection
```

## Goal

Create reproducible message boundaries while preserving archive and message provenance.

M1 answers:

- where does a candidate event segment start?
- where does it end?
- which messages belong to it?
- which boundary strategy produced it?
- why was this boundary emitted?

M1 does not answer:

- what does this mean?
- did identity change?
- is this important?
- should this influence runtime?

## Non-goals

M1 must not produce:

- causal extraction;
- personality inference;
- identity judgment;
- persona generation;
- runtime eligibility;
- activation weights;
- governance status.

## Segmenter strategy interface

The framework should support multiple segmentation strategies:

```text
TurnWindowSegmenter
SemanticBoundarySegmenter
TopicTransitionSegmenter
LongitudinalExperienceSegmenter
```

Only `TurnWindowSegmenter` is expected in the first M1 implementation.

The names of future semantic strategies are reserved, but M1 must not implement causal or identity interpretation.

## Input contract

Input must conform to:

```text
schemas/normalized_archive.schema.json
```

Required source guarantees:

- archive identity exists;
- message IDs exist;
- message-level provenance exists;
- immutable refs exist.

## Output contract

Output must conform to:

```text
schemas/event_segment.schema.json
```

Each segment must contain:

- `segment_id`;
- `archive_id`;
- `message_refs`;
- `start_message_id`;
- `end_message_id`;
- `boundary`;
- `provenance_refs`;
- `created_by`.

## Forbidden output fields

Event segments must not contain:

- `meaning`;
- `impact`;
- `identity_change`;
- `personality`;
- `runtime_eligibility`;
- `activation_weight`;
- `governance_status`.

## Completion criteria

M1 is complete when:

1. Event Segment schema exists.
2. Segmentation framework emits schema-compatible segments.
3. Segment provenance is preserved.
4. Boundaries are reproducible for deterministic strategies.
5. Contract tests prevent semantic claims and persona fields.
