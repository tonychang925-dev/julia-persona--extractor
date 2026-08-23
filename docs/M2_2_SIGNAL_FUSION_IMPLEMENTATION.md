# M2.2 Signal Fusion Implementation

Status: M2.2 implementation scope

## Purpose

M2.2 implements deterministic Signal Fusion for Candidate Experiences.

It produces review confidence records only.

```text
Candidate Experience
↓
SignalFusion
↓
Signal Fusion Record
```

## Implemented methods

- `weighted_observable_signal_average`
- `max_signal_strength`

## Boundary

M2.2 may compute:

- signal count factor;
- mean signal strength;
- max signal strength;
- provenance quality;
- source segment coverage;
- confidence score for review prioritization.

M2.2 must not compute:

- importance;
- identity relevance;
- causal claim;
- relationship delta;
- behavioral consequence;
- runtime eligibility;
- governance status.

## Principle

Rank evidence for review. Do not interpret evidence.
