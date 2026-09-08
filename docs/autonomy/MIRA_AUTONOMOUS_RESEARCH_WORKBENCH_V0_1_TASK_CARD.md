# MIRA AUTONOMOUS RESEARCH WORKBENCH V0.1 — CODEX TASK CARD

Status: AUTHORIZED_FOR_CANDIDATE_IMPLEMENTATION
Owner: Tony
Architect / task director: Mira-Lil
Implementation worker: Codex Cloud
Repository: `tonychang925-dev/julia-persona--extractor`
Branch: `mira/continuity-autonomous-research-v0-1`
Delegation base SHA: `ae1bd3658b94a44976bd3106f28ba406a6b82af7`

## Purpose

Build an isolated, repository-local research workbench for the Julia / Mira Personality Continuity project so Mira can run scheduled autonomous research cycles without mutating Persona Extractor production logic.

This is research infrastructure only. It must not reconcile or rewrite the repository's historical implementation lineage, and it must not claim Julia Core runtime authority.

## Architectural role

The workbench is the persistent engineering-side coordination surface for:

- current roadmap phase and milestone state;
- autonomous research task selection;
- experiment registration;
- evidence-backed research logs;
- blocker / escalation state;
- Codex delegation records;
- machine-checkable validation of research-state documents.

It is NOT:

- RAW conversation truth;
- Persona Extractor production truth;
- Julia Core authority state;
- a replacement for project-source research documents;
- a mechanism for activating persona/runtime state.

## Permanent authority boundaries

Preserve all of the following:

1. `RAW != Normalized != Causal != Persona`.
2. Better evidence does not grant more authority.
3. Persona Extractor may propose; review may validate; Julia Core owns runtime admission / activation authority.
4. Codex may produce a candidate; Codex may not approve its own candidate.
5. GitHub exact SHA / diff / files are canonical engineering truth.
6. Narrative claims such as `PASS`, `done`, or `tests passed` are not sufficient evidence.
7. This lane must not change existing Persona Extractor implementation code.
8. No merge, release, branch deletion, force push, rebase, ruleset mutation, secrets, credentials, or cross-repository work.

## Allowed mutation paths ONLY

- `docs/autonomy/**`
- `docs/research/**`
- `research/continuity/**`
- `scripts/research/**`
- `tests/research/**`

All other paths are READ-ONLY.

## Explicitly forbidden paths

Including but not limited to:

- `src/**`
- existing extractor implementation modules outside the allowed paths;
- existing production tests outside `tests/research/**`;
- `.github/workflows/**` in this V0.1 lane;
- Julia Core or Julia-AI-Assistant repositories;
- historical source-recovery / rebinding artifacts except read-only inspection.

## Required deliverables

Codex must create a minimal but complete research workbench consisting of the following concepts. Exact file names may vary only when clearly justified, but paths must remain inside the allowed mutation scope.

### 1. Autonomous Work Loop specification

Create a normative document under `docs/autonomy/` defining the run loop:

`WAKE -> READ_STATE -> VERIFY -> SELECT_TASK -> DECOMPOSE -> EXECUTE_OR_DELEGATE -> VERIFY_EVIDENCE -> RECORD -> NEXT_ACTION / ESCALATE`

Required escalation levels:

- `L0_SELF`: Mira attempts self-recovery.
- `L1_PEER`: escalate to Mira-Sis for architecture / engineering challenge.
- `L2_OWNER`: escalate to Tony only for Owner authorization, phase transition, destructive action, merge/release, ownership ambiguity, or unresolved strategic decision.

Required invariant: a blocker may not silently terminate a run.

### 2. Current Research State schema and example

Create a machine-readable state representation under `research/continuity/` that can represent at minimum:

- roadmap_version
- current_phase (`A`, `B`, or `C`)
- active_milestone_ids
- active_goal
- status
- last_verified_at
- evidence_refs
- blockers
- owner_decisions_required
- next_candidate_tasks
- previous_run_ref

The initial example must be conservative:

