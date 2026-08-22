"""Archive loading entry points."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def load_json(path: str | Path) -> Any:
    """Load a UTF-8 JSON archive from disk."""
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)
