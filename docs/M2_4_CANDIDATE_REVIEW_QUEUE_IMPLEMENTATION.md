# M2.4 Candidate Review Queue Implementation

Status: M2.4 implementation scope

## Purpose

M2.4 implements Candidate Review Queue workflow state transitions.

It is a workflow state machine, not a causal or identity judge.

```text
Candidate Review Record
↓
Transition Validation
↓
Updated Review Record
```

## Boundary

M2.4 may:

- validate review state transitions;
- append transition history;
- preserve candidate, fusion, and provenance references;
- move records through the review workflow.

M2.4 must not:

- auto-approve identity relevance;
- auto-reject causal value;
- run LLM judging;
- score personality;
- emit runtime authority.

## Allowed transitions

```text
detected → scored
scored → review_pending
review_pending → accepted_for_extraction
review_pending → rejected
```

## Principle

Workflow gate, not meaning gate.
