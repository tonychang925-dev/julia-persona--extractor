"""Candidate Review Queue implementation.

This module manages workflow state only. It does not perform causal
interpretation, identity relevance judgment, personality scoring, or runtime
authority decisions.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from persona_extractor.review.state_machine import assert_valid_transition

FORBIDDEN_REVIEW_FIELDS = {
    "identity_relevance",
    "causal_value",
    "importance",
    "meaning",
    "identity_change",
    "personality",
    "causal_claim",
    "relationship_delta",
    "behavioral_consequence",
    "runtime_eligibility",
    "activation_weight",
    "governance_status",
}


class CandidateReviewQueue:
    """Create and transition Candidate Review Records."""

    component = "CandidateReviewQueue"
    version = "0.1.0"

    def create_record(
        self,
        candidate: dict[str, Any],
        fusion: dict[str, Any] | None = None,
        state: str = "detected",
        reason: str = "candidate detected",
        actor: str | None = None,
    ) -> dict[str, Any]:
        assert_valid_transition(None, state)
        record = {
            "schema_version": "0.2.0",
            "review_id": candidate["candidate_id"].replace("candidate", "review", 1),
            "candidate_id": candidate["candidate_id"],
            "fusion_id": fusion["fusion_id"] if fusion else None,
            "review_state": state,
            "decision_reason": reason,
            "provenance_refs": list(candidate["provenance_refs"]),
            "history": [
                self._transition(
                    source=None,
                    target=state,
                    actor=actor or self.component,
                    reason=reason,
                    provenance_refs=candidate["provenance_refs"],
                )
            ],
            "created_by": {"component": self.component, "version": self.version},
        }
        self._assert_no_forbidden_fields(record)
        return record

    def transition(
        self,
        record: dict[str, Any],
        target_state: str,
        reason: str,
        actor: str | None = None,
    ) -> dict[str, Any]:
        source_state = record["review_state"]
        assert_valid_transition(source_state, target_state)
        updated = deepcopy(record)
        updated["review_state"] = target_state
        updated["decision_reason"] = reason
        updated["history"].append(
            self._transition(
                source=source_state,
                target=target_state,
                actor=actor or self.component,
                reason=reason,
                provenance_refs=updated["provenance_refs"],
            )
        )
        self._assert_no_forbidden_fields(updated)
        return updated

    @staticmethod
    def _transition(
        source: str | None,
        target: str,
        actor: str,
        reason: str,
        provenance_refs: list[str],
    ) -> dict[str, Any]:
        return {
            "from": source,
            "to": target,
            "actor": actor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "provenance_refs": list(provenance_refs),
        }

    @staticmethod
    def _assert_no_forbidden_fields(record: dict[str, Any]) -> None:
        forbidden = FORBIDDEN_REVIEW_FIELDS.intersection(record.keys())
        if forbidden:
            raise AssertionError(f"review record emitted forbidden fields: {sorted(forbidden)}")
