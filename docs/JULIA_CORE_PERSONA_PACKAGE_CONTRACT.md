# Julia Core Persona Package Contract

Status: v0.2 architecture-freeze draft

## Purpose

This contract defines the boundary between Julia Persona Extractor and Julia Core.

The extractor constructs evidence-backed continuity representations. Julia Core decides which structures may influence runtime judgment.

## Boundary summary

```text
Extractor Data Plane
  writes evidence-backed proposals

Julia Core Control Plane
  grants or denies runtime authority
```

Extractor says:

> I found evidence that this may be important.

Julia Core says:

> This structure has or has not earned long-term runtime influence.

## Extractor-owned fields

Extractor may write:

```json
{
  "manifest": {},
  "experiences": [],
  "causal_graph": {},
  "provenance": {},
  "validation": {
    "extractor_status": "review_pending"
  },
  "evolution": {
    "package_lifecycle_status": "extracted"
  }
}
```

Extractor-owned responsibilities:

- archive normalization;
- event segmentation;
- candidate experience detection;
- causal experience candidate generation;
- density scoring;
- provenance export;
- review queue preparation;
- package generation.

## Core-owned fields

Julia Core may write or approve:

```json
{
  "runtime_eligibility": true,
  "activation_weight": {},
  "governance_status": "active",
  "runtime_scope": {},
  "challenge_state": {},
  "deprecation_reason": null
}
```

Core-owned responsibilities:

- runtime eligibility;
- activation policy;
- continuity contract enforcement;
- conflict resolution;
- governance status;
- runtime lifecycle transitions.

## Forbidden coupling

Extractor must not assume that extracted means active.

Persona Host must not activate package elements without Control Plane approval.

Julia Core must not require access to the full raw archive at runtime when package provenance is sufficient for traceable review.

## Review handoff

A Persona Package handed to Julia Core should include:

- package manifest;
- candidate or validated causal experience nodes;
- causal graph;
- provenance lineage;
- density scores with factor breakdown;
- uncertainty markers;
- review status;
- lifecycle history.
