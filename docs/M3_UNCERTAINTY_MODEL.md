# M3 Uncertainty Model

Status: design preparation

## Purpose

M3 uncertainty model prevents causal interpretation from sounding more certain than the evidence allows.

## Required uncertainty fields

A Causal Experience proposal should include:

```json
{
  "uncertainty": {
    "evidence_strength": 0.0,
    "interpretation_confidence": 0.0,
    "alternative_explanations": [],
    "uncertainty_scope": [],
    "requires_review": true
  }
}
```

## Field definitions

### evidence_strength

How much direct evidence supports the observed event structure.

This is not causal confidence.

### interpretation_confidence

How strongly the extractor believes the proposed causal interpretation follows from the observed event.

This must be lower when alternatives exist.

### alternative_explanations

Other plausible interpretations of the same evidence.

Every proposed Causal Experience should allow alternatives.

### uncertainty_scope

The parts of the proposal that remain uncertain.

Examples:

- `trigger`
- `response`
- `transition`
- `relationship_delta`
- `behavioral_consequence`
- `activation_conditions`

### requires_review

Whether human or governance review is required before validation.

Default should be true.

## Confidence rule

A numeric confidence score must always have a documented basis.

Forbidden:

```json
{
  "confidence": 0.95
}
```

Required:

```json
{
  "confidence": {
    "score": 0.62,
    "basis": ["evidence_strength", "candidate_review", "alternative_explanations"],
    "limitations": []
  }
}
