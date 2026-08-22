# Persona Package Lifecycle Specification

Status: v0.2 architecture-freeze draft

## Purpose

Persona Package lifecycle states define how extracted structures move from evidence-backed proposals to runtime-eligible material.

The extractor may create reviewable packages. It does not grant runtime authority.

## Lifecycle states

```text
created
↓
extracted
↓
review_pending
↓
validated
↓
installed
↓
active
↓
challenged
↓
deprecated
```

## State definitions

### created

The package container exists, but may not yet contain completed extraction output.

### extracted

The extractor has generated candidate experiences, graph structures, and provenance references.

### review_pending

The package is ready for human or governance review.

### validated

A review process has accepted the package or selected package elements as sufficiently evidence-backed.

### installed

Persona Host has installed the package into a managed environment.

### active

Julia Core or another compatible Control Plane has granted runtime eligibility to selected package elements.

### challenged

A package element has conflicting evidence, changed context, failed benchmark behavior, or governance concern.

### deprecated

A package element is no longer eligible for runtime influence, but remains preserved as historical evidence.

## Deletion rule

Deprecated material should not be deleted by default.

A deprecated formation path may still explain historical behavior, prior runtime state, or later correction.

## Authority boundary

Extractor can set:

- `created`
- `extracted`
- `review_pending`

Human review / governance can set:

- `validated`
- `challenged`
- `deprecated`

Persona Host can set:

- `installed`

Julia Core Control Plane can set:

- `active`
- runtime-specific `challenged`
- runtime-specific `deprecated`

## Required lifecycle metadata

Each lifecycle transition should record:

- `from_status`
- `to_status`
- `actor`
- `timestamp`
- `reason`
- `evidence_refs`
