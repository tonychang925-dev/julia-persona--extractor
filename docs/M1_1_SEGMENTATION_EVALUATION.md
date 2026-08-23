# M1.1 Segmentation Evaluation

Status: M1.1 scope contract

## Purpose

M1.1 evaluates whether Event Segment output is reliable enough to feed Candidate Experience Detection.

It measures container quality only. It does not interpret segment meaning.

```text
Event Segment Collection
↓
Segmentation Evaluation
↓
Segmentation Metrics Report
```

## Metrics

### Coverage

Measures whether every archive message is represented exactly once.

Fields:

- `total_messages`
- `segmented_messages`
- `unsegmented_messages`
- `duplicate_messages`
- `coverage_ratio`

### Boundary Stability

Measures whether deterministic strategies produce identical segment boundaries for the same archive and parameters.

Fields:

- `deterministic`
- `stable`
- `signature`

### Segment Size Distribution

Measures segment container size shape.

Fields:

- `count`
- `min`
- `max`
- `mean`
- `median`
- `p95`

### Provenance Completeness

Measures whether each segment links back to archive/message provenance.

Fields:

- `segments_with_provenance`
- `segments_missing_provenance`
- `complete`

### Segmentation Neutrality

Verifies the evaluator and segmenter do not emit semantic or persona claims.

Forbidden fields:

- `meaning`
- `impact`
- `identity_change`
- `personality`
- `runtime_eligibility`
- `activation_weight`
- `governance_status`
- `causal_claim`

## Non-goals

M1.1 must not produce:

- candidate experience detection;
- causal extraction;
- identity judgment;
- persona package generation;
- runtime authority.
