# M3 Causal Experience Design Principles

Status: design preparation

## Purpose

M3 defines how an accepted Candidate Experience may become a proposed Causal Experience Node.

M3 is the first phase that may produce interpretation.

Because of that, M3 must be stricter than M1/M2.

## Core principle

Interpretation must sit on top of preserved observation.

```text
Observed Event
↓
Causal Interpretation
↓
Uncertainty
↓
Validation
```

## Reality Before Interpretation

M3 must preserve the separation between:

```json
{
  "observed_event": {},
  "interpretation": {},
  "confidence": {},
  "uncertainty": {},
  "validation": {}
}
```

M3 must not collapse evidence and meaning into:

```json
{
  "event_meaning": "..."
}
```

## Candidate Before Causality

Only candidates that passed the M2 review workflow may enter M3.

Allowed input state:

```text
accepted_for_extraction
```

A high review confidence score is not sufficient by itself.

## Extractor is proposal, not authority

M3 extractor may propose:

- possible causal claim;
- possible trigger;
- possible response;
- possible transition;
- possible consequence;
- uncertainty and alternatives.

M3 extractor must not grant:

- validation;
- runtime eligibility;
- identity authority;
- activation weight;
- governance status.

## Causal Experience proposal boundary

A Causal Experience proposal should answer:

- what was observed?
- what interpretation is proposed?
- which evidence supports the proposal?
- what alternatives remain possible?
- what confidence is claimed and why?
- what validation is required?

It should not answer:

- should this enter runtime?
- is this permanently part of persona?
- does this define identity?

## Required M3 guardrails

Before implementation, M3 must define:

1. causal experience schema update;
2. uncertainty model;
3. alternative explanation structure;
4. validation boundary;
5. contract tests preventing runtime authority fields.
