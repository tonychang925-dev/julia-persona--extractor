# M2.0 Observable Signal Detector

Status: M2.0 implementation scope

## Purpose

M2.0 implements rule-based observable signal detection over Event Segments.

It turns evidence containers into Candidate Experiences when observable, non-semantic signals are present.

```text
Event Segment Collection
↓
Observable Signal Detector
↓
Candidate Experience Collection
```

## Boundary

M2.0 may detect:

- repeated references;
- time gap proximity;
- manual review markers;
- simple conversation length change.

M2.0 must not detect:

- identity change;
- personality traits;
- causal claims;
- relationship deltas;
- behavioral consequences;
- runtime eligibility.

## Principle

Candidate Before Causality.

The detector may say:

> This region has observable signals and may be worth review.

It must not say:

> This region means a persona changed.

## First implementation

The first implementation is deterministic and rule-based:

- `RepeatedReferenceDetector`
- `ManualReviewMarkerDetector`
- `CandidateExperienceDetector`

LLM-based detection is out of scope for M2.0.
