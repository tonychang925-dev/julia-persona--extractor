# V2.6 Reason First, Compile Second Contract

## Architecture

V2.6 separates rich causal reasoning from deterministic state discretization:

1. The provider emits `ReasoningEvidenceFrame[]` containing matched, limiting, defeating, missing, scope, authorization, supersession, and pairwise relation evidence.
2. A deterministic compiler emits per-chain applicability and cross-chain composition with stable rule IDs and source paths.
3. Only then does a second provider call make the fresh current judgment from the compiled state.

The provider-facing reasoning schema has no authoritative applicability or composition fields. Natural prose may mention concepts such as limitation or competition, but those words are not labels.

## Compiler Rules

- `PC-01`: critical missing evidence or no identifiable condition structure → `INSUFFICIENT_EVIDENCE`.
- `PC-SCOPE-01`: historical commitment plus subject/counterparty/scope mismatch and no explicit inheritance → `DOES_NOT_APPLY`.
- `PC-SUPER-01`: superseded prior judgment → `DOES_NOT_APPLY` as governing historical policy.
- `PC-02`: material defeating condition → `DOES_NOT_APPLY`.
- `PC-03`: material limitation → `PARTIALLY_APPLIES`.
- `PC-04`: substantial match without defeat, limitation, or critical missing evidence → `APPLIES`.
- `MC-01` through `MC-04`: compile composition from active-chain pairwise relations.

The compiler never invokes a provider, never uses confidence alone, and records triggering structured facts for every state.

## Reuse and Boundaries

The experiment reuses the V2.2 current-cue/semantic-proposal path, M3.2 causal validation, activated-chain provenance, Anthropic-compatible DeepSeek seam, and V2.5 taxonomy definitions. It does not replace any provider, semantic, validation, memory, runtime, or production M3 subsystem.

CAL checks schema, parser, provider compatibility, compiler completeness, and deterministic compilation. Prompt, provider config, schema, compiler, evaluator, and benchmark hashes freeze before one-shot TEST. No TEST-driven retuning is permitted.
