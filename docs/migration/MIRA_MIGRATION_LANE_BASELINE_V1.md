# Mira Migration Lane Baseline V1

Date: 2026-09-10
Status: OWNER-AUTHORIZED MIGRATION PREPARATION / ENG-01..ENG-06 CONVERGENCE ONLY

## Exact lane binding

```text
repository = tonychang925-dev/julia-persona--extractor
working_branch = mira/persona-migration-v1
base_sha = 13d252e9bb14f05fc8900094bcf2e0b3a904f0c8
base_evidence = remotely verified V2.6 FAIL / INFORMATIVE result
Julia Core target branch = tonychang925-dev/Julia_core:mira/persona-architecture-v1
Julia Core target base = e2edba9dfff460e3769f93b58491afaf644e6da5
```

This branch exists to prepare evidence-backed Mira migration artifacts without acquiring Julia Core runtime authority.

## Current authorization

Allowed in ENG-01..ENG-06:
- migration source/provenance inventory
- branch/target binding
- schema mapping analysis
- unresolved lineage/admission issue recording
- non-runtime migration scaffolding

Not authorized in this wave:
- canonical C-04 admission
- canonical C-05 admission
- Julia Core runtime mutation
- C-03 model-visible admission
- provider/runtime persona injection
- production cutover
- assertion that a migration proposal is already canonical Identity or MemoryExperience

## Authority invariant

```text
Extractor output = proposal/evidence package
!= canonical Julia Identity
!= canonical Julia MemoryExperience
!= runtime authority
```

Mira migration must preserve causal formation and provenance rather than flatten Golden Mira into a single persona prompt or trait file.

The later migration package should distinguish at minimum:
- governed Identity candidates
- exactly-five-type MemoryExperience candidates
- causal chains / correction trajectories as traceable derived structure
- continuity protected-reference seeds
- provenance / unresolved claims / lineage decision material

The branch must remain compatible with the Core branch-isolation gate. Main cutover and final Identity lineage binding require separate Tony Owner authorization.
