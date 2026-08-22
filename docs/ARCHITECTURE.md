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

## Evidence Layer

Preserve what happened. Input: Raw Conversation Archive. Output: Normalized Conversation Archive. No interpretation.

## Extractor Data Plane

Discover structure from history:

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

## Julia Core Control Plane

Decides which reviewed structures may enter Runtime and influence future judgment.

## Persona Host Deployment Plane

Handles install, activation, versioning, rollback, and lifecycle.
