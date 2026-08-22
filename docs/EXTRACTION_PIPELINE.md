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

## Stage contracts

### Archive Normalization

Converts source-specific exports into `NormalizedConversationArchive`.

Must preserve:

- source format;
- source conversation identifiers;
- message identifiers where available;
- timestamps where available;
- participant roles;
- content;
- provenance path.

Must not produce:

- identity claims;
- causal claims;
- density scores.

### Event Segmentation

Groups normalized messages into event candidates using boundaries such as topic shift, temporal gap, decision moment, emotional transition, or explicit task completion.

### Candidate Experience Detection

Identifies segments that may contain durable persona-forming evidence.

### Causal Experience Extraction

Builds `CausalExperienceNode` candidates with trigger, response, transition, relationship delta, behavioral consequence, activation conditions, and provenance.

### Density Scoring

Ranks candidates by evidence coverage, repetition, causal clarity, and downstream behavioral consequence.

### Human Review Preparation

Packages claims for review before runtime eligibility decisions.

### Persona Package Generation

Exports reviewed structures into a portable package format.