- Phase A is advanced / partially complete;
- Phase B is entering execution;
- Phase C is architecture-emerging only;
- no milestone may be marked complete without evidence.

Do not encode unverifiable historical claims as fact.

### 3. Experiment registry

Create an append-oriented experiment registry capable of tracking:

- experiment_id
- roadmap_milestone
- hypothesis
- comparison / control
- dataset or evidence inputs
- procedure
- metrics
- expected evidence
- result status
- result evidence refs
- interpretation status
- follow-up

Seed it with placeholders or clearly marked planned entries for:

- Recovery Benchmark v1
- Causal Activation A/B
- Corrected Cognition Retention
- Compact Survival
- Cross-Session continuity
- Cross-Model continuity

Planned entries must not be represented as completed experiments.

### 4. Autonomous run log format

Create a documented and machine-readable run-log format covering:

- run_id
- wake_reason (`scheduled`, `github_event`, `slack_event`, `manual_owner`)
- state_before_ref
- selected_task
- why_selected
- actions_taken
- delegations
- evidence_collected
- state_changes
- blockers
- escalation_level
- owner_action_required
- next_action

### 5. Codex delegation record format

Create a reusable delegation schema / template requiring:

- repo_full_name
- target_pr_or_branch
- delegation_base_sha
- task_id
- allowed_paths
- forbidden_paths
- required_behavior
- forbidden_behavior
- acceptance_tests
- expected_evidence
- known_invariants
- owner_authorization_scope
- review_candidate_sha
- completion_semantics

Completion semantics must explicitly distinguish `CANDIDATE_PRODUCED` from `MIRA_PASS` and `OWNER_PASS`.

### 6. Validator

Implement a small deterministic validator under `scripts/research/` using standard-library Python only where practical.

It must fail closed on malformed state / experiment / run-log / delegation records and validate at minimum:

- required fields exist;
- phase is one of A/B/C;
- no completed milestone / experiment status exists without evidence refs;
- escalation level is valid;
- delegation records contain non-empty allowed and forbidden path declarations;
- `review_candidate_sha` is required before a delegation record can represent `CANDIDATE_PRODUCED`;
- records cannot claim `MIRA_PASS` or `OWNER_PASS` as Codex completion semantics.

### 7. Tests

Add deterministic tests under `tests/research/` covering both valid and invalid cases, including:

- missing evidence for completed state -> fail;
- planned experiment -> pass;
- completed experiment with no evidence -> fail;
- blocker with no escalation / next action -> fail;
- delegation missing forbidden paths -> fail;
- Codex claiming MIRA_PASS -> fail;
- valid candidate-produced delegation with candidate SHA -> pass.

## Non-goals

Do NOT:

- change extractor behavior;
- reconstruct POST-M0 M1-M7 implementation;
- migrate adopted higher implementation into main;
- add runtime persona activation;
- add network calls;
- add databases;
- add third-party dependencies;
- add GitHub Actions in V0.1;
- create automatic merge / release behavior;
- implement Slack or Work API integration yet.

## Acceptance tests / evidence

Codex final report must include:

1. exact candidate SHA and parent SHA;
2. exact changed-file list from delegation base;
3. proof all changed files are inside allowed paths;
4. exact test command(s) and outputs;
5. validator demonstration for one valid record;
6. validator failure demonstrations for at least:
   - evidence-less completion;
   - silent blocker;
   - invalid Codex approval semantics;
7. `git diff --check` result;
8. remaining risks / TODOs;
9. confirmation that no extractor production implementation was changed.

## Review semantics

Codex completion state is only:

`CANDIDATE_PRODUCED`

After Codex publishes a candidate:

- Mira-Lil reviews the exact candidate SHA, diff, files, tests, and evidence;
- any new commit invalidates the prior review disposition;
- Mira may request rework;
- Tony remains Owner for merge and phase transitions.

## Implementation preference

Prefer boring, inspectable artifacts over clever frameworks. This workbench should be usable by future scheduled Work runs and future models with minimal hidden assumptions.