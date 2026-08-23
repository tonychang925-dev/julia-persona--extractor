"""Candidate review state machine for M2.4."""

from __future__ import annotations

ALLOWED_TRANSITIONS: dict[str | None, set[str]] = {
    None: {"detected"},
    "detected": {"scored"},
    "scored": {"review_pending"},
    "review_pending": {"accepted_for_extraction", "rejected"},
    "accepted_for_extraction": set(),
    "rejected": set(),
}

REVIEW_STATES = {
    "detected",
    "scored",
    "review_pending",
    "accepted_for_extraction",
    "rejected",
}


def is_valid_transition(source: str | None, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS[source]


def assert_valid_transition(source: str | None, target: str) -> None:
    if source not in ALLOWED_TRANSITIONS:
        raise ValueError(f"unknown source review state: {source}")
    if target not in REVIEW_STATES:
        raise ValueError(f"unknown target review state: {target}")
    if not is_valid_transition(source, target):
        raise ValueError(f"invalid review transition: {source} -> {target}")
