# Contributing

Julia Persona Extractor v0.1 is focused on the Data Plane foundation.

## Current priority

M0 — Archive Normalization:

1. preserve raw evidence provenance;
2. normalize archive formats without interpretation;
3. define stable schemas before AI extraction;
4. keep Persona Package output portable.

## Commit convention

Use task-specific commit messages, for example:

- `Initialize persona extractor architecture`
- `Add normalized archive schema`
- `Add ChatGPT archive adapter`
- `Implement first event segmentation prototype`

## Design rule

Extractor output is a reviewable proposal. Julia Core governance decides what can affect runtime identity continuity.
