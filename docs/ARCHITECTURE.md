# Architecture

Julia Persona Extractor is the Data Plane for evidence-backed persona continuity representation.

## Frozen boundary for v0.1

```text
Raw Conversation Archive
        ↓
Evidence Layer
        ↓
Normalized Conversation Archive
        ↓
Extractor Data Plane
        ↓
Reviewable Persona Package
        ↓
Julia Core Control Plane
```

## 1. Evidence Layer

Responsibility: preserve what happened.

Input:

- Raw Conversation Archive

Output:

- Normalized Conversation Archive

Rules:

- no identity interpretation;
- no causal claims;
- all normalized messages retain provenance;
- evidence may be reinterpreted later, but must not disappear.

## 2. Extractor Data Plane

Responsibility: discover structure from historical evidence.

Pipeline:

```text
Normalized Archive
↓
Event Segmentation
↓
Candidate Experience Detection
↓
Causal Experience Extraction
↓
Density Scoring
↓
Human Review Preparation
↓
Persona Package Generation
```

The extractor produces candidate continuity structures. It does not grant runtime authority.

## 3. Julia Core Control Plane

Responsibility: decide which structures may enter runtime and influence future judgment.

Control Plane concerns:

- validation contract;
- runtime eligibility;
- governance;
- continuity benchmark;
- lifecycle state.

## 4. Deployment Plane

Persona Host remains a separate system responsible for:

- install;
- activation;
- versioning;
- rollback;
- lifecycle management.
