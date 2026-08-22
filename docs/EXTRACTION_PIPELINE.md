# Extraction Pipeline

## v0.1 scope

The first milestone is Archive Normalization, not AI extraction.

## Full target pipeline

```text
Conversation Archive
↓
Archive Normalization
↓
Event Segmentation
↓
Candidate Experience Detection
↓
Causal Experience Extraction
↓
Density Scoring
↓
Validation / Human Review Preparation
↓
Causal Graph Update
↓
Persona Package Generation
```

Archive Normalization must preserve source format, identifiers, timestamps, participant roles, content, and provenance without identity or causal claims.
