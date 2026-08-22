from __future__ import annotations

from typing import Any


def normalize_claude_conversation(raw: dict[str, Any], source_path: str | None = None) -> dict[str, Any]:
    raise NotImplementedError("Claude normalization contract reserved for M0 follow-up.")
