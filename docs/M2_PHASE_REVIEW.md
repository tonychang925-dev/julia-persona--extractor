# M2 Phase Review

Status: phase review

## Purpose

M2 built the Observation Pipeline: a bounded path from Event Segments to reviewed Candidate Experiences without crossing into causal or identity interpretation.

M2 principle:

> Rank evidence for review. Do not interpret evidence.

## Completed stages

```text
M2.0 Observable Signal Detector
↓
M2.1 Signal Fusion Contract
↓
M2.2 Signal Fusion Implementation
↓
M2.3 Candidate Review Queue Contract
↓
M2.4 Candidate Review Queue Implementation
```

## M2 responsibility table

| Stage | Question answered | Explicit non-goal |
| --- | --- | --- |
| Observable Signal | What observable change was detected? | Meaning or identity inference |
| Candidate Experience | Is this region worth further review? | Causal claim |
| Signal Fusion | How strong is the review evidence? | Importance judgment |
| Review Queue | May this candidate enter next analysis? | Identity-forming approval |

## Boundary table

M2 components may:

- detect observable signals;
- aggregate observable signal strength;
- compute review confidence;
- manage workflow state;
- preserve provenance;
- append review history.

M2 components must not:

- approve identity relevance;
- assert causal value;
- infer relationship delta;
- infer behavioral consequence;
- run LLM judgment;
- score personality;
- emit runtime authority.

## Current pipeline

```text
Evidence
↓
Segment
↓
Signal
↓
Candidate
↓
Confidence
↓
Review Gate
↓
Accepted for Next Analysis Stage
```

`accepted_for_extraction` means only:

> This candidate may enter the next analysis stage.

It does not mean:

> This candidate is important, causal, identity-relevant, or runtime-eligible.

## M3 readiness

M3 is the first phase allowed to cross from observation into interpretation.

Before M3 implementation, the project must freeze:

1. Causal Experience design principles.
2. Uncertainty model.
3. Validation boundary.
