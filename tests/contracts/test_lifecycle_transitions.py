from __future__ import annotations

VALID_TRANSITIONS = {
    None: {"created"},
    "created": {"extracted"},
    "extracted": {"review_pending"},
    "review_pending": {"validated", "challenged", "deprecated"},
    "validated": {"installed", "challenged", "deprecated"},
    "installed": {"active", "challenged", "deprecated"},
    "active": {"challenged", "deprecated"},
    "challenged": {"validated", "deprecated"},
    "deprecated": set(),
}


def is_valid_transition(source: str | None, target: str) -> bool:
    return target in VALID_TRANSITIONS[source]


def test_created_cannot_jump_to_active():
    assert not is_valid_transition("created", "active")


def test_review_path_to_active_is_valid():
    path = [
        (None, "created"),
        ("created", "extracted"),
        ("extracted", "review_pending"),
        ("review_pending", "validated"),
        ("validated", "installed"),
        ("installed", "active"),
    ]
    assert all(is_valid_transition(source, target) for source, target in path)
