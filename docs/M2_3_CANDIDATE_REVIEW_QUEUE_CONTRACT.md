# M2.3 Candidate Review Queue Contract

Status: M2.3 scope contract

## Purpose

M2.3 defines workflow governance for Candidate Experiences after Signal Fusion.

Candidate Review Queue decides whether a candidate should enter the next analysis stage.

It does not decide whether a candidate is important, identity-relevant, or causal.

```text
Candidate Experience
+
Signal Fusion Record
↓
Candidate Review Queue
↓
Review Decision Record
```

## Core principle

Review Priority ≠ Identity Importance.

`accepted_for_extraction` means:

> This candidate may enter the next analysis stage.

It does not mean:

> This candidate is identity-forming.

`rejected` means:

> This candidate will not enter the current extraction pipeline.

It does not mean:

> This experience did not happen.

## Review state machine

```text
detected
↓
scored
↓
review_pending
↓        ↓
accepted_for_extraction   rejected
```

## Allowed states

- `detected`
- `scored`
- `review_pending`
- `accepted_for_extraction`
- `rejected`

## Forbidden outputs

Review records must not contain:

- `identity_relevance`
- `causal_value`
- `importance`
- `meaning`
- `identity_change`
- `personality`
- `causal_claim`
- `relationship_delta`
- `behavioral_consequence`
- `runtime_eligibility`
- `activation_weight`
- `governance_status`

## Completion criteria

1. Candidate Review Record schema exists.
2. Review state machine is explicit.
3. Review record references candidate and optional fusion record.
4. Review record preserves provenance.
5. Contract tests prevent causal, identity, importance, and runtime authority fields.
