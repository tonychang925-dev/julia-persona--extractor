# M3 Validation Boundary

Status: design preparation

## Purpose

M3 validation boundary defines who may propose, review, validate, or activate Causal Experience structures.

## Authority split

### Extractor may propose

Extractor may create:

- causal experience proposal;
- observed event structure;
- interpretation draft;
- uncertainty model;
- alternative explanations;
- provenance references.

### Review layer may validate

Review layer may decide:

- evidence sufficient for validation;
- interpretation needs revision;
- proposal should be rejected;
- proposal should remain pending.

### Julia Core may grant runtime authority

Julia Core Control Plane may decide:

- runtime eligibility;
- activation weight;
- governance status;
- lifecycle transition into active runtime use.

## Forbidden M3 extractor fields

M3 extractor output must not contain:

- `runtime_eligibility`
- `activation_weight`
- `governance_status`
- `active_runtime_scope`
- `identity_authority_granted`

## M3 lifecycle proposal states

Allowed extractor-side states:

- `proposed`
- `needs_review`
- `revision_required`

Validation-side states:

- `validated`
- `rejected`
- `challenged`

Runtime-side states:

- `installed`
- `active`
- `deprecated`

## Required handoff

A Causal Experience proposal entering validation must include:

- accepted candidate review record;
- signal fusion record;
- source candidate;
- event segments;
- message/archive provenance;
- observed event;
- interpretation;
- uncertainty;
- alternative explanations.
