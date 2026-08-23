# M2.1 Signal Fusion Contract

Status: M2.1 scope contract

## Purpose

M2.1 defines how multiple observable detection signals may be combined into a traceable candidate confidence record.

Signal Fusion is not causal interpretation.

It only answers:

> How strongly do observable signals support reviewing this candidate?

```text
Candidate Experience
↓
Signal Fusion
↓
Candidate Confidence Record
```

## Boundary

M2.1 may combine:

- signal count;
- signal strength;
- signal consistency;
- provenance quality;
- source segment coverage.

M2.1 must not output:

- importance;
- identity relevance;
- causal claim;
- relationship delta;
- behavioral consequence;
- runtime eligibility;
- governance status.

## Output shape

```json
{
  "fusion_id": "",
  "candidate_id": "",
  "signals": [],
  "fusion_method": "",
  "confidence": {},
  "provenance_refs": [],
  "created_by": {}
}
```

## Allowed basis factors

- `signal_count`
- `signal_strength`
- `signal_consistency`
- `provenance_quality`
- `source_segment_coverage`

## Non-goals

M2.1 does not decide whether a candidate is important.

M2.1 does not decide whether a candidate is identity-relevant.

M2.1 does not create Causal Experience Nodes.

## Completion criteria

1. Signal Fusion schema exists.
2. Fusion references a Candidate Experience.
3. Fusion references original detection signals.
4. Fusion preserves candidate provenance.
5. Contract tests prevent importance, identity, causal, and runtime authority fields.
