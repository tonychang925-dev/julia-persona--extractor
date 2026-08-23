"""Segmentation strategy interface.

M1 segmentation is evidence structuring, not semantic extraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Segmenter(ABC):
    """Base interface for event segmentation strategies.

    Implementations produce reproducible event boundaries from a Normalized
    Conversation Archive.

    Not responsible for:
    - semantic interpretation;
    - importance scoring;
    - causal inference;
    - identity or persona judgment.
    """

    @abstractmethod
    def segment(self, archive: dict[str, Any]) -> list[dict[str, Any]]:
        """Return Event Segment schema-compatible dictionaries."""
        raise NotImplementedError
