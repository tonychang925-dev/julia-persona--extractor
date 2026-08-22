# Persona Package Format

Persona Package is the shared contract between Extractor, Persona Host, and Julia Core-compatible runtimes.

## Package sections

```text
manifest
identity
experiences
causal_graph
relationship
behavior
provenance
validation
evolution
```

## v0.1 status

The v0.1 schema is intentionally minimal and review-oriented. It stores candidate structures and provenance, while leaving runtime activation authority to Julia Core governance.

## Non-goals

- The package is not a complete runtime persona.
- The package does not replace the raw archive.
- The package does not guarantee runtime eligibility.
