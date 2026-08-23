# M1.5 Candidate Experience Detection Contract

Status: M1.5 scope contract

## Purpose

M1.5 defines how Event Segments become Candidate Experiences for later analysis.

A Candidate Experience is not a causal interpretation.

It only means:

> This evidence region may be worth further review.

```text
Event Segment Collection
↓
Candidate Experience Detection
↓
Candidate Experience Collection
```

## Boundary

M1.5 answers:

- which segment or segment group should be reviewed later?
- which non-semantic signals triggered detection?
- how confident is the detector that this region is worth review?
- which evidence supports the candidate container?

M1.5 does not answer:

- what does this mean?
- did identity change?
- what personality trait exists?
- what causal experience formed?
- should this affect runtime?

## Output shape

A Candidate Experience should contain:

```json
{
  "candidate_id": "",
  "source_segments": [],
  "detection_signals": [],
  "confidence": {},
  "provenance_refs": [],
  "created_by": {}
}
```

## Allowed detection signals

Detection signals describe observable patterns, not meaning.

Allowed signal families:

- `conversation_length_change`
- `topic_transition`
- `emotional_intensity_change`
- `response_pattern_shift`
- `repeated_reference`
- `time_gap_proximity`
- `manual_review_marker`

## Forbidden fields and claims

Candidate Experiences must not contain:

- `meaning`
- `impact`
- `identity_change`
- `personality`
- `causal_claim`
- `relationship_delta`
- `behavioral_consequence`
- `runtime_eligibility`
- `activation_weight`
- `governance_status`

## Completion criteria

M1.5 is complete when:

1. Candidate Experience schema exists.
2. Candidate output references Event Segments, not raw free-floating claims.
3. Detection signals are observable and non-semantic.
4. Provenance is preserved from candidate to segment/message/archive.
5. Contract tests prevent causal, identity, persona, and runtime authority fields.
